"""Configuration-path locations for the Cursor agent."""

from pathlib import Path
from typing import ClassVar, override

from robotter.agents.Agent import OperatingSystem
from robotter.agents.AgentImpl import AgentImpl


# ----------------------------------------------------------------------
class Cursor(AgentImpl):
    """The Cursor agent."""

    name: ClassVar[str] = "Cursor"

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetGlobalConfigurationFilename(cls, operating_system: OperatingSystem) -> Path:
        return cls._GetHomeRoot(operating_system) / ".cursor" / "rules" / "main.mdc"

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetProjectConfigurationName(cls) -> str:
        return ".cursor/rules/main.mdc"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetGlobalSkillsRoot(operating_system: OperatingSystem) -> Path | None:
        if operating_system == OperatingSystem.Windows:
            return Path("%USERPROFILE%") / ".cursor" / "skills"

        return Path("~") / ".cursor" / "skills"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetProjectSkillsRoot() -> Path | None:
        return Path(".cursor") / "skills"
