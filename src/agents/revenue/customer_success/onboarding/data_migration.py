"""
Data Migration Agent - TASK-2024

Handles data migration from legacy systems, validates data integrity, and ensures
smooth transition. Coordinates extraction, transformation, validation, and loading.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("data_migration", tier="revenue", category="customer_success")
class DataMigrationAgent(BaseAgent):
    """
    Data Migration Agent.

    Manages complete migration lifecycle:
    - Discovery: Identify source systems and data scope
    - Planning: Create migration strategy and timeline
    - Extraction: Pull data from legacy systems
    - Transformation: Map and transform data to new schema
    - Validation: Verify data integrity and completeness
    - Loading: Import data into new system
    - Verification: Post-migration validation and reconciliation
    """

    # Migration phases
    MIGRATION_PHASES = {
        "discovery": {"weight": 10, "critical": True},
        "planning": {"weight": 15, "critical": True},
        "extraction": {"weight": 20, "critical": True},
        "transformation": {"weight": 20, "critical": True},
        "validation": {"weight": 15, "critical": True},
        "loading": {"weight": 15, "critical": True},
        "verification": {"weight": 5, "critical": True}
    }

    # Data quality thresholds
    QUALITY_THRESHOLDS = {
        "excellent": 99.0,
        "good": 95.0,
        "acceptable": 90.0,
        "poor": 80.0
    }

    def __init__(self):
        config = AgentConfig(
            name="data_migration",
            type=AgentType.SPECIALIST,
            model="claude-3-sonnet-20240229",
            temperature=0.2,
            max_tokens=750,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.KB_SEARCH
            ],
            kb_category="customer_success",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Manage data migration process and validate integrity.

        Args:
            state: Current agent state with migration data

        Returns:
            Updated state with migration status and data quality metrics
        """
        self.logger.info("data_migration_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        migration_data = state.get("entities", {}).get("migration_data", {})
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "data_migration_details",
            customer_id=customer_id,
            current_phase=migration_data.get("current_phase"),
            records_migrated=migration_data.get("records_migrated", 0)
        )

        # Analyze migration status
        migration_analysis = self._analyze_migration_status(
            migration_data,
            customer_metadata
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(migration_analysis)

        # Assess risks
        risks = self._assess_migration_risks(migration_analysis, migration_data)

        # Build response
        response = self._format_migration_report(
            migration_analysis,
            recommendations,
            risks
        )

        state["agent_response"] = response
        state["migration_status"] = migration_analysis["overall_status"]
        state["migration_phase"] = migration_analysis["current_phase"]
        state["data_quality_score"] = migration_analysis["data_quality_score"]
        state["migration_progress"] = migration_analysis["progress_percentage"]
        state["migration_analysis"] = migration_analysis
        state["response_confidence"] = 0.91
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "data_migration_completed",
            customer_id=customer_id,
            migration_status=migration_analysis["overall_status"],
            data_quality=migration_analysis["data_quality_score"],
            progress=migration_analysis["progress_percentage"]
        )

        return state

    def _analyze_migration_status(
        self,
        migration_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze data migration status and quality.

        Args:
            migration_data: Migration metrics and progress data
            customer_metadata: Customer profile data

        Returns:
            Comprehensive migration analysis
        """
        current_phase = migration_data.get("current_phase", "discovery")
        completed_phases = migration_data.get("completed_phases", [])

        # Calculate overall progress
        progress_percentage = self._calculate_progress(current_phase, completed_phases)

        # Calculate data quality metrics
        quality_metrics = self._calculate_data_quality(migration_data)

        # Analyze migration velocity
        velocity_analysis = self._analyze_velocity(migration_data)

        # Identify data issues
        data_issues = self._identify_data_issues(migration_data, quality_metrics)

        # Determine overall status
        overall_status = self._determine_migration_status(
            current_phase,
            quality_metrics,
            data_issues,
            velocity_analysis
        )

        # Calculate estimated completion
        estimated_completion = self._estimate_completion(
            progress_percentage,
            velocity_analysis,
            data_issues
        )

        return {
            "overall_status": overall_status,
            "current_phase": current_phase,
            "completed_phases": completed_phases,
            "progress_percentage": progress_percentage,
            "data_quality_score": quality_metrics["overall_quality"],
            "data_quality_category": quality_metrics["quality_category"],
            "records_total": migration_data.get("total_records", 0),
            "records_migrated": migration_data.get("records_migrated", 0),
            "records_failed": migration_data.get("records_failed", 0),
            "velocity_analysis": velocity_analysis,
            "data_issues": data_issues,
            "estimated_completion_days": estimated_completion,
            "quality_metrics": quality_metrics,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _calculate_progress(
        self,
        current_phase: str,
        completed_phases: List[str]
    ) -> int:
        """Calculate overall migration progress percentage."""
        total_weight = sum(phase["weight"] for phase in self.MIGRATION_PHASES.values())
        completed_weight = sum(
            self.MIGRATION_PHASES[phase]["weight"]
            for phase in completed_phases
            if phase in self.MIGRATION_PHASES
        )

        # Add 50% of current phase weight
        if current_phase in self.MIGRATION_PHASES and current_phase not in completed_phases:
            completed_weight += self.MIGRATION_PHASES[current_phase]["weight"] * 0.5

        return int((completed_weight / total_weight) * 100)

    def _calculate_data_quality(self, migration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive data quality metrics."""
        total_records = migration_data.get("total_records", 0)
        migrated_records = migration_data.get("records_migrated", 0)
        failed_records = migration_data.get("records_failed", 0)

        # Success rate
        success_rate = ((migrated_records - failed_records) / total_records * 100) if total_records > 0 else 100

        # Validation metrics
        validation_passed = migration_data.get("validation_passed", 0)
        validation_total = migration_data.get("validation_total", migrated_records)
        validation_rate = (validation_passed / validation_total * 100) if validation_total > 0 else 100

        # Completeness score
        completeness = migration_data.get("data_completeness", 95.0)

        # Schema compliance
        schema_compliance = migration_data.get("schema_compliance", 98.0)

        # Calculate overall quality (weighted average)
        overall_quality = (
            success_rate * 0.3 +
            validation_rate * 0.3 +
            completeness * 0.2 +
            schema_compliance * 0.2
        )

        # Determine quality category
        quality_category = "poor"
        for category, threshold in sorted(self.QUALITY_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if overall_quality >= threshold:
                quality_category = category
                break

        return {
            "overall_quality": round(overall_quality, 2),
            "quality_category": quality_category,
            "success_rate": round(success_rate, 2),
            "validation_rate": round(validation_rate, 2),
            "completeness": round(completeness, 2),
            "schema_compliance": round(schema_compliance, 2)
        }

    def _analyze_velocity(self, migration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze migration velocity and throughput."""
        start_date_str = migration_data.get("migration_start_date")
        if not start_date_str:
            return {
                "status": "not_started",
                "days_elapsed": 0,
                "records_per_day": 0
            }

        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        except:
            start_date = datetime.utcnow()

        days_elapsed = max((datetime.utcnow() - start_date).days, 1)
        records_migrated = migration_data.get("records_migrated", 0)
        records_per_day = int(records_migrated / days_elapsed)

        # Determine velocity status
        expected_daily_rate = migration_data.get("expected_daily_rate", 1000)
        if records_per_day >= expected_daily_rate:
            velocity_status = "on_track"
        elif records_per_day >= expected_daily_rate * 0.7:
            velocity_status = "slightly_behind"
        else:
            velocity_status = "behind_schedule"

        return {
            "status": velocity_status,
            "days_elapsed": days_elapsed,
            "records_per_day": records_per_day,
            "expected_daily_rate": expected_daily_rate
        }

    def _identify_data_issues(
        self,
        migration_data: Dict[str, Any],
        quality_metrics: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify data quality and migration issues."""
        issues = []

        # Failed records issue
        failed_records = migration_data.get("records_failed", 0)
        if failed_records > 100:
            issues.append({
                "issue": f"{failed_records} records failed migration",
                "severity": "high",
                "impact": "Data loss risk - need to investigate failure patterns",
                "category": "data_loss"
            })

        # Validation failures
        if quality_metrics["validation_rate"] < 90:
            issues.append({
                "issue": f"Low validation rate: {quality_metrics['validation_rate']}%",
                "severity": "critical",
                "impact": "Data integrity concerns - migrated data may be corrupted",
                "category": "data_integrity"
            })

        # Incomplete data
        if quality_metrics["completeness"] < 90:
            issues.append({
                "issue": f"Data completeness only {quality_metrics['completeness']}%",
                "severity": "high",
                "impact": "Missing critical data fields",
                "category": "data_completeness"
            })

        # Schema compliance issues
        if quality_metrics["schema_compliance"] < 95:
            issues.append({
                "issue": f"Schema compliance at {quality_metrics['schema_compliance']}%",
                "severity": "medium",
                "impact": "Data transformation errors detected",
                "category": "schema_mapping"
            })

        # Legacy system access issues
        if migration_data.get("source_system_errors", False):
            issues.append({
                "issue": "Legacy system connection errors",
                "severity": "critical",
                "impact": "Cannot extract data - migration blocked",
                "category": "connectivity"
            })

        # Duplicate records
        duplicate_count = migration_data.get("duplicate_records", 0)
        if duplicate_count > 50:
            issues.append({
                "issue": f"{duplicate_count} duplicate records detected",
                "severity": "medium",
                "impact": "Data deduplication required",
                "category": "data_quality"
            })

        return issues

    def _determine_migration_status(
        self,
        current_phase: str,
        quality_metrics: Dict[str, Any],
        data_issues: List[Dict[str, str]],
        velocity_analysis: Dict[str, Any]
    ) -> str:
        """Determine overall migration status."""
        critical_issues = [i for i in data_issues if i["severity"] == "critical"]
        high_issues = [i for i in data_issues if i["severity"] == "high"]

        if critical_issues:
            return "blocked"
        elif current_phase == "verification" and quality_metrics["overall_quality"] >= 95:
            return "completed_excellent"
        elif current_phase == "verification":
            return "completed_with_issues"
        elif high_issues and velocity_analysis["status"] == "behind_schedule":
            return "at_risk"
        elif velocity_analysis["status"] == "on_track" and not high_issues:
            return "on_track"
        else:
            return "in_progress"

    def _estimate_completion(
        self,
        progress_pct: int,
        velocity_analysis: Dict[str, Any],
        data_issues: List[Dict[str, str]]
    ) -> int:
        """Estimate days until migration completion."""
        if progress_pct >= 100:
            return 0

        # Base estimate from velocity
        days_elapsed = velocity_analysis.get("days_elapsed", 1)
        estimated_total_days = int((days_elapsed / progress_pct) * 100) if progress_pct > 0 else 30

        # Add buffer for issues
        critical_issues = [i for i in data_issues if i["severity"] == "critical"]
        high_issues = [i for i in data_issues if i["severity"] == "high"]

        buffer_days = len(critical_issues) * 5 + len(high_issues) * 2

        remaining_days = estimated_total_days - days_elapsed + buffer_days

        return max(remaining_days, 0)

    def _assess_migration_risks(
        self,
        migration_analysis: Dict[str, Any],
        migration_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Assess migration risks."""
        risks = []

        # Data loss risk
        if migration_analysis["data_quality_score"] < 95:
            risks.append({
                "risk": "Data quality below acceptable threshold",
                "probability": "high",
                "impact": "Customer may lose critical business data",
                "mitigation": "Pause migration, fix transformation logic, re-migrate failed records"
            })

        # Timeline risk
        if migration_analysis["estimated_completion_days"] > 20:
            risks.append({
                "risk": "Migration timeline at risk",
                "probability": "medium",
                "impact": "Delays onboarding completion and time-to-value",
                "mitigation": "Increase migration resources, parallelize extraction"
            })

        # Legacy system dependency
        if migration_data.get("legacy_system_required", True):
            risks.append({
                "risk": "Dependency on legacy system access",
                "probability": "medium",
                "impact": "Migration can be blocked by legacy system downtime",
                "mitigation": "Create data snapshots, establish backup extraction method"
            })

        return risks

    def _generate_recommendations(
        self,
        migration_analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate migration recommendations."""
        recommendations = []

        status = migration_analysis["overall_status"]
        data_issues = migration_analysis.get("data_issues", [])
        quality_score = migration_analysis["data_quality_score"]

        # Status-based recommendations
        if status == "blocked":
            recommendations.append({
                "action": "Halt migration and resolve critical issues immediately",
                "priority": "critical",
                "owner": "Data Migration Specialist",
                "timeline": "Before proceeding"
            })

        if status == "at_risk":
            recommendations.append({
                "action": "Increase migration resources to accelerate timeline",
                "priority": "high",
                "owner": "Solutions Engineer",
                "timeline": "This week"
            })

        # Issue-based recommendations
        for issue in data_issues:
            if issue["category"] == "data_integrity":
                recommendations.append({
                    "action": "Review and fix data transformation mappings",
                    "priority": "critical",
                    "owner": "Data Migration Specialist",
                    "timeline": "Within 2 days"
                })
            elif issue["category"] == "connectivity":
                recommendations.append({
                    "action": "Work with customer IT to restore legacy system access",
                    "priority": "critical",
                    "owner": "Solutions Engineer",
                    "timeline": "Immediately"
                })

        # Quality-based recommendations
        if quality_score < 90:
            recommendations.append({
                "action": "Perform comprehensive data quality audit",
                "priority": "high",
                "owner": "Data Migration Specialist",
                "timeline": "Before loading phase"
            })

        # Proactive recommendations
        if migration_analysis["current_phase"] in ["loading", "verification"]:
            recommendations.append({
                "action": "Schedule customer data validation review session",
                "priority": "medium",
                "owner": "CSM",
                "timeline": "Before sign-off"
            })

        return recommendations[:5]

    def _format_migration_report(
        self,
        migration_analysis: Dict[str, Any],
        recommendations: List[Dict[str, str]],
        risks: List[Dict[str, str]]
    ) -> str:
        """Format data migration report."""
        status = migration_analysis["overall_status"]

        status_emoji = {
            "completed_excellent": "????",
            "completed_with_issues": "???",
            "on_track": "????",
            "in_progress": "???",
            "at_risk": "??????",
            "blocked": "????"
        }

        quality_emoji = {
            "excellent": "????",
            "good": "???",
            "acceptable": "??????",
            "poor": "????"
        }

        report = f"""**{status_emoji.get(status, '????')} Data Migration Report**

**Overall Status:** {status.replace('_', ' ').title()}
**Current Phase:** {migration_analysis['current_phase'].title()}
**Progress:** {migration_analysis['progress_percentage']}%

**Data Quality Metrics:**
- Overall Quality Score: {migration_analysis['data_quality_score']}/100 {quality_emoji.get(migration_analysis['data_quality_category'], '????')}
- Category: {migration_analysis['data_quality_category'].title()}
- Success Rate: {migration_analysis['quality_metrics']['success_rate']}%
- Validation Rate: {migration_analysis['quality_metrics']['validation_rate']}%
- Completeness: {migration_analysis['quality_metrics']['completeness']}%
- Schema Compliance: {migration_analysis['quality_metrics']['schema_compliance']}%

**Migration Progress:**
- Records Migrated: {migration_analysis['records_migrated']:,}/{migration_analysis['records_total']:,}
- Records Failed: {migration_analysis['records_failed']:,}
- Completed Phases: {len(migration_analysis['completed_phases'])}/{len(self.MIGRATION_PHASES)}

**Velocity Analysis:**
- Status: {migration_analysis['velocity_analysis']['status'].replace('_', ' ').title()}
- Days Elapsed: {migration_analysis['velocity_analysis']['days_elapsed']}
- Records/Day: {migration_analysis['velocity_analysis']['records_per_day']:,}
- Estimated Completion: {migration_analysis['estimated_completion_days']} days
"""

        # Data Issues
        if migration_analysis.get("data_issues"):
            report += "\n**???? Data Issues:**\n"
            for issue in migration_analysis["data_issues"][:3]:
                report += f"- **{issue['issue']}** ({issue['severity']} severity)\n"
                report += f"  Impact: {issue['impact']}\n"
                report += f"  Category: {issue['category']}\n"

        # Risks
        if risks:
            report += "\n**?????? Migration Risks:**\n"
            for risk in risks[:2]:
                report += f"- **{risk['risk']}** (Probability: {risk['probability']})\n"
                report += f"  Impact: {risk['impact']}\n"
                report += f"  Mitigation: {risk['mitigation']}\n"

        # Recommendations
        if recommendations:
            report += "\n**???? Recommended Actions:**\n"
            for i, rec in enumerate(recommendations[:3], 1):
                report += f"{i}. **{rec['action']}**\n"
                report += f"   - Priority: {rec['priority'].upper()}\n"
                report += f"   - Owner: {rec['owner']}\n"
                report += f"   - Timeline: {rec['timeline']}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Data Migration Agent (TASK-2024)")
        print("=" * 70)

        agent = DataMigrationAgent()

        # Test 1: Migration on track
        print("\n\nTest 1: Migration On Track - Good Quality")
        print("-" * 70)

        state1 = create_initial_state(
            "Check data migration status",
            context={
                "customer_id": "cust_123",
                "customer_metadata": {"plan": "enterprise"}
            }
        )
        state1["entities"] = {
            "migration_data": {
                "current_phase": "validation",
                "completed_phases": ["discovery", "planning", "extraction", "transformation"],
                "migration_start_date": (datetime.utcnow() - timedelta(days=10)).isoformat(),
                "total_records": 50000,
                "records_migrated": 48500,
                "records_failed": 50,
                "validation_passed": 47800,
                "validation_total": 48500,
                "data_completeness": 97.5,
                "schema_compliance": 98.5,
                "expected_daily_rate": 5000
            }
        }

        result1 = await agent.process(state1)

        print(f"Status: {result1['migration_status']}")
        print(f"Phase: {result1['migration_phase']}")
        print(f"Quality: {result1['data_quality_score']}/100")
        print(f"Progress: {result1['migration_progress']}%")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Migration at risk
        print("\n\n" + "=" * 70)
        print("Test 2: Migration At Risk - Quality Issues")
        print("-" * 70)

        state2 = create_initial_state(
            "Assess migration issues",
            context={
                "customer_id": "cust_456",
                "customer_metadata": {"plan": "premium"}
            }
        )
        state2["entities"] = {
            "migration_data": {
                "current_phase": "transformation",
                "completed_phases": ["discovery", "planning", "extraction"],
                "migration_start_date": (datetime.utcnow() - timedelta(days=15)).isoformat(),
                "total_records": 30000,
                "records_migrated": 15000,
                "records_failed": 2000,
                "validation_passed": 11000,
                "validation_total": 15000,
                "data_completeness": 82.0,
                "schema_compliance": 88.0,
                "expected_daily_rate": 2000,
                "source_system_errors": True,
                "duplicate_records": 150
            }
        }

        result2 = await agent.process(state2)

        print(f"Status: {result2['migration_status']}")
        print(f"Quality: {result2['data_quality_score']}/100")
        print(f"\nResponse preview:\n{result2['agent_response'][:700]}...")

    asyncio.run(test())
