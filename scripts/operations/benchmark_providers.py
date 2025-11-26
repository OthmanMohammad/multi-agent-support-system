#!/usr/bin/env python3
"""
Benchmark script for context providers.

Measures latency, throughput, and error rates for all providers.

Usage:
    python scripts/benchmark_providers.py
    python scripts/benchmark_providers.py --provider customer_intelligence
    python scripts/benchmark_providers.py --iterations 100
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import statistics
import structlog

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.infrastructure.context_enrichment.registry import get_registry
from src.services.infrastructure.context_enrichment.types import ProviderStatus
from src.database.connection import get_db_session
from src.database.unit_of_work import UnitOfWork

logger = structlog.get_logger(__name__)


async def get_sample_customer_id() -> str:
    """Get a sample customer ID from database"""
    async for session in get_db_session():
        uow = UnitOfWork(session)
        customers = await uow.customers.find_all()
        if customers:
            return str(customers[0].id)
        return "00000000-0000-0000-0000-000000000000"


async def benchmark_provider(
    provider_name: str,
    customer_id: str,
    iterations: int = 100
) -> Dict:
    """
    Benchmark a single provider.

    Args:
        provider_name: Provider name
        customer_id: Customer ID to test with
        iterations: Number of iterations

    Returns:
        Benchmark results
    """
    registry = get_registry()
    provider = registry.get_provider(provider_name)

    if not provider:
        return {
            "provider": provider_name,
            "status": "not_found",
            "error": "Provider not found in registry"
        }

    latencies = []
    errors = 0
    timeouts = 0

    logger.info(
        "benchmarking_provider",
        provider=provider_name,
        iterations=iterations
    )

    for i in range(iterations):
        start = datetime.utcnow()

        try:
            data = await asyncio.wait_for(
                provider.fetch(customer_id=customer_id),
                timeout=5.0  # 5 second timeout
            )

            latency_ms = (datetime.utcnow() - start).total_seconds() * 1000
            latencies.append(latency_ms)

        except asyncio.TimeoutError:
            timeouts += 1
            latencies.append(5000)  # 5 second timeout

        except Exception as e:
            errors += 1
            logger.warning(
                "provider_error",
                provider=provider_name,
                iteration=i,
                error=str(e)
            )

    # Calculate statistics
    if latencies:
        return {
            "provider": provider_name,
            "status": "success",
            "iterations": iterations,
            "latency": {
                "min": min(latencies),
                "max": max(latencies),
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
                "p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
            },
            "errors": errors,
            "timeouts": timeouts,
            "error_rate": (errors / iterations) * 100,
            "timeout_rate": (timeouts / iterations) * 100
        }
    else:
        return {
            "provider": provider_name,
            "status": "failed",
            "error": "All requests failed"
        }


async def benchmark_all_providers(iterations: int = 100, verbose: bool = False):
    """
    Benchmark all registered providers.

    Args:
        iterations: Number of iterations per provider
        verbose: Print detailed results
    """
    registry = get_registry()
    provider_names = registry.list_providers()

    if not provider_names:
        print("No providers registered")
        return

    # Get sample customer ID
    customer_id = await get_sample_customer_id()

    if verbose:
        print(f"\n{'='*80}")
        print(f"Provider Benchmark")
        print(f"{'='*80}")
        print(f"Providers: {len(provider_names)}")
        print(f"Iterations per provider: {iterations}")
        print(f"Customer ID: {customer_id}")
        print(f"{'='*80}\n")

    results = []

    for provider_name in provider_names:
        if verbose:
            print(f"Benchmarking {provider_name}...", end=" ", flush=True)

        result = await benchmark_provider(
            provider_name=provider_name,
            customer_id=customer_id,
            iterations=iterations
        )

        results.append(result)

        if verbose:
            if result["status"] == "success":
                print(f"??? (p95: {result['latency']['p95']:.2f}ms)")
            else:
                print(f"??? ({result.get('error', 'failed')})")

    # Print summary
    if verbose:
        print(f"\n{'='*80}")
        print(f"Benchmark Results")
        print(f"{'='*80}\n")

        # Sort by p95 latency
        successful_results = [r for r in results if r["status"] == "success"]
        successful_results.sort(key=lambda r: r["latency"]["p95"])

        for result in successful_results:
            name = result["provider"]
            lat = result["latency"]

            print(f"{name:30} | p50: {lat['median']:6.2f}ms | p95: {lat['p95']:6.2f}ms | "
                  f"p99: {lat['p99']:6.2f}ms | errors: {result['errors']}")

        # Show failed providers
        failed_results = [r for r in results if r["status"] != "success"]
        if failed_results:
            print(f"\nFailed Providers:")
            for result in failed_results:
                print(f"  {result['provider']}: {result.get('error', 'unknown error')}")

        # Overall statistics
        print(f"\n{'='*80}")
        print(f"Overall Statistics")
        print(f"{'='*80}")

        if successful_results:
            all_p95s = [r["latency"]["p95"] for r in successful_results]
            all_errors = sum(r["errors"] for r in successful_results)
            total_requests = len(successful_results) * iterations

            print(f"Total Providers: {len(provider_names)}")
            print(f"Successful: {len(successful_results)}")
            print(f"Failed: {len(failed_results)}")
            print(f"Fastest p95: {min(all_p95s):.2f}ms ({successful_results[0]['provider']})")
            print(f"Slowest p95: {max(all_p95s):.2f}ms")
            print(f"Average p95: {statistics.mean(all_p95s):.2f}ms")
            print(f"Total Errors: {all_errors}/{total_requests} ({all_errors/total_requests*100:.2f}%)")

        print(f"{'='*80}\n")

    return results


async def benchmark_concurrent_load(
    provider_name: str,
    customer_id: str,
    concurrency: int = 10,
    duration_seconds: int = 10,
    verbose: bool = False
):
    """
    Benchmark provider under concurrent load.

    Args:
        provider_name: Provider name
        customer_id: Customer ID
        concurrency: Number of concurrent requests
        duration_seconds: Test duration in seconds
        verbose: Print results
    """
    registry = get_registry()
    provider = registry.get_provider(provider_name)

    if not provider:
        print(f"Provider {provider_name} not found")
        return

    if verbose:
        print(f"\n{'='*60}")
        print(f"Concurrent Load Test: {provider_name}")
        print(f"{'='*60}")
        print(f"Concurrency: {concurrency}")
        print(f"Duration: {duration_seconds}s")
        print(f"{'='*60}\n")

    async def worker():
        """Worker that continuously makes requests"""
        latencies = []
        errors = 0
        end_time = datetime.utcnow().timestamp() + duration_seconds

        while datetime.utcnow().timestamp() < end_time:
            start = datetime.utcnow()
            try:
                await provider.fetch(customer_id=customer_id)
                latency = (datetime.utcnow() - start).total_seconds() * 1000
                latencies.append(latency)
            except Exception:
                errors += 1

        return latencies, errors

    # Run workers
    start = datetime.utcnow()
    results = await asyncio.gather(*[worker() for _ in range(concurrency)])
    elapsed = (datetime.utcnow() - start).total_seconds()

    # Aggregate results
    all_latencies = []
    total_errors = 0

    for latencies, errors in results:
        all_latencies.extend(latencies)
        total_errors += errors

    total_requests = len(all_latencies) + total_errors
    throughput = total_requests / elapsed

    if verbose and all_latencies:
        print(f"Results:")
        print(f"  Total Requests: {total_requests:,}")
        print(f"  Successful: {len(all_latencies):,}")
        print(f"  Errors: {total_errors:,}")
        print(f"  Throughput: {throughput:.2f} req/sec")
        print(f"  Latency:")
        print(f"    Min: {min(all_latencies):.2f}ms")
        print(f"    Mean: {statistics.mean(all_latencies):.2f}ms")
        print(f"    p95: {statistics.quantiles(all_latencies, n=20)[18]:.2f}ms")
        print(f"    Max: {max(all_latencies):.2f}ms")
        print(f"{'='*60}\n")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Benchmark context providers"
    )

    parser.add_argument(
        "--provider",
        help="Specific provider to benchmark (benchmarks all if not specified)"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of iterations per provider (default: 100)"
    )
    parser.add_argument(
        "--concurrent",
        action="store_true",
        help="Run concurrent load test"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Concurrency level for load test (default: 10)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Duration for load test in seconds (default: 10)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed results"
    )

    args = parser.parse_args()

    customer_id = await get_sample_customer_id()

    if args.concurrent:
        # Concurrent load test
        provider_name = args.provider or "customer_intelligence"
        await benchmark_concurrent_load(
            provider_name=provider_name,
            customer_id=customer_id,
            concurrency=args.concurrency,
            duration_seconds=args.duration,
            verbose=args.verbose
        )
    elif args.provider:
        # Single provider benchmark
        result = await benchmark_provider(
            provider_name=args.provider,
            customer_id=customer_id,
            iterations=args.iterations
        )

        if args.verbose:
            print(f"\nResults for {args.provider}:")
            if result["status"] == "success":
                print(f"  Mean: {result['latency']['mean']:.2f}ms")
                print(f"  Median: {result['latency']['median']:.2f}ms")
                print(f"  p95: {result['latency']['p95']:.2f}ms")
                print(f"  p99: {result['latency']['p99']:.2f}ms")
                print(f"  Errors: {result['errors']}/{args.iterations}")
            else:
                print(f"  Status: {result['status']}")
                print(f"  Error: {result.get('error')}")
    else:
        # Benchmark all providers
        await benchmark_all_providers(
            iterations=args.iterations,
            verbose=args.verbose
        )


if __name__ == "__main__":
    asyncio.run(main())
