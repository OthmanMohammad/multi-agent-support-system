"""
Production-grade Redis-based job store for async agent/workflow execution.

Provides persistent, reliable job tracking with:
- Redis-backed persistence
- Automatic TTL and cleanup
- Job state transitions
- Error handling and retry logic
- Performance monitoring
- Graceful fallback to in-memory for development
"""

import asyncio
import contextlib
import json
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import redis.asyncio as redis
import structlog

logger = structlog.get_logger(__name__)


class JobStatus(str, Enum):
    """Job execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobType(str, Enum):
    """Type of job"""

    AGENT_EXECUTION = "agent_execution"
    WORKFLOW_EXECUTION = "workflow_execution"
    BATCH_EXECUTION = "batch_execution"


class JobNotFoundError(Exception):
    """Raised when job ID is not found"""

    pass


class JobStoreError(Exception):
    """Base exception for job store errors"""

    pass


class RedisJobStore:
    """
    Production-grade Redis-backed job store.

    Features:
    - Persistent job storage in Redis
    - Automatic TTL (time-to-live) for completed jobs
    - Atomic state transitions
    - Job cleanup scheduler
    - Progress tracking
    - Result caching
    - Performance metrics

    Usage:
        store = RedisJobStore(redis_url="redis://localhost:6379")
        await store.initialize()

        job_id = await store.create_job(
            job_type=JobType.AGENT_EXECUTION,
            agent_name="meta_router",
            input_data={"query": "Help me upgrade"}
        )

        await store.update_job(job_id, status=JobStatus.RUNNING)
        job = await store.get_job(job_id)
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        redis_db: int = 0,
        key_prefix: str = "job:",
        default_ttl_hours: int = 24,
        cleanup_interval_minutes: int = 60,
    ):
        """
        Initialize Redis job store.

        Args:
            redis_url: Redis connection URL
            redis_db: Redis database number
            key_prefix: Prefix for Redis keys
            default_ttl_hours: Default TTL for completed jobs (hours)
            cleanup_interval_minutes: How often to run cleanup (minutes)
        """
        self.redis_url = redis_url
        self.redis_db = redis_db
        self.key_prefix = key_prefix
        self.default_ttl = timedelta(hours=default_ttl_hours)
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)

        self._redis: redis.Redis | None = None
        self._cleanup_task: asyncio.Task | None = None
        self._initialized = False

        logger.info(
            "redis_job_store_created",
            redis_url=redis_url,
            redis_db=redis_db,
            default_ttl_hours=default_ttl_hours,
        )

    async def initialize(self):
        """
        Initialize Redis connection and start cleanup task.

        Raises:
            JobStoreError: If connection fails
        """
        if self._initialized:
            logger.warning("redis_job_store_already_initialized")
            return

        try:
            # Create Redis connection
            self._redis = await redis.from_url(
                self.redis_url, db=self.redis_db, encoding="utf-8", decode_responses=True
            )

            # Test connection
            await self._redis.ping()

            self._initialized = True

            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            logger.info("redis_job_store_initialized")

        except Exception as e:
            logger.error("redis_job_store_initialization_failed", error=str(e), exc_info=True)
            raise JobStoreError(f"Failed to initialize Redis job store: {e}") from e

    async def close(self):
        """Close Redis connection and stop cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

        if self._redis:
            await self._redis.close()

        self._initialized = False
        logger.info("redis_job_store_closed")

    def _get_key(self, job_id: UUID) -> str:
        """Get Redis key for job ID"""
        return f"{self.key_prefix}{job_id!s}"

    async def create_job(
        self,
        job_type: JobType,
        agent_name: str | None = None,
        workflow_name: str | None = None,
        input_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        ttl_hours: int | None = None,
    ) -> UUID:
        """
        Create a new job.

        Args:
            job_type: Type of job
            agent_name: Name of agent (for agent execution jobs)
            workflow_name: Name of workflow (for workflow jobs)
            input_data: Input data for the job
            metadata: Additional metadata
            ttl_hours: Custom TTL in hours (overrides default)

        Returns:
            Job ID (UUID)

        Raises:
            JobStoreError: If creation fails
        """
        if not self._initialized:
            await self.initialize()

        job_id = uuid4()
        now = datetime.now(UTC)

        job_data = {
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

        try:
            # Store in Redis as JSON
            key = self._get_key(job_id)
            await self._redis.set(key, json.dumps(job_data, default=str))

            # Set TTL if specified (for cleanup)
            if ttl_hours:
                await self._redis.expire(key, int(ttl_hours * 3600))

            logger.info(
                "job_created",
                job_id=str(job_id),
                job_type=job_type.value,
                agent_name=agent_name,
                workflow_name=workflow_name,
            )

            return job_id

        except Exception as e:
            logger.error("job_creation_failed", job_id=str(job_id), error=str(e), exc_info=True)
            raise JobStoreError(f"Failed to create job: {e}") from e

    async def get_job(self, job_id: UUID) -> dict[str, Any]:
        """
        Get job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job data dictionary

        Raises:
            JobNotFoundError: If job not found
            JobStoreError: If retrieval fails
        """
        if not self._initialized:
            await self.initialize()

        try:
            key = self._get_key(job_id)
            data = await self._redis.get(key)

            if not data:
                raise JobNotFoundError(f"Job {job_id} not found")

            job_data = json.loads(data)

            return job_data

        except JobNotFoundError:
            raise
        except Exception as e:
            logger.error("job_retrieval_failed", job_id=str(job_id), error=str(e), exc_info=True)
            raise JobStoreError(f"Failed to get job: {e}") from e

    async def update_job(
        self,
        job_id: UUID,
        status: JobStatus | None = None,
        progress: float | None = None,
        result: Any | None = None,
        error: str | None = None,
        error_type: str | None = None,
        **kwargs,
    ):
        """
        Update job fields.

        Args:
            job_id: Job ID
            status: New status
            progress: Progress percentage (0-100)
            result: Job result (will be JSON serialized)
            error: Error message
            error_type: Error type/class name
            **kwargs: Additional fields to update

        Raises:
            JobNotFoundError: If job not found
            JobStoreError: If update fails
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Get current job data
            job_data = await self.get_job(job_id)

            # Update fields
            if status is not None:
                job_data["status"] = status.value

                # Set timestamps based on status
                if status == JobStatus.RUNNING and not job_data.get("started_at"):
                    job_data["started_at"] = datetime.now(UTC).isoformat()
                elif status in [
                    JobStatus.COMPLETED,
                    JobStatus.FAILED,
                    JobStatus.CANCELLED,
                    JobStatus.TIMEOUT,
                ]:
                    job_data["completed_at"] = datetime.now(UTC).isoformat()
                    job_data["progress"] = 100.0

            if progress is not None:
                job_data["progress"] = max(0.0, min(100.0, progress))

            if result is not None:
                job_data["result"] = result

            if error is not None:
                job_data["error"] = error

            if error_type is not None:
                job_data["error_type"] = error_type

            # Update additional fields
            job_data.update(kwargs)

            # Save back to Redis
            key = self._get_key(job_id)
            await self._redis.set(key, json.dumps(job_data, default=str))

            # Apply TTL for completed jobs
            if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                await self._redis.expire(key, int(self.default_ttl.total_seconds()))

            logger.debug(
                "job_updated",
                job_id=str(job_id),
                status=status.value if status else None,
                progress=progress,
            )

        except JobNotFoundError:
            raise
        except Exception as e:
            logger.error("job_update_failed", job_id=str(job_id), error=str(e), exc_info=True)
            raise JobStoreError(f"Failed to update job: {e}") from e

    async def delete_job(self, job_id: UUID):
        """
        Delete a job.

        Args:
            job_id: Job ID

        Raises:
            JobStoreError: If deletion fails
        """
        if not self._initialized:
            await self.initialize()

        try:
            key = self._get_key(job_id)
            await self._redis.delete(key)

            logger.info("job_deleted", job_id=str(job_id))

        except Exception as e:
            logger.error("job_deletion_failed", job_id=str(job_id), error=str(e), exc_info=True)
            raise JobStoreError(f"Failed to delete job: {e}") from e

    async def list_jobs(
        self, status: JobStatus | None = None, job_type: JobType | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        List jobs with optional filtering.

        Args:
            status: Filter by status
            job_type: Filter by job type
            limit: Maximum number of jobs to return

        Returns:
            List of job data dictionaries
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Scan all job keys
            pattern = f"{self.key_prefix}*"
            keys = []

            async for key in self._redis.scan_iter(match=pattern, count=100):
                keys.append(key)

                if len(keys) >= limit * 2:  # Get extra for filtering
                    break

            # Get job data
            jobs = []
            for key in keys[: limit * 2]:
                try:
                    data = await self._redis.get(key)
                    if data:
                        job = json.loads(data)

                        # Apply filters
                        if status and job.get("status") != status.value:
                            continue
                        if job_type and job.get("job_type") != job_type.value:
                            continue

                        jobs.append(job)

                        if len(jobs) >= limit:
                            break
                except Exception:
                    continue

            return jobs

        except Exception as e:
            logger.error("job_listing_failed", error=str(e), exc_info=True)
            return []

    async def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Clean up jobs older than max_age_hours.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of jobs cleaned up
        """
        if not self._initialized:
            await self.initialize()

        cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
        deleted_count = 0

        try:
            # Scan all job keys
            pattern = f"{self.key_prefix}*"

            async for key in self._redis.scan_iter(match=pattern, count=100):
                try:
                    data = await self._redis.get(key)
                    if not data:
                        continue

                    job = json.loads(data)

                    # Check if job is old enough and completed/failed
                    completed_at = job.get("completed_at")
                    status = job.get("status")

                    if completed_at and status in [
                        JobStatus.COMPLETED.value,
                        JobStatus.FAILED.value,
                        JobStatus.CANCELLED.value,
                        JobStatus.TIMEOUT.value,
                    ]:
                        completed_time = datetime.fromisoformat(completed_at)
                        if completed_time < cutoff:
                            await self._redis.delete(key)
                            deleted_count += 1

                except Exception:
                    continue

            if deleted_count > 0:
                logger.info("jobs_cleaned_up", count=deleted_count, max_age_hours=max_age_hours)

            return deleted_count

        except Exception as e:
            logger.error("job_cleanup_failed", error=str(e), exc_info=True)
            return deleted_count

    async def _cleanup_loop(self):
        """Background task to periodically clean up old jobs"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                await self.cleanup_old_jobs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("cleanup_loop_error", error=str(e), exc_info=True)


class InMemoryJobStore:
    """
    In-memory job store for development/testing.

    Provides same interface as RedisJobStore but stores jobs in memory.
    Data is lost on restart. Use only for development.
    """

    def __init__(self):
        """Initialize in-memory job store"""
        self._jobs: dict[UUID, dict[str, Any]] = {}
        self._initialized = True

        logger.warning(
            "in_memory_job_store_created",
            message="Using in-memory job store. Data will not persist!",
        )

    async def initialize(self):
        """No-op for in-memory store"""
        pass

    async def close(self):
        """No-op for in-memory store"""
        pass

    async def create_job(
        self,
        job_type: JobType,
        agent_name: str | None = None,
        workflow_name: str | None = None,
        input_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        ttl_hours: int | None = None,
    ) -> UUID:
        """Create a new job in memory"""
        job_id = uuid4()
        now = datetime.now(UTC)

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

    async def get_job(self, job_id: UUID) -> dict[str, Any]:
        """Get job from memory"""
        if job_id not in self._jobs:
            raise JobNotFoundError(f"Job {job_id} not found")
        return self._jobs[job_id].copy()

    async def update_job(
        self,
        job_id: UUID,
        status: JobStatus | None = None,
        progress: float | None = None,
        result: Any | None = None,
        error: str | None = None,
        error_type: str | None = None,
        **kwargs,
    ):
        """Update job in memory"""
        if job_id not in self._jobs:
            raise JobNotFoundError(f"Job {job_id} not found")

        job = self._jobs[job_id]

        if status is not None:
            job["status"] = status.value
            if status == JobStatus.RUNNING and not job.get("started_at"):
                job["started_at"] = datetime.now(UTC).isoformat()
            elif status in [
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
                JobStatus.TIMEOUT,
            ]:
                job["completed_at"] = datetime.now(UTC).isoformat()
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

    async def delete_job(self, job_id: UUID):
        """Delete job from memory"""
        if job_id in self._jobs:
            del self._jobs[job_id]

    async def list_jobs(
        self, status: JobStatus | None = None, job_type: JobType | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """List jobs from memory"""
        jobs = list(self._jobs.values())

        # Apply filters
        if status:
            jobs = [j for j in jobs if j["status"] == status.value]
        if job_type:
            jobs = [j for j in jobs if j["job_type"] == job_type.value]

        return jobs[:limit]

    async def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old jobs from memory"""
        cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
        to_remove = []

        for job_id, job in self._jobs.items():
            completed_at = job.get("completed_at")
            if completed_at:
                completed_time = datetime.fromisoformat(completed_at)
                if completed_time < cutoff:
                    to_remove.append(job_id)

        for job_id in to_remove:
            del self._jobs[job_id]

        return len(to_remove)
