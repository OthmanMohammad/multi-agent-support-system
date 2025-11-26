#!/usr/bin/env python3
"""
Cache warming script for context enrichment.

Preloads context for high-value customers to ensure sub-10ms response times.

Usage:
    python scripts/warm_cache.py --customers all
    python scripts/warm_cache.py --customers enterprise
    python scripts/warm_cache.py --customer-ids cust_1,cust_2,cust_3
    python scripts/warm_cache.py --file customers.txt
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List
import structlog

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.infrastructure.context_enrichment.orchestrator import get_orchestrator
from src.services.infrastructure.context_enrichment.cache import get_cache
from src.services.infrastructure.context_enrichment.types import AgentType
from src.database.connection import get_db_session
from src.database.unit_of_work import UnitOfWork

logger = structlog.get_logger(__name__)


async def get_customer_ids(strategy: str, customer_ids: str = None, file_path: str = None) -> List[str]:
    """
    Get customer IDs based on warming strategy.

    Args:
        strategy: Warming strategy (all, enterprise, high_value, etc.)
        customer_ids: Comma-separated customer IDs
        file_path: Path to file with customer IDs

    Returns:
        List of customer IDs
    """
    if customer_ids:
        # Explicit customer IDs
        return customer_ids.split(',')

    if file_path:
        # Load from file
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    # Query database based on strategy
    async for session in get_db_session():
        uow = UnitOfWork(session)

        if strategy == "all":
            customers = await uow.customers.find_all()
        elif strategy == "enterprise":
            customers = await uow.customers.find_by(plan="enterprise")
        elif strategy == "high_value":
            # Customers with MRR > $1000
            subscriptions = await uow.subscriptions.find_by(status="active")
            customers = [
                await uow.customers.get_by_id(sub.customer_id)
                for sub in subscriptions
                if hasattr(sub, 'mrr') and float(sub.mrr) > 1000
            ]
        elif strategy == "at_risk":
            # Customers with high churn risk
            customers = await uow.customers.find_all()
            customers = [
                c for c in customers
                if c.extra_metadata and c.extra_metadata.get('churn_risk', 0) > 0.5
            ]
        else:
            logger.error("Unknown warming strategy", strategy=strategy)
            return []

        return [str(c.id) for c in customers if c]


async def warm_customer(
    customer_id: str,
    agent_types: List[AgentType],
    orchestrator
) -> dict:
    """
    Warm cache for a single customer.

    Args:
        customer_id: Customer ID
        agent_types: Agent types to warm
        orchestrator: Orchestrator instance

    Returns:
        Warming result
    """
    start = datetime.utcnow()
    results = {}

    for agent_type in agent_types:
        try:
            context = await orchestrator.enrich(
                customer_id=customer_id,
                agent_type=agent_type,
                force_refresh=True  # Force fresh data
            )

            results[agent_type.value] = {
                "status": "success",
                "latency_ms": context.latency_ms
            }

        except Exception as e:
            logger.error(
                "cache_warm_failed",
                customer_id=customer_id,
                agent_type=agent_type.value,
                error=str(e)
            )
            results[agent_type.value] = {
                "status": "failed",
                "error": str(e)
            }

    elapsed_ms = int((datetime.utcnow() - start).total_seconds() * 1000)

    return {
        "customer_id": customer_id,
        "results": results,
        "total_latency_ms": elapsed_ms
    }


async def warm_cache(
    customer_ids: List[str],
    agent_types: List[AgentType],
    batch_size: int = 10,
    verbose: bool = False
):
    """
    Warm cache for multiple customers.

    Args:
        customer_ids: List of customer IDs
        agent_types: Agent types to warm
        batch_size: Number of customers to process in parallel
        verbose: Print detailed progress
    """
    orchestrator = get_orchestrator()
    cache = get_cache()

    logger.info(
        "cache_warming_started",
        customer_count=len(customer_ids),
        agent_types=[at.value for at in agent_types],
        batch_size=batch_size
    )

    if verbose:
        print(f"\n{'='*60}")
        print(f"Cache Warming Started")
        print(f"{'='*60}")
        print(f"Customers: {len(customer_ids)}")
        print(f"Agent Types: {[at.value for at in agent_types]}")
        print(f"Batch Size: {batch_size}")
        print(f"{'='*60}\n")

    start_time = datetime.utcnow()
    total_success = 0
    total_failed = 0

    # Process in batches
    for i in range(0, len(customer_ids), batch_size):
        batch = customer_ids[i:i + batch_size]

        if verbose:
            print(f"Processing batch {i//batch_size + 1}/{(len(customer_ids)-1)//batch_size + 1}...")

        # Process batch in parallel
        tasks = [
            warm_customer(cid, agent_types, orchestrator)
            for cid in batch
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes/failures
        for result in results:
            if isinstance(result, Exception):
                total_failed += 1
            elif result:
                success_count = sum(
                    1 for r in result["results"].values()
                    if r["status"] == "success"
                )
                if success_count > 0:
                    total_success += 1
                else:
                    total_failed += 1

        if verbose:
            print(f"  Completed {min(i + batch_size, len(customer_ids))}/{len(customer_ids)}")

    elapsed = (datetime.utcnow() - start_time).total_seconds()

    # Get cache stats
    stats = await cache.get_stats()

    logger.info(
        "cache_warming_completed",
        customer_count=len(customer_ids),
        success_count=total_success,
        failed_count=total_failed,
        elapsed_seconds=elapsed,
        cache_l1_size=stats.l1_size,
        cache_l2_size=stats.l2_size
    )

    if verbose:
        print(f"\n{'='*60}")
        print(f"Cache Warming Completed")
        print(f"{'='*60}")
        print(f"Total Customers: {len(customer_ids)}")
        print(f"Successful: {total_success}")
        print(f"Failed: {total_failed}")
        print(f"Elapsed Time: {elapsed:.2f}s")
        print(f"Rate: {len(customer_ids)/elapsed:.2f} customers/sec")
        print(f"\nCache Stats:")
        print(f"  L1 Size: {stats.l1_size}")
        print(f"  L2 Size: {stats.l2_size}")
        print(f"  L1 Hit Rate: {stats.l1_hit_rate:.1f}%")
        print(f"  L2 Hit Rate: {stats.l2_hit_rate:.1f}%")
        print(f"{'='*60}\n")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Warm context enrichment cache for customers"
    )

    parser.add_argument(
        "--customers",
        choices=["all", "enterprise", "high_value", "at_risk"],
        help="Customer selection strategy"
    )
    parser.add_argument(
        "--customer-ids",
        help="Comma-separated customer IDs"
    )
    parser.add_argument(
        "--file",
        help="File with customer IDs (one per line)"
    )
    parser.add_argument(
        "--agent-types",
        default="support,billing",
        help="Comma-separated agent types to warm (default: support,billing)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for parallel processing (default: 10)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress"
    )

    args = parser.parse_args()

    # Validate arguments
    if not any([args.customers, args.customer_ids, args.file]):
        parser.error("Must specify --customers, --customer-ids, or --file")

    # Get customer IDs
    customer_ids = await get_customer_ids(
        strategy=args.customers,
        customer_ids=args.customer_ids,
        file_path=args.file
    )

    if not customer_ids:
        print("No customers found to warm")
        return

    # Parse agent types
    agent_types = [
        AgentType(at.strip())
        for at in args.agent_types.split(',')
    ]

    # Warm cache
    await warm_cache(
        customer_ids=customer_ids,
        agent_types=agent_types,
        batch_size=args.batch_size,
        verbose=args.verbose
    )


if __name__ == "__main__":
    asyncio.run(main())
