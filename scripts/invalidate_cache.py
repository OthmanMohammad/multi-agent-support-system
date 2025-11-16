#!/usr/bin/env python3
"""
Cache invalidation script for context enrichment.

Invalidates cached context when customer data changes.

Usage:
    python scripts/invalidate_cache.py --customer cust_123
    python scripts/invalidate_cache.py --customer cust_123 --agent-type support
    python scripts/invalidate_cache.py --all
    python scripts/invalidate_cache.py --file customers.txt
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import structlog

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.infrastructure.context_enrichment.orchestrator import get_orchestrator
from src.services.infrastructure.context_enrichment.cache import get_cache
from src.services.infrastructure.context_enrichment.types import AgentType
from src.database.connection import get_db_session
from src.database.unit_of_work import UnitOfWork

logger = structlog.get_logger(__name__)


async def invalidate_customer(
    customer_id: str,
    agent_type: Optional[AgentType] = None,
    verbose: bool = False
):
    """
    Invalidate cache for a single customer.

    Args:
        customer_id: Customer ID
        agent_type: Specific agent type (invalidates all if None)
        verbose: Print progress
    """
    orchestrator = get_orchestrator()

    try:
        await orchestrator.invalidate_cache(
            customer_id=customer_id,
            agent_type=agent_type
        )

        if verbose:
            if agent_type:
                print(f"??? Invalidated cache for customer {customer_id} (agent: {agent_type.value})")
            else:
                print(f"??? Invalidated cache for customer {customer_id} (all agents)")

        return True

    except Exception as e:
        logger.error(
            "cache_invalidation_failed",
            customer_id=customer_id,
            agent_type=agent_type.value if agent_type else None,
            error=str(e)
        )

        if verbose:
            print(f"??? Failed to invalidate cache for customer {customer_id}: {str(e)}")

        return False


async def invalidate_multiple(
    customer_ids: List[str],
    agent_type: Optional[AgentType] = None,
    batch_size: int = 100,
    verbose: bool = False
):
    """
    Invalidate cache for multiple customers.

    Args:
        customer_ids: List of customer IDs
        agent_type: Specific agent type (invalidates all if None)
        batch_size: Batch size for parallel processing
        verbose: Print progress
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"Cache Invalidation")
        print(f"{'='*60}")
        print(f"Customers: {len(customer_ids)}")
        if agent_type:
            print(f"Agent Type: {agent_type.value}")
        else:
            print(f"Agent Type: All")
        print(f"{'='*60}\n")

    start_time = datetime.utcnow()
    success_count = 0
    failed_count = 0

    # Process in batches
    for i in range(0, len(customer_ids), batch_size):
        batch = customer_ids[i:i + batch_size]

        if verbose:
            print(f"Processing batch {i//batch_size + 1}/{(len(customer_ids)-1)//batch_size + 1}...")

        # Process batch in parallel
        tasks = [
            invalidate_customer(cid, agent_type, verbose=False)
            for cid in batch
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes/failures
        for result in results:
            if isinstance(result, Exception) or result is False:
                failed_count += 1
            else:
                success_count += 1

    elapsed = (datetime.utcnow() - start_time).total_seconds()

    if verbose:
        print(f"\n{'='*60}")
        print(f"Invalidation Completed")
        print(f"{'='*60}")
        print(f"Total: {len(customer_ids)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {failed_count}")
        print(f"Elapsed Time: {elapsed:.2f}s")
        print(f"Rate: {len(customer_ids)/elapsed:.2f} customers/sec")
        print(f"{'='*60}\n")


async def invalidate_all(verbose: bool = False):
    """
    Invalidate entire cache.

    Args:
        verbose: Print progress
    """
    cache = get_cache()

    if verbose:
        print(f"\n{'='*60}")
        print(f"Clearing entire cache...")
        print(f"{'='*60}\n")

    start_time = datetime.utcnow()

    try:
        await cache.clear()
        elapsed = (datetime.utcnow() - start_time).total_seconds()

        if verbose:
            print(f"??? Cache cleared successfully")
            print(f"Elapsed Time: {elapsed:.2f}s")
            print(f"{'='*60}\n")

        return True

    except Exception as e:
        logger.error("cache_clear_failed", error=str(e))

        if verbose:
            print(f"??? Failed to clear cache: {str(e)}")
            print(f"{'='*60}\n")

        return False


async def get_all_customer_ids() -> List[str]:
    """Get all customer IDs from database"""
    async for session in get_db_session():
        uow = UnitOfWork(session)
        customers = await uow.customers.find_all()
        return [str(c.id) for c in customers if c]


async def load_customer_ids_from_file(file_path: str) -> List[str]:
    """Load customer IDs from file"""
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]


async def invalidate_pattern(
    pattern: str,
    verbose: bool = False
):
    """
    Invalidate cache entries matching a pattern.

    Args:
        pattern: Redis pattern (e.g., "context:*:support")
        verbose: Print progress
    """
    cache = get_cache()

    if not cache.redis_available:
        print("Redis not available - pattern invalidation requires Redis")
        return

    if verbose:
        print(f"\n{'='*60}")
        print(f"Invalidating pattern: {pattern}")
        print(f"{'='*60}\n")

    try:
        # Scan and delete matching keys
        deleted_count = 0
        cursor = 0

        while True:
            cursor, keys = await cache.redis_client.scan(
                cursor=cursor,
                match=pattern,
                count=100
            )

            if keys:
                await cache.redis_client.delete(*keys)
                deleted_count += len(keys)

            if cursor == 0:
                break

        if verbose:
            print(f"??? Invalidated {deleted_count} cache entries")
            print(f"{'='*60}\n")

        return deleted_count

    except Exception as e:
        logger.error("pattern_invalidation_failed", pattern=pattern, error=str(e))

        if verbose:
            print(f"??? Pattern invalidation failed: {str(e)}")
            print(f"{'='*60}\n")

        return 0


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Invalidate context enrichment cache"
    )

    parser.add_argument(
        "--customer",
        help="Customer ID to invalidate"
    )
    parser.add_argument(
        "--file",
        help="File with customer IDs (one per line)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Invalidate entire cache"
    )
    parser.add_argument(
        "--pattern",
        help="Redis pattern to invalidate (e.g., 'context:*:support')"
    )
    parser.add_argument(
        "--agent-type",
        choices=["support", "billing", "success", "sales", "legal", "product", "operations"],
        help="Specific agent type to invalidate"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for parallel processing (default: 100)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress"
    )

    args = parser.parse_args()

    # Validate arguments
    if not any([args.customer, args.file, args.all, args.pattern]):
        parser.error("Must specify --customer, --file, --all, or --pattern")

    # Parse agent type
    agent_type = AgentType(args.agent_type) if args.agent_type else None

    if args.all:
        # Invalidate entire cache
        await invalidate_all(verbose=args.verbose)

    elif args.pattern:
        # Invalidate by pattern
        await invalidate_pattern(
            pattern=args.pattern,
            verbose=args.verbose
        )

    elif args.customer:
        # Single customer
        await invalidate_customer(
            customer_id=args.customer,
            agent_type=agent_type,
            verbose=args.verbose
        )

    elif args.file:
        # Multiple customers from file
        customer_ids = await load_customer_ids_from_file(args.file)

        if not customer_ids:
            print("No customer IDs found in file")
            return

        await invalidate_multiple(
            customer_ids=customer_ids,
            agent_type=agent_type,
            batch_size=args.batch_size,
            verbose=args.verbose
        )


if __name__ == "__main__":
    asyncio.run(main())
