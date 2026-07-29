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
    global_skill_templates = {
        OperatingSystem.Windows: r"%USERPROFILE%\.claude\skills\my-skill\SKILL.md",
        OperatingSystem.MacOS: "~/.claude/skills/my-skill/SKILL.md",
        OperatingSystem.Linux: "~/.claude/skills/my-skill/SKILL.md",
    }
    project_skill_path = ".claude/skills/my-skill/SKILL.md"
    global_skills_root_templates = {
        OperatingSystem.Windows: r"%USERPROFILE%\.claude\skills",
        OperatingSystem.MacOS: "~/.claude/skills",
        OperatingSystem.Linux: "~/.claude/skills",
    }
    project_skills_root = ".claude/skills"
