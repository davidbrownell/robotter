"""Unit tests for robotter.agents.Grok"""

from robotter.agents.Agent import OperatingSystem
from robotter.agents.Grok import Grok

from .AgentTestBase import AgentTestBase


# ----------------------------------------------------------------------
class TestGrok(AgentTestBase):
    agent_type = Grok
    expected_name = "Grok"
    global_template = {
        OperatingSystem.Windows: r"%USERPROFILE%\.grok\AGENTS.md",
        OperatingSystem.MacOS: "~/.grok/AGENTS.md",
        OperatingSystem.Linux: "~/.grok/AGENTS.md",
    }
    project_path = "AGENTS.md"
    global_skill_templates = {
        OperatingSystem.Windows: r"%USERPROFILE%\.grok\skills\my-skill\SKILL.md",
        OperatingSystem.MacOS: "~/.grok/skills/my-skill/SKILL.md",
        OperatingSystem.Linux: "~/.grok/skills/my-skill/SKILL.md",
    }
    project_skill_path = ".grok/skills/my-skill/SKILL.md"
    global_skills_root_templates = {
        OperatingSystem.Windows: r"%USERPROFILE%\.grok\skills",
        OperatingSystem.MacOS: "~/.grok/skills",
        OperatingSystem.Linux: "~/.grok/skills",
    }
    project_skills_root = ".grok/skills"
