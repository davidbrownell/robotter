"""Configuration-path locations for the OpenCode agent."""

from pathlib import Path
from typing import ClassVar, override

from robotter.agents.Agent import OperatingSystem
from robotter.agents.AgentImpl import AgentImpl


# ----------------------------------------------------------------------
class OpenCode(AgentImpl):
    """The OpenCode agent."""

    name: ClassVar[str] = "OpenCode"

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetGlobalConfigurationFilename(cls, operating_system: OperatingSystem) -> Path:
        return cls._GetHomeRoot(operating_system) / ".config" / "opencode" / "AGENTS.md"

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
