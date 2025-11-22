#!/usr/bin/env python3
"""
Orphaned GPU Instance Cleanup Script

Safety mechanism to prevent forgotten GPU instances from running indefinitely.

Should be run periodically via cron job (e.g., daily at 4 AM):
    0 4 * * * cd ~/multi-agent-system && python scripts/cleanup_orphaned_gpus.py

Vast.ai GPU Orchestration
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.vllm.vastai.orchestrator import gpu_orchestrator
from src.utils.logging.setup import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)


async def main():
    """
    Cleanup any orphaned GPU instances.

    An orphaned instance is one that:
    - Is running on Vast.ai
    - Is not tracked by the orchestrator
    - Was likely left running due to application crash or restart
    """
    logger.info(
        "orphaned_gpu_cleanup_started",
        timestamp=datetime.utcnow().isoformat(),
        script="cleanup_orphaned_gpus.py",
    )

    try:
        # Run cleanup
        await gpu_orchestrator.cleanup_orphaned_instances()

        logger.info(
            "orphaned_gpu_cleanup_completed",
            status="success",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Exit successfully
        sys.exit(0)

    except Exception as e:
        logger.error(
            "orphaned_gpu_cleanup_failed",
            error=str(e),
            exc_info=True,
            timestamp=datetime.utcnow().isoformat(),
        )

        # Exit with error code
        sys.exit(1)

    finally:
        # Cleanup resources
        await gpu_orchestrator.close()


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
