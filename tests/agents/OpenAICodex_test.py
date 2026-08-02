"""Unit tests for robotter.agents.OpenAICodex"""

from robotter.agents.Agent import OperatingSystem
from robotter.agents.OpenAICodex import OpenAICodex

from .AgentTestBase import AgentTestBase


# ----------------------------------------------------------------------
class TestOpenAICodex(AgentTestBase):
    agent_type = OpenAICodex
    expected_name = "OpenAI Codex"
    global_template = {
        OperatingSystem.Windows: r"%USERPROFILE%\.codex\AGENTS.md",
        OperatingSystem.MacOS: "~/.codex/AGENTS.md",
        OperatingSystem.Linux: "~/.codex/AGENTS.md",
    }
    project_path = "AGENTS.md"
    global_skill_templates = {
        OperatingSystem.Windows: r"%USERPROFILE%\.agents\skills\my-skill\SKILL.md",
        OperatingSystem.MacOS: "~/.agents/skills/my-skill/SKILL.md",
        OperatingSystem.Linux: "~/.agents/skills/my-skill/SKILL.md",
    }
    project_skill_path = ".agents/skills/my-skill/SKILL.md"
    global_skills_root_templates = {
        OperatingSystem.Windows: r"%USERPROFILE%\.agents\skills",
        OperatingSystem.MacOS: "~/.agents/skills",
        OperatingSystem.Linux: "~/.agents/skills",
    }
    project_skills_root = ".agents/skills"
