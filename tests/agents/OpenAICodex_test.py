"""Unit tests for robotter.agents.OpenAICodex"""

from robotter.agents.Agent import OperatingSystem
from robotter.agents.OpenAICodex import OpenAICodex

from .AgentTestBase import AgentTestBase


# ----------------------------------------------------------------------
class TestOpenAICodex(AgentTestBase):
    agent_type = OpenAICodex
    expected_name = "OpenAI Codex"
    global_templates = {
        OperatingSystem.Windows: [r"%USERPROFILE%\.codex\AGENTS.md"],
        OperatingSystem.MacOS: ["~/.codex/AGENTS.md"],
        OperatingSystem.Linux: ["~/.codex/AGENTS.md"],
    }
    project_paths = ["AGENTS.md"]
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
