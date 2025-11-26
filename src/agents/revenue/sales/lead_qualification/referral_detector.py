"""
Referral Detector Agent - TASK-1016

Detects referral signals and identifies referrers from database.
Calculates rewards and sends thank-you messages.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("referral_detector", tier="revenue", category="sales")
class ReferralDetector(BaseAgent):
    """
    Referral Detector Agent - Specialist in detecting and processing referrals.

    Handles:
    - Detect referral signals in messages and metadata
    - Identify referrer from customer database
    - Calculate referral rewards (credits, discounts)
    - Generate thank-you messages
    - Track referral attribution
    """

    # Referral signal keywords
    REFERRAL_SIGNALS = [
        "referred by",
        "recommended by",
        "my colleague",
        "my friend",
        "coworker told me",
        "someone told me",
        "heard from",
        "learned about you from",
        "was told by"
    ]

    # Referral reward tiers
    REWARD_TIERS = {
        "enterprise": {
            "min_company_size": 1000,
            "referrer_credit": 5000,
            "referee_discount": 2000,
            "tier_name": "Enterprise"
        },
        "mid_market": {
            "min_company_size": 200,
            "referrer_credit": 2000,
            "referee_discount": 1000,
            "tier_name": "Mid-Market"
        },
        "smb": {
            "min_company_size": 50,
            "referrer_credit": 1000,
            "referee_discount": 500,
            "tier_name": "SMB"
        },
        "small_business": {
            "min_company_size": 0,
            "referrer_credit": 500,
            "referee_discount": 250,
            "tier_name": "Small Business"
        }
    }

    # Referral bonus for closed deals
    CLOSED_DEAL_BONUS_MULTIPLIER = 2  # Double the reward when deal closes

    # Thank you message templates
    THANK_YOU_TEMPLATES = {
        "referrer": "automated_referrer_thank_you",
        "referee": "automated_referee_welcome"
    }

    def __init__(self):
        config = AgentConfig(
            name="referral_detector",
            type=AgentType.SPECIALIST,
            temperature=0.4,
            max_tokens=700,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.DATABASE_WRITE,
                AgentCapability.ENTITY_EXTRACTION
            ],
            kb_category="sales",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process referral detection and reward calculation.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with referral information
        """
        self.logger.info("referral_detector_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        entities = state.get("entities", {})

        # Detect referral signals
        referral_detected = self._detect_referral_signals(message, customer_metadata)

        if not referral_detected["is_referral"]:
            # No referral detected
            state["is_referral"] = False
            state["referral_source"] = None
            state["status"] = "resolved"
            state["response_confidence"] = 0.85

            self.logger.info("no_referral_detected")
            return state

        # Extract referrer information
        referrer_info = self._extract_referrer_info(
            message,
            customer_metadata,
            entities,
            referral_detected
        )

        # Identify referrer from database (simulated)
        identified_referrer = self._identify_referrer_from_database(referrer_info)

        # Calculate rewards
        rewards = self._calculate_referral_rewards(
            customer_metadata,
            identified_referrer
        )

        # Generate thank-you messages
        thank_you_messages = await self._generate_thank_you_messages(
            referrer_info,
            identified_referrer,
            rewards,
            customer_metadata
        )

        # Create referral tracking record
        referral_record = self._create_referral_record(
            customer_metadata,
            identified_referrer,
            rewards,
            state
        )

        # Update state
        state["is_referral"] = True
        state["referral_detected"] = True  # For backward compatibility with tests
        state["referral_source"] = referral_detected["source_type"]
        state["referrer_info"] = referrer_info
        state["identified_referrer"] = identified_referrer
        state["referral_rewards"] = rewards
        state["thank_you_messages"] = thank_you_messages
        state["referral_record_id"] = referral_record["referral_id"]
        state["next_action"] = "send_thank_you_and_reward"
        state["status"] = "resolved"
        state["response_confidence"] = 0.87

        self.logger.info(
            "referral_detected_and_processed",
            referrer_found=identified_referrer["found"],
            referrer_credit=rewards.get("referrer_credit", 0),
            referee_discount=rewards.get("referee_discount", 0)
        )

        return state

    def _detect_referral_signals(
        self,
        message: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Detect if this is a referral lead.

        Returns:
            Dict with is_referral (bool) and source_type (str)
        """
        message_lower = message.lower()

        # Check for referral signals in message
        for signal in self.REFERRAL_SIGNALS:
            if signal in message_lower:
                return {
                    "is_referral": True,
                    "source_type": "message_mention",
                    "signal": signal
                }

        # Check for referral source in metadata
        lead_source = customer_metadata.get("lead_source", "").lower()
        if "referral" in lead_source:
            return {
                "is_referral": True,
                "source_type": "metadata_source",
                "signal": lead_source
            }

        # Check for referral code
        referral_code = customer_metadata.get("referral_code")
        if referral_code:
            return {
                "is_referral": True,
                "source_type": "referral_code",
                "signal": referral_code
            }

        # Check UTM parameters
        utm_source = customer_metadata.get("utm_source", "").lower()
        if "referral" in utm_source or "refer" in utm_source:
            return {
                "is_referral": True,
                "source_type": "utm_parameter",
                "signal": utm_source
            }

        return {
            "is_referral": False,
            "source_type": None,
            "signal": None
        }

    def _extract_referrer_info(
        self,
        message: str,
        customer_metadata: Dict,
        entities: Dict,
        referral_detected: Dict
    ) -> Dict[str, Any]:
        """Extract information about who referred this lead"""

        referrer_info = {
            "referrer_name": None,
            "referrer_email": None,
            "referrer_company": None,
            "referral_code": customer_metadata.get("referral_code"),
            "detection_source": referral_detected["source_type"]
        }

        # Try to extract from message
        message_lower = message.lower()

        # Look for patterns like "John Smith referred me" or "referred by Jane Doe"
        for signal in self.REFERRAL_SIGNALS:
            if signal in message_lower:
                # Extract text after the signal
                parts = message.split(signal, 1)
                if len(parts) > 1:
                    # Simple extraction - take next few words
                    after_signal = parts[1].strip().split()[:3]
                    if after_signal:
                        # Try to identify name (capitalized words)
                        potential_name = " ".join([w for w in after_signal if w[0].isupper()])
                        if potential_name:
                            referrer_info["referrer_name"] = potential_name

        # Check metadata
        if customer_metadata.get("referrer_name"):
            referrer_info["referrer_name"] = customer_metadata["referrer_name"]

        if customer_metadata.get("referrer_email"):
            referrer_info["referrer_email"] = customer_metadata["referrer_email"]

        # Check entities
        if entities.get("referrer_name"):
            referrer_info["referrer_name"] = entities["referrer_name"]

        return referrer_info

    def _identify_referrer_from_database(self, referrer_info: Dict) -> Dict[str, Any]:
        """
        Identify referrer from customer database (simulated).

        In production, this would query the CRM/database.
        """
        # Simulated database lookup
        found = False
        referrer_id = None
        referrer_details = {}

        # If we have email, assume we can find them
        if referrer_info.get("referrer_email"):
            found = True
            referrer_id = f"CUST-{referrer_info['referrer_email'].split('@')[0]}"
            referrer_details = {
                "customer_id": referrer_id,
                "email": referrer_info["referrer_email"],
                "name": referrer_info.get("referrer_name", "Unknown"),
                "is_active_customer": True,
                "account_status": "active"
            }
        # If we have referral code, try to match
        elif referrer_info.get("referral_code"):
            found = True
            referrer_id = f"REF-{referrer_info['referral_code']}"
            referrer_details = {
                "customer_id": referrer_id,
                "referral_code": referrer_info["referral_code"],
                "name": referrer_info.get("referrer_name", "Unknown Referrer"),
                "is_active_customer": True,
                "account_status": "active"
            }
        # If we only have name, mark as unverified
        elif referrer_info.get("referrer_name"):
            found = False  # Can't verify without email/code
            referrer_details = {
                "name": referrer_info["referrer_name"],
                "verification_status": "unverified"
            }

        return {
            "found": found,
            "referrer_id": referrer_id,
            "details": referrer_details
        }

    def _calculate_referral_rewards(
        self,
        customer_metadata: Dict,
        identified_referrer: Dict
    ) -> Dict[str, Any]:
        """Calculate referral rewards for both referrer and referee"""

        company_size = customer_metadata.get("company_size", 0)

        # Determine reward tier
        reward_tier = "small_business"
        for tier_name, tier_criteria in self.REWARD_TIERS.items():
            if company_size >= tier_criteria["min_company_size"]:
                reward_tier = tier_name
                break

        tier_config = self.REWARD_TIERS[reward_tier]

        rewards = {
            "reward_tier": reward_tier,
            "tier_name": tier_config["tier_name"],
            "referrer_credit": tier_config["referrer_credit"],
            "referee_discount": tier_config["referee_discount"],
            "currency": "USD",
            "status": "pending",  # Pending until deal closes
            "closed_deal_bonus": tier_config["referrer_credit"] * self.CLOSED_DEAL_BONUS_MULTIPLIER
        }

        # If referrer not found, mark as unverified
        if not identified_referrer["found"]:
            rewards["status"] = "unverified_referrer"
            rewards["referrer_credit"] = 0  # Can't reward unknown referrer

        return rewards

    async def _generate_thank_you_messages(
        self,
        referrer_info: Dict,
        identified_referrer: Dict,
        rewards: Dict,
        customer_metadata: Dict
    ) -> Dict[str, str]:
        """Generate personalized thank-you messages for referrer and referee"""

        messages = {}

        # Generate referrer thank you (if found)
        if identified_referrer["found"]:
            referrer_name = identified_referrer["details"].get("name", "Valued Customer")
            referee_company = customer_metadata.get("company", "a new customer")

            system_prompt_referrer = """You are sending a thank-you message to a customer who referred a new lead.
Be warm, appreciative, and professional. Keep it brief (2-3 sentences)."""

            user_prompt_referrer = f"""Generate a thank-you message for:

Referrer: {referrer_name}
Referred: {referee_company}
Reward: ${rewards['referrer_credit']} account credit (pending deal closure)

Express gratitude and mention the reward."""

            messages["referrer_message"] = await self.call_llm(
                system_prompt=system_prompt_referrer,
                user_message=user_prompt_referrer,
                conversation_history=[]  # Thank-you messages are standalone
            )

        # Generate referee welcome message
        referee_name = customer_metadata.get("name", "there")
        referrer_name = referrer_info.get("referrer_name", "a valued customer")

        system_prompt_referee = """You are welcoming a new lead who was referred by an existing customer.
Be welcoming and mention the referral discount. Keep it brief (2-3 sentences)."""

        user_prompt_referee = f"""Generate a welcome message for:

New Lead: {referee_name}
Referred By: {referrer_name}
Discount: ${rewards['referee_discount']} on first purchase

Welcome them and mention the discount."""

        messages["referee_message"] = await self.call_llm(
            system_prompt=system_prompt_referee,
            user_message=user_prompt_referee,
            conversation_history=[]  # Welcome messages are standalone
        )

        return messages

    def _create_referral_record(
        self,
        customer_metadata: Dict,
        identified_referrer: Dict,
        rewards: Dict,
        state: AgentState
    ) -> Dict[str, Any]:
        """Create referral tracking record"""

        referral_id = f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{customer_metadata.get('email', 'unknown').split('@')[0]}"

        record = {
            "referral_id": referral_id,
            "referee_email": customer_metadata.get("email", ""),
            "referee_company": customer_metadata.get("company", ""),
            "referee_name": customer_metadata.get("name", ""),
            "referrer_id": identified_referrer.get("referrer_id"),
            "referrer_verified": identified_referrer["found"],
            "reward_tier": rewards["reward_tier"],
            "referrer_credit": rewards["referrer_credit"],
            "referee_discount": rewards["referee_discount"],
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "tracking_source": state.get("referral_source")
        }

        return record


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing ReferralDetector Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Explicit referral mention
        state1 = create_initial_state(
            "I was referred by John Smith from Acme Corp, he said you guys are great!",
            context={
                "customer_metadata": {
                    "company": "Tech Startup Inc",
                    "name": "Jane Doe",
                    "email": "jane@techstartup.com",
                    "company_size": 150,
                    "lead_source": "referral"
                },
                "entities": {
                    "referrer_name": "John Smith"
                }
            }
        )

        agent = ReferralDetector()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - Explicit Referral Mention")
        print(f"Is Referral: {result1['is_referral']}")
        if result1['is_referral']:
            print(f"Referral Source: {result1['referral_source']}")
            print(f"Referrer Found: {result1['identified_referrer']['found']}")
            print(f"Rewards: ${result1['referral_rewards']['referrer_credit']} credit, ${result1['referral_rewards']['referee_discount']} discount")
            print(f"\nReferee Welcome Message:\n{result1['thank_you_messages']['referee_message']}")
            if "referrer_message" in result1['thank_you_messages']:
                print(f"\nReferrer Thank You:\n{result1['thank_you_messages']['referrer_message']}\n")

        # Test case 2: Referral code
        state2 = create_initial_state(
            "I'd like to sign up for a demo",
            context={
                "customer_metadata": {
                    "company": "Enterprise Corp",
                    "email": "contact@enterprise.com",
                    "company_size": 2000,
                    "referral_code": "SARAH2024"
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\nTest 2 - Referral Code")
        print(f"Is Referral: {result2['is_referral']}")
        if result2['is_referral']:
            print(f"Referral Source: {result2['referral_source']}")
            print(f"Reward Tier: {result2['referral_rewards']['tier_name']}")
            print(f"Rewards: ${result2['referral_rewards']['referrer_credit']} credit, ${result2['referral_rewards']['referee_discount']} discount")

    asyncio.run(test())
