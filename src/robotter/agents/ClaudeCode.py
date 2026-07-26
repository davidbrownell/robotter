"""Configuration-path locations for Anthropic's Claude Code agent."""

from typing import TYPE_CHECKING, ClassVar

from robotter.agents.Agent import Agent, OperatingSystem

if TYPE_CHECKING:
    from collections.abc import Iterator


# ----------------------------------------------------------------------
class ClaudeCode(Agent):
    """Anthropic's Claude Code agent."""

    name: ClassVar[str] = "Claude Code"

    # ----------------------------------------------------------------------
    @staticmethod
    def _EnumGlobalConfigurationPaths(operating_system: OperatingSystem) -> Iterator[str]:
        if operating_system == OperatingSystem.Windows:
            yield r"%USERPROFILE%\.claude\CLAUDE.md"
        else:
            yield "~/.claude/CLAUDE.md"

    # ----------------------------------------------------------------------
    @staticmethod
    def _EnumProjectConfigurationPaths() -> Iterator[str]:
        yield "CLAUDE.md"
