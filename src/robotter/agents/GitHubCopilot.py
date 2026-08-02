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
    def _GetProjectSkillsRoot() -> Path | None:
        return Path(".github") / "skills"

    # ----------------------------------------------------------------------
    @classmethod
    def _GetGlobalSkillPath(cls, skill_name: str, operating_system: OperatingSystem) -> Path | None:
        root = cls._GetGlobalSkillsRoot(operating_system)
        if root is None:
            return None  # pragma: no cover

        return root / skill_name / "SKILL.md"

    # ----------------------------------------------------------------------
    @classmethod
    def _GetProjectSkillPath(cls, skill_name: str) -> Path | None:
        root = cls._GetProjectSkillsRoot()
        if root is None:
            return None  # pragma: no cover

        return root / skill_name / "SKILL.md"
