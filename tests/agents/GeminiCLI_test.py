"""Unit tests for robotter.agents.GeminiCLI"""

from robotter.agents.Agent import OperatingSystem
from robotter.agents.GeminiCLI import GeminiCLI

from .AgentTestBase import AgentTestBase


# ----------------------------------------------------------------------
class TestGeminiCLI(AgentTestBase):
    agent_type = GeminiCLI
    expected_name = "Gemini CLI"
    global_template = {
        OperatingSystem.Windows: r"%USERPROFILE%\.gemini\GEMINI.md",
        OperatingSystem.MacOS: "~/.gemini/GEMINI.md",
        OperatingSystem.Linux: "~/.gemini/GEMINI.md",
    }
    project_path = "GEMINI.md"
    global_skill_templates = {
        OperatingSystem.Windows: r"%USERPROFILE%\.gemini\skills\my-skill\SKILL.md",
        OperatingSystem.MacOS: "~/.gemini/skills/my-skill/SKILL.md",
        OperatingSystem.Linux: "~/.gemini/skills/my-skill/SKILL.md",
    }
    project_skill_path = ".gemini/skills/my-skill/SKILL.md"
    global_skills_root_templates = {
        OperatingSystem.Windows: r"%USERPROFILE%\.gemini\skills",
        OperatingSystem.MacOS: "~/.gemini/skills",
        OperatingSystem.Linux: "~/.gemini/skills",
    }
    project_skills_root = ".gemini/skills"
