"""Configuration-path locations for Anthropic's Claude Code agent."""

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from robotter.agents.Agent import Agent, OperatingSystem

if TYPE_CHECKING:
    from collections.abc import Iterator


# ----------------------------------------------------------------------
class ClaudeCode(Agent):
    """Anthropic's Claude Code agent."""

    name: ClassVar[str] = "Claude Code"

    # ----------------------------------------------------------------------
    @staticmethod
    def _EnumGlobalConfigurationPaths(operating_system: OperatingSystem) -> Iterator[Path]:
        if operating_system == OperatingSystem.Windows:
            yield Path("%USERPROFILE%") / ".claude" / "CLAUDE.md"
        else:
            yield Path("~") / ".claude" / "CLAUDE.md"

    # ----------------------------------------------------------------------
    @staticmethod
    def _EnumProjectConfigurationNames() -> Iterator[str]:
        yield "CLAUDE.md"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetGlobalSkillsRoot(operating_system: OperatingSystem) -> Path | None:
        if operating_system == OperatingSystem.Windows:
            return Path("%USERPROFILE%") / ".claude" / "skills"

        return Path("~") / ".claude" / "skills"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetProjectSkillsRoot() -> Path | None:
        return Path(".claude") / "skills"

    # ----------------------------------------------------------------------
    @classmethod
    def _GetGlobalSkillPath(cls, skill_name: str, operating_system: OperatingSystem) -> Path | None:
        root = cls._GetGlobalSkillsRoot(operating_system)
        if root is None:
            return None  # pragma: no cover

        return root / skill_name / "SKILL.md"

    # ----------------------------------------------------------------------
    @classmethod
    def _GetProjectSkillPath(cls, skill_name: str) -> Path | None:
        root = cls._GetProjectSkillsRoot()
        if root is None:
            return None  # pragma: no cover

        return root / skill_name / "SKILL.md"
