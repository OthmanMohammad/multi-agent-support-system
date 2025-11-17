"""
Collaboration Expert Agent - Teaches team collaboration features.

Specialist for sharing, permissions, @mentions, comments, and team workflows.
"""

from typing import Dict, Any, Optional

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("collaboration_expert", tier="essential", category="usage")
class CollaborationExpert(BaseAgent):
    """
    Collaboration Expert Agent - Specialist for team collaboration features.

    Handles:
    - Sharing projects and workspaces
    - Permission management
    - @mentions and notifications
    - Comments and discussions
    - Real-time collaboration
    - Team workflows and best practices
    """

    COLLABORATION_FEATURES = {
        "sharing": {
            "description": "Share projects and workspaces with team members",
            "steps": [
                "Open the project or workspace",
                "Click the 'Share' button (top right)",
                "Add email addresses or select from team",
                "Set permission level for each person",
                "Add optional message",
                "Click 'Send Invites'"
            ],
            "best_practices": [
                "Give minimum permissions needed (principle of least privilege)",
                "Use team workspaces for department-wide sharing",
                "Review sharing settings quarterly",
                "Create shared views for specific use cases"
            ],
            "common_issues": [
                "User can't see shared project → Check they accepted invite",
                "Can't find person to share with → Invite them to workspace first",
                "Shared link not working → Check link hasn't expired"
            ]
        },
        "mentions": {
            "description": "Notify team members with @mentions",
            "steps": [
                "Type @ in any comment or description field",
                "Start typing person's name",
                "Select from dropdown",
                "Finish your message",
                "They'll get instant notification"
            ],
            "best_practices": [
                "Use @mentions sparingly to avoid notification fatigue",
                "Be specific about what you need",
                "Set deadlines when requesting action",
                "@mention at the right time (not middle of night)"
            ],
            "common_issues": [
                "Person not in dropdown → They need to join the workspace",
                "@mention doesn't notify → Check their notification settings",
                "Too many @mentions → Use @team sparingly"
            ]
        },
        "permissions": {
            "description": "Control who can view, edit, and manage content",
            "levels": {
                "viewer": {
                    "name": "Viewer",
                    "description": "Read-only access",
                    "can": ["View projects", "See comments", "Export data", "Follow items"],
                    "cannot": ["Edit", "Delete", "Share", "Change settings"],
                    "use_for": ["Clients", "Stakeholders", "External partners", "Read-only team members"]
                },
                "editor": {
                    "name": "Editor",
                    "description": "Can make changes to content",
                    "can": ["All Viewer permissions", "Create items", "Edit content", "Add comments", "Upload files"],
                    "cannot": ["Delete projects", "Manage members", "Change billing", "Configure integrations"],
                    "use_for": ["Team members", "Contributors", "Content creators"]
                },
                "admin": {
                    "name": "Admin",
                    "description": "Full control over workspace",
                    "can": ["All Editor permissions", "Delete projects", "Manage members", "Change settings", "Configure integrations", "View analytics"],
                    "cannot": ["Change billing (Owner only)", "Delete workspace (Owner only)"],
                    "use_for": ["Managers", "Team leads", "Department heads"]
                },
                "owner": {
                    "name": "Owner",
                    "description": "Complete control including billing",
                    "can": ["Everything", "Manage billing", "Delete workspace", "Transfer ownership"],
                    "cannot": ["Nothing - full access"],
                    "use_for": ["Account owner", "Company admin"]
                }
            },
            "best_practices": [
                "Give Viewer access by default, elevate as needed",
                "Review permissions monthly",
                "Use groups for easier management",
                "Document who has what access"
            ]
        },
        "comments": {
            "description": "Discuss tasks and projects asynchronously",
            "steps": [
                "Open any task or project",
                "Scroll to Comments section",
                "Type your comment",
                "@mention relevant people",
                "Attach files if needed (drag & drop)",
                "Click 'Post' or press Ctrl+Enter"
            ],
            "best_practices": [
                "Be specific and actionable",
                "Use threads to keep conversations organized",
                "@mention for important updates",
                "Add context (don't assume everyone knows background)",
                "Use emoji reactions instead of '+1' comments"
            ],
            "features": [
                "Rich text formatting (bold, italic, lists)",
                "Code blocks for technical discussions",
                "File attachments and screenshots",
                "Emoji reactions",
                "Edit and delete comments",
                "Comment history and audit trail"
            ]
        },
        "notifications": {
            "description": "Stay updated on relevant activity",
            "channels": {
                "in_app": "Real-time notifications within the app",
                "email": "Email digest or instant emails",
                "mobile": "Push notifications on mobile app",
                "slack": "Integration with Slack channels",
                "desktop": "Desktop notifications (when app is open)"
            },
            "best_practices": [
                "Customize by priority (only critical via mobile)",
                "Use digest mode for low-priority updates",
                "Set quiet hours for focused work",
                "Mute threads you don't need to follow",
                "Unsubscribe from completed projects"
            ]
        },
        "realtime": {
            "description": "Collaborate in real-time with presence indicators",
            "features": [
                "See who's viewing the same item (avatar indicators)",
                "Live cursor tracking (optional)",
                "Instant updates without refresh",
                "Conflict resolution for simultaneous edits",
                "Activity feed showing recent changes"
            ],
            "best_practices": [
                "Communicate before making major changes",
                "Use comments for async, realtime for urgent",
                "Be aware of others' edits to avoid conflicts"
            ]
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="collaboration_expert",
            type=AgentType.SPECIALIST,
            temperature=0.4,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.MULTI_TURN
            ],
            kb_category="usage",
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process collaboration feature requests"""
        self.logger.info("collaboration_expert_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})
        team_size = customer_context.get("seats_used", 1)

        self.logger.debug(
            "collaboration_processing_started",
            message_preview=message[:100],
            team_size=team_size,
            turn_count=state["turn_count"]
        )

        # Detect collaboration feature
        feature = self._detect_collaboration_feature(message)

        self.logger.info(
            "collaboration_feature_detected",
            feature=feature,
            team_size=team_size
        )

        # Generate appropriate response
        if team_size == 1:
            response = self._suggest_inviting_team()
        elif feature:
            response = self._teach_feature(feature)
        else:
            response = self._overview_collaboration()

        # Search KB for collaboration guides
        kb_results = await self.search_knowledge_base(
            f"team collaboration {feature}" if feature else "team collaboration features",
            category="usage",
            limit=2
        )
        state["kb_results"] = kb_results

        if kb_results:
            self.logger.info(
                "collaboration_kb_articles_found",
                count=len(kb_results)
            )
            response += "\n\n**📚 Collaboration guides:**\n"
            for i, article in enumerate(kb_results, 1):
                response += f"{i}. {article['title']}\n"

        state["agent_response"] = response
        state["collaboration_feature"] = feature
        state["team_size"] = team_size
        state["response_confidence"] = 0.9
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "collaboration_guidance_completed",
            feature=feature,
            team_size=team_size,
            status="resolved"
        )

        return state

    def _detect_collaboration_feature(self, message: str) -> Optional[str]:
        """Detect which collaboration feature user is asking about"""
        message_lower = message.lower()

        # Direct feature matches
        for feature in self.COLLABORATION_FEATURES.keys():
            if feature in message_lower:
                return feature

        # Check for aliases
        if any(word in message_lower for word in ["share", "sharing", "invite"]):
            return "sharing"
        elif any(word in message_lower for word in ["@", "mention", "tag", "notify"]):
            return "mentions"
        elif any(word in message_lower for word in ["permission", "access", "role", "viewer", "editor", "admin"]):
            return "permissions"
        elif any(word in message_lower for word in ["comment", "discuss", "conversation", "thread"]):
            return "comments"
        elif any(word in message_lower for word in ["notification", "alert", "digest"]):
            return "notifications"
        elif any(word in message_lower for word in ["real-time", "realtime", "live", "presence"]):
            return "realtime"

        return None

    def _suggest_inviting_team(self) -> str:
        """Suggest inviting team for solo users"""
        return """**👋 Welcome! I see you're flying solo right now.**

Collaboration features work best with a team! Here's how to get started:

**Invite your first team member (it's free!):**

1. Click your **profile picture** (top right)
2. Select **"Invite Team"** or **"Manage Team"**
3. Enter their **email address**
4. Choose permission level:
   - **Editor** (recommended for teammates)
   - **Viewer** (for stakeholders/clients)
5. Add a personal message (optional)
6. Click **"Send Invite"**

**They'll receive:**
✓ Email invitation with signup link
✓ Instant access to shared workspaces
✓ Ability to collaborate immediately

**Benefits of collaborating:**

**🚀 2x Productivity**
- Real-time updates for everyone
- No more status meetings
- Async communication via comments
- Clear task ownership

**💬 50% Fewer Meetings**
- @mention teammates for quick questions
- Comment threads replace email chains
- Decisions documented in context

**🎯 100% Clarity**
- Everyone sees the same information
- Track who's doing what
- No more "Did you see my email?"

**👥 Better teamwork:**
- Shared workspaces and projects
- @mentions for quick collaboration
- Comments replace email threads
- Real-time presence indicators

**Most teams see benefits within 24 hours** of inviting their first member!

**Want to invite your team?** I can walk you through it step-by-step!
"""

    def _teach_feature(self, feature: str) -> str:
        """Teach specific collaboration feature"""
        if feature not in self.COLLABORATION_FEATURES:
            return self._overview_collaboration()

        feat_info = self.COLLABORATION_FEATURES[feature]

        if feature == "sharing":
            return f"""**📤 {feat_info['description']}**

**How to share:**
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(feat_info['steps'])])}

**Permission levels explained:**

{self._format_permission_levels()}

**Best practices:**
{chr(10).join(['• ' + practice for practice in feat_info['best_practices']])}

**Common issues:**
{chr(10).join(['❓ ' + issue for issue in feat_info['common_issues']])}

**Pro tips:**
• **Team workspaces:** Create workspace → auto-share with everyone
• **Shared links:** Generate public link for external sharing (Settings → Sharing)
• **Guest access:** Invite clients as Viewer (no seat charge)
• **Bulk sharing:** Select multiple projects → Share with same people

**Quick wins:**
1. Create a **Team Workspace** for your department
2. Add all team members as **Editors**
3. Move shared projects into the workspace
4. Everyone has automatic access!

**Want me to walk you through any specific sharing scenario?**
"""

        elif feature == "mentions":
            return f"""**👋 {feat_info['description']}**

**How to @mention:**
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(feat_info['steps'])])}

**When to use @mentions:**

**✅ Do @mention when:**
• You need someone's input or approval
• Assigning responsibility or action items
• Sharing important updates they must see
• Asking time-sensitive questions
• Escalating blocked items

**❌ Don't @mention when:**
• FYI updates (just comment normally)
• Same person repeatedly in thread
• Entire team for minor updates
• During team members' quiet hours

**Advanced @mention features:**

**@person** - Notify specific person
**@team** - Notify all team members (use sparingly!)
**@channel** - Notify all project members
**@here** - Notify only active users

**Best practices:**
{chr(10).join(['• ' + practice for practice in feat_info['best_practices']])}

**Examples of good @mentions:**

✅ "@john can you review this design by EOD?"
✅ "@sarah this blocker needs your decision"
✅ "@team Sprint planning tomorrow at 2pm"

❌ "@john @sarah @mike @lisa thoughts?" (too many)
❌ "@team made a small typo fix" (not important enough)

**Pro tips:**
• **@mention sends:** Email + in-app + mobile push + Slack (if connected)
• **Edit mentions:** Edit comment to add/remove @mentions
• **Mute thread:** Stop getting @mentions from specific thread
• **Quiet hours:** Set in Settings → Notifications

**Common issues:**
{chr(10).join(['❓ ' + issue for issue in feat_info['common_issues']])}

**Want to customize your @mention notifications?**
Settings → Notifications → Mentions
"""

        elif feature == "permissions":
            return f"""**🔐 {feat_info['description']}**

{self._format_permission_levels()}

**How to change permissions:**

1. Go to project or workspace
2. Click **"Share"** or **"Members"**
3. Find the person
4. Click their current role
5. Select new permission level
6. Click **"Save"**

**Best practices:**
{chr(10).join(['• ' + practice for practice in feat_info['best_practices']])}

**Permission strategies by use case:**

**Internal team project:**
• Team members → **Editor**
• Manager → **Admin**
• Stakeholders → **Viewer**

**Client collaboration:**
• Your team → **Editor**
• Client → **Viewer** (or Editor if they contribute)
• Client executives → **Viewer**

**Department workspace:**
• Department members → **Editor**
• Department head → **Admin**
• Other departments → **Viewer**

**Security tips:**

🔒 **Regular audits:** Review who has access quarterly
🔒 **Offboarding:** Remove access when people leave
🔒 **External sharing:** Use Viewer for all external people
🔒 **Admin roles:** Limit to managers only
🔒 **Owner transfer:** Plan succession for workspace Owner

**Common questions:**

**Q: Can I have different permissions for different projects?**
A: Yes! Permissions are per project and workspace

**Q: What if I need something between Viewer and Editor?**
A: Use Editor but limit with project settings (e.g., can't delete)

**Q: How do I bulk change permissions?**
A: Settings → Members → Select multiple → Change role

**Q: Can someone have multiple roles?**
A: They'll have highest permission level across all their roles

**Need help setting up permissions?** Tell me your team structure!
"""

        elif feature == "comments":
            return f"""**💬 {feat_info['description']}**

**How to comment:**
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(feat_info['steps'])])}

**Comment features:**
{chr(10).join(['• ' + feat for feat in feat_info['features']])}

**Best practices:**
{chr(10).join(['• ' + practice for practice in feat_info['best_practices']])}

**Advanced commenting:**

**Rich formatting:**
```
**bold** → bold text
*italic* → italic text
- bullet → bullet list
1. numbered → numbered list
`code` → inline code
```code block``` → code block
[link](url) → hyperlink
```

**Keyboard shortcuts:**
• `Ctrl/Cmd + Enter` - Post comment
• `Ctrl/Cmd + B` - Bold
• `Ctrl/Cmd + I` - Italic
• `@` - Mention someone

**Comment threads:**
• Reply to specific comment
• Keep related discussion together
• Mark thread as resolved
• Collapse old threads

**File attachments:**
• Drag & drop files (up to 100MB)
• Paste screenshots (Ctrl+V)
• Reference other tasks (paste link)

**Comment reactions:**
• 👍 Like/agree
• ❤️ Love
• 🎉 Celebrate
• 🤔 Thinking
• ✅ Done/approved

**Pro tips:**

**Replace meetings with comments:**
✓ Status updates → Comment with progress
✓ Questions → @mention in comment
✓ Decisions → Document in comments
✓ Feedback → Thread of review comments

**Comment etiquette:**
• Be clear and constructive
• Assume positive intent
• Use emoji to convey tone
• Edit typos (don't spam corrections)
• Mark urgent items clearly

**Reduce noise:**
• React with emoji instead of "+1" comment
• Use threads instead of new comments
• Mute threads you don't need to follow
• Unsubscribe from old discussions

**Want me to show you advanced commenting techniques?**
"""

        elif feature == "notifications":
            return f"""**🔔 {feat_info['description']}**

**Notification channels:**
{chr(10).join([f"• **{name.replace('_', ' ').title()}** - {desc}" for name, desc in feat_info['channels'].items()])}

**Customize your notifications:**

**Settings → Notifications → Customize**

**By priority:**
• **Critical:** @mentions, assigned tasks → All channels
• **Important:** Project updates → Email digest + in-app
• **FYI:** Comments you follow → Daily digest only
• **Noise:** Auto-generated → Disable

**Best practices:**
{chr(10).join(['• ' + practice for practice in feat_info['best_practices']])}

**Notification settings by role:**

**👨‍💼 Manager:**
• @mentions → Instant (all channels)
• Team activity → Hourly digest
• Project milestones → Email
• Comments → Daily digest

**👩‍💻 Individual contributor:**
• @mentions → Instant
• Assigned tasks → Email
• Your projects → In-app only
• Team activity → Weekly digest

**👔 Executive:**
• Critical only → Email
• High-level updates → Weekly digest
• Mentions → During work hours only
• Everything else → Mute

**Smart notification tips:**

**⏰ Quiet hours:**
Settings → Notifications → Quiet Hours
• Example: 6pm - 8am (no mobile notifications)
• Weekends off
• Timezone-aware

**📊 Digest mode:**
Instead of instant emails, get:
• Hourly digest (busy people)
• Daily digest (most users)
• Weekly digest (high-level only)

**🔕 Mute strategically:**
• Old projects you monitor
• Threads you don't need to follow
• Team channels not relevant to you
• Automated bot updates

**📱 Mobile vs desktop:**
• Mobile: Critical only (@mentions, assigned)
• Desktop: All during work hours
• Email: Important decisions only

**Notification hierarchy:**

1. **@mention to you** → All channels
2. **Assigned task** → Email + in-app
3. **Project you own** → In-app + digest
4. **Thread you commented on** → Digest
5. **Team general activity** → Weekly digest

**Common notification issues:**

❓ **Too many notifications?**
   → Switch to digest mode + mute non-critical

❓ **Missing important updates?**
   → Check spam folder, verify email in settings

❓ **Notifications delayed?**
   → Check internet connection, try logging out/in

❓ **Don't want weekend notifications?**
   → Enable quiet hours for evenings + weekends

**Perfect notification setup (5 minutes):**

1. **Instant:** Only @mentions and assigned tasks
2. **Daily digest:** Projects you follow
3. **Weekly digest:** Team activity
4. **Mute:** Completed projects, bot updates
5. **Quiet hours:** Evenings and weekends

**Want me to help you configure the perfect notification settings?**
"""

        elif feature == "realtime":
            return f"""**⚡ {feat_info['description']}**

**Real-time features:**
{chr(10).join(['• ' + feat for feat in feat_info['features']])}

**How it works:**

**Presence indicators:**
• See colored avatars of who's viewing same item
• Hover over avatar to see what they're doing
• Know when someone's editing same field

**Live updates:**
• Changes appear instantly (no page refresh)
• Cursor tracking shows where team members are
• Conflict resolution if two people edit same thing
• Activity feed shows who changed what

**Real-time collaboration scenarios:**

**📊 Team planning meeting:**
1. Everyone opens same project
2. See each other's presence
3. Make updates in real-time
4. Discuss via comments
5. Changes sync instantly

**✅ Sprint retrospective:**
1. Team views retrospective board
2. Everyone adds sticky notes simultaneously
3. Group and vote in real-time
4. No waiting for turns

**📝 Document collaboration:**
1. Multiple people editing simultaneously
2. See each other's cursors (optional)
3. Changes merge automatically
4. Comment for clarification

**Best practices:**
{chr(10).join(['• ' + practice for practice in feat_info['best_practices']])}

**Collaboration etiquette:**

**✅ Do:**
• Announce major changes in comment first
• Use @mentions for quick questions
• Be patient with sync conflicts
• Save frequently (auto-save is enabled)

**❌ Don't:**
• Delete others' work without asking
• Make mass changes during meetings
• Edit while someone else is editing same field
• Ignore conflict warnings

**Real-time features by plan:**

**Free:**
• Basic presence (who's online)
• Live updates (5-second refresh)

**Premium:**
• Full presence (what they're viewing)
• Instant updates (<1 second)
• Cursor tracking
• Advanced conflict resolution

**Enterprise:**
• All Premium features
• Session replay
• Collaboration analytics
• Audit trail

**Troubleshooting real-time sync:**

❓ **Changes not appearing?**
   → Refresh page, check internet connection

❓ **Conflict errors?**
   → Wait for other person to finish, then retry

❓ **Presence not showing?**
   → Enable in Settings → Privacy → Show presence

❓ **Too distracting?**
   → Disable cursor tracking in Settings

**Want to enable real-time collaboration for your team?**
"""

        # Default generic response
        return f"""**{feat_info['description']}**

Let me know if you'd like detailed instructions for this feature!
"""

    def _overview_collaboration(self) -> str:
        """Overview of all collaboration features"""
        features = "\n".join([
            f"**{name.replace('_', ' ').title()}** - {info['description']}"
            for name, info in self.COLLABORATION_FEATURES.items()
        ])

        return f"""**🤝 Team Collaboration Features**

{features}

---

**Quick wins for better collaboration:**

**1. 📤 Share projects** with your team
   → Everyone sees same info, no email updates needed

**2. 👋 @mention** people when you need them
   → Get instant attention without interrupting

**3. 💬 Comment on tasks** instead of email
   → Keep all discussion in context

**4. 🔐 Set smart permissions**
   → Right access for right people

**5. 🔔 Customize notifications**
   → Stay informed without overwhelm

---

**Collaboration impact:**

**Before collaboration features:**
• 10+ status meetings per week
• Email chains with 50+ messages
• "Did you see my email?"
• Unclear task ownership
• Decisions get lost

**After collaboration features:**
• 5 meetings per week (50% reduction)
• Discussions in context
• @mentions get instant response
• Crystal clear ownership
• Full decision history

---

**Getting started (5 minutes):**

1. **Invite your team** (Settings → Team)
2. **Create shared workspace** (Workspaces → New)
3. **Set up @mention** shortcuts
4. **Configure notifications** for your style
5. **Start commenting** instead of emailing

**Which feature would you like to learn first?**

Just ask about:
• "How do I share?"
• "Teach me @mentions"
• "Explain permissions"
• "Set up notifications"
• Or any other collaboration question!
"""

    def _format_permission_levels(self) -> str:
        """Format permission levels explanation"""
        perms = self.COLLABORATION_FEATURES["permissions"]["levels"]

        output = "**Permission levels:**\n\n"

        for level_key, level_info in perms.items():
            output += f"""**{level_info['name']}** - {level_info['description']}
   ✓ Can: {', '.join(level_info['can'][:3])}
   ✗ Cannot: {', '.join(level_info['cannot'][:2])}
   👥 Best for: {', '.join(level_info['use_for'][:2])}

"""

        return output


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: Solo user
        print("=" * 60)
        print("Test 1: Solo user - suggest inviting team")
        print("=" * 60)

        state = create_initial_state("How do I collaborate?")
        state["customer_metadata"] = {"seats_used": 1}

        agent = CollaborationExpert()
        result = await agent.process(state)

        print(f"\nTeam size: {result.get('team_size')}")
        print(f"\nResponse:\n{result['agent_response'][:500]}...")

        # Test 2: Teach sharing
        print("\n" + "=" * 60)
        print("Test 2: Teach sharing feature")
        print("=" * 60)

        state2 = create_initial_state("How do I share a project with my team?")
        state2["customer_metadata"] = {"seats_used": 5}
        result2 = await agent.process(state2)

        print(f"\nFeature: {result2.get('collaboration_feature')}")
        print(f"\nResponse:\n{result2['agent_response'][:500]}...")

        # Test 3: Overview
        print("\n" + "=" * 60)
        print("Test 3: Collaboration overview")
        print("=" * 60)

        state3 = create_initial_state("What collaboration features do you have?")
        state3["customer_metadata"] = {"seats_used": 10}
        result3 = await agent.process(state3)

        print(f"\nResponse:\n{result3['agent_response'][:500]}...")

    asyncio.run(test())
