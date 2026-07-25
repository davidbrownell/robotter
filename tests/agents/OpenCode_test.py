"""Unit tests for robotter.agents.OpenCode"""

from robotter.agents.Agent import OperatingSystem
from robotter.agents.OpenCode import OpenCode

from .AgentTestBase import AgentTestBase


# ----------------------------------------------------------------------
class TestOpenCode(AgentTestBase):
    agent_type = OpenCode
    expected_name = "OpenCode"
    global_templates = {
        OperatingSystem.Windows: [r"%USERPROFILE%\.config\opencode\AGENTS.md"],
        OperatingSystem.MacOS: ["~/.config/opencode/AGENTS.md"],
        OperatingSystem.Linux: ["~/.config/opencode/AGENTS.md"],
    }
    project_paths = ["AGENTS.md"]
