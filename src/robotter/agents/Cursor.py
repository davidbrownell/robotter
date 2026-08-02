"""Configuration-path locations for the Cursor agent."""

from pathlib import Path
from typing import ClassVar, override

from robotter.agents.Agent import Agent, OperatingSystem


# ----------------------------------------------------------------------
class Cursor(Agent):
    """The Cursor agent.

    Cursor reads rules from a `.cursor/rules/` directory of `.mdc` files rather than a
    single configuration file: project rules from `<project>/.cursor/rules/` and global
    (user-level) rules from `~/.cursor/rules/`. This agent targets a single `main.mdc`
    file within those directories.

    Cursor does not implement the cross-agent Agent Skills standard, so skills are
    unsupported (every skill method returns `None`).
    """

    name: ClassVar[str] = "Cursor"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetGlobalConfigurationFilename(operating_system: OperatingSystem) -> Path:
        if operating_system == OperatingSystem.Windows:
            return Path("%USERPROFILE%") / ".cursor" / "rules" / "main.mdc"

        return Path("~") / ".cursor" / "rules" / "main.mdc"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetProjectConfigurationName() -> str:
        return ".cursor/rules/main.mdc"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetGlobalSkillsRoot(operating_system: OperatingSystem) -> Path | None:
        return None

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetProjectSkillsRoot() -> Path | None:
        return None

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetGlobalSkillPath(skill_name: str, operating_system: OperatingSystem) -> Path | None:
        return None

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetProjectSkillPath(skill_name: str) -> Path | None:
        return None
