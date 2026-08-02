"""Configuration-path locations for Google's Gemini CLI agent."""

from pathlib import Path
from typing import ClassVar, override

from robotter.agents.Agent import Agent, OperatingSystem


# ----------------------------------------------------------------------
class GeminiCLI(Agent):
    r"""Google's Gemini CLI agent.

    Gemini CLI reads context from `GEMINI.md` files: project context from a
    `GEMINI.md` file at the project root and global (user-level) context from
    `~/.gemini/GEMINI.md` (`%USERPROFILE%\\.gemini\\GEMINI.md` on Windows).

    Gemini CLI does not implement the cross-agent Agent Skills standard, so skills are
    unsupported (every skill method returns `None`).
    """

    name: ClassVar[str] = "Gemini CLI"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetGlobalConfigurationFilename(operating_system: OperatingSystem) -> Path:
        if operating_system == OperatingSystem.Windows:
            return Path("%USERPROFILE%") / ".gemini" / "GEMINI.md"

        return Path("~") / ".gemini" / "GEMINI.md"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetProjectConfigurationName() -> str:
        return "GEMINI.md"

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
