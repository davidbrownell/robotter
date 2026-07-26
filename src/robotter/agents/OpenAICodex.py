"""Configuration-path locations for OpenAI's Codex CLI agent."""

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
    def _EnumGlobalConfigurationPaths(operating_system: OperatingSystem) -> Iterator[str]:
        if operating_system == OperatingSystem.Windows:
            yield r"%USERPROFILE%\.codex\AGENTS.md"
        else:
            yield "~/.codex/AGENTS.md"

    # ----------------------------------------------------------------------
    @staticmethod
    def _EnumProjectConfigurationNames() -> Iterator[str]:
        yield "AGENTS.md"
