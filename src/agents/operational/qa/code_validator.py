"""
Code Validator Agent - TASK-2106

Validates code examples in responses for syntax, security, and best practices.
Supports Python, JavaScript, cURL, SQL, and other common languages.
Uses Claude Haiku for efficient code validation.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
import re

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("code_validator", tier="operational", category="qa")
class CodeValidatorAgent(BaseAgent):
    """
    Code Validator Agent.

    Validates code examples in responses:
    - Syntax validation for common languages
    - Security vulnerability detection
    - Best practices compliance
    - Proper error handling
    - Code completeness (imports, dependencies)
    - Language-specific linting
    - Dangerous patterns detection

    Supported languages: Python, JavaScript, TypeScript, cURL, SQL, Shell, JSON, YAML
    """

    # Supported languages and their patterns
    SUPPORTED_LANGUAGES = {
        "python": {
            "markers": ["```python", "```py"],
            "dangerous_patterns": [
                r"eval\(",
                r"exec\(",
                r"os\.system\(",
                r"subprocess\.call\(['\"].*shell=True"
            ],
            "required_patterns": []
        },
        "javascript": {
            "markers": ["```javascript", "```js", "```jsx"],
            "dangerous_patterns": [
                r"eval\(",
                r"innerHTML\s*=",
                r"document\.write\("
            ],
            "required_patterns": []
        },
        "sql": {
            "markers": ["```sql"],
            "dangerous_patterns": [
                r"DROP\s+TABLE",
                r"DELETE\s+FROM.*WHERE.*1\s*=\s*1",
                r"--\s*$"
            ],
            "required_patterns": []
        },
        "curl": {
            "markers": ["```bash", "```curl", "```sh"],
            "dangerous_patterns": [
                r"-k\s+",  # insecure SSL
                r"--insecure"
            ],
            "required_patterns": []
        }
    }

    # Common code quality issues
    CODE_ISSUES = {
        "hardcoded_credentials": [
            r"password\s*=\s*['\"][\w]+['\"]",
            r"api[_-]?key\s*=\s*['\"][\w]+['\"]",
            r"secret\s*=\s*['\"][\w]+['\"]"
        ],
        "missing_error_handling": [
            r"requests\.(get|post|put|delete)\(",
            r"fetch\("
        ],
        "insecure_practices": [
            r"md5\(",
            r"sha1\("
        ]
    }

    def __init__(self):
        config = AgentConfig(
            name="code_validator",
            type=AgentType.ANALYZER,
            temperature=0.1,
            max_tokens=2000,
            capabilities=[],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Validate code examples in response.

        Args:
            state: Current agent state with response to check

        Returns:
            Updated state with code validation results
        """
        self.logger.info("code_validation_started")

        state = self.update_state(state)

        # Extract parameters
        response_text = state.get("entities", {}).get("response_text", state.get("agent_response", ""))
        # Ensure response_text is a string
        if response_text is None:
            response_text = ""
        strict_mode = state.get("entities", {}).get("strict_mode", False)

        self.logger.debug(
            "code_validation_details",
            response_length=len(response_text),
            strict_mode=strict_mode
        )

        # Extract code blocks
        code_blocks = self._extract_code_blocks(response_text)

        if not code_blocks:
            # No code to validate
            state["agent_response"] = "No code blocks found in response"
            state["code_validation_passed"] = True
            state["code_blocks_found"] = 0
            state["validation_score"] = 100.0
            state["response_confidence"] = 0.99
            state["status"] = "resolved"
            state["next_agent"] = None
            return state

        # Validate each code block
        validation_results = []
        for block in code_blocks:
            result = self._validate_code_block(block, strict_mode)
            validation_results.append(result)

        # Aggregate issues
        all_issues = self._aggregate_issues(validation_results)

        # Generate recommendations
        recommendations = self._generate_recommendations(validation_results, all_issues)

        # Calculate validation score
        validation_score = self._calculate_validation_score(validation_results)

        # Determine pass/fail
        passed = self._determine_pass_fail(all_issues, strict_mode)

        # Format response
        response = self._format_validation_report(
            code_blocks,
            validation_results,
            all_issues,
            recommendations,
            validation_score,
            passed
        )

        state["agent_response"] = response
        state["code_validation_passed"] = passed
        state["validation_score"] = validation_score
        state["code_blocks_found"] = len(code_blocks)
        state["validation_results"] = validation_results
        state["code_issues"] = all_issues
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.91
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "code_validation_completed",
            blocks_validated=len(code_blocks),
            issues_found=len(all_issues),
            validation_score=validation_score,
            passed=passed
        )

        return state

    def _extract_code_blocks(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Extract code blocks from response.

        Args:
            response_text: Response text

        Returns:
            List of code blocks with metadata
        """
        code_blocks = []

        # Pattern for markdown code blocks
        pattern = r"```(\w+)?\n(.*?)```"
        matches = re.finditer(pattern, response_text, re.DOTALL)

        for i, match in enumerate(matches):
            language = match.group(1) or "unknown"
            code = match.group(2).strip()

            code_blocks.append({
                "block_id": f"block_{i}",
                "language": language.lower(),
                "code": code,
                "line_count": len(code.split("\n")),
                "char_count": len(code)
            })

        # Also check for inline code with backticks (for small snippets)
        inline_pattern = r"`([^`]+)`"
        inline_matches = re.finditer(inline_pattern, response_text)

        for i, match in enumerate(inline_matches):
            code = match.group(1).strip()
            # Only include if looks like code (has special chars)
            if any(char in code for char in ["(", ")", "{", "}", "[", "]", "=", ";"]):
                code_blocks.append({
                    "block_id": f"inline_{i}",
                    "language": "inline",
                    "code": code,
                    "line_count": 1,
                    "char_count": len(code)
                })

        return code_blocks

    def _validate_code_block(
        self,
        code_block: Dict[str, Any],
        strict_mode: bool
    ) -> Dict[str, Any]:
        """
        Validate a single code block.

        Args:
            code_block: Code block to validate
            strict_mode: Strict validation mode

        Returns:
            Validation results
        """
        language = code_block["language"]
        code = code_block["code"]
        issues = []

        # Check for dangerous patterns
        dangerous_issues = self._check_dangerous_patterns(code, language)
        issues.extend(dangerous_issues)

        # Check for hardcoded credentials
        credential_issues = self._check_hardcoded_credentials(code)
        issues.extend(credential_issues)

        # Check for common security issues
        security_issues = self._check_security_issues(code, language)
        issues.extend(security_issues)

        # Check basic syntax (simple heuristics)
        syntax_issues = self._check_basic_syntax(code, language)
        issues.extend(syntax_issues)

        # Check completeness
        completeness_issues = self._check_completeness(code, language)
        if strict_mode:
            issues.extend(completeness_issues)

        return {
            "block_id": code_block["block_id"],
            "language": language,
            "line_count": code_block["line_count"],
            "issues": issues,
            "passed": len([i for i in issues if i["severity"] in ["critical", "high"]]) == 0,
            "validated_at": datetime.now(UTC).isoformat()
        }

    def _check_dangerous_patterns(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Check for dangerous code patterns."""
        issues = []

        if language in self.SUPPORTED_LANGUAGES:
            patterns = self.SUPPORTED_LANGUAGES[language]["dangerous_patterns"]

            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    issues.append({
                        "type": "dangerous_pattern",
                        "severity": "critical",
                        "message": f"Dangerous pattern detected: {pattern}",
                        "pattern": pattern
                    })

        return issues

    def _check_hardcoded_credentials(self, code: str) -> List[Dict[str, Any]]:
        """Check for hardcoded credentials."""
        issues = []

        for pattern in self.CODE_ISSUES["hardcoded_credentials"]:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "type": "hardcoded_credential",
                    "severity": "critical",
                    "message": "Hardcoded credential detected - use environment variables",
                    "snippet": match.group(0)
                })

        return issues

    def _check_security_issues(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Check for common security issues."""
        issues = []

        # Check for weak cryptography
        for pattern in self.CODE_ISSUES["insecure_practices"]:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    "type": "weak_cryptography",
                    "severity": "high",
                    "message": "Weak cryptographic algorithm detected - use SHA-256 or stronger"
                })

        # Check for SQL injection risk (if SQL or contains SQL)
        if language == "sql" or "SELECT" in code.upper():
            if re.search(r"['\"].*\+.*['\"]", code) or re.search(r"f['\"].*\{.*\}.*['\"]", code):
                issues.append({
                    "type": "sql_injection_risk",
                    "severity": "critical",
                    "message": "Potential SQL injection vulnerability - use parameterized queries"
                })

        return issues

    def _check_basic_syntax(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Check basic syntax issues."""
        issues = []

        # Check for unmatched brackets/braces
        if language in ["python", "javascript", "typescript"]:
            open_parens = code.count("(")
            close_parens = code.count(")")
            open_braces = code.count("{")
            close_braces = code.count("}")
            open_brackets = code.count("[")
            close_brackets = code.count("]")

            if open_parens != close_parens:
                issues.append({
                    "type": "syntax_error",
                    "severity": "high",
                    "message": f"Unmatched parentheses: {open_parens} open, {close_parens} close"
                })

            if open_braces != close_braces:
                issues.append({
                    "type": "syntax_error",
                    "severity": "high",
                    "message": f"Unmatched braces: {open_braces} open, {close_braces} close"
                })

            if open_brackets != close_brackets:
                issues.append({
                    "type": "syntax_error",
                    "severity": "high",
                    "message": f"Unmatched brackets: {open_brackets} open, {close_brackets} close"
                })

        return issues

    def _check_completeness(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Check code completeness."""
        issues = []

        # Check for imports/includes in Python
        if language == "python":
            uses_requests = "requests." in code
            has_import = "import requests" in code or "from requests" in code

            if uses_requests and not has_import:
                issues.append({
                    "type": "missing_import",
                    "severity": "medium",
                    "message": "Using 'requests' without import statement"
                })

        # Check for error handling in HTTP requests
        if any(pattern in code for pattern in ["requests.get", "requests.post", "fetch("]):
            has_try_catch = "try:" in code or "except" in code or "catch" in code

            if not has_try_catch:
                issues.append({
                    "type": "missing_error_handling",
                    "severity": "medium",
                    "message": "HTTP request without error handling"
                })

        return issues

    def _aggregate_issues(self, validation_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate all issues from validation results."""
        all_issues = []

        for result in validation_results:
            for issue in result["issues"]:
                all_issues.append({
                    **issue,
                    "block_id": result["block_id"],
                    "language": result["language"]
                })

        return all_issues

    def _generate_recommendations(
        self,
        validation_results: List[Dict[str, Any]],
        all_issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate code validation recommendations."""
        recommendations = []

        if not all_issues:
            recommendations.append("All code examples are valid and secure")
            return recommendations

        # Group by severity
        critical = [i for i in all_issues if i["severity"] == "critical"]
        high = [i for i in all_issues if i["severity"] == "high"]
        medium = [i for i in all_issues if i["severity"] == "medium"]

        if critical:
            recommendations.append(
                f"CRITICAL: Fix {len(critical)} critical code issues before sending (security risks)"
            )

        if high:
            recommendations.append(
                f"HIGH PRIORITY: Address {len(high)} high-severity code issues"
            )

        # Specific recommendations by issue type
        issue_types = {}
        for issue in all_issues:
            issue_type = issue["type"]
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        if "hardcoded_credential" in issue_types:
            recommendations.append(
                "Replace hardcoded credentials with environment variables or placeholders"
            )

        if "sql_injection_risk" in issue_types:
            recommendations.append(
                "Use parameterized queries to prevent SQL injection"
            )

        if "missing_error_handling" in issue_types:
            recommendations.append(
                "Add try/catch blocks for better error handling"
            )

        return recommendations

    def _calculate_validation_score(self, validation_results: List[Dict[str, Any]]) -> float:
        """Calculate validation score (0-100)."""
        if not validation_results:
            return 100.0

        total_issues = 0
        severity_weights = {"critical": 25, "high": 10, "medium": 5, "low": 2}

        for result in validation_results:
            for issue in result["issues"]:
                severity = issue.get("severity", "low")
                total_issues += severity_weights.get(severity, 0)

        # Start at 100, deduct for issues
        score = max(0, 100 - total_issues)

        return round(score, 1)

    def _determine_pass_fail(self, all_issues: List[Dict[str, Any]], strict_mode: bool) -> bool:
        """Determine if code validation passes."""
        critical = [i for i in all_issues if i["severity"] == "critical"]
        high = [i for i in all_issues if i["severity"] == "high"]

        if strict_mode:
            return len(critical) == 0 and len(high) == 0
        else:
            return len(critical) == 0

    def _format_validation_report(
        self,
        code_blocks: List[Dict[str, Any]],
        validation_results: List[Dict[str, Any]],
        all_issues: List[Dict[str, Any]],
        recommendations: List[str],
        validation_score: float,
        passed: bool
    ) -> str:
        """Format code validation report."""
        status_icon = "✅" if passed else "❌"

        report = f"""**Code Validation Report**

**Status:** {status_icon} {"PASSED" if passed else "FAILED"}
**Validation Score:** {validation_score}/100
**Code Blocks Found:** {len(code_blocks)}
**Issues Detected:** {len(all_issues)}

**Code Blocks:**
"""

        for result in validation_results:
            block_status = "✓" if result["passed"] else "✗"
            report += f"{block_status} {result['block_id']} ({result['language']}) - {result['line_count']} lines\n"

        # Issues
        if all_issues:
            report += f"\n**Issues Detected:**\n"

            # Group by severity
            for severity in ["critical", "high", "medium"]:
                severity_issues = [i for i in all_issues if i["severity"] == severity]
                if severity_issues:
                    for issue in severity_issues[:3]:  # Top 3 per severity
                        icon = "🔴" if severity == "critical" else "⚠️" if severity == "high" else "ℹ️"
                        report += f"{icon} [{severity.upper()}] {issue['message']}\n"
                        report += f"   Block: {issue['block_id']} ({issue['language']})\n"

        # Recommendations
        if recommendations:
            report += f"\n**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Code validation completed at {datetime.now(UTC).isoformat()}*"

        return report
