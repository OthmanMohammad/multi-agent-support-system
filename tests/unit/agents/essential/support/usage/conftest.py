"""
Pytest fixtures for usage agent tests.
"""

import pytest
from src.agents.essential.support.usage.feature_teacher import FeatureTeacher
from src.agents.essential.support.usage.workflow_optimizer import WorkflowOptimizer
from src.agents.essential.support.usage.export_specialist import ExportSpecialist
from src.agents.essential.support.usage.import_specialist import ImportSpecialist
from src.agents.essential.support.usage.collaboration_expert import CollaborationExpert


@pytest.fixture
def feature_teacher():
    """Feature Teacher agent instance"""
    return FeatureTeacher()


@pytest.fixture
def workflow_optimizer():
    """Workflow Optimizer agent instance"""
    return WorkflowOptimizer()


@pytest.fixture
def export_specialist():
    """Export Specialist agent instance"""
    return ExportSpecialist()


@pytest.fixture
def import_specialist():
    """Import Specialist agent instance"""
    return ImportSpecialist()


@pytest.fixture
def collaboration_expert():
    """Collaboration Expert agent instance"""
    return CollaborationExpert()
