"""
Standalone test for job store (doesn't require full project setup).

This tests the core job store functionality without dependencies.
"""
import asyncio
from uuid import UUID
from datetime import datetime

# Inline job store code for testing
import json
from typing import Dict, Any, Optional, List
from uuid import uuid4
from datetime import timedelta
from enum import Enum


class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    """Type of job"""
    AGENT_EXECUTION = "agent_execution"
    WORKFLOW_EXECUTION = "workflow_execution"


class JobNotFoundError(Exception):
    """Raised when job ID is not found"""
    pass


class InMemoryJobStore:
    """In-memory job store for testing"""

    def __init__(self):
        self._jobs: Dict[UUID, Dict[str, Any]] = {}
        self._initialized = True

    async def initialize(self):
        """No-op for in-memory store"""
        pass

    async def close(self):
        """No-op for in-memory store"""
        pass

    async def create_job(
        self,
        job_type: JobType,
        agent_name: Optional[str] = None,
        workflow_name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ttl_hours: Optional[int] = None
    ) -> UUID:
        """Create a new job in memory"""
        job_id = uuid4()
        now = datetime.utcnow()

        self._jobs[job_id] = {
            "job_id": str(job_id),
            "job_type": job_type.value,
            "agent_name": agent_name,
            "workflow_name": workflow_name,
            "input_data": input_data or {},
            "metadata": metadata or {},
            "status": JobStatus.PENDING.value,
            "created_at": now.isoformat(),
            "started_at": None,
            "completed_at": None,
            "progress": 0.0,
            "result": None,
            "error": None,
            "error_type": None,
        }

        return job_id

    async def get_job(self, job_id: UUID) -> Dict[str, Any]:
        """Get job from memory"""
        if job_id not in self._jobs:
            raise JobNotFoundError(f"Job {job_id} not found")
        return self._jobs[job_id].copy()

    async def update_job(
        self,
        job_id: UUID,
        status: Optional[JobStatus] = None,
        progress: Optional[float] = None,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        error_type: Optional[str] = None,
        **kwargs
    ):
        """Update job in memory"""
        if job_id not in self._jobs:
            raise JobNotFoundError(f"Job {job_id} not found")

        job = self._jobs[job_id]

        if status is not None:
            job["status"] = status.value
            if status == JobStatus.RUNNING and not job.get("started_at"):
                job["started_at"] = datetime.utcnow().isoformat()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                job["completed_at"] = datetime.utcnow().isoformat()
                job["progress"] = 100.0

        if progress is not None:
            job["progress"] = max(0.0, min(100.0, progress))
        if result is not None:
            job["result"] = result
        if error is not None:
            job["error"] = error
        if error_type is not None:
            job["error_type"] = error_type

        job.update(kwargs)

    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List jobs from memory"""
        jobs = list(self._jobs.values())

        # Apply filters
        if status:
            jobs = [j for j in jobs if j["status"] == status.value]
        if job_type:
            jobs = [j for j in jobs if j["job_type"] == job_type.value]

        return jobs[:limit]


# =============================================================================
# TESTS
# =============================================================================

async def test_create_agent_job():
    """Test creating an agent execution job"""
    store = InMemoryJobStore()
    await store.initialize()

    job_id = await store.create_job(
        job_type=JobType.AGENT_EXECUTION,
        agent_name="meta_router",
        input_data={"query": "Help me upgrade"},
        metadata={"user_id": "user123"}
    )

    assert isinstance(job_id, UUID)
    print(f"✓ Created job: {job_id}")

    # Verify job was created
    job = await store.get_job(job_id)
    assert job["job_id"] == str(job_id)
    assert job["job_type"] == JobType.AGENT_EXECUTION.value
    assert job["agent_name"] == "meta_router"
    assert job["status"] == JobStatus.PENDING.value
    assert job["progress"] == 0.0
    print("✓ Job created successfully with correct data")


async def test_update_job_status():
    """Test updating job status"""
    store = InMemoryJobStore()
    await store.initialize()

    job_id = await store.create_job(
        job_type=JobType.AGENT_EXECUTION,
        agent_name="test_agent"
    )

    # Update to running
    await store.update_job(job_id, status=JobStatus.RUNNING)
    job = await store.get_job(job_id)
    assert job["status"] == JobStatus.RUNNING.value
    assert job["started_at"] is not None
    print("✓ Job status updated to RUNNING")

    # Update to completed
    await store.update_job(
        job_id,
        status=JobStatus.COMPLETED,
        result={"response": "Done!"}
    )
    job = await store.get_job(job_id)
    assert job["status"] == JobStatus.COMPLETED.value
    assert job["completed_at"] is not None
    assert job["progress"] == 100.0
    assert job["result"]["response"] == "Done!"
    print("✓ Job completed successfully")


async def test_full_job_lifecycle():
    """Test complete job lifecycle: create → run → complete"""
    store = InMemoryJobStore()
    await store.initialize()

    # Create job
    job_id = await store.create_job(
        job_type=JobType.AGENT_EXECUTION,
        agent_name="lifecycle_agent",
        input_data={"query": "Test query"}
    )
    print(f"✓ Created job {job_id}")

    # Start job
    await store.update_job(job_id, status=JobStatus.RUNNING)
    job = await store.get_job(job_id)
    assert job["status"] == JobStatus.RUNNING.value
    print("✓ Job started")

    # Update progress
    await store.update_job(job_id, progress=50.0)
    job = await store.get_job(job_id)
    assert job["progress"] == 50.0
    print("✓ Progress updated to 50%")

    # Complete job
    await store.update_job(
        job_id,
        status=JobStatus.COMPLETED,
        result={"response": "Job completed successfully"}
    )

    job = await store.get_job(job_id)
    assert job["status"] == JobStatus.COMPLETED.value
    assert job["completed_at"] is not None
    assert job["progress"] == 100.0
    print("✓ Job completed successfully")
    print(f"✓ Final result: {job['result']}")


async def test_concurrent_jobs():
    """Test creating multiple jobs concurrently"""
    store = InMemoryJobStore()
    await store.initialize()

    async def create_job(i):
        return await store.create_job(
            job_type=JobType.AGENT_EXECUTION,
            agent_name=f"concurrent_agent_{i}"
        )

    # Create 10 jobs concurrently
    job_ids = await asyncio.gather(*[create_job(i) for i in range(10)])

    assert len(job_ids) == 10
    assert len(set(job_ids)) == 10  # All unique
    print(f"✓ Created {len(job_ids)} concurrent jobs successfully")


async def test_error_handling():
    """Test error handling"""
    store = InMemoryJobStore()
    await store.initialize()

    job_id = await store.create_job(
        job_type=JobType.AGENT_EXECUTION,
        agent_name="error_agent"
    )

    # Simulate failure
    await store.update_job(
        job_id,
        status=JobStatus.FAILED,
        error="Agent execution failed",
        error_type="AgentExecutionError"
    )

    job = await store.get_job(job_id)
    assert job["status"] == JobStatus.FAILED.value
    assert job["error"] == "Agent execution failed"
    assert job["error_type"] == "AgentExecutionError"
    print("✓ Error handling works correctly")


async def main():
    """Run all tests"""
    print("=" * 70)
    print("TESTING JOB STORE - STANDALONE")
    print("=" * 70)
    print()

    tests = [
        ("Create Agent Job", test_create_agent_job),
        ("Update Job Status", test_update_job_status),
        ("Full Job Lifecycle", test_full_job_lifecycle),
        ("Concurrent Jobs", test_concurrent_jobs),
        ("Error Handling", test_error_handling),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\nTest: {name}")
        print("-" * 70)
        try:
            await test_func()
            passed += 1
            print(f"✅ {name} PASSED\n")
        except Exception as e:
            failed += 1
            print(f"❌ {name} FAILED: {e}\n")
            import traceback
            traceback.print_exc()

    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Job store is working correctly!")
    else:
        print(f"\n⚠️  {failed} tests failed. Please review.")


if __name__ == "__main__":
    asyncio.run(main())
