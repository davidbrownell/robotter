"""Configuration-path locations for the Cline agent."""

from pathlib import Path
from typing import ClassVar, override

from robotter.agents.Agent import Agent, OperatingSystem


# ----------------------------------------------------------------------
class Cline(Agent):
    r"""The Cline agent.

    Cline reads rules from a directory of `.md`/`.txt` files rather than a single
    configuration file: project rules from `<project>/.clinerules/` and global
    (user-level) rules from a `Cline/Rules` directory under the user's `Documents`
    folder (`%USERPROFILE%\\Documents\\Cline\\Rules` on Windows, `~/Documents/Cline/Rules`
    otherwise). This agent targets a single `main.md` file within those directories.

    Cline implements the cross-agent Agent Skills standard: project skills live under
    `<project>/.cline/skills/` and global (user-level) skills under `~/.cline/skills/`
    (`%USERPROFILE%\\.cline\\skills` on Windows), with each skill defined by a `SKILL.md`
    file in its own directory.
    """

    name: ClassVar[str] = "Cline"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetGlobalConfigurationFilename(operating_system: OperatingSystem) -> Path:
        if operating_system == OperatingSystem.Windows:
            return Path("%USERPROFILE%") / "Documents" / "Cline" / "Rules" / "main.md"

        return Path("~") / "Documents" / "Cline" / "Rules" / "main.md"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetProjectConfigurationName() -> str:
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
