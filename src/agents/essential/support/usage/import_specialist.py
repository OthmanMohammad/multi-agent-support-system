"""
Import Specialist Agent - Helps import data from other tools.

Specialist for importing data from competitors (Asana, Trello, Monday) or CSV files.
"""

from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("import_specialist", tier="essential", category="usage")
class ImportSpecialist(BaseAgent):
    """
    Import Specialist Agent - Specialist for data migration and imports.

    Handles:
    - Imports from Asana, Trello, Monday.com
    - CSV file imports
    - Field mapping guidance
    - Data validation
    - Migration best practices
    - Bulk import operations
    """

    SUPPORTED_IMPORTS = {
        "asana": {
            "name": "Asana",
            "fields": ["projects", "tasks", "assignees", "due_dates", "tags", "sections"],
            "export_instructions": "In Asana: Menu → Export → JSON or CSV",
            "migration_time": "15-45 minutes",
            "preserves": ["Task hierarchy", "Assignees", "Due dates", "Custom fields"],
            "limitations": ["Comments (as notes)", "Attachments (links only)"],
        },
        "trello": {
            "name": "Trello",
            "fields": ["boards", "lists", "cards", "members", "labels", "due_dates"],
            "export_instructions": "In Trello: Board Menu → More → Print and Export → Export JSON",
            "migration_time": "10-30 minutes",
            "preserves": ["Board structure", "Card descriptions", "Members", "Labels"],
            "limitations": ["Power-Ups not transferred", "Attachments (links only)"],
        },
        "monday": {
            "name": "Monday.com",
            "fields": ["boards", "items", "columns", "users", "status", "timeline"],
            "export_instructions": "In Monday: Board Menu → Export to Excel",
            "migration_time": "20-60 minutes",
            "preserves": ["Board structure", "Column data", "Status", "People assignments"],
            "limitations": ["Automations need recreation", "Integrations not transferred"],
        },
        "jira": {
            "name": "Jira",
            "fields": ["projects", "issues", "sprints", "assignees", "labels", "components"],
            "export_instructions": "In Jira: Issues → Export → CSV (all fields)",
            "migration_time": "30-90 minutes",
            "preserves": ["Issue hierarchy", "Custom fields", "Assignees", "Sprint data"],
            "limitations": ["Workflows need recreation", "Attachments (links only)"],
        },
        "csv": {
            "name": "CSV File",
            "fields": ["custom mappable fields"],
            "export_instructions": "Prepare CSV with headers: name, description, assignee, due_date, status",
            "migration_time": "5-20 minutes",
            "preserves": ["All data in columns"],
            "limitations": ["No hierarchy", "Plain text only"],
        },
        "excel": {
            "name": "Microsoft Excel",
            "fields": ["custom mappable fields with formulas"],
            "export_instructions": "Save as .xlsx or .csv format",
            "migration_time": "5-20 minutes",
            "preserves": ["Data and basic formatting"],
            "limitations": ["Formulas not executed", "Macros not transferred"],
        },
    }

    def __init__(self):
        config = AgentConfig(
            name="import_specialist",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.MULTI_TURN,
            ],
            kb_category="usage",
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process import requests"""
        self.logger.info("import_specialist_processing_started")

        state = self.update_state(state)

        message = state["current_message"]

        self.logger.debug(
            "import_processing_started",
            message_preview=message[:100],
            turn_count=state["turn_count"],
        )

        # Detect import source
        import_source = self._detect_import_source(message)

        self.logger.info("import_source_detected", source=import_source)

        # Generate guidance
        if import_source and import_source in self.SUPPORTED_IMPORTS:
            guide = self._create_import_guide(import_source)
        else:
            guide = self._list_supported_imports()

        # Search KB for import documentation
        kb_results = await self.search_knowledge_base(
            f"{import_source} import migration guide" if import_source else "data import guide",
            category="usage",
            limit=2,
        )
        state["kb_results"] = kb_results

        if kb_results:
            self.logger.info("import_kb_articles_found", count=len(kb_results))
            guide += "\n\n**📚 Import guides:**\n"
            for i, article in enumerate(kb_results, 1):
                guide += f"{i}. {article['title']}\n"

        state["agent_response"] = guide
        state["import_source"] = import_source
        state["response_confidence"] = 0.9
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info("import_guidance_completed", source=import_source, status="resolved")

        return state

    def _detect_import_source(self, message: str) -> str | None:
        """Detect which tool user is importing from"""
        message_lower = message.lower()

        for source_key, source_info in self.SUPPORTED_IMPORTS.items():
            if source_key in message_lower or source_info["name"].lower() in message_lower:
                return source_key

        # Check for generic terms
        if any(word in message_lower for word in ["spreadsheet", "excel"]):
            return "excel"
        elif "csv" in message_lower or "comma" in message_lower:
            return "csv"

        return None

    def _create_import_guide(self, source: str) -> str:
        """Create step-by-step import guide for specific source"""
        source_info = self.SUPPORTED_IMPORTS[source]

        if source in ["csv", "excel"]:
            return self._create_csv_guide(source, source_info)
        else:
            return self._create_tool_migration_guide(source, source_info)

    def _create_csv_guide(self, source: str, source_info: dict[str, Any]) -> str:
        """Create guide for CSV/Excel import"""
        return f"""**📥 Importing from {source_info["name"]}**

**Time estimate:** {source_info["migration_time"]}

**Step 1: Prepare your file**

Your {source.upper()} should have these columns (headers in first row):
• **name** (required) - Item/task name
• **description** (optional) - Detailed description
• **assignee** (optional) - Email address of assignee
• **due_date** (optional) - Format: YYYY-MM-DD (e.g., 2024-12-25)
• **status** (optional) - One of: todo, in_progress, done, blocked
• **priority** (optional) - One of: low, medium, high, urgent
• **tags** (optional) - Comma-separated tags
• **project** (optional) - Project name to assign to

**Example CSV format:**
```
name,description,assignee,due_date,status,priority,tags
"Design homepage","Create mockups for new homepage","designer@company.com","2024-12-15","in_progress","high","design,website"
"Review PR #123","Code review for authentication feature","dev@company.com","2024-12-10","todo","medium","development,review"
"Client meeting","Discuss Q4 requirements","pm@company.com","2024-12-08","done","high","meeting,client"
```

**Step 2: Validate your data**

✓ File encoding: UTF-8 (avoid special character issues)
✓ Date format: YYYY-MM-DD only
✓ Email addresses: Valid format
✓ Status values: Exactly match our values (case-insensitive)
✓ File size: Maximum 10,000 rows per file
✓ Headers: First row must contain column names

**Step 3: Upload and import**

1. Go to **Settings → Import → Upload CSV/Excel**
2. Click "Choose File" and select your file
3. Click "Upload"
4. **Map columns** to our fields:
   - Drag and drop to match your columns with our fields
   - Preview shows first 5 rows
5. **Review import preview**:
   - Check for errors (highlighted in red)
   - Verify data looks correct
   - See how many items will be created
6. Click **"Import"** to start
7. Wait for completion (email notification sent)

**Common issues & solutions:**

❌ **Date format errors**
   → Use YYYY-MM-DD format only (2024-12-25, not 12/25/2024)

❌ **Special characters broken**
   → Save file as UTF-8 encoding

❌ **Missing required fields**
   → "name" column is required, others optional

❌ **File too large**
   → Split into multiple files (max 10,000 rows each)

❌ **Duplicate entries**
   → We'll skip duplicates based on "name" field

**Pro tips:**
• **Test first:** Import 5-10 rows to verify format
• **Backup original:** Keep your original file safe
• **Clean data:** Remove empty rows and columns
• **Use templates:** Download our CSV template (Settings → Import → Template)

**Need help?** I can review your CSV structure - just paste the first few rows!
"""

    def _create_tool_migration_guide(self, source: str, source_info: dict[str, Any]) -> str:
        """Create guide for migrating from another tool"""
        return f"""**📥 Migrating from {source_info["name"]} to Our Platform**

**Migration overview:**
• Time estimate: {source_info["migration_time"]}
• Difficulty: Medium
• Data preserved: {", ".join(source_info["preserves"][:3])}

---

**Phase 1: Export from {source_info["name"]}**

**{source_info["export_instructions"]}**

Detailed steps:
1. Log into your {source_info["name"]} account
2. Navigate to the board/project you want to export
3. Follow the export instructions above
4. Save the exported file to your computer
5. **Important:** Don't modify the exported file

**What gets exported:**
{chr(10).join(["✓ " + field.title() for field in source_info["fields"]])}

---

**Phase 2: Upload to Our Platform**

1. Go to **Settings → Import → {source_info["name"]}**
2. Click **"Choose File"** and select your exported file
3. Click **"Upload"**
4. Wait for file validation (usually <1 minute)

---

**Phase 3: Field Mapping**

We'll automatically map these fields:
{chr(10).join(["✓ " + field.title() for field in source_info["fields"][:4]])}

**Manual mapping may be needed for:**
• Custom fields
• Special tags or labels
• Team member assignments (if emails differ)

**Mapping interface:**
• Drag and drop to match fields
• Preview shows how data will look
• Red highlights indicate issues
• Skip fields you don't want to import

---

**Phase 4: Review & Import**

1. **Preview your data:**
   - Check first 10 items look correct
   - Verify dates, assignees, and status
   - Look for any errors (highlighted)

2. **Configure import options:**
   - Create new project or import to existing?
   - Preserve original IDs? (for reference)
   - Skip duplicates? (recommended: yes)

3. **Start import:**
   - Click **"Start Import"**
   - Processing time: {source_info["migration_time"]}
   - You'll receive email when done
   - Don't close the browser (optional - can monitor progress)

---

**What gets preserved:**
{chr(10).join(["✓ " + item for item in source_info["preserves"]])}

**Limitations to know:**
{chr(10).join(["⚠️  " + item for item in source_info["limitations"]])}

---

**Post-migration checklist:**

□ Verify all items imported correctly
□ Check team member assignments
□ Review due dates and priorities
□ Set up automations (if you had any in {source_info["name"]})
□ Configure notifications
□ Invite team members
□ Archive {source_info["name"]} workspace (when ready)

---

**Common migration issues:**

**❌ "Team member not found"**
Solution: Invite team members first, or map to existing users

**❌ "Duplicate project name"**
Solution: Rename project in import settings or merge with existing

**❌ "Date format invalid"**
Solution: This shouldn't happen with {source_info["name"]} exports - contact support

**❌ "File too large"**
Solution: Export smaller boards separately, or contact support for large migrations

---

**Migration best practices:**

**1. Test with small board first**
   • Start with 10-20 items
   • Verify everything works
   • Then migrate larger boards

**2. Communicate with team**
   • Let team know migration is happening
   • Set a cutover date
   • Provide training if needed

**3. Run parallel for 1 week**
   • Keep {source_info["name"]} active temporarily
   • Sync critical updates manually
   • Switch fully when confident

**4. Don't delete {source_info["name"]} data immediately**
   • Keep for 30 days as backup
   • Export final backup
   • Cancel subscription after verification period

---

**Need help?**
• Test import issues? I can troubleshoot
• Large migration (>10,000 items)? Contact support for white-glove migration
• Need custom field mapping? I can guide you
• Want to automate? Ask about our API import option

**Ready to start?** Let me know which phase you're on!
"""

    def _list_supported_imports(self) -> str:
        """List all supported import sources"""
        tools = []
        files = []

        for source_key, source_info in self.SUPPORTED_IMPORTS.items():
            if source_key in ["csv", "excel"]:
                files.append(
                    f"**{source_info['name']}**\n"
                    f"   • Fields: {', '.join(source_info['fields'][:3])}\n"
                    f"   • Time: {source_info['migration_time']}"
                )
            else:
                tools.append(
                    f"**{source_info['name']}**\n"
                    f"   • Imports: {', '.join(source_info['fields'][:3])}\n"
                    f"   • Migration time: {source_info['migration_time']}"
                )

        tools_section = "\n\n".join(tools)
        files_section = "\n\n".join(files)

        return f"""**📥 Import & Migration Guide**

**Migrate from these tools:**

{tools_section}

**Import from files:**

{files_section}

---

**Which are you migrating from?**

Just tell me the tool name or file type, and I'll provide detailed step-by-step instructions!

**Popular migrations:**
• "I'm migrating from Asana"
• "I want to import a CSV file"
• "Help me move from Trello"

**Need something else?** We also support:
• API import (for developers)
• Zapier/Make integrations
• Custom migration services (for enterprise)

Let me know how I can help!
"""


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: Asana migration
        print("=" * 60)
        print("Test 1: Migrating from Asana")
        print("=" * 60)

        state = create_initial_state("I want to migrate from Asana")

        agent = ImportSpecialist()
        result = await agent.process(state)

        print(f"\nSource: {result.get('import_source')}")
        print(f"\nResponse:\n{result['agent_response'][:500]}...")

        # Test 2: CSV import
        print("\n" + "=" * 60)
        print("Test 2: Import CSV file")
        print("=" * 60)

        state2 = create_initial_state("How do I import a CSV file?")
        result2 = await agent.process(state2)

        print(f"\nSource: {result2.get('import_source')}")
        print(f"\nResponse:\n{result2['agent_response'][:500]}...")

        # Test 3: List all options
        print("\n" + "=" * 60)
        print("Test 3: List all import options")
        print("=" * 60)

        state3 = create_initial_state("What can I import?")
        result3 = await agent.process(state3)

        print(f"\nResponse:\n{result3['agent_response'][:500]}...")

    asyncio.run(test())
