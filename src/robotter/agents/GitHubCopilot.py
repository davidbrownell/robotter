"""Configuration-path locations for GitHub Copilot (as hosted within Visual Studio Code)."""

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from robotter.agents.Agent import Agent, OperatingSystem

if TYPE_CHECKING:
    from collections.abc import Iterator


# ----------------------------------------------------------------------
class GitHubCopilot(Agent):
    """GitHub Copilot (as hosted within Visual Studio Code)."""

    name: ClassVar[str] = "GitHub Copilot"

    # ----------------------------------------------------------------------
    @staticmethod
    def _EnumGlobalConfigurationPaths(operating_system: OperatingSystem) -> Iterator[Path]:
        if operating_system == OperatingSystem.Windows:
            yield Path("%APPDATA%") / "Code" / "User" / "prompts"
        elif operating_system == OperatingSystem.MacOS:
            yield Path("~") / "Library" / "Application Support" / "Code" / "User" / "prompts"
        else:
            yield Path("~") / ".config" / "Code" / "User" / "prompts"

    # ----------------------------------------------------------------------
    @staticmethod
    def _EnumProjectConfigurationNames() -> Iterator[str]:
        yield ".github/copilot-instructions.md"

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
