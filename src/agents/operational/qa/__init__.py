"""
Quality Assurance Swarm - Tier 3: Operational Excellence

This module contains 10 specialized QA agents for comprehensive
quality validation of customer responses before sending.

Agents:
- ResponseVerifierAgent (TASK-2101): Final quality gate coordinator
- FactCheckerAgent (TASK-2102): Verify facts against knowledge base
- PolicyCheckerAgent (TASK-2103): Ensure company policy compliance
- ToneCheckerAgent (TASK-2104): Validate appropriate, empathetic tone
- CompletenessCheckerAgent (TASK-2105): Ensure complete answers
- CodeValidatorAgent (TASK-2106): Validate code examples (Python, JS, cURL, etc.)
- LinkCheckerAgent (TASK-2107): Verify all links work (HTTP 200)
- SensitivityCheckerAgent (TASK-2108): Detect inappropriate/biased content
- HallucinationDetectorAgent (TASK-2109): Detect AI-generated false information
- CitationValidatorAgent (TASK-2110): Ensure proper citations and sources

All agents follow quality gate pattern: check response and return pass/fail with detailed feedback.
"""

from src.agents.operational.qa.response_verifier import ResponseVerifierAgent
from src.agents.operational.qa.fact_checker import FactCheckerAgent
from src.agents.operational.qa.policy_checker import PolicyCheckerAgent
from src.agents.operational.qa.tone_checker import ToneCheckerAgent
from src.agents.operational.qa.completeness_checker import CompletenessCheckerAgent
from src.agents.operational.qa.code_validator import CodeValidatorAgent
from src.agents.operational.qa.link_checker import LinkCheckerAgent
from src.agents.operational.qa.sensitivity_checker import SensitivityCheckerAgent
from src.agents.operational.qa.hallucination_detector import HallucinationDetectorAgent
from src.agents.operational.qa.citation_validator import CitationValidatorAgent


__all__ = [
    "ResponseVerifierAgent",
    "FactCheckerAgent",
    "PolicyCheckerAgent",
    "ToneCheckerAgent",
    "CompletenessCheckerAgent",
    "CodeValidatorAgent",
    "LinkCheckerAgent",
    "SensitivityCheckerAgent",
    "HallucinationDetectorAgent",
    "CitationValidatorAgent",
]
