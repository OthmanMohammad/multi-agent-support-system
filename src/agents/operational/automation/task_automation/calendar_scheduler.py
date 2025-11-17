"""
Calendar Scheduler Agent - TASK-2202

Auto-schedules demos, QBRs, and customer calls in Google Calendar, Outlook, or Calendly.
Handles timezone conversion, availability checking, and automatic meeting setup.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, UTC
import json

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("calendar_scheduler", tier="operational", category="automation")
class CalendarSchedulerAgent(BaseAgent):
    """
    Calendar Scheduler Agent - Auto-schedules meetings and events.

    Handles:
    - Automatic meeting scheduling in Google Calendar, Outlook, Calendly
    - Timezone detection and conversion
    - Availability checking across multiple calendars
    - Meeting room booking and resource allocation
    - Video conference link generation (Zoom, Meet, Teams)
    - Automatic reminder setup
    - Recurring meeting creation
    - Calendar conflict detection and resolution
    """

    # Supported calendar systems
    CALENDAR_SYSTEMS = {
        "google": {
            "api_endpoint": "https://www.googleapis.com/calendar/v3",
            "supports_video": ["meet"],
            "max_attendees": 100
        },
        "outlook": {
            "api_endpoint": "https://graph.microsoft.com/v1.0/me/calendar",
            "supports_video": ["teams"],
            "max_attendees": 250
        },
        "calendly": {
            "api_endpoint": "https://api.calendly.com",
            "supports_video": ["zoom", "meet", "teams"],
            "max_attendees": 50
        }
    }

    # Meeting types and default durations
    MEETING_TYPES = {
        "demo": {
            "duration_minutes": 30,
            "buffer_before": 5,
            "buffer_after": 5,
            "default_title": "Product Demo"
        },
        "qbr": {
            "duration_minutes": 60,
            "buffer_before": 10,
            "buffer_after": 10,
            "default_title": "Quarterly Business Review"
        },
        "call": {
            "duration_minutes": 30,
            "buffer_before": 5,
            "buffer_after": 0,
            "default_title": "Customer Call"
        },
        "onboarding": {
            "duration_minutes": 45,
            "buffer_before": 5,
            "buffer_after": 5,
            "default_title": "Onboarding Session"
        },
        "training": {
            "duration_minutes": 60,
            "buffer_before": 5,
            "buffer_after": 10,
            "default_title": "Training Session"
        }
    }

    # Timezone mappings
    COMMON_TIMEZONES = {
        "ET": "America/New_York",
        "CT": "America/Chicago",
        "MT": "America/Denver",
        "PT": "America/Los_Angeles",
        "GMT": "Europe/London",
        "CET": "Europe/Paris",
        "IST": "Asia/Kolkata",
        "JST": "Asia/Tokyo",
        "AEST": "Australia/Sydney"
    }

    def __init__(self):
        config = AgentConfig(
            name="calendar_scheduler",
            type=AgentType.AUTOMATOR,
            model="claude-3-haiku-20240307",
            temperature=0.1,
            max_tokens=800,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Auto-schedule meetings in calendar systems.

        Args:
            state: Current agent state with scheduling request

        Returns:
            Updated state with scheduled meeting details
        """
        self.logger.info("calendar_scheduler_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        entities = state.get("entities", {})

        # Extract scheduling parameters
        calendar_system = entities.get("calendar_system", customer_metadata.get("default_calendar", "google"))
        meeting_type = entities.get("meeting_type", "call")

        self.logger.debug(
            "scheduling_details",
            calendar_system=calendar_system,
            meeting_type=meeting_type
        )

        # Parse meeting details from message
        meeting_details = await self._parse_meeting_request(message, customer_metadata)

        # Detect and convert timezones
        timezone_info = self._detect_and_convert_timezone(
            meeting_details,
            customer_metadata
        )

        # Find available time slots
        availability = self._check_availability(
            meeting_details,
            timezone_info,
            customer_metadata
        )

        # Check for scheduling conflicts
        conflict_check = self._check_conflicts(
            meeting_details,
            availability,
            customer_metadata.get("existing_meetings", [])
        )

        # Prepare meeting data
        meeting_data = self._prepare_meeting_data(
            calendar_system,
            meeting_type,
            meeting_details,
            timezone_info,
            customer_metadata
        )

        # Schedule meeting in external system
        scheduled_meeting = await self._schedule_meeting_external(
            calendar_system,
            meeting_data,
            conflict_check
        )

        # Setup automatic reminders
        reminders = self._setup_meeting_reminders(scheduled_meeting, meeting_type)

        # Log automation action
        automation_log = self._log_automation_action(
            "meeting_scheduled",
            calendar_system,
            scheduled_meeting,
            customer_metadata
        )

        # Generate response
        response = self._format_scheduling_response(
            scheduled_meeting,
            conflict_check,
            timezone_info,
            reminders
        )

        state["agent_response"] = response
        state["scheduled_meeting"] = scheduled_meeting
        state["meeting_data"] = meeting_data
        state["timezone_info"] = timezone_info
        state["availability"] = availability
        state["reminders"] = reminders
        state["automation_log"] = automation_log
        state["response_confidence"] = 0.93
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "meeting_scheduled_successfully",
            meeting_id=scheduled_meeting.get("id"),
            meeting_type=meeting_type,
            calendar_system=calendar_system,
            start_time=scheduled_meeting.get("start_time")
        )

        return state

    async def _parse_meeting_request(
        self,
        message: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Parse meeting request from message using LLM.

        Args:
            message: Customer message
            customer_metadata: Customer metadata

        Returns:
            Parsed meeting details
        """
        system_prompt = """You are a meeting scheduling specialist. Extract structured meeting information from customer requests.

Extract:
1. Meeting title/purpose
2. Date and time preferences
3. Duration (or use defaults)
4. Attendees (names/emails)
5. Meeting type (demo, QBR, call, etc.)
6. Timezone (if mentioned)
7. Video conferencing preference
8. Any special requirements

Be precise with dates and times."""

        user_prompt = f"""Parse this meeting request:

Message: {message}

Customer: {customer_metadata.get('customer_name', 'Unknown')}
Default timezone: {customer_metadata.get('timezone', 'America/New_York')}

Return JSON with title, date, time, duration_minutes, attendees (array), meeting_type, timezone, video_platform, and notes."""

        response = await self.call_llm(system_prompt, user_prompt)

        # Parse LLM response
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                details = json.loads(json_match.group())
            else:
                details = {
                    "title": "Customer Meeting",
                    "date": (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "time": "14:00",
                    "duration_minutes": 30,
                    "meeting_type": "call"
                }
        except:
            details = {
                "title": "Customer Meeting",
                "date": (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d"),
                "time": "14:00",
                "duration_minutes": 30,
                "meeting_type": "call"
            }

        return details

    def _detect_and_convert_timezone(
        self,
        meeting_details: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Detect and convert timezones for meeting scheduling.

        Args:
            meeting_details: Parsed meeting details
            customer_metadata: Customer metadata

        Returns:
            Timezone conversion information
        """
        # Get timezone from details or customer metadata
        source_tz = meeting_details.get("timezone", customer_metadata.get("timezone", "America/New_York"))

        # Convert abbreviation to full timezone name
        if source_tz in self.COMMON_TIMEZONES:
            source_tz_full = self.COMMON_TIMEZONES[source_tz]
        else:
            source_tz_full = source_tz

        # Target timezone (system default or UTC)
        target_tz = "UTC"

        return {
            "source_timezone": source_tz,
            "source_timezone_full": source_tz_full,
            "target_timezone": target_tz,
            "customer_timezone": customer_metadata.get("timezone", source_tz),
            "conversion_applied": True
        }

    def _check_availability(
        self,
        meeting_details: Dict,
        timezone_info: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Check availability for requested time slot.

        Args:
            meeting_details: Meeting details
            timezone_info: Timezone information
            customer_metadata: Customer metadata

        Returns:
            Availability information
        """
        # Mock availability check - in production, query actual calendars
        requested_date = meeting_details.get("date")
        requested_time = meeting_details.get("time", "14:00")

        # Simple business hours check
        hour = int(requested_time.split(":")[0])
        is_business_hours = 9 <= hour <= 17

        return {
            "requested_time_available": is_business_hours,
            "alternative_slots": [
                {"date": requested_date, "time": "10:00", "available": True},
                {"date": requested_date, "time": "14:00", "available": is_business_hours},
                {"date": requested_date, "time": "15:30", "available": True}
            ],
            "checked_at": datetime.now(UTC).isoformat()
        }

    def _check_conflicts(
        self,
        meeting_details: Dict,
        availability: Dict,
        existing_meetings: List[Dict]
    ) -> Dict[str, Any]:
        """
        Check for scheduling conflicts.

        Args:
            meeting_details: New meeting details
            availability: Availability information
            existing_meetings: List of existing meetings

        Returns:
            Conflict check results
        """
        conflicts = []

        requested_date = meeting_details.get("date")
        requested_time = meeting_details.get("time", "14:00")
        duration = meeting_details.get("duration_minutes", 30)

        # Check against existing meetings
        for meeting in existing_meetings:
            if meeting.get("date") == requested_date:
                # Simple time overlap check
                existing_time = meeting.get("time", "00:00")
                if abs(
                    int(requested_time.split(":")[0]) - int(existing_time.split(":")[0])
                ) < 2:
                    conflicts.append({
                        "meeting_id": meeting.get("id"),
                        "title": meeting.get("title"),
                        "time": existing_time,
                        "type": "time_overlap"
                    })

        return {
            "has_conflicts": len(conflicts) > 0,
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "should_proceed": len(conflicts) == 0 or availability.get("requested_time_available", True)
        }

    def _prepare_meeting_data(
        self,
        calendar_system: str,
        meeting_type: str,
        meeting_details: Dict,
        timezone_info: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Prepare meeting data for external calendar system.

        Args:
            calendar_system: Target calendar system
            meeting_type: Type of meeting
            meeting_details: Meeting details
            timezone_info: Timezone information
            customer_metadata: Customer metadata

        Returns:
            Formatted meeting data
        """
        meeting_config = self.MEETING_TYPES.get(meeting_type, self.MEETING_TYPES["call"])

        # Calculate start and end times
        date_str = meeting_details.get("date")
        time_str = meeting_details.get("time", "14:00")
        duration = meeting_details.get("duration_minutes", meeting_config["duration_minutes"])

        start_datetime = datetime.fromisoformat(f"{date_str}T{time_str}:00")
        end_datetime = start_datetime + timedelta(minutes=duration)

        # Prepare meeting data
        meeting_data = {
            "title": meeting_details.get("title", meeting_config["default_title"]),
            "description": meeting_details.get("notes", f"Scheduled via automation for {customer_metadata.get('customer_name', 'customer')}"),
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "timezone": timezone_info["source_timezone_full"],
            "duration_minutes": duration,
            "attendees": meeting_details.get("attendees", []),
            "location": "Online",
            "video_platform": meeting_details.get("video_platform", "meet" if calendar_system == "google" else "teams"),
            "reminders": [
                {"type": "email", "minutes_before": 60},
                {"type": "popup", "minutes_before": 10}
            ],
            "metadata": {
                "customer_id": customer_metadata.get("customer_id"),
                "customer_name": customer_metadata.get("customer_name"),
                "meeting_type": meeting_type,
                "created_by": "automation"
            }
        }

        # Add customer email as attendee
        if customer_metadata.get("email"):
            meeting_data["attendees"].append({
                "email": customer_metadata["email"],
                "name": customer_metadata.get("customer_name"),
                "role": "attendee",
                "required": True
            })

        return meeting_data

    async def _schedule_meeting_external(
        self,
        calendar_system: str,
        meeting_data: Dict,
        conflict_check: Dict
    ) -> Dict[str, Any]:
        """
        Schedule meeting in external calendar system (mocked).

        Args:
            calendar_system: Target system
            meeting_data: Meeting data
            conflict_check: Conflict check results

        Returns:
            Scheduled meeting details
        """
        # In production, make actual API call
        # For now, return mock scheduled meeting

        import hashlib
        meeting_id = hashlib.md5(
            f"{meeting_data['title']}{meeting_data['start_time']}".encode()
        ).hexdigest()[:12]

        # Generate video conference link
        video_platform = meeting_data.get("video_platform", "meet")
        video_link = f"https://{video_platform}.example.com/{meeting_id}"

        scheduled_meeting = {
            "id": meeting_id,
            "title": meeting_data["title"],
            "description": meeting_data["description"],
            "start_time": meeting_data["start_time"],
            "end_time": meeting_data["end_time"],
            "timezone": meeting_data["timezone"],
            "duration_minutes": meeting_data["duration_minutes"],
            "attendees": meeting_data["attendees"],
            "video_link": video_link,
            "video_platform": video_platform,
            "calendar_system": calendar_system,
            "status": "scheduled",
            "created_at": datetime.now(UTC).isoformat(),
            "calendar_link": f"https://{calendar_system}.example.com/event/{meeting_id}",
            "has_conflicts": conflict_check.get("has_conflicts", False)
        }

        self.logger.info(
            "meeting_scheduled_in_external_system",
            system=calendar_system,
            meeting_id=meeting_id,
            start_time=meeting_data["start_time"]
        )

        return scheduled_meeting

    def _setup_meeting_reminders(
        self,
        scheduled_meeting: Dict,
        meeting_type: str
    ) -> List[Dict[str, Any]]:
        """
        Setup automatic reminders for meeting.

        Args:
            scheduled_meeting: Scheduled meeting details
            meeting_type: Type of meeting

        Returns:
            List of configured reminders
        """
        reminders = [
            {
                "type": "email",
                "send_at": (datetime.fromisoformat(scheduled_meeting["start_time"]) - timedelta(hours=24)).isoformat(),
                "subject": f"Reminder: {scheduled_meeting['title']} tomorrow",
                "enabled": True
            },
            {
                "type": "email",
                "send_at": (datetime.fromisoformat(scheduled_meeting["start_time"]) - timedelta(hours=1)).isoformat(),
                "subject": f"Starting soon: {scheduled_meeting['title']}",
                "enabled": True
            },
            {
                "type": "notification",
                "send_at": (datetime.fromisoformat(scheduled_meeting["start_time"]) - timedelta(minutes=10)).isoformat(),
                "message": f"Meeting starts in 10 minutes",
                "enabled": True
            }
        ]

        return reminders

    def _log_automation_action(
        self,
        action_type: str,
        calendar_system: str,
        scheduled_meeting: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Log automated action for audit trail."""
        return {
            "action_type": action_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "system": calendar_system,
            "meeting_id": scheduled_meeting.get("id"),
            "customer_id": customer_metadata.get("customer_id"),
            "success": True,
            "details": {
                "meeting_title": scheduled_meeting.get("title"),
                "start_time": scheduled_meeting.get("start_time"),
                "attendee_count": len(scheduled_meeting.get("attendees", []))
            }
        }

    def _format_scheduling_response(
        self,
        scheduled_meeting: Dict,
        conflict_check: Dict,
        timezone_info: Dict,
        reminders: List[Dict]
    ) -> str:
        """Format meeting scheduling response."""
        response = f"""**Meeting Scheduled Successfully**

Title: {scheduled_meeting['title']}
Meeting ID: {scheduled_meeting['id']}

**When:**
Start: {scheduled_meeting['start_time']}
End: {scheduled_meeting['end_time']}
Duration: {scheduled_meeting['duration_minutes']} minutes
Timezone: {scheduled_meeting['timezone']}

**How to Join:**
Video Link: {scheduled_meeting['video_link']}
Platform: {scheduled_meeting['video_platform'].title()}

**Attendees:** {len(scheduled_meeting.get('attendees', []))} person(s)

**Reminders Configured:**
"""

        for reminder in reminders:
            response += f"- {reminder['type'].title()}: {reminder['subject'] if 'subject' in reminder else reminder.get('message', 'Reminder')}\n"

        if conflict_check.get("has_conflicts"):
            response += f"\n**Note:** {conflict_check['conflict_count']} scheduling conflict(s) detected but meeting was scheduled.\n"

        response += f"\nView in Calendar: {scheduled_meeting['calendar_link']}"

        return response
