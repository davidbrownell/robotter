"""Configuration-path locations for the Cline agent."""

from pathlib import Path
from typing import ClassVar, override

from robotter.agents.Agent import OperatingSystem
from robotter.agents.AgentImpl import AgentImpl


# ----------------------------------------------------------------------
class Cline(AgentImpl):
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
