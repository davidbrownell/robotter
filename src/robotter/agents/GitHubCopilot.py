"""Configuration-path locations for GitHub Copilot (as hosted within Visual Studio Code)."""

from pathlib import Path
from typing import ClassVar, override

from robotter.agents.Agent import OperatingSystem
from robotter.agents.AgentImpl import AgentImpl


# ----------------------------------------------------------------------
class GitHubCopilot(AgentImpl):
    """GitHub Copilot (as hosted within Visual Studio Code)."""

    name: ClassVar[str] = "GitHub Copilot"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetGlobalConfigurationFilename(operating_system: OperatingSystem) -> Path:
        if operating_system == OperatingSystem.Windows:
            return Path("%APPDATA%") / "Code" / "User" / "prompts"

        if operating_system == OperatingSystem.MacOS:
            return Path("~") / "Library" / "Application Support" / "Code" / "User" / "prompts"

        return Path("~") / ".config" / "Code" / "User" / "prompts"

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetProjectConfigurationName(cls) -> str:
        return ".github/copilot-instructions.md"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetGlobalSkillsRoot(operating_system: OperatingSystem) -> Path | None:
        # Unlike the global configuration file (which lives under the Visual Studio Code
        # user directory), Agent Skills follow the cross-agent open standard and are read
        # from the home directory. This divergence is intentional; the two features do not
        # share a root. See https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills.
        if operating_system == OperatingSystem.Windows:
            return Path("%USERPROFILE%") / ".copilot" / "skills"

        return Path("~") / ".copilot" / "skills"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetProjectSkillsRoot() -> Path | None:
        return Path(".github") / "skills"
