"""
Comprehensive Database Seed Script

Populates the database with realistic test data for development and testing:
- 100+ customers across various industries and plans
- 500+ conversations with message history
- Subscriptions, invoices, and payments
- Usage events and feature adoption
- Sales pipeline (leads, deals)
"""
import asyncio
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.connection import AsyncSessionLocal
from src.database.models.customer import Customer
from src.database.models.conversation import Conversation
from src.database.models.message import Message
from src.database.models.subscription import Subscription, Invoice, Payment, UsageEvent
from src.database.models.sales import Lead, Deal
from src.database.models.analytics import FeatureUsage

# Seed data constants
INDUSTRIES = [
    "Technology", "Healthcare", "Finance", "Education", "Retail",
    "Manufacturing", "Professional Services", "Media", "Real Estate", "Legal"
]

COMPANY_NAME_PREFIXES = [
    "Acme", "Global", "Tech", "Smart", "Digital", "Cloud", "Data",
    "Quantum", "Nexus", "Fusion", "Vertex", "Summit", "Prime", "Core"
]

COMPANY_NAME_SUFFIXES = [
    "Solutions", "Systems", "Technologies", "Enterprises", "Group",
    "Corp", "Inc", "Labs", "Innovations", "Dynamics", "Ventures"
]

INTENTS = [
    "technical_support", "billing_question", "feature_request",
    "account_management", "integration_help", "bug_report",
    "general_inquiry", "sales_question", "upgrade_request"
]

FEATURES = [
    "dashboard", "reports", "api_access", "integrations", "analytics",
    "collaboration", "automation", "mobile_app", "exports", "notifications"
]


def random_company_name() -> str:
    """Generate a random company name"""
    prefix = random.choice(COMPANY_NAME_PREFIXES)
    suffix = random.choice(COMPANY_NAME_SUFFIXES)
    return f"{prefix} {suffix}"


def random_date_between(start_days_ago: int, end_days_ago: int = 0) -> datetime:
    """Generate a random datetime between start and end days ago (negative for future)"""
    start = datetime.now(timezone.utc) - timedelta(days=start_days_ago)
    end = datetime.now(timezone.utc) - timedelta(days=end_days_ago)
    delta = end - start
    # Handle both past and future dates
    if delta.total_seconds() < 0:
        start, end = end, start
        delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


async def create_customers(session: AsyncSession, count: int = 100) -> list[Customer]:
    """Create customer records with realistic data"""
    print(f"\n📊 Creating {count} customers...")
    customers = []

    plans = ["free", "basic", "premium", "enterprise"]
    plan_weights = [30, 40, 20, 10]  # Distribution: 30% free, 40% basic, etc.

    for i in range(count):
        plan = random.choices(plans, weights=plan_weights)[0]

        # Calculate metrics based on plan
        if plan == "free":
            mrr = 0
            health_score = random.randint(40, 70)
            company_size = random.randint(1, 50)
        elif plan == "basic":
            mrr = random.randint(50, 200)
            health_score = random.randint(60, 85)
            company_size = random.randint(10, 200)
        elif plan == "premium":
            mrr = random.randint(200, 1000)
            health_score = random.randint(70, 95)
            company_size = random.randint(50, 1000)
        else:  # enterprise
            mrr = random.randint(1000, 10000)
            health_score = random.randint(80, 98)
            company_size = random.randint(100, 10000)

        ltv = mrr * random.randint(12, 36)  # 1-3 years
        churn_risk = max(0.05, min(0.95, (100 - health_score) / 100))
        nps_score = min(10, max(1, health_score // 10))

        company_name = random_company_name()

        customer = Customer(
            email=f"contact+{i}@{company_name.lower().replace(' ', '')}.com",
            name=company_name,
            plan=plan,
            extra_metadata={
                "company_size": company_size,
                "industry": random.choice(INDUSTRIES),
                "mrr": float(mrr),
                "ltv": float(ltv),
                "health_score": health_score,
                "churn_risk": round(churn_risk, 2),
                "nps_score": nps_score,
                "customer_since": random_date_between(365, 30).isoformat(),
                "primary_contact": f"John Doe {i}",
                "phone": f"+1-555-{random.randint(1000, 9999)}",
                "country": random.choice(["US", "UK", "CA", "AU", "DE", "FR"]),
            }
        )
        session.add(customer)
        customers.append(customer)

        if (i + 1) % 20 == 0:
            print(f"  ✓ Created {i + 1}/{count} customers")

    await session.flush()
    print(f"✅ Created {count} customers")
    return customers


async def create_subscriptions(session: AsyncSession, customers: list[Customer]) -> list[Subscription]:
    """Create subscription records for customers"""
    print(f"\n💳 Creating subscriptions...")
    subscriptions = []

    for customer in customers:
        if customer.plan == "free":
            continue  # Free customers don't have subscriptions

        # Billing cycle
        billing_cycle = random.choice(["monthly", "annual"])

        # MRR from customer metadata
        mrr = Decimal(str(customer.extra_metadata.get("mrr", 0)))
        arr = mrr * 12 if billing_cycle == "annual" else None

        # Seat allocation
        company_size = customer.extra_metadata.get("company_size", 10)
        seats_total = max(1, company_size // 10)  # Roughly 10% of company size
        seats_used = max(1, int(seats_total * random.uniform(0.5, 1.0)))

        # Status
        status_weights = [85, 5, 5, 5]  # 85% active, 5% past_due, etc.
        status = random.choices(
            ["active", "past_due", "canceled", "trialing"],
            weights=status_weights
        )[0]

        # Dates
        current_period_start = random_date_between(30, 0)
        current_period_end = current_period_start + timedelta(days=30 if billing_cycle == "monthly" else 365)

        # Trial (10% of subscriptions)
        trial_start = None
        trial_end = None
        if random.random() < 0.1 and status == "trialing":
            trial_start = current_period_start
            trial_end = trial_start + timedelta(days=14)

        subscription = Subscription(
            customer_id=customer.id,
            plan=customer.plan,
            billing_cycle=billing_cycle,
            mrr=mrr,
            arr=arr,
            seats_total=seats_total,
            seats_used=seats_used,
            status=status,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=random.random() < 0.05,  # 5% canceling
            trial_start=trial_start,
            trial_end=trial_end
        )
        session.add(subscription)
        subscriptions.append(subscription)

    await session.flush()
    print(f"✅ Created {len(subscriptions)} subscriptions")
    return subscriptions


async def create_conversations(session: AsyncSession, customers: list[Customer], count: int = 500) -> list[Conversation]:
    """Create conversation records with messages"""
    print(f"\n💬 Creating {count} conversations with messages...")
    conversations = []

    # Message templates
    user_messages = [
        "I need help with my account",
        "How do I integrate with your API?",
        "I'm experiencing sync issues",
        "Can you explain the pricing?",
        "I'd like to upgrade my plan",
        "How do I export my data?",
        "I found a bug in the dashboard",
        "What features are included in premium?",
        "I can't log in to my account",
        "How do I add more team members?",
    ]

    agent_messages = [
        "I'd be happy to help you with that. Let me look into this for you.",
        "Thanks for reaching out! I can definitely assist with this.",
        "I understand your concern. Let me provide some information.",
        "Great question! Here's what you need to know:",
        "I've checked your account and here's what I found:",
        "Let me walk you through the steps to resolve this:",
        "I can help you with that upgrade right away.",
        "Here's the documentation that explains this feature:",
        "I see the issue. Let me help you fix this.",
        "No problem! I'm here to help.",
    ]

    for i in range(count):
        # Pick a random customer (weighted towards paying customers)
        customer = random.choice([c for c in customers if c.plan != "free"] * 3 + customers)

        # Conversation details
        primary_intent = random.choice(INTENTS)
        status = random.choices(["resolved", "active", "escalated"], weights=[80, 15, 5])[0]

        # Sentiment (-1 to 1)
        if status == "resolved":
            sentiment_avg = random.uniform(0.5, 1.0)  # Positive
        elif status == "escalated":
            sentiment_avg = random.uniform(-1.0, 0.0)  # Negative
        else:
            sentiment_avg = random.uniform(-0.2, 0.8)  # Mixed

        # Timing
        started_at = random_date_between(90, 0)
        resolution_time_seconds = random.randint(60, 3600) if status == "resolved" else None
        ended_at = started_at + timedelta(seconds=resolution_time_seconds) if resolution_time_seconds else None

        # Agents involved
        agent_count = random.randint(1, 3)
        agents = [f"agent_{random.choice(['support', 'sales', 'billing', 'technical'])}_{j}" for j in range(agent_count)]

        conversation = Conversation(
            customer_id=customer.id,
            status=status,
            primary_intent=primary_intent,
            agents_involved=agents,
            sentiment_avg=round(sentiment_avg, 2),
            kb_articles_used=[f"article_{random.randint(1, 50)}" for _ in range(random.randint(0, 3))],
            started_at=started_at,
            ended_at=ended_at,
            resolution_time_seconds=resolution_time_seconds,
            extra_metadata={
                "channel": random.choice(["web", "email", "slack", "api"]),
                "csat_score": random.randint(1, 5) if status == "resolved" else None,
                "escalated": status == "escalated",
            }
        )
        session.add(conversation)
        await session.flush()  # Flush to get conversation.id
        conversations.append(conversation)

        # Create messages for this conversation
        num_messages = random.randint(2, 10)
        for msg_idx in range(num_messages):
            is_user = msg_idx % 2 == 0
            message_time = started_at + timedelta(seconds=msg_idx * random.randint(30, 300))

            message = Message(
                conversation_id=conversation.id,
                role="user" if is_user else "assistant",
                content=random.choice(user_messages if is_user else agent_messages),
                agent_name=None if is_user else random.choice(agents),
                sentiment=round(random.uniform(-0.5, 1.0), 2) if is_user else None,
                created_at=message_time
            )
            session.add(message)

        if (i + 1) % 100 == 0:
            print(f"  ✓ Created {i + 1}/{count} conversations")

    await session.flush()
    print(f"✅ Created {count} conversations with messages")
    return conversations


async def create_usage_events(session: AsyncSession, customers: list[Customer], count: int = 1000):
    """Create usage event records"""
    print(f"\n📈 Creating {count} usage events...")

    for i in range(count):
        customer = random.choice(customers)

        event = UsageEvent(
            customer_id=customer.id,
            event_type=random.choice(["api_call", "page_view", "feature_usage", "export", "report_generation"]),
            quantity=random.randint(1, 100),
            timestamp=random_date_between(30, 0),
            extra_metadata={
                "feature": random.choice(FEATURES),
                "duration_ms": random.randint(100, 5000),
                "success": random.random() > 0.05,  # 95% success rate
            }
        )
        session.add(event)

        if (i + 1) % 200 == 0:
            print(f"  ✓ Created {i + 1}/{count} usage events")

    await session.flush()
    print(f"✅ Created {count} usage events")


async def create_feature_usage(session: AsyncSession, customers: list[Customer]):
    """Create feature usage analytics"""
    print(f"\n🎯 Creating feature usage analytics...")

    records = 0
    for customer in customers:
        # Each customer uses 3-7 features
        used_features = random.sample(FEATURES, random.randint(3, 7))

        for feature in used_features:
            # Usage over last 30 days
            for day in range(0, 30, random.randint(1, 5)):
                usage_date = datetime.now(timezone.utc) - timedelta(days=day)

                feature_usage = FeatureUsage(
                    customer_id=customer.id,
                    feature_name=feature,
                    usage_count=random.randint(1, 100),
                    date=usage_date
                )
                session.add(feature_usage)
                records += 1

    await session.flush()
    print(f"✅ Created {records} feature usage records")


async def create_sales_pipeline(session: AsyncSession, customers: list[Customer]):
    """Create leads and deals for sales pipeline"""
    print(f"\n💼 Creating sales pipeline...")

    # Create leads (some converted to customers, some still in pipeline)
    lead_count = 0
    for i in range(150):
        # 60% converted, 40% in pipeline
        is_converted = random.random() < 0.6

        if is_converted and customers:
            # Link to existing customer
            customer = random.choice(customers[:60])  # Use first 60 customers as converted leads
            status = "converted"
            converted_at = customer.created_at
            converted_to_customer_id = customer.id
        else:
            status = random.choice(["new", "mql", "sql", "qualified", "disqualified"])
            converted_at = None
            converted_to_customer_id = None

        lead = Lead(
            email=f"lead{i}@example.com",
            name=f"Lead {i}",
            company=random_company_name(),
            qualification_status=status,
            source=random.choice(["website", "referral", "cold_outreach", "event", "partner"]),
            lead_score=random.randint(0, 100),
            converted_at=converted_at,
            converted_to_customer_id=converted_to_customer_id,
            extra_metadata={
                "industry": random.choice(INDUSTRIES),
                "company_size": random.randint(1, 1000),
                "estimated_value": random.randint(1000, 50000),
            }
        )
        session.add(lead)
        lead_count += 1

    await session.flush()
    print(f"✅ Created {lead_count} leads")

    # Create deals for paying customers
    deal_count = 0
    for customer in [c for c in customers if c.plan in ["premium", "enterprise"]]:
        # 70% have active deals
        if random.random() < 0.7:
            deal_value = Decimal(str(customer.extra_metadata.get("mrr", 0))) * Decimal("12")

            deal = Deal(
                customer_id=customer.id,
                name=f"Renewal - {customer.name}",
                value=deal_value,
                stage=random.choice(["qualification", "proposal", "negotiation", "closed_won", "closed_lost"]),
                probability=random.randint(20, 90),
                expected_close_date=random_date_between(-90, 0),  # Future dates: 0 to 90 days from now
                extra_metadata={
                    "deal_type": random.choice(["new_business", "renewal", "upsell", "expansion"]),
                    "competitor": random.choice(["None", "CompetitorA", "CompetitorB"]),
                }
            )
            session.add(deal)
            deal_count += 1

    await session.flush()
    print(f"✅ Created {deal_count} deals")


async def seed_database():
    """Main seeding function"""
    print("=" * 60)
    print("🌱 SEEDING DATABASE WITH TEST DATA")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        try:
            # Check if database already has data
            result = await session.execute(select(Customer).limit(1))
            existing_customer = result.scalar_one_or_none()

            if existing_customer:
                print("\n⚠️  Database already contains data!")
                confirm = input("Do you want to continue anyway? (yes/no): ")
                if confirm.lower() != "yes":
                    print("Cancelled")
                    return

            # Create all the data
            customers = await create_customers(session, count=120)
            await create_subscriptions(session, customers)
            await create_conversations(session, customers, count=500)
            await create_usage_events(session, customers, count=1000)
            await create_feature_usage(session, customers)
            await create_sales_pipeline(session, customers)

            # Commit everything
            print("\n💾 Committing to database...")
            await session.commit()

            print("\n" + "=" * 60)
            print("✅ DATABASE SEEDING COMPLETE!")
            print("=" * 60)
            print(f"\nCreated:")
            print(f"  • {len(customers)} customers")
            print(f"  • {len([c for c in customers if c.plan != 'free'])} subscriptions")
            print(f"  • 500 conversations with messages")
            print(f"  • 1000 usage events")
            print(f"  • Feature usage analytics")
            print(f"  • Sales pipeline (leads & deals)")
            print("\nYour database is ready for testing! 🚀")

        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())