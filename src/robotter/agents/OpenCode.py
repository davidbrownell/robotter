"""Configuration-path locations for the OpenCode agent."""

from typing import TYPE_CHECKING, ClassVar

from robotter.agents.Agent import Agent, OperatingSystem

if TYPE_CHECKING:
    from collections.abc import Iterator


# ----------------------------------------------------------------------
class OpenCode(Agent):
    """The OpenCode agent."""

    name: ClassVar[str] = "OpenCode"

    # ----------------------------------------------------------------------
    @staticmethod
    def _EnumGlobalConfigurationPaths(operating_system: OperatingSystem) -> Iterator[str]:
        if operating_system == OperatingSystem.Windows:
            yield r"%USERPROFILE%\.config\opencode\AGENTS.md"
        else:
            yield "~/.config/opencode/AGENTS.md"

    # ----------------------------------------------------------------------
    @staticmethod
    def _EnumProjectConfigurationPaths() -> Iterator[str]:
        yield "AGENTS.md"
