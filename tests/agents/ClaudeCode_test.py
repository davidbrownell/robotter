"""Unit tests for robotter.agents.ClaudeCode"""

from robotter.agents.Agent import OperatingSystem
from robotter.agents.ClaudeCode import ClaudeCode

from .AgentTestBase import AgentTestBase


# ----------------------------------------------------------------------
class TestClaudeCode(AgentTestBase):
    agent_type = ClaudeCode
    expected_name = "Claude Code"
    global_templates = {
        OperatingSystem.Windows: [r"%USERPROFILE%\.claude\CLAUDE.md"],
        OperatingSystem.MacOS: ["~/.claude/CLAUDE.md"],
        OperatingSystem.Linux: ["~/.claude/CLAUDE.md"],
    }
    project_paths = ["CLAUDE.md"]
