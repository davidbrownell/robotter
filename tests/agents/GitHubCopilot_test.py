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
