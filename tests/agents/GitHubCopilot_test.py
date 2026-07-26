"""Unit tests for robotter.agents.GitHubCopilot"""

from robotter.agents.Agent import OperatingSystem
from robotter.agents.GitHubCopilot import GitHubCopilot

from .AgentTestBase import AgentTestBase


# ----------------------------------------------------------------------
class TestGitHubCopilot(AgentTestBase):
    agent_type = GitHubCopilot
    expected_name = "GitHub Copilot"
    global_templates = {
        OperatingSystem.Windows: [r"%APPDATA%\Code\User\prompts"],
        OperatingSystem.MacOS: ["~/Library/Application Support/Code/User/prompts"],
        OperatingSystem.Linux: ["~/.config/Code/User/prompts"],
    }
    project_paths = [".github/copilot-instructions.md"]
