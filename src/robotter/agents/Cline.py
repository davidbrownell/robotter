"""Configuration-path locations for the Cline agent."""

from pathlib import Path
from typing import ClassVar, override

from robotter.agents.Agent import OperatingSystem
from robotter.agents.AgentImpl import AgentImpl


# ----------------------------------------------------------------------
class Cline(AgentImpl):
    """The Cline agent."""

    name: ClassVar[str] = "Cline"

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetGlobalConfigurationFilename(cls, operating_system: OperatingSystem) -> Path:
        return cls._GetHomeRoot(operating_system) / "Documents" / "Cline" / "Rules" / "main.md"

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetProjectConfigurationName(cls) -> str:
        return ".clinerules/main.md"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetGlobalSkillsRoot(operating_system: OperatingSystem) -> Path | None:
        if operating_system == OperatingSystem.Windows:
            return Path("%USERPROFILE%") / ".cline" / "skills"

        return Path("~") / ".cline" / "skills"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetProjectSkillsRoot() -> Path | None:
        return Path(".cline") / "skills"
