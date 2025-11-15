"""
Unit tests for Import Specialist agent.
"""

import pytest
from src.agents.essential.support.usage.import_specialist import ImportSpecialist
from src.workflow.state import create_initial_state


class TestImportSpecialist:
    """Test suite for Import Specialist agent"""

    @pytest.fixture
    def import_specialist(self):
        """Import Specialist instance"""
        return ImportSpecialist()

    def test_initialization(self, import_specialist):
        """Test Import Specialist initializes correctly"""
        assert import_specialist.config.name == "import_specialist"
        assert import_specialist.config.type.value == "specialist"
        assert import_specialist.config.tier == "essential"

    @pytest.mark.asyncio
    async def test_migrate_from_asana(self, import_specialist):
        """Test migrating from Asana"""
        state = create_initial_state("I want to migrate from Asana")

        result = await import_specialist.process(state)

        assert result["import_source"] == "asana"
        assert "asana" in result["agent_response"].lower()
        assert "step" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_migrate_from_trello(self, import_specialist):
        """Test migrating from Trello"""
        state = create_initial_state("Migrate from Trello")

        result = await import_specialist.process(state)

        assert result["import_source"] == "trello"
        assert "trello" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_migrate_from_monday(self, import_specialist):
        """Test migrating from Monday.com"""
        state = create_initial_state("How do I import from Monday.com?")

        result = await import_specialist.process(state)

        assert result["import_source"] == "monday"
        assert "monday" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_import_csv_file(self, import_specialist):
        """Test importing CSV file"""
        state = create_initial_state("How do I import a CSV file?")

        result = await import_specialist.process(state)

        assert result["import_source"] == "csv"
        assert "csv" in result["agent_response"].lower()
        assert "utf-8" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_import_excel_file(self, import_specialist):
        """Test importing Excel file"""
        state = create_initial_state("Import from Excel spreadsheet")

        result = await import_specialist.process(state)

        assert result["import_source"] == "excel"
        assert "excel" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_list_supported_imports(self, import_specialist):
        """Test listing all supported import sources"""
        state = create_initial_state("What can I import?")

        result = await import_specialist.process(state)

        assert result["import_source"] is None
        assert "asana" in result["agent_response"].lower()
        assert "trello" in result["agent_response"].lower()
        assert "csv" in result["agent_response"].lower()

    def test_detect_import_source_asana(self, import_specialist):
        """Test detecting Asana as import source"""
        assert import_specialist._detect_import_source("migrate from Asana") == "asana"
        assert import_specialist._detect_import_source("import Asana data") == "asana"

    def test_detect_import_source_trello(self, import_specialist):
        """Test detecting Trello as import source"""
        assert import_specialist._detect_import_source("coming from Trello") == "trello"

    def test_detect_import_source_monday(self, import_specialist):
        """Test detecting Monday.com as import source"""
        assert import_specialist._detect_import_source("Monday.com migration") == "monday"

    def test_detect_import_source_jira(self, import_specialist):
        """Test detecting Jira as import source"""
        assert import_specialist._detect_import_source("import from Jira") == "jira"

    def test_detect_import_source_csv(self, import_specialist):
        """Test detecting CSV as import source"""
        assert import_specialist._detect_import_source("upload CSV file") == "csv"
        assert import_specialist._detect_import_source("import comma-separated") == "csv"

    def test_detect_import_source_excel(self, import_specialist):
        """Test detecting Excel as import source"""
        assert import_specialist._detect_import_source("import Excel file") == "excel"
        assert import_specialist._detect_import_source("upload spreadsheet") == "excel"

    def test_detect_import_source_none(self, import_specialist):
        """Test detecting no import source"""
        assert import_specialist._detect_import_source("help with import") is None

    def test_create_csv_guide(self, import_specialist):
        """Test creating CSV import guide"""
        source_info = import_specialist.SUPPORTED_IMPORTS["csv"]
        guide = import_specialist._create_csv_guide("csv", source_info)

        assert "CSV" in guide
        assert "name" in guide  # Required field
        assert "UTF-8" in guide
        assert "example" in guide.lower()

    def test_create_tool_migration_guide_asana(self, import_specialist):
        """Test creating migration guide for Asana"""
        source_info = import_specialist.SUPPORTED_IMPORTS["asana"]
        guide = import_specialist._create_tool_migration_guide("asana", source_info)

        assert "Asana" in guide
        assert "phase" in guide.lower()
        assert "export" in guide.lower()
        assert "import" in guide.lower()

    def test_create_tool_migration_guide_trello(self, import_specialist):
        """Test creating migration guide for Trello"""
        source_info = import_specialist.SUPPORTED_IMPORTS["trello"]
        guide = import_specialist._create_tool_migration_guide("trello", source_info)

        assert "Trello" in guide
        assert "board" in guide.lower()

    def test_list_supported_imports_content(self, import_specialist):
        """Test content of supported imports list"""
        imports_list = import_specialist._list_supported_imports()

        assert "Asana" in imports_list
        assert "Trello" in imports_list
        assert "Monday" in imports_list
        assert "CSV" in imports_list
        assert "Excel" in imports_list

    def test_csv_guide_has_example(self, import_specialist):
        """Test CSV guide includes example format"""
        source_info = import_specialist.SUPPORTED_IMPORTS["csv"]
        guide = import_specialist._create_csv_guide("csv", source_info)

        assert "name,description,assignee" in guide
        assert "YYYY-MM-DD" in guide

    def test_migration_guide_has_phases(self, import_specialist):
        """Test migration guide includes all phases"""
        source_info = import_specialist.SUPPORTED_IMPORTS["asana"]
        guide = import_specialist._create_tool_migration_guide("asana", source_info)

        assert "Phase 1" in guide
        assert "Phase 2" in guide
        assert "Phase 3" in guide
        assert "Phase 4" in guide

    @pytest.mark.asyncio
    async def test_import_specialist_confidence(self, import_specialist):
        """Test Import Specialist returns high confidence"""
        state = create_initial_state("Import from Asana")

        result = await import_specialist.process(state)

        assert result["response_confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_import_specialist_routing(self, import_specialist):
        """Test Import Specialist doesn't route to another agent"""
        state = create_initial_state("Import CSV")

        result = await import_specialist.process(state)

        assert result["next_agent"] is None
        assert result["status"] == "resolved"
