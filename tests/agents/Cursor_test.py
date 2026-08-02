"""Unit tests for robotter.agents.Cursor"""

from robotter.agents.Agent import OperatingSystem
from robotter.agents.Cursor import Cursor

from .AgentTestBase import AgentTestBase


# ----------------------------------------------------------------------
class TestCursor(AgentTestBase):
    agent_type = Cursor
    expected_name = "Cursor"
    global_template = {
        OperatingSystem.Windows: r"%USERPROFILE%\.cursor\rules\main.mdc",
        OperatingSystem.MacOS: "~/.cursor/rules/main.mdc",
        OperatingSystem.Linux: "~/.cursor/rules/main.mdc",
    }
    project_path = ".cursor/rules/main.mdc"
    global_skill_templates = {
        OperatingSystem.Windows: None,
        OperatingSystem.MacOS: None,
        OperatingSystem.Linux: None,
    }
    project_skill_path = None
    global_skills_root_templates = {
        OperatingSystem.Windows: None,
        OperatingSystem.MacOS: None,
        OperatingSystem.Linux: None,
    }
    project_skills_root = None
