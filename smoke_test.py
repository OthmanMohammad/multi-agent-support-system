#!/usr/bin/env python3
"""
Comprehensive Smoke Test Script
Tests all critical components of the multi-agent support system
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


class SmokeTest:
    """Comprehensive smoke test runner"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0

    def log_test(self, name: str, status: str, message: str = ""):
        """Log test result"""
        symbol = "✓" if status == "PASS" else "✗"
        color = "\033[92m" if status == "PASS" else "\033[91m"
        reset = "\033[0m"

        print(f"{color}{symbol} {name}{reset}")
        if message:
            print(f"  {message}")

        self.results.append({
            "name": name,
            "status": status,
            "message": message,
            "timestamp": datetime.now(UTC)
        })

        if status == "PASS":
            self.passed += 1
        else:
            self.failed += 1

    async def test_agent_registry(self) -> bool:
        """Test 1: Agent Registry - Verify agents can be loaded"""
        try:
            from src.services.infrastructure.agent_registry import AgentRegistry
            from src.agents.loader import load_all_agents

            # Load all agents
            load_all_agents()

            # Get agent count
            agent_count = len(AgentRegistry._agents)

            if agent_count >= 200:
                self.log_test(
                    "Agent Registry",
                    "PASS",
                    f"Loaded {agent_count} agents successfully"
                )
                return True
            else:
                self.log_test(
                    "Agent Registry",
                    "FAIL",
                    f"Only {agent_count} agents loaded (expected 200+)"
                )
                return False

        except Exception as e:
            self.log_test("Agent Registry", "FAIL", f"Error: {str(e)}")
            return False

    async def test_database_connection(self) -> bool:
        """Test 2: Database Connection"""
        try:
            from src.database.connection import get_async_session

            async with get_async_session() as session:
                # Try a simple query
                result = await session.execute("SELECT 1")
                value = result.scalar()

                if value == 1:
                    self.log_test(
                        "Database Connection",
                        "PASS",
                        "Successfully connected to PostgreSQL"
                    )
                    return True
                else:
                    self.log_test(
                        "Database Connection",
                        "FAIL",
                        "Unexpected query result"
                    )
                    return False

        except Exception as e:
            self.log_test(
                "Database Connection",
                "FAIL",
                f"Cannot connect to database: {str(e)}"
            )
            return False

    async def test_job_store(self) -> bool:
        """Test 3: Job Store - In-memory fallback"""
        try:
            from src.services.job_store import InMemoryJobStore, JobType

            store = InMemoryJobStore()
            await store.initialize()

            # Create a test job
            job_id = await store.create_job(
                job_type=JobType.AGENT_EXECUTION,
                metadata={"test": "smoke_test"}
            )

            # Retrieve the job
            job = await store.get_job(job_id)

            if job and job["metadata"]["test"] == "smoke_test":
                self.log_test(
                    "Job Store",
                    "PASS",
                    "Job store create/retrieve working"
                )
                await store.close()
                return True
            else:
                self.log_test(
                    "Job Store",
                    "FAIL",
                    "Job not found or corrupted"
                )
                await store.close()
                return False

        except Exception as e:
            self.log_test("Job Store", "FAIL", f"Error: {str(e)}")
            return False

    async def test_workflow_patterns(self) -> bool:
        """Test 4: Workflow Patterns - Can import all patterns"""
        try:
            from src.workflow.patterns.sequential import SequentialWorkflow
            from src.workflow.patterns.parallel import ParallelWorkflow
            from src.workflow.patterns.debate import DebateWorkflow
            from src.workflow.patterns.verification import VerificationWorkflow
            from src.workflow.patterns.expert_panel import ExpertPanelWorkflow

            patterns_loaded = [
                "Sequential",
                "Parallel",
                "Debate",
                "Verification",
                "Expert Panel"
            ]

            self.log_test(
                "Workflow Patterns",
                "PASS",
                f"All 5 patterns loaded: {', '.join(patterns_loaded)}"
            )
            return True

        except Exception as e:
            self.log_test("Workflow Patterns", "FAIL", f"Error: {str(e)}")
            return False

    async def test_context_enrichment(self) -> bool:
        """Test 5: Context Enrichment Service"""
        try:
            from src.services.infrastructure.context_enrichment.service import (
                ContextEnrichmentService
            )

            service = ContextEnrichmentService()

            # Test service initialization
            if service:
                self.log_test(
                    "Context Enrichment",
                    "PASS",
                    "Service initialized successfully"
                )
                return True
            else:
                self.log_test(
                    "Context Enrichment",
                    "FAIL",
                    "Service not initialized"
                )
                return False

        except Exception as e:
            self.log_test("Context Enrichment", "FAIL", f"Error: {str(e)}")
            return False

    async def test_configuration(self) -> bool:
        """Test 6: Configuration Loading"""
        try:
            from src.core.config import get_settings

            settings = get_settings()

            # Check critical settings
            checks = [
                hasattr(settings, 'database'),
                hasattr(settings, 'api'),
                hasattr(settings, 'anthropic'),
                hasattr(settings, 'logging'),
            ]

            if all(checks):
                self.log_test(
                    "Configuration",
                    "PASS",
                    "All config sections loaded"
                )
                return True
            else:
                self.log_test(
                    "Configuration",
                    "FAIL",
                    "Missing configuration sections"
                )
                return False

        except Exception as e:
            self.log_test("Configuration", "FAIL", f"Error: {str(e)}")
            return False

    async def test_agent_base_class(self) -> bool:
        """Test 7: Agent Base Class"""
        try:
            from src.agents.base.base_agent import BaseAgent

            # Check class exists and has required methods
            required_methods = ['execute', '_execute']
            has_methods = all(hasattr(BaseAgent, m) for m in required_methods)

            if has_methods:
                self.log_test(
                    "Agent Base Class",
                    "PASS",
                    "Base agent structure valid"
                )
                return True
            else:
                self.log_test(
                    "Agent Base Class",
                    "FAIL",
                    "Missing required methods"
                )
                return False

        except Exception as e:
            self.log_test("Agent Base Class", "FAIL", f"Error: {str(e)}")
            return False

    async def test_workflow_engine(self) -> bool:
        """Test 8: Workflow Engine"""
        try:
            from src.workflow.engine import AgentWorkflowEngine

            engine = AgentWorkflowEngine(timeout=30, max_retries=2)

            if engine:
                self.log_test(
                    "Workflow Engine",
                    "PASS",
                    "Engine initialized successfully"
                )
                return True
            else:
                self.log_test(
                    "Workflow Engine",
                    "FAIL",
                    "Engine not initialized"
                )
                return False

        except Exception as e:
            self.log_test("Workflow Engine", "FAIL", f"Error: {str(e)}")
            return False

    async def test_api_models(self) -> bool:
        """Test 9: API Models"""
        try:
            from src.api.models.agent_models import (
                AgentExecuteRequest,
                AgentExecuteResponse
            )
            from src.api.models.workflow_models import (
                SequentialWorkflowRequest,
                WorkflowJobResponse
            )

            # Test model creation
            request = AgentExecuteRequest(
                agent_name="test",
                query="test query"
            )

            if request.agent_name == "test":
                self.log_test(
                    "API Models",
                    "PASS",
                    "Pydantic models working correctly"
                )
                return True
            else:
                self.log_test(
                    "API Models",
                    "FAIL",
                    "Model validation failed"
                )
                return False

        except Exception as e:
            self.log_test("API Models", "FAIL", f"Error: {str(e)}")
            return False

    async def test_datetime_fixes(self) -> bool:
        """Test 10: DateTime Fixes - Verify no deprecated usage"""
        try:
            import subprocess
            result = subprocess.run(
                ['grep', '-r', 'datetime.utcnow()', 'src/', '--include=*.py'],
                capture_output=True,
                text=True
            )

            # If grep finds nothing, return code is 1
            if result.returncode == 1:
                self.log_test(
                    "DateTime Deprecations",
                    "PASS",
                    "No deprecated datetime.utcnow() found"
                )
                return True
            else:
                count = len(result.stdout.split('\n')) - 1
                self.log_test(
                    "DateTime Deprecations",
                    "FAIL",
                    f"{count} instances still remain"
                )
                return False

        except Exception as e:
            self.log_test("DateTime Deprecations", "FAIL", f"Error: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all smoke tests"""
        print("="*70)
        print("MULTI-AGENT SUPPORT SYSTEM - SMOKE TEST SUITE")
        print("="*70)
        print(f"Started at: {datetime.now(UTC).isoformat()}")
        print()

        # Run all tests
        tests = [
            self.test_configuration,
            self.test_agent_registry,
            self.test_agent_base_class,
            self.test_job_store,
            self.test_workflow_patterns,
            self.test_workflow_engine,
            self.test_context_enrichment,
            self.test_api_models,
            self.test_datetime_fixes,
            # Database test last (may fail in environments without DB)
            self.test_database_connection,
        ]

        for test in tests:
            await test()
            print()  # Blank line between tests

        # Summary
        print("="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: \033[92m{self.passed}\033[0m")
        print(f"Failed: \033[91m{self.failed}\033[0m")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        print("="*70)

        return self.failed == 0


async def main():
    """Main entry point"""
    tester = SmokeTest()
    success = await tester.run_all_tests()

    if success:
        print("\n✓ All smoke tests PASSED! System is healthy.")
        sys.exit(0)
    else:
        print("\n✗ Some smoke tests FAILED. See details above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
