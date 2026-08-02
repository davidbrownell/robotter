"""Unit tests for robotter.agents.GitHubCopilot"""

from robotter.agents.Agent import OperatingSystem
from robotter.agents.GitHubCopilot import GitHubCopilot

from .AgentTestBase import AgentTestBase


# ----------------------------------------------------------------------
class TestGitHubCopilot(AgentTestBase):
    agent_type = GitHubCopilot
    expected_name = "GitHub Copilot"
    global_template = {
        OperatingSystem.Windows: r"%APPDATA%\Code\User\prompts",
        OperatingSystem.MacOS: "~/Library/Application Support/Code/User/prompts",
        OperatingSystem.Linux: "~/.config/Code/User/prompts",
    }
    project_path = ".github/copilot-instructions.md"
    global_skill_templates = {
        OperatingSystem.Windows: r"%USERPROFILE%\.copilot\skills\my-skill\SKILL.md",
        OperatingSystem.MacOS: "~/.copilot/skills/my-skill/SKILL.md",
        OperatingSystem.Linux: "~/.copilot/skills/my-skill/SKILL.md",
    }
    project_skill_path = ".github/skills/my-skill/SKILL.md"
    global_skills_root_templates = {
        OperatingSystem.Windows: r"%USERPROFILE%\.copilot\skills",
        OperatingSystem.MacOS: "~/.copilot/skills",
        OperatingSystem.Linux: "~/.copilot/skills",
    }
    project_skills_root = ".github/skills"
