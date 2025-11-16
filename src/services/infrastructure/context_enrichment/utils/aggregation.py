"""
Result aggregation utilities.

Combines and merges results from multiple providers into a unified context.
Handles conflicts, deduplication, and intelligent merging strategies.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog

from src.services.infrastructure.context_enrichment.types import (
    ProviderResult,
    AgentType,
    ProviderStatus
)

logger = structlog.get_logger(__name__)


class ResultAggregator:
    """
    Aggregates results from multiple context providers.

    Features:
    - Intelligent merging of overlapping data
    - Conflict resolution with provider priority
    - Deduplication of redundant data
    - Data quality scoring
    - Fallback handling for failed providers

    Example:
        >>> aggregator = ResultAggregator()
        >>> results = [result1, result2, result3]
        >>> aggregated = await aggregator.aggregate(results, AgentType.SUPPORT)
    """

    def __init__(self):
        self.logger = logger.bind(component="aggregator")

    async def aggregate(
        self,
        results: List[ProviderResult],
        agent_type: AgentType
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple providers.

        Args:
            results: List of provider results
            agent_type: Agent type requesting context

        Returns:
            Aggregated data dictionary
        """
        if not results:
            return {}

        # Filter successful results
        successful_results = [
            r for r in results
            if r.status == ProviderStatus.SUCCESS and r.data
        ]

        if not successful_results:
            self.logger.warning(
                "no_successful_results",
                total_results=len(results),
                agent_type=agent_type.value
            )
            return {}

        # Start with empty aggregated data
        aggregated: Dict[str, Any] = {}

        # Process each result in priority order
        prioritized_results = self._prioritize_results(successful_results)

        for result in prioritized_results:
            # Merge result data into aggregated data
            aggregated = self._merge_data(
                aggregated,
                result.data,
                result.provider_name
            )

        # Deduplicate data
        aggregated = self._deduplicate(aggregated)

        # Add metadata
        aggregated["_metadata"] = {
            "providers_used": [r.provider_name for r in successful_results],
            "providers_failed": [r.provider_name for r in results if r.status != ProviderStatus.SUCCESS],
            "total_latency_ms": sum(r.latency_ms for r in results),
            "aggregated_at": datetime.utcnow(),
        }

        self.logger.debug(
            "aggregation_completed",
            successful_count=len(successful_results),
            failed_count=len(results) - len(successful_results),
            data_keys=len(aggregated)
        )

        return aggregated

    def _prioritize_results(
        self,
        results: List[ProviderResult]
    ) -> List[ProviderResult]:
        """
        Prioritize results by latency and provider order.

        Faster providers are preferred, as they likely have fresher data.

        Args:
            results: List of provider results

        Returns:
            Sorted list of results
        """
        # Sort by latency (faster = higher priority)
        return sorted(results, key=lambda r: r.latency_ms)

    def _merge_data(
        self,
        target: Dict[str, Any],
        source: Dict[str, Any],
        provider_name: str
    ) -> Dict[str, Any]:
        """
        Merge source data into target data.

        Args:
            target: Target dictionary
            source: Source dictionary to merge
            provider_name: Name of provider providing source data

        Returns:
            Merged dictionary
        """
        for key, value in source.items():
            if key not in target:
                # New key - add it
                target[key] = value
            elif isinstance(value, dict) and isinstance(target[key], dict):
                # Both are dicts - merge recursively
                target[key] = self._merge_dicts(target[key], value, provider_name)
            elif isinstance(value, list) and isinstance(target[key], list):
                # Both are lists - merge with deduplication
                target[key] = self._merge_lists(target[key], value)
            else:
                # Conflict - use conflict resolution strategy
                target[key] = self._resolve_conflict(
                    target[key],
                    value,
                    key,
                    provider_name
                )

        return target

    def _merge_dicts(
        self,
        dict1: Dict[str, Any],
        dict2: Dict[str, Any],
        provider_name: str
    ) -> Dict[str, Any]:
        """
        Recursively merge two dictionaries.

        Args:
            dict1: First dictionary
            dict2: Second dictionary
            provider_name: Provider name for conflict resolution

        Returns:
            Merged dictionary
        """
        result = dict1.copy()

        for key, value in dict2.items():
            if key not in result:
                result[key] = value
            elif isinstance(value, dict) and isinstance(result[key], dict):
                result[key] = self._merge_dicts(result[key], value, provider_name)
            elif isinstance(value, list) and isinstance(result[key], list):
                result[key] = self._merge_lists(result[key], value)
            else:
                result[key] = self._resolve_conflict(
                    result[key],
                    value,
                    key,
                    provider_name
                )

        return result

    def _merge_lists(self, list1: List, list2: List) -> List:
        """
        Merge two lists with deduplication.

        Args:
            list1: First list
            list2: Second list

        Returns:
            Merged list with duplicates removed
        """
        # Simple concatenation with deduplication
        result = list1.copy()

        for item in list2:
            # Check if item already exists
            if item not in result:
                result.append(item)

        return result

    def _resolve_conflict(
        self,
        value1: Any,
        value2: Any,
        key: str,
        provider_name: str
    ) -> Any:
        """
        Resolve conflict between two values.

        Strategy:
        1. Prefer non-None values
        2. Prefer non-empty values
        3. Prefer newer timestamps
        4. Prefer higher numeric values (for metrics)
        5. Default to first value

        Args:
            value1: First value
            value2: Second value
            key: Key name
            provider_name: Provider name

        Returns:
            Resolved value
        """
        # Prefer non-None
        if value1 is None:
            return value2
        if value2 is None:
            return value1

        # Prefer non-empty
        if not value1 and value2:
            return value2
        if not value2 and value1:
            return value1

        # For timestamps, prefer newer
        if isinstance(value1, datetime) and isinstance(value2, datetime):
            return max(value1, value2)

        # For numeric values in specific keys, prefer higher
        if key in ['health_score', 'nps_score', 'engagement_score']:
            try:
                num1 = float(value1)
                num2 = float(value2)
                return max(num1, num2)
            except (ValueError, TypeError):
                pass

        # For counts and metrics, prefer higher
        if key.endswith('_count') or key.endswith('_total'):
            try:
                num1 = float(value1)
                num2 = float(value2)
                return max(num1, num2)
            except (ValueError, TypeError):
                pass

        # Default: keep first value
        self.logger.debug(
            "conflict_resolved_to_first",
            key=key,
            value1=str(value1)[:50],
            value2=str(value2)[:50],
            provider=provider_name
        )

        return value1

    def _deduplicate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deduplicate data recursively.

        Args:
            data: Data dictionary

        Returns:
            Deduplicated dictionary
        """
        result = {}

        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = self._deduplicate(value)
            elif isinstance(value, list):
                result[key] = self._deduplicate_list(value)
            else:
                result[key] = value

        return result

    def _deduplicate_list(self, items: List) -> List:
        """
        Deduplicate list while preserving order.

        Args:
            items: List to deduplicate

        Returns:
            Deduplicated list
        """
        seen = set()
        result = []

        for item in items:
            # For hashable items
            try:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            except TypeError:
                # For unhashable items (dicts, lists), do simple check
                if item not in result:
                    result.append(item)

        return result

    async def merge_with_previous(
        self,
        current: Dict[str, Any],
        previous: Dict[str, Any],
        max_age_seconds: int = 3600
    ) -> Dict[str, Any]:
        """
        Merge current data with previous cached data.

        Useful for filling gaps when some providers fail.

        Args:
            current: Current aggregated data
            previous: Previous cached data
            max_age_seconds: Maximum age of previous data to use

        Returns:
            Merged data
        """
        # Check if previous data is too old
        if "_metadata" in previous:
            aggregated_at = previous["_metadata"].get("aggregated_at")
            if aggregated_at:
                age = (datetime.utcnow() - aggregated_at).total_seconds()
                if age > max_age_seconds:
                    self.logger.debug(
                        "previous_data_too_old",
                        age_seconds=age,
                        max_age=max_age_seconds
                    )
                    return current

        # Merge previous into current (current takes priority)
        merged = previous.copy()
        merged = self._merge_data(merged, current, "current")

        return merged

    def calculate_completeness(self, data: Dict[str, Any]) -> float:
        """
        Calculate completeness score of aggregated data.

        Args:
            data: Aggregated data

        Returns:
            Completeness score (0-100)
        """
        if not data:
            return 0.0

        # Define expected top-level keys
        expected_keys = {
            "company_name",
            "plan",
            "health_score",
            "mrr",
            "segments",
            "subscription",
            "billing",
            "support_history",
            "engagement_metrics",
        }

        # Count present keys
        present_keys = set(data.keys()) & expected_keys
        completeness = (len(present_keys) / len(expected_keys)) * 100

        return completeness

    def calculate_freshness(self, data: Dict[str, Any]) -> float:
        """
        Calculate freshness score of aggregated data.

        Based on timestamps in the data.

        Args:
            data: Aggregated data

        Returns:
            Freshness score (0-100)
        """
        if "_metadata" not in data:
            return 50.0  # Unknown

        aggregated_at = data["_metadata"].get("aggregated_at")
        if not aggregated_at:
            return 50.0

        # Calculate age in seconds
        age = (datetime.utcnow() - aggregated_at).total_seconds()

        # Scoring:
        # < 30s: 100
        # < 5min: 90
        # < 15min: 70
        # < 1hr: 50
        # < 24hr: 30
        # > 24hr: 10

        if age < 30:
            return 100.0
        elif age < 300:  # 5 min
            return 90.0
        elif age < 900:  # 15 min
            return 70.0
        elif age < 3600:  # 1 hour
            return 50.0
        elif age < 86400:  # 24 hours
            return 30.0
        else:
            return 10.0

    def extract_summary(
        self,
        data: Dict[str, Any],
        agent_type: AgentType
    ) -> Dict[str, Any]:
        """
        Extract key summary information for agent.

        Args:
            data: Aggregated data
            agent_type: Agent type

        Returns:
            Summary dictionary
        """
        summary = {}

        # Extract key fields based on agent type
        if agent_type == AgentType.SUPPORT:
            summary = {
                "customer": data.get("company_name"),
                "plan": data.get("plan"),
                "health_score": data.get("health_score"),
                "open_tickets": data.get("support_history", {}).get("open_tickets"),
                "last_conversation": data.get("support_history", {}).get("last_conversation"),
            }
        elif agent_type == AgentType.BILLING:
            summary = {
                "customer": data.get("company_name"),
                "mrr": data.get("mrr"),
                "arr": data.get("arr"),
                "payment_status": data.get("payment_health", {}).get("payment_method_valid"),
                "overdue_invoices": data.get("payment_health", {}).get("overdue_invoices"),
            }
        elif agent_type == AgentType.SUCCESS:
            summary = {
                "customer": data.get("company_name"),
                "health_score": data.get("health_score"),
                "health_trend": data.get("health_trend"),
                "churn_risk": data.get("churn_risk"),
                "nps_score": data.get("nps_score"),
                "engagement_trend": data.get("engagement_metrics", {}).get("trend"),
            }
        elif agent_type == AgentType.SALES:
            summary = {
                "customer": data.get("company_name"),
                "plan": data.get("plan"),
                "arr": data.get("arr"),
                "expansion_opportunities": data.get("expansion_opportunities", []),
                "seat_utilization": data.get("subscription", {}).get("seat_utilization"),
            }
        else:
            # Generic summary
            summary = {
                "customer": data.get("company_name"),
                "plan": data.get("plan"),
                "health_score": data.get("health_score"),
            }

        # Remove None values
        summary = {k: v for k, v in summary.items() if v is not None}

        return summary
