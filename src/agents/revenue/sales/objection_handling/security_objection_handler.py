"""
Security Objection Handler Agent - TASK-1034

Handles security and compliance concerns by providing certifications,
case studies, security features, and compliance documentation.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("security_objection_handler", tier="revenue", category="sales")
class SecurityObjectionHandler(BaseAgent):
    """
    Security Objection Handler Agent - Specialist in security and compliance concerns.

    Handles:
    - Security and compliance objections
    - Certifications (SOC 2, GDPR, HIPAA, ISO)
    - Security case studies and references
    - Security feature explanations
    - Compliance documentation
    """

    # Response strategies for different security concerns
    RESPONSE_STRATEGIES = {
        "compliance_certification": {
            "approach": "certification_proof",
            "tactics": ["provide_certifications", "audit_reports", "compliance_documentation"],
            "supporting_materials": ["soc2_report", "compliance_matrix", "certification_docs"]
        },
        "data_security": {
            "approach": "security_features",
            "tactics": ["encryption_details", "security_architecture", "security_whitepaper"],
            "supporting_materials": ["security_whitepaper", "architecture_diagram", "penetration_test_results"]
        },
        "data_residency": {
            "approach": "infrastructure_details",
            "tactics": ["data_center_locations", "regional_deployment", "data_sovereignty"],
            "supporting_materials": ["infrastructure_map", "data_residency_guide", "regional_compliance"]
        },
        "access_control": {
            "approach": "feature_demonstration",
            "tactics": ["rbac_demo", "sso_integration", "audit_logging"],
            "supporting_materials": ["rbac_guide", "sso_setup_docs", "audit_log_examples"]
        },
        "security_practices": {
            "approach": "process_transparency",
            "tactics": ["security_program", "incident_response", "vulnerability_management"],
            "supporting_materials": ["security_program_overview", "incident_response_plan", "vuln_management_policy"]
        }
    }

    # Security certifications and compliance
    CERTIFICATIONS = {
        "soc2_type2": {
            "name": "SOC 2 Type II",
            "status": "certified",
            "issuer": "AICPA",
            "valid_until": "2026-12-31",
            "scope": "Security, Availability, Confidentiality",
            "report_available": True,
            "description": "Annual third-party audit of security controls"
        },
        "iso27001": {
            "name": "ISO 27001",
            "status": "certified",
            "issuer": "ISO",
            "valid_until": "2026-06-30",
            "scope": "Information Security Management System",
            "report_available": True,
            "description": "International standard for information security"
        },
        "gdpr": {
            "name": "GDPR Compliant",
            "status": "compliant",
            "issuer": "EU",
            "scope": "Data protection and privacy for EU residents",
            "report_available": True,
            "description": "Full compliance with EU data protection regulation"
        },
        "hipaa": {
            "name": "HIPAA Compliant",
            "status": "compliant",
            "issuer": "HHS",
            "scope": "Protected Health Information (PHI)",
            "report_available": True,
            "description": "Compliant for handling healthcare data"
        },
        "pci_dss": {
            "name": "PCI DSS Level 1",
            "status": "certified",
            "issuer": "PCI SSC",
            "valid_until": "2026-03-31",
            "scope": "Payment card data security",
            "report_available": False,
            "description": "Highest level of payment security compliance"
        },
        "ccpa": {
            "name": "CCPA Compliant",
            "status": "compliant",
            "issuer": "California",
            "scope": "California consumer privacy rights",
            "report_available": True,
            "description": "California Consumer Privacy Act compliance"
        }
    }

    # Security features
    SECURITY_FEATURES = {
        "encryption": {
            "at_rest": "AES-256 encryption for all data at rest",
            "in_transit": "TLS 1.3 for all data in transit",
            "key_management": "AWS KMS with automatic key rotation",
            "description": "Military-grade encryption for all data"
        },
        "access_control": {
            "rbac": "Role-based access control with granular permissions",
            "sso": "SAML 2.0 SSO integration (Okta, Azure AD, Google)",
            "mfa": "Multi-factor authentication required for all users",
            "session_management": "Automatic session timeout and IP whitelisting",
            "description": "Enterprise-grade access controls"
        },
        "network_security": {
            "firewall": "Web Application Firewall (WAF) with DDoS protection",
            "vpc": "Isolated VPC with private subnets",
            "intrusion_detection": "24/7 intrusion detection and prevention",
            "description": "Multi-layer network security"
        },
        "monitoring": {
            "logging": "Comprehensive audit logs for all actions",
            "siem": "SIEM integration for security monitoring",
            "alerting": "Real-time security alerts and notifications",
            "retention": "5-year log retention for compliance",
            "description": "Complete visibility and audit trail"
        },
        "vulnerability_management": {
            "scanning": "Weekly automated vulnerability scanning",
            "penetration_testing": "Annual third-party penetration testing",
            "bug_bounty": "Active bug bounty program",
            "patching": "24-hour SLA for critical security patches",
            "description": "Proactive security management"
        },
        "data_protection": {
            "backup": "Automated daily backups with 30-day retention",
            "disaster_recovery": "99.99% uptime SLA with multi-region failover",
            "data_deletion": "Secure data deletion upon request",
            "data_portability": "Easy data export in standard formats",
            "description": "Data protection and business continuity"
        }
    }

    # Industry-specific compliance requirements
    INDUSTRY_COMPLIANCE = {
        "healthcare": {
            "required": ["hipaa", "gdpr"],
            "recommended": ["soc2_type2", "iso27001"],
            "key_features": ["encryption", "access_control", "monitoring"],
            "documentation": "HIPAA Business Associate Agreement available"
        },
        "finance": {
            "required": ["soc2_type2", "pci_dss"],
            "recommended": ["iso27001", "gdpr"],
            "key_features": ["encryption", "access_control", "monitoring", "vulnerability_management"],
            "documentation": "SOC 2 Type II report available under NDA"
        },
        "technology": {
            "required": ["soc2_type2"],
            "recommended": ["iso27001", "gdpr"],
            "key_features": ["encryption", "access_control", "network_security"],
            "documentation": "Security whitepaper and architecture diagrams available"
        },
        "retail": {
            "required": ["pci_dss", "gdpr"],
            "recommended": ["soc2_type2"],
            "key_features": ["encryption", "network_security", "data_protection"],
            "documentation": "PCI compliance documentation available"
        },
        "government": {
            "required": ["soc2_type2", "iso27001"],
            "recommended": ["fedramp"],
            "key_features": ["encryption", "access_control", "monitoring", "data_protection"],
            "documentation": "FedRAMP certification in progress"
        }
    }

    # Security case studies
    SECURITY_CASE_STUDIES = {
        "healthcare_hipaa": {
            "company": "HealthTech Solutions (Healthcare, 1000+ employees)",
            "challenge": "Needed HIPAA compliance for patient data",
            "solution": "Deployed with BAA, encryption, audit logs, and role-based access",
            "result": "Passed HIPAA audit with zero findings, 100% data security",
            "quote": "Their security infrastructure exceeded our requirements",
            "industry": "healthcare"
        },
        "finance_sox": {
            "company": "FinServe Corp (Financial Services, 500+ employees)",
            "challenge": "Required SOX and PCI compliance",
            "solution": "SOC 2 Type II certified platform with comprehensive audit trails",
            "result": "Passed SOX audit, reduced compliance costs by 40%",
            "quote": "The security controls saved us months of compliance work",
            "industry": "finance"
        },
        "enterprise_security": {
            "company": "Global Tech Inc (Technology, 2000+ employees)",
            "challenge": "Enterprise security requirements and pen testing",
            "solution": "Passed rigorous security assessment and pen testing",
            "result": "Zero critical vulnerabilities found in security audit",
            "quote": "Best-in-class security we've seen from a SaaS vendor",
            "industry": "technology"
        }
    }

    # Severity indicators
    SEVERITY_INDICATORS = {
        "blocker": ["cannot proceed", "security audit required", "compliance mandatory", "deal breaker"],
        "major": ["security concern", "need to verify", "compliance required", "must meet"],
        "minor": ["curious about", "wondering if", "what about", "interested in"]
    }

    def __init__(self):
        config = AgentConfig(
            name="security_objection_handler",
            type=AgentType.SPECIALIST,
            model="claude-3-5-sonnet-20240620",
            temperature=0.2,  # Lower temperature for factual accuracy
            max_tokens=1200,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.ENTITY_EXTRACTION
            ],
            kb_category="sales",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process security objection handling.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with security response
        """
        self.logger.info("security_objection_handler_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "security_objection_details",
            message_preview=message[:100],
            turn_count=state["turn_count"]
        )

        # Identify security concern type
        concern_type = self._identify_concern_type(message)

        # Assess objection severity
        objection_severity = self._assess_severity(message)

        # Get industry-specific compliance requirements
        industry = customer_metadata.get("industry", "technology").lower()
        industry_compliance = self.INDUSTRY_COMPLIANCE.get(industry, self.INDUSTRY_COMPLIANCE["technology"])

        # Get relevant certifications
        relevant_certifications = self._get_relevant_certifications(concern_type, industry_compliance)

        # Get relevant security features
        relevant_features = self._get_relevant_features(concern_type, industry_compliance)

        # Get response strategy
        strategy = self.RESPONSE_STRATEGIES.get(concern_type, self.RESPONSE_STRATEGIES["security_practices"])

        # Get relevant case studies
        case_studies = self._get_case_studies(industry, concern_type)

        # Search knowledge base
        kb_results = await self.search_knowledge_base(
            message,
            category="sales",
            limit=4
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_security_response(
            message,
            concern_type,
            objection_severity,
            relevant_certifications,
            relevant_features,
            industry_compliance,
            strategy,
            case_studies,
            kb_results,
            customer_metadata
        )

        # Calculate resolution confidence
        resolution_confidence = self._calculate_resolution_confidence(
            concern_type,
            objection_severity,
            relevant_certifications,
            industry_compliance
        )

        # Determine escalation need
        needs_escalation = self._check_escalation_needed(
            objection_severity,
            resolution_confidence,
            concern_type
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = resolution_confidence
        state["concern_type"] = concern_type
        state["objection_severity"] = objection_severity
        state["relevant_certifications"] = relevant_certifications
        state["relevant_features"] = relevant_features
        state["industry_compliance"] = industry_compliance
        state["response_strategy"] = strategy
        state["case_studies"] = case_studies
        state["needs_escalation"] = needs_escalation
        state["status"] = "escalated" if needs_escalation else "resolved"

        self.logger.info(
            "security_objection_handler_completed",
            concern_type=concern_type,
            severity=objection_severity,
            confidence=resolution_confidence,
            escalated=needs_escalation
        )

        return state

    def _identify_concern_type(self, message: str) -> str:
        """Identify the type of security concern"""
        message_lower = message.lower()

        if any(term in message_lower for term in ["soc 2", "iso", "hipaa", "gdpr", "pci", "compliance", "certified"]):
            return "compliance_certification"
        elif any(term in message_lower for term in ["encryption", "secure", "protect data", "data security"]):
            return "data_security"
        elif any(term in message_lower for term in ["data center", "where is data", "data residency", "region"]):
            return "data_residency"
        elif any(term in message_lower for term in ["access control", "permissions", "sso", "authentication", "rbac"]):
            return "access_control"
        else:
            return "security_practices"

    def _assess_severity(self, message: str) -> str:
        """Assess the severity of the security objection"""
        message_lower = message.lower()

        for severity, indicators in self.SEVERITY_INDICATORS.items():
            if any(indicator in message_lower for indicator in indicators):
                return severity

        return "minor"

    def _get_relevant_certifications(
        self,
        concern_type: str,
        industry_compliance: Dict
    ) -> List[Dict[str, Any]]:
        """Get relevant certifications based on concern and industry"""
        certifications = []

        # Add required certifications for industry
        for cert_key in industry_compliance.get("required", []):
            if cert_key in self.CERTIFICATIONS:
                certifications.append({
                    "key": cert_key,
                    "data": self.CERTIFICATIONS[cert_key],
                    "priority": "required"
                })

        # Add recommended certifications
        for cert_key in industry_compliance.get("recommended", []):
            if cert_key in self.CERTIFICATIONS:
                certifications.append({
                    "key": cert_key,
                    "data": self.CERTIFICATIONS[cert_key],
                    "priority": "recommended"
                })

        # If compliance_certification concern, add all certifications
        if concern_type == "compliance_certification":
            for cert_key, cert_data in self.CERTIFICATIONS.items():
                if not any(c["key"] == cert_key for c in certifications):
                    certifications.append({
                        "key": cert_key,
                        "data": cert_data,
                        "priority": "additional"
                    })

        return certifications

    def _get_relevant_features(
        self,
        concern_type: str,
        industry_compliance: Dict
    ) -> List[Dict[str, Any]]:
        """Get relevant security features"""
        features = []

        # Get industry-specific key features
        key_features = industry_compliance.get("key_features", [])

        for feature_key in key_features:
            if feature_key in self.SECURITY_FEATURES:
                features.append({
                    "key": feature_key,
                    "data": self.SECURITY_FEATURES[feature_key]
                })

        # Add concern-specific features
        concern_features = {
            "data_security": ["encryption", "data_protection"],
            "access_control": ["access_control", "monitoring"],
            "security_practices": ["vulnerability_management", "monitoring"],
            "data_residency": ["data_protection", "network_security"]
        }

        for feature_key in concern_features.get(concern_type, []):
            if feature_key in self.SECURITY_FEATURES:
                if not any(f["key"] == feature_key for f in features):
                    features.append({
                        "key": feature_key,
                        "data": self.SECURITY_FEATURES[feature_key]
                    })

        return features

    def _get_case_studies(self, industry: str, concern_type: str) -> List[Dict[str, Any]]:
        """Get relevant security case studies"""
        case_studies = []

        for study_key, study_data in self.SECURITY_CASE_STUDIES.items():
            # Match by industry first
            if study_data.get("industry", "").lower() == industry:
                case_studies.insert(0, study_data)  # Priority to same industry
            else:
                case_studies.append(study_data)

        return case_studies[:2]  # Return top 2

    def _calculate_resolution_confidence(
        self,
        concern_type: str,
        severity: str,
        certifications: List[Dict],
        industry_compliance: Dict
    ) -> float:
        """Calculate confidence in resolving the security objection"""
        base_confidence = 0.85  # High base confidence for security (we have good coverage)

        # Adjust for severity
        severity_adjustments = {
            "minor": 0.10,
            "major": 0.0,
            "blocker": -0.10
        }
        confidence = base_confidence + severity_adjustments.get(severity, 0.0)

        # Boost if we have required certifications
        required_certs = industry_compliance.get("required", [])
        has_all_required = all(
            any(c["key"] == req for c in certifications)
            for req in required_certs
        )
        if has_all_required:
            confidence += 0.05

        return min(max(confidence, 0.0), 1.0)

    def _check_escalation_needed(
        self,
        severity: str,
        confidence: float,
        concern_type: str
    ) -> bool:
        """Determine if escalation to security team is needed"""
        # Escalate if blocker and specific compliance questions
        if severity == "blocker" and concern_type in ["compliance_certification", "data_residency"]:
            return True

        # Escalate if low confidence
        if confidence < 0.70:
            return True

        return False

    async def _generate_security_response(
        self,
        message: str,
        concern_type: str,
        severity: str,
        certifications: List[Dict],
        features: List[Dict],
        industry_compliance: Dict,
        strategy: Dict,
        case_studies: List[Dict],
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate personalized security response"""

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant documentation:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        # Build certifications context
        cert_context = "\n\nSecurity Certifications:\n"
        for cert in certifications:
            cert_data = cert["data"]
            cert_context += f"\n✓ {cert_data['name']} ({cert.get('priority', 'additional').upper()})\n"
            cert_context += f"  Status: {cert_data['status'].title()}\n"
            cert_context += f"  Scope: {cert_data['scope']}\n"
            cert_context += f"  Description: {cert_data['description']}\n"
            if cert_data.get("report_available"):
                cert_context += f"  Report: Available upon request\n"

        # Build features context
        features_context = "\n\nSecurity Features:\n"
        for feature in features:
            feature_data = feature["data"]
            features_context += f"\n{feature['key'].replace('_', ' ').title()}:\n"
            features_context += f"  {feature_data['description']}\n"
            for key, value in feature_data.items():
                if key != "description":
                    features_context += f"  • {key.replace('_', ' ').title()}: {value}\n"

        # Build case studies context
        case_context = ""
        if case_studies:
            case_context = "\n\nSecurity Case Studies:\n"
            for study in case_studies:
                case_context += f"\n{study['company']}:\n"
                case_context += f"  Challenge: {study['challenge']}\n"
                case_context += f"  Solution: {study['solution']}\n"
                case_context += f"  Result: {study['result']}\n"
                case_context += f"  Quote: \"{study['quote']}\"\n"

        # Build industry compliance context
        compliance_context = f"\n\nIndustry Compliance ({customer_metadata.get('industry', 'General').title()}):\n"
        compliance_context += f"Required: {', '.join(industry_compliance.get('required', []))}\n"
        compliance_context += f"Recommended: {', '.join(industry_compliance.get('recommended', []))}\n"
        compliance_context += f"Documentation: {industry_compliance.get('documentation', 'Available upon request')}\n"

        system_prompt = f"""You are a Security Objection Handler specialist addressing security and compliance concerns.

Objection Analysis:
- Concern Type: {concern_type.replace('_', ' ').title()}
- Severity: {severity.upper()}
- Response Strategy: {strategy['approach'].replace('_', ' ').title()}

Customer Profile:
- Company: {customer_metadata.get('company', 'Unknown')}
- Industry: {customer_metadata.get('industry', 'Unknown')}
- Role: {customer_metadata.get('title', 'Unknown')}

Your response should:
1. Take their security concerns seriously and professionally
2. Provide specific, factual information about certifications and features
3. Reference relevant industry compliance requirements
4. Share case studies from similar companies/industries
5. Offer to provide detailed documentation and reports
6. Be precise and avoid vague security claims
7. Offer next steps (security review, documentation sharing, security team call)

Key Tactics: {', '.join(strategy['tactics'])}
Supporting Materials: {', '.join(strategy['supporting_materials'])}

IMPORTANT: Be factual and precise. Security is critical - provide specific details."""

        user_prompt = f"""Customer message: {message}

{cert_context}
{features_context}
{compliance_context}
{case_context}
{kb_context}

Generate a professional, factual response that addresses their security concern."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing SecurityObjectionHandler Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Healthcare HIPAA compliance
        state1 = create_initial_state(
            "We handle patient data and need to ensure HIPAA compliance. Are you certified?",
            context={
                "customer_metadata": {
                    "company": "HealthTech Solutions",
                    "title": "Chief Compliance Officer",
                    "company_size": 300,
                    "industry": "healthcare"
                }
            }
        )

        agent = SecurityObjectionHandler()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - HIPAA Compliance (Healthcare)")
        print(f"Concern Type: {result1['concern_type']}")
        print(f"Severity: {result1['objection_severity']}")
        print(f"Resolution Confidence: {result1['response_confidence']:.2f}")
        print(f"Certifications Provided: {len(result1['relevant_certifications'])}")
        print(f"Security Features: {len(result1['relevant_features'])}")
        print(f"Needs Escalation: {result1['needs_escalation']}")
        print(f"Response:\n{result1['agent_response']}\n")

        # Test case 2: Financial services SOC 2
        state2 = create_initial_state(
            "Our security audit requires SOC 2 Type II certification. Do you have this?",
            context={
                "customer_metadata": {
                    "company": "FinServe Corp",
                    "title": "CISO",
                    "company_size": 500,
                    "industry": "finance"
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\nTest 2 - SOC 2 Certification (Finance)")
        print(f"Concern Type: {result2['concern_type']}")
        print(f"Severity: {result2['objection_severity']}")
        print(f"Resolution Confidence: {result2['response_confidence']:.2f}")
        print(f"Certifications Provided: {len(result2['relevant_certifications'])}")
        print(f"Case Studies: {len(result2['case_studies'])}")
        print(f"Response:\n{result2['agent_response']}\n")

        # Test case 3: Data encryption and security
        state3 = create_initial_state(
            "How do you encrypt our data? We need military-grade security for customer information.",
            context={
                "customer_metadata": {
                    "company": "SecureTech Inc",
                    "title": "VP of Engineering",
                    "company_size": 150,
                    "industry": "technology"
                }
            }
        )

        result3 = await agent.process(state3)

        print(f"\nTest 3 - Data Encryption and Security")
        print(f"Concern Type: {result3['concern_type']}")
        print(f"Severity: {result3['objection_severity']}")
        print(f"Resolution Confidence: {result3['response_confidence']:.2f}")
        print(f"Security Features: {len(result3['relevant_features'])}")
        print(f"Response:\n{result3['agent_response']}\n")

    asyncio.run(test())
