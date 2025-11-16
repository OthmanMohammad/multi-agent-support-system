"""
Locust load testing for context enrichment system.

Usage:
    locust -f locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, events
import random
from uuid import uuid4
import time


class ContextEnrichmentUser(HttpUser):
    """
    Simulates user making context enrichment requests.

    Load test profile:
    - Target: 10,000 req/sec
    - p95 latency: < 100ms
    - Cache hit rate: > 80%
    """

    wait_time = between(0.1, 0.5)  # Wait 100-500ms between requests

    # Sample customer IDs to simulate cache hits
    customer_ids = [str(uuid4()) for _ in range(100)]

    def on_start(self):
        """Called when a user starts"""
        self.agent_types = ["support", "billing", "success", "sales"]

    @task(10)
    def enrich_support_agent(self):
        """Most common: Support agent enrichment"""
        customer_id = random.choice(self.customer_ids)

        with self.client.post(
            "/api/v1/context/enrich",
            json={
                "customer_id": customer_id,
                "agent_type": "support",
            },
            catch_response=True,
            name="/context/enrich [support]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                latency_ms = data.get("latency_ms", 0)

                # Verify p95 latency requirement
                if latency_ms > 100:
                    response.failure(f"Latency {latency_ms}ms exceeds 100ms threshold")
                else:
                    response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(3)
    def enrich_billing_agent(self):
        """Billing agent enrichment"""
        customer_id = random.choice(self.customer_ids)

        with self.client.post(
            "/api/v1/context/enrich",
            json={
                "customer_id": customer_id,
                "agent_type": "billing",
            },
            catch_response=True,
            name="/context/enrich [billing]"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status code: {response.status_code}")

    @task(2)
    def enrich_success_agent(self):
        """Success agent enrichment"""
        customer_id = random.choice(self.customer_ids)

        with self.client.post(
            "/api/v1/context/enrich",
            json={
                "customer_id": customer_id,
                "agent_type": "success",
            },
            catch_response=True,
            name="/context/enrich [success]"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def enrich_with_conversation(self):
        """Enrichment with conversation ID"""
        customer_id = random.choice(self.customer_ids)
        conversation_id = str(uuid4())

        with self.client.post(
            "/api/v1/context/enrich",
            json={
                "customer_id": customer_id,
                "agent_type": "support",
                "conversation_id": conversation_id,
            },
            catch_response=True,
            name="/context/enrich [with_conversation]"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def force_refresh(self):
        """Force refresh to bypass cache"""
        customer_id = random.choice(self.customer_ids)

        with self.client.post(
            "/api/v1/context/enrich",
            json={
                "customer_id": customer_id,
                "agent_type": "support",
                "force_refresh": True,
            },
            catch_response=True,
            name="/context/enrich [force_refresh]"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def health_check(self):
        """Health check endpoint"""
        with self.client.get(
            "/api/v1/context/health",
            catch_response=True,
            name="/context/health"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def cache_stats(self):
        """Get cache statistics"""
        with self.client.get(
            "/api/v1/context/cache/stats",
            catch_response=True,
            name="/context/cache/stats"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status code: {response.status_code}")


class BurstUser(HttpUser):
    """
    Simulates burst traffic patterns.

    Useful for testing system behavior under sudden load spikes.
    """

    wait_time = between(0.01, 0.1)  # Very short wait times

    customer_ids = [str(uuid4()) for _ in range(50)]

    @task
    def burst_enrichment(self):
        """Rapid enrichment requests"""
        customer_id = random.choice(self.customer_ids)

        self.client.post(
            "/api/v1/context/enrich",
            json={
                "customer_id": customer_id,
                "agent_type": random.choice(["support", "billing"]),
            },
            name="/context/enrich [burst]"
        )


# Custom events for detailed metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("=" * 60)
    print("Context Enrichment Load Test Started")
    print("=" * 60)
    print(f"Target: 10,000 req/sec")
    print(f"Requirement: p95 < 100ms")
    print(f"Cache hit rate target: > 80%")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("=" * 60)
    print("Context Enrichment Load Test Completed")
    print("=" * 60)

    # Print summary statistics
    stats = environment.stats
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    p95 = stats.total.get_response_time_percentile(0.95)

    print(f"Total requests: {total_requests:,}")
    print(f"Total failures: {total_failures:,}")
    print(f"Failure rate: {(total_failures/total_requests*100):.2f}%")
    print(f"p95 latency: {p95:.2f}ms")
    print(f"RPS: {stats.total.total_rps:.2f}")

    # Verify requirements
    print("\nRequirements Check:")
    print(f"  ??? p95 < 100ms: {'PASS' if p95 < 100 else 'FAIL'} ({p95:.2f}ms)")
    print(f"  ??? Failure rate < 1%: {'PASS' if (total_failures/total_requests*100) < 1 else 'FAIL'}")

    print("=" * 60)
