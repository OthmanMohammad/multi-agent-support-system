"""
Encryption Validator Agent - TASK-2309

Validates encryption at rest and in transit across all systems.
Ensures compliance with security standards and best practices.
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("encryption_validator", tier="operational", category="security")
class EncryptionValidatorAgent(BaseAgent):
    """
    Encryption Validator Agent.

    Comprehensive encryption validation:
    - Encryption at rest (databases, storage, backups)
    - Encryption in transit (TLS/SSL, API calls)
    - Key management practices
    - Certificate validation
    - Cipher suite strength
    - Algorithm compliance
    - Key rotation policies
    - Encryption coverage analysis

    Standards:
    - TLS 1.2+ required
    - AES-256 for data at rest
    - RSA 2048+ or ECC 256+ for keys
    - No deprecated algorithms (MD5, SHA1, DES, RC4)
    """

    # Approved encryption algorithms
    APPROVED_ALGORITHMS = {
        "symmetric": {
            "AES-256-GCM": {"strength": "strong", "key_size": 256},
            "AES-256-CBC": {"strength": "strong", "key_size": 256},
            "AES-128-GCM": {"strength": "adequate", "key_size": 128},
            "ChaCha20-Poly1305": {"strength": "strong", "key_size": 256}
        },
        "asymmetric": {
            "RSA-4096": {"strength": "strong", "key_size": 4096},
            "RSA-2048": {"strength": "adequate", "key_size": 2048},
            "ECDSA-P256": {"strength": "strong", "key_size": 256},
            "ECDSA-P384": {"strength": "strong", "key_size": 384},
            "Ed25519": {"strength": "strong", "key_size": 256}
        },
        "hash": {
            "SHA-256": {"strength": "strong"},
            "SHA-384": {"strength": "strong"},
            "SHA-512": {"strength": "strong"},
            "SHA3-256": {"strength": "strong"}
        }
    }

    # Deprecated/weak algorithms
    DEPRECATED_ALGORITHMS = [
        "DES", "3DES", "RC4", "MD5", "SHA1",
        "AES-128-ECB", "RSA-1024", "DSA"
    ]

    # TLS versions
    TLS_VERSIONS = {
        "TLS 1.3": {"status": "approved", "strength": "strong"},
        "TLS 1.2": {"status": "approved", "strength": "adequate"},
        "TLS 1.1": {"status": "deprecated", "strength": "weak"},
        "TLS 1.0": {"status": "deprecated", "strength": "weak"},
        "SSL 3.0": {"status": "forbidden", "strength": "insecure"},
        "SSL 2.0": {"status": "forbidden", "strength": "insecure"}
    }

    # Key rotation policies (in days)
    KEY_ROTATION_PERIODS = {
        "symmetric_keys": 90,
        "certificates": 365,
        "api_keys": 180,
        "signing_keys": 730
    }

    def __init__(self):
        config = AgentConfig(
            name="encryption_validator",
            type=AgentType.SECURITY,
            model="claude-sonnet-4-5-20250929",
            temperature=0.1,
            max_tokens=2500,
            capabilities=[AgentCapability.DATABASE_READ],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Validate encryption across systems.

        Args:
            state: Current agent state with encryption configuration

        Returns:
            Updated state with validation results
        """
        self.logger.info("encryption_validation_started")

        state = self.update_state(state)

        # Extract parameters
        validation_scope = state.get("entities", {}).get("scope", "comprehensive")  # comprehensive, transit, rest
        databases = state.get("entities", {}).get("databases", [])
        storage_systems = state.get("entities", {}).get("storage_systems", [])
        api_endpoints = state.get("entities", {}).get("api_endpoints", [])
        certificates = state.get("entities", {}).get("certificates", [])
        encryption_keys = state.get("entities", {}).get("encryption_keys", [])

        self.logger.debug(
            "encryption_validation_details",
            scope=validation_scope,
            databases=len(databases),
            api_endpoints=len(api_endpoints)
        )

        # Validate encryption at rest
        rest_results = []
        if validation_scope in ["comprehensive", "rest"]:
            rest_results = self._validate_encryption_at_rest(
                databases,
                storage_systems
            )

        # Validate encryption in transit
        transit_results = []
        if validation_scope in ["comprehensive", "transit"]:
            transit_results = self._validate_encryption_in_transit(
                api_endpoints,
                certificates
            )

        # Validate key management
        key_management_results = self._validate_key_management(encryption_keys)

        # Check for deprecated algorithms
        deprecated_usage = self._check_deprecated_algorithms(
            rest_results + transit_results + key_management_results
        )

        # Validate certificate health
        certificate_issues = self._validate_certificates(certificates)

        # Calculate encryption coverage
        coverage_score = self._calculate_encryption_coverage(
            rest_results,
            transit_results,
            len(databases) + len(storage_systems) + len(api_endpoints)
        )

        # Identify vulnerabilities
        vulnerabilities = self._identify_vulnerabilities(
            deprecated_usage,
            certificate_issues,
            rest_results,
            transit_results
        )

        # Generate remediation plan
        remediation_plan = self._generate_remediation_plan(vulnerabilities)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            coverage_score,
            vulnerabilities,
            deprecated_usage,
            certificate_issues
        )

        # Format response
        response = self._format_validation_report(
            validation_scope,
            rest_results,
            transit_results,
            key_management_results,
            coverage_score,
            vulnerabilities,
            certificate_issues,
            remediation_plan,
            recommendations
        )

        state["agent_response"] = response
        state["encryption_at_rest"] = rest_results
        state["encryption_in_transit"] = transit_results
        state["key_management"] = key_management_results
        state["encryption_coverage"] = coverage_score
        state["vulnerabilities"] = vulnerabilities
        state["certificate_issues"] = certificate_issues
        state["remediation_plan"] = remediation_plan
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.95
        state["status"] = "resolved"
        state["next_agent"] = None

        # Alert on critical vulnerabilities
        critical_vulns = [v for v in vulnerabilities if v["severity"] == "critical"]
        if critical_vulns:
            state["alert_pagerduty"] = True
            state["alert_severity"] = "critical"
            state["alert_message"] = f"CRITICAL: {len(critical_vulns)} encryption vulnerabilities"

        self.logger.info(
            "encryption_validation_completed",
            coverage_score=coverage_score,
            vulnerabilities=len(vulnerabilities),
            critical_count=len(critical_vulns)
        )

        return state

    def _validate_encryption_at_rest(
        self,
        databases: List[Dict[str, Any]],
        storage_systems: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate encryption at rest for databases and storage.

        Args:
            databases: Database configurations
            storage_systems: Storage system configurations

        Returns:
            Validation results
        """
        results = []

        # Validate databases
        for db in databases:
            db_name = db.get("name", "unknown")
            encryption_enabled = db.get("encryption_enabled", False)
            encryption_algorithm = db.get("encryption_algorithm", "none")

            validation = {
                "system_type": "database",
                "system_name": db_name,
                "encryption_enabled": encryption_enabled,
                "algorithm": encryption_algorithm,
                "compliant": False,
                "issues": []
            }

            if not encryption_enabled:
                validation["issues"].append("Encryption not enabled")
                validation["severity"] = "critical"
            elif encryption_algorithm in self.DEPRECATED_ALGORITHMS:
                validation["issues"].append(f"Using deprecated algorithm: {encryption_algorithm}")
                validation["severity"] = "high"
            elif encryption_algorithm in self.APPROVED_ALGORITHMS["symmetric"]:
                validation["compliant"] = True
                validation["severity"] = "none"
                validation["algorithm_strength"] = self.APPROVED_ALGORITHMS["symmetric"][encryption_algorithm]["strength"]
            else:
                validation["issues"].append(f"Unknown encryption algorithm: {encryption_algorithm}")
                validation["severity"] = "medium"

            results.append(validation)

        # Validate storage systems
        for storage in storage_systems:
            storage_name = storage.get("name", "unknown")
            encryption_enabled = storage.get("encryption_enabled", False)
            encryption_type = storage.get("encryption_type", "none")  # SSE-S3, SSE-KMS, etc.

            validation = {
                "system_type": "storage",
                "system_name": storage_name,
                "encryption_enabled": encryption_enabled,
                "encryption_type": encryption_type,
                "compliant": False,
                "issues": []
            }

            if not encryption_enabled:
                validation["issues"].append("Storage encryption not enabled")
                validation["severity"] = "critical"
            elif encryption_type in ["SSE-KMS", "SSE-C", "AES-256"]:
                validation["compliant"] = True
                validation["severity"] = "none"
            else:
                validation["issues"].append(f"Weak encryption type: {encryption_type}")
                validation["severity"] = "high"

            results.append(validation)

        return results

    def _validate_encryption_in_transit(
        self,
        api_endpoints: List[Dict[str, Any]],
        certificates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate encryption in transit (TLS/SSL).

        Args:
            api_endpoints: API endpoint configurations
            certificates: SSL/TLS certificates

        Returns:
            Validation results
        """
        results = []

        for endpoint in api_endpoints:
            endpoint_url = endpoint.get("url", "unknown")
            tls_enabled = endpoint.get("tls_enabled", False)
            tls_version = endpoint.get("tls_version", "none")
            cipher_suites = endpoint.get("cipher_suites", [])

            validation = {
                "system_type": "api_endpoint",
                "endpoint": endpoint_url,
                "tls_enabled": tls_enabled,
                "tls_version": tls_version,
                "compliant": False,
                "issues": []
            }

            if not tls_enabled:
                validation["issues"].append("TLS not enabled - unencrypted traffic")
                validation["severity"] = "critical"
            elif tls_version not in self.TLS_VERSIONS:
                validation["issues"].append(f"Unknown TLS version: {tls_version}")
                validation["severity"] = "high"
            else:
                tls_info = self.TLS_VERSIONS[tls_version]
                if tls_info["status"] == "forbidden":
                    validation["issues"].append(f"Forbidden TLS version: {tls_version}")
                    validation["severity"] = "critical"
                elif tls_info["status"] == "deprecated":
                    validation["issues"].append(f"Deprecated TLS version: {tls_version}")
                    validation["severity"] = "high"
                else:
                    validation["compliant"] = True
                    validation["severity"] = "none"
                    validation["tls_strength"] = tls_info["strength"]

            # Check cipher suites
            weak_ciphers = [c for c in cipher_suites if any(w in c for w in ["RC4", "DES", "MD5"])]
            if weak_ciphers:
                validation["issues"].append(f"Weak cipher suites detected: {', '.join(weak_ciphers)}")
                validation["severity"] = "high"
                validation["compliant"] = False

            results.append(validation)

        return results

    def _validate_key_management(
        self,
        encryption_keys: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate encryption key management practices.

        Args:
            encryption_keys: Encryption key metadata

        Returns:
            Validation results
        """
        results = []

        for key in encryption_keys:
            key_id = key.get("key_id", "unknown")
            key_type = key.get("key_type", "symmetric")
            algorithm = key.get("algorithm", "unknown")
            created_at = datetime.fromisoformat(key.get("created_at", datetime.utcnow().isoformat()))
            last_rotated = datetime.fromisoformat(key.get("last_rotated", created_at.isoformat()))

            validation = {
                "key_id": key_id,
                "key_type": key_type,
                "algorithm": algorithm,
                "compliant": False,
                "issues": []
            }

            # Check algorithm
            if algorithm in self.DEPRECATED_ALGORITHMS:
                validation["issues"].append(f"Deprecated algorithm: {algorithm}")
                validation["severity"] = "critical"
            elif key_type == "symmetric" and algorithm in self.APPROVED_ALGORITHMS["symmetric"]:
                validation["compliant"] = True
                validation["severity"] = "none"
            elif key_type == "asymmetric" and algorithm in self.APPROVED_ALGORITHMS["asymmetric"]:
                validation["compliant"] = True
                validation["severity"] = "none"

            # Check rotation
            rotation_period = self.KEY_ROTATION_PERIODS.get(f"{key_type}_keys", 365)
            days_since_rotation = (datetime.utcnow() - last_rotated).days

            if days_since_rotation > rotation_period:
                validation["issues"].append(
                    f"Key not rotated in {days_since_rotation} days (policy: {rotation_period} days)"
                )
                validation["severity"] = "high" if validation.get("severity") == "none" else validation.get("severity")
                validation["compliant"] = False

            validation["days_since_rotation"] = days_since_rotation
            validation["rotation_policy_days"] = rotation_period

            results.append(validation)

        return results

    def _validate_certificates(
        self,
        certificates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate SSL/TLS certificates."""
        issues = []

        for cert in certificates:
            cert_name = cert.get("name", "unknown")
            expiry_date = datetime.fromisoformat(cert.get("expiry_date", datetime.utcnow().isoformat()))
            days_until_expiry = (expiry_date - datetime.utcnow()).days

            if days_until_expiry < 0:
                issues.append({
                    "certificate": cert_name,
                    "issue": "Certificate expired",
                    "severity": "critical",
                    "days_expired": abs(days_until_expiry)
                })
            elif days_until_expiry < 30:
                issues.append({
                    "certificate": cert_name,
                    "issue": "Certificate expiring soon",
                    "severity": "high",
                    "days_until_expiry": days_until_expiry
                })

            # Check key size
            key_size = cert.get("key_size", 0)
            if key_size < 2048:
                issues.append({
                    "certificate": cert_name,
                    "issue": f"Weak key size: {key_size} bits (minimum 2048)",
                    "severity": "high"
                })

        return issues

    def _check_deprecated_algorithms(
        self,
        all_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Check for usage of deprecated algorithms."""
        deprecated_usage = []

        for result in all_results:
            algorithm = result.get("algorithm", "")
            if algorithm in self.DEPRECATED_ALGORITHMS:
                deprecated_usage.append({
                    "system": result.get("system_name", result.get("endpoint", "unknown")),
                    "algorithm": algorithm,
                    "severity": "critical",
                    "message": f"Deprecated algorithm in use: {algorithm}"
                })

        return deprecated_usage

    def _calculate_encryption_coverage(
        self,
        rest_results: List[Dict[str, Any]],
        transit_results: List[Dict[str, Any]],
        total_systems: int
    ) -> float:
        """Calculate encryption coverage percentage (0-100)."""
        if total_systems == 0:
            return 100.0

        all_results = rest_results + transit_results
        encrypted = len([r for r in all_results if r.get("encryption_enabled") or r.get("tls_enabled")])

        coverage = (encrypted / total_systems) * 100
        return round(coverage, 1)

    def _identify_vulnerabilities(
        self,
        deprecated_usage: List[Dict[str, Any]],
        certificate_issues: List[Dict[str, Any]],
        rest_results: List[Dict[str, Any]],
        transit_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify all encryption vulnerabilities."""
        vulnerabilities = []

        # Add deprecated algorithm vulnerabilities
        vulnerabilities.extend(deprecated_usage)

        # Add certificate vulnerabilities
        vulnerabilities.extend(certificate_issues)

        # Add unencrypted systems
        for result in rest_results + transit_results:
            if not result.get("encryption_enabled") and not result.get("tls_enabled"):
                vulnerabilities.append({
                    "system": result.get("system_name", result.get("endpoint", "unknown")),
                    "severity": "critical",
                    "message": "No encryption enabled",
                    "type": result.get("system_type")
                })

        return vulnerabilities

    def _generate_remediation_plan(
        self,
        vulnerabilities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized remediation plan."""
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_vulns = sorted(
            vulnerabilities,
            key=lambda v: severity_order.get(v.get("severity", "low"), 999)
        )

        plan = []
        for i, vuln in enumerate(sorted_vulns, 1):
            plan_item = {
                "priority": i,
                "severity": vuln.get("severity"),
                "system": vuln.get("system", vuln.get("certificate", "unknown")),
                "issue": vuln.get("message", vuln.get("issue")),
                "action": self._get_remediation_action(vuln),
                "deadline": self._get_remediation_deadline(vuln.get("severity"))
            }
            plan.append(plan_item)

        return plan

    def _get_remediation_action(self, vulnerability: Dict[str, Any]) -> str:
        """Get specific remediation action for vulnerability."""
        if "deprecated algorithm" in vulnerability.get("message", "").lower():
            return "Upgrade to AES-256-GCM or approved algorithm"
        elif "certificate expired" in vulnerability.get("issue", "").lower():
            return "Renew certificate immediately"
        elif "no encryption" in vulnerability.get("message", "").lower():
            return "Enable encryption at rest/transit"
        elif "tls" in vulnerability.get("message", "").lower():
            return "Upgrade to TLS 1.2 or 1.3"
        else:
            return "Review and remediate security issue"

    def _get_remediation_deadline(self, severity: str) -> str:
        """Get remediation deadline based on severity."""
        deadlines = {
            "critical": timedelta(days=1),
            "high": timedelta(days=7),
            "medium": timedelta(days=30),
            "low": timedelta(days=90)
        }
        deadline = datetime.utcnow() + deadlines.get(severity, timedelta(days=30))
        return deadline.isoformat()

    def _generate_recommendations(
        self,
        coverage_score: float,
        vulnerabilities: List[Dict[str, Any]],
        deprecated_usage: List[Dict[str, Any]],
        certificate_issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate encryption recommendations."""
        recommendations = []

        if coverage_score < 100:
            recommendations.append(
                f"Encryption coverage at {coverage_score}%. "
                "Enable encryption on all systems to reach 100%."
            )

        critical_vulns = [v for v in vulnerabilities if v.get("severity") == "critical"]
        if critical_vulns:
            recommendations.append(
                f"CRITICAL: {len(critical_vulns)} critical encryption vulnerabilities. "
                "Remediate within 24 hours."
            )

        if deprecated_usage:
            recommendations.append(
                f"{len(deprecated_usage)} systems using deprecated algorithms. "
                "Upgrade to approved algorithms immediately."
            )

        if certificate_issues:
            recommendations.append(
                f"{len(certificate_issues)} certificate issues detected. "
                "Review and renew certificates."
            )

        recommendations.append(
            "Implement automated certificate renewal (Let's Encrypt, AWS Certificate Manager)"
        )

        recommendations.append(
            "Enforce TLS 1.2+ minimum across all endpoints"
        )

        recommendations.append(
            "Implement automated key rotation per policy"
        )

        return recommendations

    def _format_validation_report(
        self,
        validation_scope: str,
        rest_results: List[Dict[str, Any]],
        transit_results: List[Dict[str, Any]],
        key_management_results: List[Dict[str, Any]],
        coverage_score: float,
        vulnerabilities: List[Dict[str, Any]],
        certificate_issues: List[Dict[str, Any]],
        remediation_plan: List[Dict[str, Any]],
        recommendations: List[str]
    ) -> str:
        """Format encryption validation report."""
        coverage_icon = "✅" if coverage_score == 100 else "⚠️" if coverage_score >= 80 else "❌"

        report = f"""**Encryption Validation Report**

**Validation Scope:** {validation_scope.upper()}
**Encryption Coverage:** {coverage_icon} {coverage_score}%
**Vulnerabilities Found:** {len(vulnerabilities)}
**Certificate Issues:** {len(certificate_issues)}

**Encryption at Rest:** {len(rest_results)} systems
"""

        compliant_rest = len([r for r in rest_results if r.get("compliant")])
        report += f"- Compliant: {compliant_rest}/{len(rest_results)}\n"

        report += f"\n**Encryption in Transit:** {len(transit_results)} endpoints\n"
        compliant_transit = len([r for r in transit_results if r.get("compliant")])
        report += f"- Compliant: {compliant_transit}/{len(transit_results)}\n"

        report += f"\n**Key Management:** {len(key_management_results)} keys\n"
        compliant_keys = len([r for r in key_management_results if r.get("compliant")])
        report += f"- Compliant: {compliant_keys}/{len(key_management_results)}\n"

        # Top vulnerabilities
        if vulnerabilities:
            report += f"\n**Top Vulnerabilities:**\n"
            for vuln in vulnerabilities[:5]:
                severity_icon = "🔴" if vuln["severity"] == "critical" else "⚠️" if vuln["severity"] == "high" else "📋"
                report += f"{severity_icon} [{vuln['severity'].upper()}] {vuln.get('system', 'unknown')}\n"
                report += f"   {vuln.get('message', vuln.get('issue', 'Unknown issue'))}\n"

        # Remediation plan
        if remediation_plan:
            report += f"\n**Remediation Plan (Top 3):**\n"
            for item in remediation_plan[:3]:
                report += f"{item['priority']}. [{item['severity'].upper()}] {item['system']}\n"
                report += f"   {item['action']}\n"
                report += f"   Deadline: {item['deadline'][:10]}\n"

        # Recommendations
        if recommendations:
            report += f"\n**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Encryption validation completed at {datetime.utcnow().isoformat()}*"
        report += f"\n*Standards: TLS 1.2+, AES-256, RSA 2048+*"

        return report
