"""Configuration-path locations for the OpenCode agent."""

from pathlib import Path
from typing import ClassVar, override

from robotter.agents.Agent import Agent, OperatingSystem


# ----------------------------------------------------------------------
class OpenCode(Agent):
    """The OpenCode agent."""

    name: ClassVar[str] = "OpenCode"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetGlobalConfigurationFilename(operating_system: OperatingSystem) -> Path:
        if operating_system == OperatingSystem.Windows:
            return Path("%USERPROFILE%") / ".config" / "opencode" / "AGENTS.md"

        return Path("~") / ".config" / "opencode" / "AGENTS.md"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetProjectConfigurationName() -> str:
        return "AGENTS.md"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetGlobalSkillsRoot(operating_system: OperatingSystem) -> Path | None:
        if operating_system == OperatingSystem.Windows:
            return Path("%USERPROFILE%") / ".config" / "opencode" / "skills"

        return Path("~") / ".config" / "opencode" / "skills"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetProjectSkillsRoot() -> Path | None:
        return Path(".opencode") / "skills"

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetGlobalSkillPath(cls, skill_name: str, operating_system: OperatingSystem) -> Path | None:
        root = cls._GetGlobalSkillsRoot(operating_system)
        if root is None:
            return None  # pragma: no cover

        return root / skill_name / "SKILL.md"

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetProjectSkillPath(cls, skill_name: str) -> Path | None:
        root = cls._GetProjectSkillsRoot()
        if root is None:
            return None  # pragma: no cover

        return root / skill_name / "SKILL.md"
