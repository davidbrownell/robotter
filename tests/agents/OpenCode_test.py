"""Unit tests for robotter.agents.OpenCode"""

from robotter.agents.Agent import OperatingSystem
from robotter.agents.OpenCode import OpenCode

from .AgentTestBase import AgentTestBase


# ----------------------------------------------------------------------
class TestOpenCode(AgentTestBase):
    agent_type = OpenCode
    expected_name = "OpenCode"
    global_template = {
        OperatingSystem.Windows: r"%USERPROFILE%\.config\opencode\AGENTS.md",
        OperatingSystem.MacOS: "~/.config/opencode/AGENTS.md",
        OperatingSystem.Linux: "~/.config/opencode/AGENTS.md",
    }
    project_path = "AGENTS.md"
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
