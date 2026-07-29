"""Configuration-path locations for OpenAI's Codex CLI agent."""

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from robotter.agents.Agent import Agent, OperatingSystem

if TYPE_CHECKING:
    from collections.abc import Iterator


# ----------------------------------------------------------------------
class OpenAICodex(Agent):
    """OpenAI's Codex CLI agent."""

    name: ClassVar[str] = "OpenAI Codex"

    # ----------------------------------------------------------------------
    @staticmethod
    def _EnumGlobalConfigurationPaths(operating_system: OperatingSystem) -> Iterator[Path]:
        if operating_system == OperatingSystem.Windows:
            yield Path("%USERPROFILE%") / ".codex" / "AGENTS.md"
        else:
            yield Path("~") / ".codex" / "AGENTS.md"

    # ----------------------------------------------------------------------
    @staticmethod
    def _EnumProjectConfigurationNames() -> Iterator[str]:
        yield "AGENTS.md"

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
