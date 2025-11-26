"""
Export Specialist Agent - Helps with data exports.

Specialist for exporting data in various formats (CSV, PDF, JSON, Excel).
"""

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("export_specialist", tier="essential", category="usage")
class ExportSpecialist(BaseAgent):
    """
    Export Specialist Agent - Specialist for data export operations.

    Handles:
    - CSV exports for spreadsheets
    - PDF exports for reports
    - JSON exports for API/integration
    - Excel exports with formatting
    - Bulk export guidance
    - Scheduled exports
    """

    EXPORT_FORMATS = {
        "csv": {
            "name": "CSV (Comma-Separated Values)",
            "description": "Spreadsheet format compatible with Excel and Google Sheets",
            "use_case": "Data analysis and manipulation",
            "file_extension": ".csv",
            "max_size": "Unlimited",
            "pros": ["Universal compatibility", "Lightweight", "Easy to edit"],
            "cons": ["No formatting", "No formulas", "Plain text only"],
        },
        "pdf": {
            "name": "PDF (Portable Document Format)",
            "description": "Printable reports with formatting preserved",
            "use_case": "Presentations and documentation",
            "file_extension": ".pdf",
            "max_size": "50 MB per file",
            "pros": ["Professional appearance", "Preserves formatting", "Shareable"],
            "cons": ["Not editable", "Larger file size", "Limited to 50MB"],
        },
        "json": {
            "name": "JSON (JavaScript Object Notation)",
            "description": "Structured data format for developers and APIs",
            "use_case": "API integration and custom scripts",
            "file_extension": ".json",
            "max_size": "Unlimited",
            "pros": ["Machine-readable", "Preserves structure", "API-friendly"],
            "cons": ["Not human-friendly", "Requires technical knowledge"],
        },
        "xlsx": {
            "name": "Excel (XLSX)",
            "description": "Microsoft Excel format with formulas and formatting",
            "use_case": "Advanced spreadsheet analysis",
            "file_extension": ".xlsx",
            "max_size": "100 MB per file",
            "pros": ["Preserves formulas", "Multiple sheets", "Rich formatting"],
            "cons": ["Requires Excel or compatible app", "Larger than CSV"],
        },
        "xml": {
            "name": "XML (Extensible Markup Language)",
            "description": "Structured data format for enterprise systems",
            "use_case": "Enterprise integration and data exchange",
            "file_extension": ".xml",
            "max_size": "Unlimited",
            "pros": ["Industry standard", "Hierarchical data", "Self-describing"],
            "cons": ["Verbose", "Requires parsing", "Technical"],
        },
    }

    EXPORT_TYPES = {
        "projects": "All project data including tasks, members, and settings",
        "tasks": "Task lists with metadata (assignees, dates, status)",
        "reports": "Analytics dashboards and custom reports",
        "time_tracking": "Time entries and activity logs",
        "comments": "All comments and discussions",
        "attachments": "Files and documents (links only in CSV/JSON)",
        "everything": "Complete account backup (all data)",
    }

    def __init__(self):
        config = AgentConfig(
            name="export_specialist",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[AgentCapability.KB_SEARCH, AgentCapability.CONTEXT_AWARE],
            kb_category="usage",
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process export requests"""
        self.logger.info("export_specialist_processing_started")

        state = self.update_state(state)

        message = state["current_message"]

        self.logger.debug(
            "export_processing_started",
            message_preview=message[:100],
            turn_count=state["turn_count"],
        )

        # Extract export intent
        export_type = self._extract_export_type(message)
        data_to_export = self._extract_data_type(message)

        self.logger.info("export_intent_detected", format=export_type, data_type=data_to_export)

        # Generate appropriate response
        if export_type == "help" or (not export_type and not data_to_export):
            response = self._explain_export_options()
        elif export_type and data_to_export:
            response = self._guide_export(export_type, data_to_export)
        elif export_type:
            response = self._explain_format_and_ask_data(export_type)
        elif data_to_export:
            response = self._explain_data_and_ask_format(data_to_export)
        else:
            response = self._explain_export_options()

        # Search KB for export documentation
        kb_results = await self.search_knowledge_base(
            "data export guide", category="usage", limit=2
        )
        state["kb_results"] = kb_results

        if kb_results:
            self.logger.info("export_kb_articles_found", count=len(kb_results))
            response += "\n\n**📚 Export documentation:**\n"
            for i, article in enumerate(kb_results, 1):
                response += f"{i}. {article['title']}\n"

        state["agent_response"] = response
        state["export_format"] = export_type
        state["export_data_type"] = data_to_export
        state["response_confidence"] = 0.9
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "export_guidance_completed",
            format=export_type,
            data_type=data_to_export,
            status="resolved",
        )

        return state

    def _extract_export_type(self, message: str) -> str | None:
        """Extract export format from message"""
        message_lower = message.lower()

        if any(
            word in message_lower for word in ["help", "what formats", "which format", "options"]
        ):
            return "help"

        for format_key in self.EXPORT_FORMATS:
            if format_key in message_lower:
                return format_key

        # Check for aliases
        if any(word in message_lower for word in ["excel", "spreadsheet"]):
            return "xlsx"
        elif "comma" in message_lower or "comma-separated" in message_lower:
            return "csv"

        return None

    def _extract_data_type(self, message: str) -> str | None:
        """Extract data type to export from message"""
        message_lower = message.lower()

        for data_key in self.EXPORT_TYPES:
            if data_key in message_lower:
                return data_key

        # Check for aliases
        if any(word in message_lower for word in ["all data", "full backup", "complete backup"]):
            return "everything"
        elif any(word in message_lower for word in ["task", "todo", "action items"]):
            return "tasks"
        elif any(word in message_lower for word in ["project"]):
            return "projects"

        return None

    def _explain_export_options(self) -> str:
        """Explain available export formats and data types"""
        formats = "\n".join(
            [
                f"**{info['name']}** ({key.upper()})\n"
                f"   • {info['description']}\n"
                f"   • Best for: {info['use_case']}\n"
                f"   • Max size: {info['max_size']}"
                for key, info in self.EXPORT_FORMATS.items()
            ]
        )

        data_types = "\n".join(
            [f"• **{key.title()}** - {desc}" for key, desc in self.EXPORT_TYPES.items()]
        )

        return f"""**📤 Data Export Guide**

**Available formats:**

{formats}

**What you can export:**

{data_types}

**How to export:**
1. Go to **Settings → Data → Export**
2. Choose what to export
3. Select format
4. Click "Generate Export"
5. Download file (email sent when ready)

**Which would you like to export?** Tell me the format and data type, and I'll walk you through it!
"""

    def _guide_export(self, export_format: str, data_type: str) -> str:
        """Provide detailed export guidance"""
        format_info = self.EXPORT_FORMATS.get(export_format, {})
        data_desc = self.EXPORT_TYPES.get(data_type, "selected data")

        return f"""**📤 Exporting {data_type.title()} as {format_info.get("name", export_format.upper())}**

**What you're exporting:**
{data_desc}

**Format details:**
• File type: {format_info.get("name", export_format.upper())}
• Extension: {format_info.get("file_extension", "")}
• Max size: {format_info.get("max_size", "Unlimited")}

**Step-by-step instructions:**

1. **Navigate to Export**
   • Go to Settings → Data → Export
   • Or use keyboard shortcut: `Ctrl/Cmd + E`

2. **Select data**
   • From the "What to export" dropdown, select **"{data_type.title()}"**
   • Choose date range (if applicable)
   • Apply any filters (optional)

3. **Choose format**
   • Select **"{format_info.get("name", export_format.upper())}"** from format dropdown
   • Configure export options (if available)

4. **Generate export**
   • Click "Generate Export" button
   • Processing time: Usually <5 minutes
   • Large exports may take up to 30 minutes

5. **Download**
   • You'll receive an email when ready
   • Download link valid for 7 days
   • Exports are also saved in Settings → Data → Export History

**What's included:**
✓ All {data_type} data and related metadata
✓ Created/modified dates and ownership
✓ Custom field values
{"✓ Attachments (for PDF/ZIP exports)" if export_format in ["pdf", "zip"] else "✓ Attachment links (actual files not included)"}

**Pro tips:**
• **Schedule recurring exports:** Settings → Automation → Scheduled Exports
• **API access:** Use our API for real-time data access (no manual export needed)
• **Incremental exports:** Export only data changed since last export
• **Backup retention:** Exports are kept for 7 days, download promptly

**File size considerations:**
{"• PDF exports are limited to 50MB. Large exports will be split into multiple files." if export_format == "pdf" else ""}
{"• Excel files can become large with lots of data. Consider CSV for very large datasets." if export_format == "xlsx" else ""}
{"• JSON exports preserve full data structure but can be verbose." if export_format == "json" else ""}

**Need help with anything specific?** Let me know!
"""

    def _explain_format_and_ask_data(self, export_format: str) -> str:
        """Explain format and ask what data to export"""
        format_info = self.EXPORT_FORMATS.get(export_format, {})

        data_options = "\n".join(
            [f"• **{key.title()}** - {desc}" for key, desc in self.EXPORT_TYPES.items()]
        )

        return f"""**You've chosen {format_info.get("name", export_format.upper())} format** ✓

**Format details:**
• {format_info.get("description", "")}
• Best for: {format_info.get("use_case", "")}
• File size limit: {format_info.get("max_size", "Unlimited")}

**Pros:**
{chr(10).join(["  ✓ " + pro for pro in format_info.get("pros", [])])}

**Cons:**
{chr(10).join(["  ✗ " + con for con in format_info.get("cons", [])])}

**What would you like to export?**

{data_options}

Just tell me what you want to export, and I'll provide detailed instructions!
"""

    def _explain_data_and_ask_format(self, data_type: str) -> str:
        """Explain data type and ask which format"""
        data_desc = self.EXPORT_TYPES.get(data_type, "data")

        formats = "\n".join(
            [
                f"• **{info['name']}** - {info['use_case']}"
                for key, info in self.EXPORT_FORMATS.items()
            ]
        )

        return f"""**You want to export: {data_type.title()}** ✓

**What's included:**
{data_desc}

**Which format would you like?**

{formats}

**Recommendations:**
• For analysis in Excel/Sheets: Use **CSV** or **XLSX**
• For presentations/printing: Use **PDF**
• For developers/API integration: Use **JSON**
• For enterprise systems: Use **XML**

Let me know your preferred format!
"""


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: Export CSV
        print("=" * 60)
        print("Test 1: Export projects as CSV")
        print("=" * 60)

        state = create_initial_state("I want to export my projects as CSV")

        agent = ExportSpecialist()
        result = await agent.process(state)

        print(f"\nFormat: {result.get('export_format')}")
        print(f"Data type: {result.get('export_data_type')}")
        print(f"\nResponse:\n{result['agent_response'][:500]}...")

        # Test 2: Ask for help
        print("\n" + "=" * 60)
        print("Test 2: Ask for export options")
        print("=" * 60)

        state2 = create_initial_state("What are my export options?")
        result2 = await agent.process(state2)

        print(f"\nResponse:\n{result2['agent_response'][:500]}...")

        # Test 3: Only format specified
        print("\n" + "=" * 60)
        print("Test 3: Only format specified (PDF)")
        print("=" * 60)

        state3 = create_initial_state("I want to export as PDF")
        result3 = await agent.process(state3)

        print(f"\nResponse:\n{result3['agent_response'][:500]}...")

    asyncio.run(test())
