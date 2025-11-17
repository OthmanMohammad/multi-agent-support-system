"""
Query Builder Agent - TASK-2021

Builds SQL queries from natural language requests.
Enables non-technical users to query data through conversational interface.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("query_builder", tier="operational", category="analytics")
class QueryBuilderAgent(BaseAgent):
    """
    Query Builder Agent.

    Converts natural language to SQL queries:
    - Natural language understanding
    - SQL query generation
    - Query validation
    - Query explanation
    - Parameter extraction
    - Safety checks (read-only enforcement)
    """

    # Database schema (simplified)
    SCHEMA = {
        "customers": ["id", "name", "email", "plan", "mrr", "created_at", "status"],
        "tickets": ["id", "customer_id", "subject", "status", "priority", "created_at", "resolved_at"],
        "subscriptions": ["id", "customer_id", "plan", "status", "mrr", "start_date", "end_date"],
        "usage": ["id", "customer_id", "feature", "usage_count", "date"],
        "events": ["id", "customer_id", "event_type", "timestamp", "properties"]
    }

    # Common query patterns
    QUERY_PATTERNS = {
        "count": "SELECT COUNT(*) FROM {table} WHERE {conditions}",
        "sum": "SELECT SUM({column}) FROM {table} WHERE {conditions}",
        "avg": "SELECT AVG({column}) FROM {table} WHERE {conditions}",
        "list": "SELECT {columns} FROM {table} WHERE {conditions} LIMIT {limit}",
        "group_by": "SELECT {group_column}, COUNT(*) as count FROM {table} WHERE {conditions} GROUP BY {group_column}"
    }

    def __init__(self):
        config = AgentConfig(
            name="query_builder",
            type=AgentType.GENERATOR,
             # Use Sonnet for better NL understanding
            temperature=0.2,
            max_tokens=1000,
            capabilities=[],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Build SQL query from natural language.

        Args:
            state: Current agent state with query request

        Returns:
            Updated state with generated SQL
        """
        self.logger.info("query_building_started")

        state = self.update_state(state)

        # Extract natural language query
        nl_query = state.get("current_message", "")
        execute_query = state.get("entities", {}).get("execute_query", False)

        self.logger.debug(
            "query_building_details",
            nl_query_length=len(nl_query),
            execute_query=execute_query
        )

        # Parse intent from natural language
        query_intent = await self._parse_query_intent(nl_query)

        # Generate SQL query
        sql_query = self._generate_sql_query(query_intent)

        # Validate query safety
        validation = self._validate_query_safety(sql_query)

        if not validation["is_safe"]:
            response = f"""**Query Builder - Safety Error**

The requested query was flagged as unsafe:
{validation['reason']}

Please rephrase your request to only query data (SELECT statements only)."""

            state["agent_response"] = response
            state["sql_query"] = None
            state["is_safe"] = False
            state["status"] = "resolved"
            return state

        # Explain the query
        explanation = self._explain_query(sql_query, query_intent)

        # Mock execution if requested
        execution_result = None
        if execute_query:
            execution_result = self._mock_execute_query(sql_query)

        # Format response
        response = self._format_query_response(
            nl_query,
            sql_query,
            explanation,
            execution_result
        )

        state["agent_response"] = response
        state["sql_query"] = sql_query
        state["query_intent"] = query_intent
        state["query_explanation"] = explanation
        state["execution_result"] = execution_result
        state["is_safe"] = True
        state["response_confidence"] = 0.85
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "query_building_completed",
            query_generated=True,
            is_safe=True,
            executed=execute_query
        )

        return state

    async def _parse_query_intent(self, nl_query: str) -> Dict[str, Any]:
        """
        Parse query intent from natural language.

        Args:
            nl_query: Natural language query

        Returns:
            Parsed intent
        """
        # Use Claude to understand the query
        system_prompt = """You are a SQL query intent parser. Extract the following from natural language queries:

1. Operation: count, sum, avg, list, group_by
2. Table: customers, tickets, subscriptions, usage, events
3. Columns: which columns to select/aggregate
4. Conditions: WHERE clause conditions
5. Group by: grouping column if applicable
6. Limit: result limit

Return as JSON structure."""

        user_message = f"""Parse this query:
"{nl_query}"

Available tables and columns:
- customers: id, name, email, plan, mrr, created_at, status
- tickets: id, customer_id, subject, status, priority, created_at, resolved_at
- subscriptions: id, customer_id, plan, status, mrr, start_date, end_date
- usage: id, customer_id, feature, usage_count, date

Return the intent as a structured format."""

        try:
            response = await self.call_llm(system_prompt, user_message, max_tokens=500)

            # Parse response (simplified - in production, use JSON parsing)
            intent = self._extract_intent_from_response(response, nl_query)
            return intent

        except Exception as e:
            self.logger.error("query_intent_parsing_failed", error=str(e))
            # Fallback to simple pattern matching
            return self._fallback_intent_parsing(nl_query)

    def _extract_intent_from_response(
        self,
        llm_response: str,
        nl_query: str
    ) -> Dict[str, Any]:
        """Extract intent from LLM response."""
        # Simplified extraction - in production, use proper JSON parsing
        nl_lower = nl_query.lower()

        # Determine operation
        if "how many" in nl_lower or "count" in nl_lower:
            operation = "count"
        elif "total" in nl_lower or "sum" in nl_lower:
            operation = "sum"
        elif "average" in nl_lower or "avg" in nl_lower:
            operation = "avg"
        elif "group by" in nl_lower or "breakdown" in nl_lower:
            operation = "group_by"
        else:
            operation = "list"

        # Determine table
        table = "customers"
        for tbl in self.SCHEMA.keys():
            if tbl.rstrip('s') in nl_lower or tbl in nl_lower:
                table = tbl
                break

        return {
            "operation": operation,
            "table": table,
            "columns": self.SCHEMA[table],
            "conditions": [],
            "group_by": None,
            "limit": 100
        }

    def _fallback_intent_parsing(self, nl_query: str) -> Dict[str, Any]:
        """Fallback intent parsing using pattern matching."""
        nl_lower = nl_query.lower()

        return {
            "operation": "list",
            "table": "customers",
            "columns": ["*"],
            "conditions": [],
            "limit": 10
        }

    def _generate_sql_query(self, query_intent: Dict[str, Any]) -> str:
        """
        Generate SQL query from intent.

        Args:
            query_intent: Parsed query intent

        Returns:
            SQL query string
        """
        operation = query_intent.get("operation", "list")
        table = query_intent.get("table", "customers")
        columns = query_intent.get("columns", ["*"])
        conditions = query_intent.get("conditions", [])
        group_by = query_intent.get("group_by")
        limit = query_intent.get("limit", 100)

        # Build SELECT clause
        if operation == "count":
            select_clause = "COUNT(*) as total"
        elif operation == "sum":
            col = columns[0] if columns and columns[0] != "*" else "mrr"
            select_clause = f"SUM({col}) as total"
        elif operation == "avg":
            col = columns[0] if columns and columns[0] != "*" else "mrr"
            select_clause = f"AVG({col}) as average"
        elif operation == "group_by" and group_by:
            select_clause = f"{group_by}, COUNT(*) as count"
        else:
            if columns and columns[0] == "*":
                select_clause = "*"
            else:
                select_clause = ", ".join(columns[:10])  # Limit columns

        # Build WHERE clause
        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        # Build GROUP BY clause
        group_by_clause = ""
        if operation == "group_by" and group_by:
            group_by_clause = f" GROUP BY {group_by}"

        # Build LIMIT clause
        limit_clause = ""
        if operation in ["list"] and limit:
            limit_clause = f" LIMIT {min(limit, 1000)}"  # Cap at 1000

        # Assemble query
        sql_query = f"SELECT {select_clause} FROM {table}{where_clause}{group_by_clause}{limit_clause};"

        return sql_query

    def _validate_query_safety(self, sql_query: str) -> Dict[str, Any]:
        """
        Validate query is safe (read-only).

        Args:
            sql_query: SQL query

        Returns:
            Validation result
        """
        sql_upper = sql_query.upper()

        # Check for dangerous operations
        dangerous_keywords = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
            "CREATE", "TRUNCATE", "GRANT", "REVOKE"
        ]

        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return {
                    "is_safe": False,
                    "reason": f"Query contains forbidden operation: {keyword}"
                }

        # Must start with SELECT
        if not sql_upper.strip().startswith("SELECT"):
            return {
                "is_safe": False,
                "reason": "Only SELECT queries are allowed"
            }

        return {
            "is_safe": True,
            "reason": "Query passed safety checks"
        }

    def _explain_query(
        self,
        sql_query: str,
        query_intent: Dict[str, Any]
    ) -> str:
        """Generate human-readable explanation of query."""
        operation = query_intent.get("operation", "list")
        table = query_intent.get("table", "table")

        explanations = {
            "count": f"This query counts the total number of records in the {table} table.",
            "sum": f"This query calculates the sum of values from the {table} table.",
            "avg": f"This query calculates the average of values from the {table} table.",
            "list": f"This query retrieves records from the {table} table.",
            "group_by": f"This query groups {table} records and counts them by category."
        }

        return explanations.get(operation, "This query retrieves data from the database.")

    def _mock_execute_query(self, sql_query: str) -> Dict[str, Any]:
        """Mock query execution for demonstration."""
        # In production, execute against actual database
        return {
            "executed": True,
            "rows_returned": 42,
            "execution_time_ms": 15.3,
            "sample_results": [
                {"column1": "value1", "column2": 123},
                {"column1": "value2", "column2": 456},
                {"column1": "value3", "column2": 789}
            ]
        }

    def _format_query_response(
        self,
        nl_query: str,
        sql_query: str,
        explanation: str,
        execution_result: Optional[Dict[str, Any]]
    ) -> str:
        """Format query builder response."""
        response = f"""**SQL Query Builder**

**Your Request:**
"{nl_query}"

**Generated SQL:**
```sql
{sql_query}
```

**Explanation:**
{explanation}

"""

        if execution_result:
            response += f"""**Execution Result:**
- Rows Returned: {execution_result['rows_returned']}
- Execution Time: {execution_result['execution_time_ms']}ms

**Sample Results:**
```json
{execution_result['sample_results'][:3]}
```
"""
        else:
            response += "**Note:** Query was generated but not executed. Use execute_query=true to run.\n"

        response += "\n*Query generated safely - read-only SELECT statement*"

        return response
