"""
Deduplicator Agent - TASK-2208

Auto-detects and merges duplicate records across contacts, companies, and tickets.
Uses fuzzy matching and intelligent merge strategies.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
import json

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("deduplicator", tier="operational", category="automation")
class DeduplicatorAgent(BaseAgent):
    """
    Deduplicator Agent - Auto-detects and merges duplicates.

    Handles:
    - Fuzzy matching for contact/company names
    - Email and domain-based matching
    - Phone number normalization and matching
    - Duplicate confidence scoring
    - Smart merge strategies (newest, most complete, manual review)
    - Relationship preservation during merge
    - Audit trail for all merges
    - Rollback capability for incorrect merges
    """

    # Duplicate detection thresholds
    SIMILARITY_THRESHOLDS = {
        "exact_match": 1.0,
        "very_high": 0.95,
        "high": 0.85,
        "medium": 0.75,
        "low": 0.65
    }

    # Matching strategies by field
    MATCHING_STRATEGIES = {
        "email": {"weight": 0.9, "method": "exact"},
        "domain": {"weight": 0.8, "method": "exact"},
        "company_name": {"weight": 0.7, "method": "fuzzy"},
        "phone": {"weight": 0.6, "method": "normalized"},
        "name": {"weight": 0.5, "method": "fuzzy"},
        "address": {"weight": 0.4, "method": "fuzzy"}
    }

    # Merge strategies
    MERGE_STRATEGIES = {
        "newest": "Keep data from newest record",
        "most_complete": "Keep record with most fields populated",
        "primary": "Keep primary record, merge secondary data",
        "manual": "Flag for manual review"
    }

    def __init__(self):
        config = AgentConfig(
            name="deduplicator",
            type=AgentType.AUTOMATOR,
            temperature=0.1,
            max_tokens=900,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Auto-detect and merge duplicate records."""
        self.logger.info("deduplicator_started")
        state = self.update_state(state)

        entities = state.get("entities", {})
        record_type = entities.get("record_type", "contact")
        merge_strategy = entities.get("merge_strategy", "most_complete")

        # Find potential duplicates
        duplicates = await self._find_duplicates(record_type)

        # Score duplicate matches
        scored_duplicates = self._score_duplicates(duplicates)

        # Filter by confidence threshold
        high_confidence_dupes = [
            d for d in scored_duplicates
            if d["confidence"] >= self.SIMILARITY_THRESHOLDS["high"]
        ]

        # Prepare merge operations
        merge_operations = self._prepare_merge_operations(
            high_confidence_dupes,
            merge_strategy
        )

        # Execute merges
        merge_results = await self._execute_merges(merge_operations)

        # Log automation action
        automation_log = self._log_automation_action(
            "duplicates_merged",
            merge_results,
            {}
        )

        # Generate response
        response = f"""**Duplicate Detection & Merge Complete**

Record Type: {record_type.title()}
Duplicates Found: {len(duplicates)}
High Confidence Matches: {len(high_confidence_dupes)}
Records Merged: {len(merge_results.get('merged', []))}

**Merge Results:**
"""
        for merge in merge_results.get('merged', [])[:5]:
            response += f"- Merged {merge['record_ids']} (Confidence: {merge['confidence']:.0%})\n"

        if len(merge_results.get('merged', [])) > 5:
            response += f"... and {len(merge_results['merged']) - 5} more\n"

        state["agent_response"] = response
        state["duplicates_found"] = duplicates
        state["merge_results"] = merge_results
        state["automation_log"] = automation_log
        state["response_confidence"] = 0.90
        state["status"] = "resolved"

        self.logger.info(
            "deduplication_completed",
            duplicates_found=len(duplicates),
            records_merged=len(merge_results.get('merged', []))
        )

        return state

    async def _find_duplicates(self, record_type: str) -> List[Dict]:
        """Find potential duplicate records (mocked)."""
        # Mock duplicate records
        return [
            {
                "record_1": {"id": "REC-001", "name": "John Smith", "email": "john@acme.com"},
                "record_2": {"id": "REC-002", "name": "Jon Smith", "email": "john@acme.com"},
                "matching_fields": ["email"]
            },
            {
                "record_1": {"id": "REC-003", "name": "Acme Corp", "domain": "acme.com"},
                "record_2": {"id": "REC-004", "name": "ACME Corporation", "domain": "acme.com"},
                "matching_fields": ["domain"]
            }
        ]

    def _score_duplicates(self, duplicates: List[Dict]) -> List[Dict]:
        """Score duplicate matches by confidence."""
        scored = []
        for dup in duplicates:
            # Calculate confidence score
            matching_fields = dup.get("matching_fields", [])
            total_weight = sum(
                self.MATCHING_STRATEGIES.get(field, {"weight": 0.5})["weight"]
                for field in matching_fields
            )
            confidence = min(total_weight, 1.0)

            scored.append({
                **dup,
                "confidence": confidence,
                "match_strength": "high" if confidence >= 0.85 else "medium" if confidence >= 0.75 else "low"
            })

        return sorted(scored, key=lambda x: x["confidence"], reverse=True)

    def _prepare_merge_operations(
        self,
        duplicates: List[Dict],
        strategy: str
    ) -> List[Dict]:
        """Prepare merge operations."""
        operations = []
        for dup in duplicates:
            operations.append({
                "primary_id": dup["record_1"]["id"],
                "secondary_id": dup["record_2"]["id"],
                "strategy": strategy,
                "confidence": dup["confidence"],
                "merge_plan": {
                    "keep_primary": True,
                    "merge_fields": ["email", "phone", "notes"]
                }
            })
        return operations

    async def _execute_merges(self, operations: List[Dict]) -> Dict:
        """Execute merge operations (mocked)."""
        merged = []
        for op in operations:
            merged.append({
                "record_ids": f"{op['primary_id']} + {op['secondary_id']}",
                "result_id": op["primary_id"],
                "confidence": op["confidence"],
                "status": "success",
                "merged_at": datetime.now(UTC).isoformat()
            })

        return {
            "merged": merged,
            "total_merges": len(merged),
            "timestamp": datetime.now(UTC).isoformat()
        }

    def _log_automation_action(
        self,
        action_type: str,
        merge_results: Dict,
        customer_metadata: Dict
    ) -> Dict:
        """Log automation action."""
        return {
            "action_type": action_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "records_merged": len(merge_results.get("merged", [])),
            "success": True
        }
