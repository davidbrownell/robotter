"""Unit tests for robotter.agents.Cline"""

from robotter.agents.Agent import OperatingSystem
from robotter.agents.Cline import Cline

from .AgentTestBase import AgentTestBase


# ----------------------------------------------------------------------
class TestCline(AgentTestBase):
    agent_type = Cline
    expected_name = "Cline"
    global_template = {
        OperatingSystem.Windows: r"%USERPROFILE%\Documents\Cline\Rules\main.md",
        OperatingSystem.MacOS: "~/Documents/Cline/Rules/main.md",
        OperatingSystem.Linux: "~/Documents/Cline/Rules/main.md",
    }
    project_path = ".clinerules/main.md"
    global_skill_templates = {
        OperatingSystem.Windows: r"%USERPROFILE%\.cline\skills\my-skill\SKILL.md",
        OperatingSystem.MacOS: "~/.cline/skills/my-skill/SKILL.md",
        OperatingSystem.Linux: "~/.cline/skills/my-skill/SKILL.md",
    }
    project_skill_path = ".cline/skills/my-skill/SKILL.md"
    global_skills_root_templates = {
        OperatingSystem.Windows: r"%USERPROFILE%\.cline\skills",
        OperatingSystem.MacOS: "~/.cline/skills",
        OperatingSystem.Linux: "~/.cline/skills",
    }
    project_skills_root = ".cline/skills"
