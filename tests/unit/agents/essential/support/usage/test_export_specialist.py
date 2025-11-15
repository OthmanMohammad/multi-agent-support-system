"""
Unit tests for Export Specialist agent.
"""

import pytest
from src.agents.essential.support.usage.export_specialist import ExportSpecialist
from src.workflow.state import create_initial_state


class TestExportSpecialist:
    """Test suite for Export Specialist agent"""

    @pytest.fixture
    def export_specialist(self):
        """Export Specialist instance"""
        return ExportSpecialist()

    def test_initialization(self, export_specialist):
        """Test Export Specialist initializes correctly"""
        assert export_specialist.config.name == "export_specialist"
        assert export_specialist.config.type.value == "specialist"
        assert export_specialist.config.tier == "essential"

    @pytest.mark.asyncio
    async def test_export_csv_projects(self, export_specialist):
        """Test exporting projects as CSV"""
        state = create_initial_state("I want to export my projects as CSV")

        result = await export_specialist.process(state)

        assert result["export_format"] == "csv"
        assert result["export_data_type"] == "projects"
        assert "csv" in result["agent_response"].lower()
        assert "step" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_export_pdf_reports(self, export_specialist):
        """Test exporting reports as PDF"""
        state = create_initial_state("Export reports to PDF")

        result = await export_specialist.process(state)

        assert result["export_format"] == "pdf"
        assert result["export_data_type"] == "reports"
        assert "pdf" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_export_json_tasks(self, export_specialist):
        """Test exporting tasks as JSON"""
        state = create_initial_state("How do I export tasks as JSON?")

        result = await export_specialist.process(state)

        assert result["export_format"] == "json"
        assert result["export_data_type"] == "tasks"

    @pytest.mark.asyncio
    async def test_export_help_request(self, export_specialist):
        """Test asking for export help"""
        state = create_initial_state("What are my export options?")

        result = await export_specialist.process(state)

        assert result["export_format"] == "help"
        assert "csv" in result["agent_response"].lower()
        assert "pdf" in result["agent_response"].lower()
        assert "json" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_export_format_only(self, export_specialist):
        """Test when only format is specified"""
        state = create_initial_state("I want to export as Excel")

        result = await export_specialist.process(state)

        assert result["export_format"] == "xlsx"
        assert "what would you like to export" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_export_data_only(self, export_specialist):
        """Test when only data type is specified"""
        state = create_initial_state("I want to export my tasks")

        result = await export_specialist.process(state)

        assert result["export_data_type"] == "tasks"
        assert "which format" in result["agent_response"].lower()

    def test_extract_export_type_csv(self, export_specialist):
        """Test extracting CSV export type"""
        assert export_specialist._extract_export_type("export as CSV") == "csv"
        assert export_specialist._extract_export_type("I need a comma-separated file") == "csv"

    def test_extract_export_type_pdf(self, export_specialist):
        """Test extracting PDF export type"""
        assert export_specialist._extract_export_type("export to PDF") == "pdf"

    def test_extract_export_type_json(self, export_specialist):
        """Test extracting JSON export type"""
        assert export_specialist._extract_export_type("export as JSON") == "json"

    def test_extract_export_type_excel(self, export_specialist):
        """Test extracting Excel export type"""
        assert export_specialist._extract_export_type("export to Excel") == "xlsx"
        assert export_specialist._extract_export_type("need a spreadsheet export") == "xlsx"

    def test_extract_export_type_help(self, export_specialist):
        """Test extracting help request"""
        assert export_specialist._extract_export_type("what are my options?") == "help"
        assert export_specialist._extract_export_type("which formats are available?") == "help"

    def test_extract_data_type_projects(self, export_specialist):
        """Test extracting projects data type"""
        assert export_specialist._extract_data_type("export my projects") == "projects"

    def test_extract_data_type_tasks(self, export_specialist):
        """Test extracting tasks data type"""
        assert export_specialist._extract_data_type("export tasks") == "tasks"
        assert export_specialist._extract_data_type("export todos") == "tasks"

    def test_extract_data_type_reports(self, export_specialist):
        """Test extracting reports data type"""
        assert export_specialist._extract_data_type("export reports") == "reports"

    def test_extract_data_type_everything(self, export_specialist):
        """Test extracting everything/backup data type"""
        assert export_specialist._extract_data_type("export everything") == "everything"
        assert export_specialist._extract_data_type("full backup") == "everything"
        assert export_specialist._extract_data_type("complete backup") == "everything"

    def test_explain_export_options(self, export_specialist):
        """Test export options explanation"""
        explanation = export_specialist._explain_export_options()

        assert "CSV" in explanation
        assert "PDF" in explanation
        assert "JSON" in explanation
        assert "XLSX" in explanation
        assert "projects" in explanation.lower()
        assert "tasks" in explanation.lower()

    def test_guide_export_csv_projects(self, export_specialist):
        """Test export guide for CSV projects"""
        guide = export_specialist._guide_export("csv", "projects")

        assert "CSV" in guide
        assert "projects" in guide.lower()
        assert "step" in guide.lower()
        assert "settings" in guide.lower()

    def test_guide_export_pdf_reports(self, export_specialist):
        """Test export guide for PDF reports"""
        guide = export_specialist._guide_export("pdf", "reports")

        assert "PDF" in guide
        assert "reports" in guide.lower()
        assert "50MB" in guide  # PDF size limit

    def test_explain_format_csv(self, export_specialist):
        """Test explaining CSV format"""
        explanation = export_specialist._explain_format_and_ask_data("csv")

        assert "CSV" in explanation
        assert "what would you like to export" in explanation.lower()

    def test_explain_data_projects(self, export_specialist):
        """Test explaining projects data type"""
        explanation = export_specialist._explain_data_and_ask_format("projects")

        assert "projects" in explanation.lower()
        assert "which format" in explanation.lower()

    @pytest.mark.asyncio
    async def test_export_specialist_confidence(self, export_specialist):
        """Test Export Specialist returns high confidence"""
        state = create_initial_state("Export my data")

        result = await export_specialist.process(state)

        assert result["response_confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_export_specialist_routing(self, export_specialist):
        """Test Export Specialist doesn't route to another agent"""
        state = create_initial_state("Export as CSV")

        result = await export_specialist.process(state)

        assert result["next_agent"] is None
        assert result["status"] == "resolved"
