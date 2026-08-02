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
        OperatingSystem.Windows: r"%USERPROFILE%\.cursor\skills\my-skill\SKILL.md",
        OperatingSystem.MacOS: "~/.cursor/skills/my-skill/SKILL.md",
        OperatingSystem.Linux: "~/.cursor/skills/my-skill/SKILL.md",
    }
    project_skill_path = ".cursor/skills/my-skill/SKILL.md"
    global_skills_root_templates = {
        OperatingSystem.Windows: r"%USERPROFILE%\.cursor\skills",
        OperatingSystem.MacOS: "~/.cursor/skills",
        OperatingSystem.Linux: "~/.cursor/skills",
    }
    project_skills_root = ".cursor/skills"
