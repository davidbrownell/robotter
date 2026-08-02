"""Configuration-path locations for GitHub Copilot (as hosted within Visual Studio Code)."""

from pathlib import Path
from typing import ClassVar

from robotter.agents.Agent import Agent, OperatingSystem


# ----------------------------------------------------------------------
class GitHubCopilot(Agent):
    """GitHub Copilot (as hosted within Visual Studio Code)."""

    name: ClassVar[str] = "GitHub Copilot"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetGlobalConfigurationFilename(operating_system: OperatingSystem) -> Path:
        if operating_system == OperatingSystem.Windows:
            return Path("%APPDATA%") / "Code" / "User" / "prompts"

        if operating_system == OperatingSystem.MacOS:
            return Path("~") / "Library" / "Application Support" / "Code" / "User" / "prompts"

        return Path("~") / ".config" / "Code" / "User" / "prompts"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetProjectConfigurationName() -> str:
        return ".github/copilot-instructions.md"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetGlobalSkillsRoot(operating_system: OperatingSystem) -> Path | None:  # noqa: ARG004
        return None

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetProjectSkillsRoot() -> Path | None:
        return None

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetGlobalSkillPath(skill_name: str, operating_system: OperatingSystem) -> Path | None:  # noqa: ARG004
        return None

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetProjectSkillPath(skill_name: str) -> Path | None:  # noqa: ARG004
        return None
