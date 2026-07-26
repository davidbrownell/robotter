"""Configuration-path locations for GitHub Copilot (as hosted within Visual Studio Code)."""

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
    def _EnumGlobalConfigurationPaths(operating_system: OperatingSystem) -> Iterator[str]:
        if operating_system == OperatingSystem.Windows:
            yield r"%APPDATA%\Code\User\prompts"
        elif operating_system == OperatingSystem.MacOS:
            yield "~/Library/Application Support/Code/User/prompts"
        else:
            yield "~/.config/Code/User/prompts"

    # ----------------------------------------------------------------------
    @staticmethod
    def _EnumProjectConfigurationPaths() -> Iterator[str]:
        yield ".github/copilot-instructions.md"
