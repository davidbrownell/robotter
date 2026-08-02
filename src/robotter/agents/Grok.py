"""Configuration-path locations for xAI's Grok CLI agent."""

from pathlib import Path
from typing import ClassVar

from robotter.agents.Agent import Agent, OperatingSystem


# ----------------------------------------------------------------------
class Grok(Agent):
    """xAI's Grok CLI agent."""

    name: ClassVar[str] = "Grok"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetGlobalConfigurationFilename(operating_system: OperatingSystem) -> Path:
        if operating_system == OperatingSystem.Windows:
            return Path("%USERPROFILE%") / ".grok" / "AGENTS.md"

        return Path("~") / ".grok" / "AGENTS.md"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetProjectConfigurationName() -> str:
        return "AGENTS.md"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetGlobalSkillsRoot(operating_system: OperatingSystem) -> Path | None:
        if operating_system == OperatingSystem.Windows:
            return Path("%USERPROFILE%") / ".grok" / "skills"

        return Path("~") / ".grok" / "skills"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetProjectSkillsRoot() -> Path | None:
        return Path(".grok") / "skills"

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
