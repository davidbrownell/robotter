"""Configuration-path locations for Google's Gemini CLI agent."""

from pathlib import Path
from typing import ClassVar, override

from robotter.agents.Agent import OperatingSystem
from robotter.agents.AgentImpl import AgentImpl


# ----------------------------------------------------------------------
class GeminiCLI(AgentImpl):
    r"""Google's Gemini CLI agent.

    Gemini CLI reads context from `GEMINI.md` files: project context from a
    `GEMINI.md` file at the project root and global (user-level) context from
    `~/.gemini/GEMINI.md` (`%USERPROFILE%\\.gemini\\GEMINI.md` on Windows).

    Gemini CLI implements the cross-agent Agent Skills standard: project skills live under
    `<project>/.gemini/skills/` and global (user-level) skills under `~/.gemini/skills/`
    (`%USERPROFILE%\\.gemini\\skills` on Windows), with each skill defined by a `SKILL.md`
    file in its own directory.
    """

    name: ClassVar[str] = "Gemini CLI"

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetGlobalConfigurationFilename(cls, operating_system: OperatingSystem) -> Path:
        return cls._GetHomeRoot(operating_system) / ".gemini" / "GEMINI.md"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetGlobalSkillsRoot(operating_system: OperatingSystem) -> Path | None:
        if operating_system == OperatingSystem.Windows:
            return Path("%USERPROFILE%") / ".gemini" / "skills"

        return Path("~") / ".gemini" / "skills"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetProjectSkillsRoot() -> Path | None:
        return Path(".gemini") / "skills"
