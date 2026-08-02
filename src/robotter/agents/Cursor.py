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

    Cursor implements the cross-agent Agent Skills standard (Cursor 2.4+): project skills
    live under `<project>/.cursor/skills/` and global (user-level) skills under
    `~/.cursor/skills/`, with each skill defined by a `SKILL.md` file in its own directory.
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
        if operating_system == OperatingSystem.Windows:
            return Path("%USERPROFILE%") / ".cursor" / "skills"

        return Path("~") / ".cursor" / "skills"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetProjectSkillsRoot() -> Path | None:
        return Path(".cursor") / "skills"

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
