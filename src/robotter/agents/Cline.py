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

    Cline does not implement the cross-agent Agent Skills standard, so skills are
    unsupported (every skill method returns `None`).
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
