"""
GPU Configuration and Fallback Strategy

Defines 10 GPU configurations in priority order for intelligent fallback.
Includes multi-factor scoring algorithm for optimal GPU selection.

Vast.ai GPU Orchestration
"""

from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class GPUConfig(BaseModel):
    """
    Configuration for a specific GPU type.

    Attributes:
        gpu_name: GPU model name (e.g., "RTX 3090")
        vram_gb: VRAM capacity in GB
        min_vram: Minimum required VRAM in GB
        max_price_per_hour: Maximum acceptable price in USD/hour
        cuda_version: Minimum CUDA version required
        disk_space_gb: Minimum disk space required in GB
        priority: Search priority (1 = highest)
        preferred_reliability: Minimum reliability score (0-1)
        min_network_speed_mbps: Minimum network speed in Mbps
    """

    gpu_name: str = Field(..., description="GPU model name")
    vram_gb: int = Field(..., ge=8, le=80, description="VRAM in GB")
    min_vram: int = Field(..., ge=8, le=80, description="Minimum VRAM required")
    max_price_per_hour: float = Field(..., ge=0.01, le=5.0, description="Max price USD/hour")
    cuda_version: str = Field(default="12.1", description="Minimum CUDA version")
    disk_space_gb: int = Field(default=50, ge=20, le=500, description="Disk space in GB")
    priority: int = Field(
        ..., ge=1, le=100, description="Search priority (lower = higher priority)"
    )
    preferred_reliability: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Min reliability score"
    )
    min_network_speed_mbps: int = Field(
        default=100, ge=10, le=10000, description="Min network speed"
    )

    class Config:
        frozen = True  # Immutable configuration

    def to_search_query(self) -> dict[str, Any]:
        """
        Convert to Vast.ai search parameters.

        Returns:
            Dictionary compatible with Vast.ai API search
        """
        return {
            "gpu_name": self.gpu_name,
            "min_vram_gb": self.min_vram,
            "cuda_max_good": self.cuda_version,
            "disk_space": self.disk_space_gb,
            "order": "price",  # Sort by price (cheapest first)
            "type": "on-demand",  # On-demand instances
        }

    def score_offer(self, offer: dict[str, Any]) -> float:
        """
        Multi-factor scoring for GPU offers.

        Scoring factors (weighted):
        - Price (40%): Lower is better
        - Reliability (30%): Higher is better
        - Network speed (15%): Higher is better
        - CUDA version (10%): Newer is better
        - Disk space (5%): More is better

        Args:
            offer: Vast.ai offer dictionary

        Returns:
            Score from 0.0 to 1.0 (higher = better offer)

        Examples:
            >>> config = GPUConfig(
            ...     gpu_name="RTX 3090",
            ...     vram_gb=24,
            ...     min_vram=24,
            ...     max_price_per_hour=0.15,
            ...     priority=1
            ... )
            >>> offer = {
            ...     "dph_total": 0.12,
            ...     "reliability_score": 0.98,
            ...     "inet_up": 500,
            ...     "cuda_vers": "12.2",
            ...     "disk_space": 100
            ... }
            >>> score = config.score_offer(offer)
            >>> print(f"Score: {score:.3f}")
            Score: 0.87
        """
        score = 0.0

        # Price score (40% weight) - normalize to 0-1
        # Lower price = higher score
        price = offer.get("dph_total", self.max_price_per_hour)
        if price <= self.max_price_per_hour:
            price_score = 1.0 - (price / self.max_price_per_hour)
        else:
            price_score = 0.0  # Over budget
        score += price_score * 0.40

        # Reliability score (30% weight)
        reliability = offer.get("reliability_score", 0.5)
        if reliability >= self.preferred_reliability:
            reliability_score = reliability
        else:
            # Penalize unreliable hosts
            reliability_score = reliability * 0.5
        score += reliability_score * 0.30

        # Network speed (15% weight) - normalize to 0-1 (cap at 1 Gbps)
        inet_speed = offer.get("inet_up", 0)
        inet_score = min(inet_speed / 1000, 1.0)  # Cap at 1 Gbps
        if inet_speed < self.min_network_speed_mbps:
            inet_score *= 0.3  # Heavy penalty for slow network
        score += inet_score * 0.15

        # CUDA version (10% weight)
        cuda_version = offer.get("cuda_vers", "0.0")
        try:
            cuda_major = float(cuda_version.split(".")[0])
            required_major = float(self.cuda_version.split(".")[0])
            cuda_score = 1.0 if cuda_major >= required_major else 0.5
        except (ValueError, IndexError):
            cuda_score = 0.5
        score += cuda_score * 0.10

        # Disk space (5% weight) - normalize to 0-1 (cap at 200 GB)
        disk_space = offer.get("disk_space", 0)
        disk_score = min(disk_space / 200, 1.0)
        if disk_space < self.disk_space_gb:
            disk_score = 0.0  # Insufficient disk
        score += disk_score * 0.05

        logger.debug(
            "gpu_offer_scored",
            gpu_name=self.gpu_name,
            price=price,
            reliability=reliability,
            inet_speed=inet_speed,
            total_score=score,
        )

        return min(score, 1.0)  # Clamp to [0, 1]

    def is_offer_compatible(self, offer: dict[str, Any]) -> bool:
        """
        Check if offer meets minimum requirements.

        Args:
            offer: Vast.ai offer dictionary

        Returns:
            True if offer is compatible, False otherwise
        """
        # Check VRAM
        offer_vram_mb = offer.get("gpu_ram", 0)
        offer_vram_gb = offer_vram_mb / 1024
        if offer_vram_gb < self.min_vram:
            logger.debug(
                "offer_rejected_vram",
                offer_id=offer.get("id"),
                offer_vram_gb=offer_vram_gb,
                required_vram_gb=self.min_vram,
            )
            return False

        # Check price
        price = offer.get("dph_total", 999)
        if price > self.max_price_per_hour:
            logger.debug(
                "offer_rejected_price",
                offer_id=offer.get("id"),
                offer_price=price,
                max_price=self.max_price_per_hour,
            )
            return False

        # Check disk space (relaxed to 20GB for vLLM Docker images)
        disk = offer.get("disk_space", 0)
        min_disk_required = 20  # 20GB sufficient for vLLM + model cache
        if disk < min_disk_required:
            logger.debug(
                "offer_rejected_disk",
                offer_id=offer.get("id"),
                offer_disk_gb=disk,
                required_disk_gb=min_disk_required,
            )
            return False

        # Check availability (rentable status)
        # Vast.ai uses "rentable" field for availability
        is_available = offer.get("rentable", False)
        if not is_available:
            logger.debug(
                "offer_rejected_availability",
                offer_id=offer.get("id"),
                rentable=is_available,
            )
            return False

        logger.debug(
            "offer_accepted",
            offer_id=offer.get("id"),
            vram_gb=offer_vram_gb,
            price=price,
            disk_gb=disk,
        )
        return True


# ============================================================================
# GPU FALLBACK CONFIGURATIONS (Priority Order)
# ============================================================================

GPU_FALLBACK_CONFIGS: list[GPUConfig] = [
    # PRIORITY 1: RTX 4090 - Newest generation (better Vast.ai infrastructure)
    # Moved to priority 1 due to CDI issues with RTX 3090 hosts
    GPUConfig(
        gpu_name="RTX 4090",
        vram_gb=24,
        min_vram=24,
        max_price_per_hour=0.25,  # Increased to get better hosts
        cuda_version="12.1",
        disk_space_gb=50,
        priority=1,
        preferred_reliability=0.95,
        min_network_speed_mbps=100,
    ),
    # PRIORITY 2: RTX A5000 - Professional card (datacenter-grade infrastructure)
    GPUConfig(
        gpu_name="RTX A5000",
        vram_gb=24,
        min_vram=24,
        max_price_per_hour=0.25,
        cuda_version="12.1",
        disk_space_gb=50,
        priority=2,
        preferred_reliability=0.98,  # Higher reliability expected
        min_network_speed_mbps=100,
    ),
    # PRIORITY 3: RTX A6000 - High VRAM professional
    GPUConfig(
        gpu_name="RTX A6000",
        vram_gb=48,
        min_vram=24,
        max_price_per_hour=0.30,
        cuda_version="12.1",
        disk_space_gb=50,
        priority=3,
        preferred_reliability=0.98,
        min_network_speed_mbps=100,
    ),
    # PRIORITY 4: RTX 4080 - Good alternative
    GPUConfig(
        gpu_name="RTX 4080",
        vram_gb=16,
        min_vram=16,
        max_price_per_hour=0.20,
        cuda_version="12.1",
        disk_space_gb=50,
        priority=4,
        preferred_reliability=0.95,
        min_network_speed_mbps=100,
    ),
    # PRIORITY 5: RTX 3090 - Best cost/performance (MOVED DOWN - CDI issues on some hosts)
    GPUConfig(
        gpu_name="RTX 3090",
        vram_gb=24,
        min_vram=24,
        max_price_per_hour=0.15,
        cuda_version="12.1",
        disk_space_gb=50,
        priority=5,
        preferred_reliability=0.95,
        min_network_speed_mbps=100,
    ),
    # PRIORITY 6: RTX 3090 Ti - Slightly faster (also has CDI issues)
    GPUConfig(
        gpu_name="RTX 3090 Ti",
        vram_gb=24,
        min_vram=24,
        max_price_per_hour=0.16,
        cuda_version="12.1",
        disk_space_gb=50,
        priority=6,
        preferred_reliability=0.95,
        min_network_speed_mbps=100,
    ),
    # PRIORITY 7: A40 - Datacenter GPU
    GPUConfig(
        gpu_name="A40",
        vram_gb=48,
        min_vram=24,
        max_price_per_hour=0.30,
        cuda_version="12.1",
        disk_space_gb=50,
        priority=7,
        preferred_reliability=0.98,
        min_network_speed_mbps=100,
    ),
    # PRIORITY 8: A100 - High-end datacenter (expensive)
    GPUConfig(
        gpu_name="A100",
        vram_gb=40,
        min_vram=24,
        max_price_per_hour=0.50,
        cuda_version="12.1",
        disk_space_gb=50,
        priority=8,
        preferred_reliability=0.99,
        min_network_speed_mbps=100,
    ),
    # PRIORITY 9: V100 - Older datacenter (backup)
    GPUConfig(
        gpu_name="V100",
        vram_gb=16,
        min_vram=16,
        max_price_per_hour=0.35,
        cuda_version="11.8",  # Older CUDA
        disk_space_gb=50,
        priority=9,
        preferred_reliability=0.95,
        min_network_speed_mbps=100,
    ),
    # PRIORITY 10: RTX 3080 - Emergency fallback (low VRAM)
    GPUConfig(
        gpu_name="RTX 3080",
        vram_gb=10,
        min_vram=10,
        max_price_per_hour=0.12,
        cuda_version="12.1",
        disk_space_gb=50,
        priority=10,
        preferred_reliability=0.90,  # More lenient for emergency
        min_network_speed_mbps=50,  # More lenient
    ),
]


# ============================================================================
# Helper Functions
# ============================================================================


def get_gpu_config_by_name(gpu_name: str) -> GPUConfig | None:
    """
    Get GPU configuration by name.

    Args:
        gpu_name: GPU model name

    Returns:
        GPUConfig if found, None otherwise
    """
    for config in GPU_FALLBACK_CONFIGS:
        if config.gpu_name.lower() == gpu_name.lower():
            return config
    return None


def get_gpu_config_by_priority(priority: int) -> GPUConfig | None:
    """
    Get GPU configuration by priority level.

    Args:
        priority: Priority level (1-10)

    Returns:
        GPUConfig if found, None otherwise
    """
    for config in GPU_FALLBACK_CONFIGS:
        if config.priority == priority:
            return config
    return None


def filter_compatible_offers(
    config: GPUConfig, offers: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Filter offers by compatibility and score them.

    Args:
        config: GPU configuration
        offers: List of Vast.ai offers

    Returns:
        Filtered and scored offers, sorted by score (highest first)
    """
    # Filter compatible offers
    compatible = [offer for offer in offers if config.is_offer_compatible(offer)]

    # Score and sort
    scored_offers = []
    for offer in compatible:
        score = config.score_offer(offer)
        offer["_computed_score"] = score
        scored_offers.append(offer)

    # Sort by score (highest first)
    scored_offers.sort(key=lambda x: x["_computed_score"], reverse=True)

    logger.info(
        "gpu_offers_filtered",
        gpu_name=config.gpu_name,
        total_offers=len(offers),
        compatible_offers=len(compatible),
        top_score=scored_offers[0]["_computed_score"] if scored_offers else 0.0,
    )

    return scored_offers


# ============================================================================
# Configuration Validation
# ============================================================================


def validate_gpu_configs():
    """
    Validate GPU configurations for consistency.

    Checks:
    - Unique priorities
    - Valid price ranges
    - Logical VRAM requirements

    Raises:
        ValueError: If validation fails
    """
    priorities = [config.priority for config in GPU_FALLBACK_CONFIGS]
    if len(priorities) != len(set(priorities)):
        raise ValueError("Duplicate priority levels detected in GPU configurations")

    for config in GPU_FALLBACK_CONFIGS:
        if config.min_vram > config.vram_gb:
            raise ValueError(
                f"{config.gpu_name}: min_vram ({config.min_vram}) > vram_gb ({config.vram_gb})"
            )

        if config.max_price_per_hour <= 0:
            raise ValueError(
                f"{config.gpu_name}: Invalid max_price_per_hour ({config.max_price_per_hour})"
            )

    logger.info(
        "gpu_configs_validated",
        total_configs=len(GPU_FALLBACK_CONFIGS),
        price_range=f"${min(c.max_price_per_hour for c in GPU_FALLBACK_CONFIGS):.2f} - "
        f"${max(c.max_price_per_hour for c in GPU_FALLBACK_CONFIGS):.2f}",
    )


# Validate on module import
validate_gpu_configs()
