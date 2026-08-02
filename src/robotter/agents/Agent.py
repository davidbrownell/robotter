"""Abstractions for locating the configuration files read by different AI coding agents.

Each AI agent (Claude Code, OpenAI Codex, OpenCode, GitHub Copilot, ...) reads its
configuration from different locations using different filenames. The `Agent` abstract
base class captures the concept of "where does an agent look for its configuration"
while leaving the agent-specific details (the paths and filenames themselves) to
derived classes.
"""

import os
import sys

from abc import ABC, abstractmethod
from enum import Enum, auto
from pathlib import Path
from typing import ClassVar


# ----------------------------------------------------------------------
class OperatingSystem(Enum):
    """Operating systems whose configuration-path conventions differ."""

    Windows = auto()
    MacOS = auto()
    Linux = auto()


# ----------------------------------------------------------------------
class Agent(ABC):
    """Abstract base class describing where an AI agent reads its configuration.

    Two scopes are modeled: global (user-level) locations are absolute and
    operating-system-specific, while project locations are relative to a project's root.
    Derived classes supply the agent-specific paths; this base class handles
    operating-system selection and environment-variable / home-directory expansion.
    """

    # The human-readable name of the agent (for example, "Claude Code"). Derived
    # classes must assign a value.
    name: ClassVar[str]

    # ----------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ----------------------------------------------------------------------
    @staticmethod
    def GetOperatingSystem() -> OperatingSystem:
        """Return the `OperatingSystem` value corresponding to the current platform.

        Any platform that is neither Windows nor macOS is reported as `Linux` (that is,
        a generic POSIX system).
        """

        if sys.platform.startswith("win"):
            return OperatingSystem.Windows

        if sys.platform == "darwin":
            return OperatingSystem.MacOS

        return OperatingSystem.Linux

    # ----------------------------------------------------------------------
    @classmethod
    def GetGlobalConfigurationFilename(cls, operating_system: OperatingSystem | None = None) -> Path:
        """Return the current operating system's global configuration filename as a fully-expanded, absolute path."""

        operating_system = operating_system or cls.GetOperatingSystem()

        filename = cls._GetGlobalConfigurationFilename(operating_system)
        return Path(os.path.expandvars(str(filename))).expanduser()

    # ----------------------------------------------------------------------
    @classmethod
    def GetProjectConfigurationFilename(cls, project_root: Path) -> Path:
        """Return the project configuration filename resolved against `project_root`."""

        return project_root / cls._GetProjectConfigurationName()

    # ----------------------------------------------------------------------
    @classmethod
    def GetGlobalSkillsRoot(cls, operating_system: OperatingSystem | None = None) -> Path | None:
        """Return the directory containing the global skills as an absolute path, or `None` if unsupported."""

        operating_system = operating_system or cls.GetOperatingSystem()

        root = cls._GetGlobalSkillsRoot(operating_system)
        if root is None:
            return None

        return Path(os.path.expandvars(str(root))).expanduser()

    # ----------------------------------------------------------------------
    @classmethod
    def GetProjectSkillsRoot(cls, project_root: Path) -> Path | None:
        """Return the directory containing the project skills under `project_root`, or `None` if unsupported."""

        relative = cls._GetProjectSkillsRoot()
        if relative is None:
            return None

        return project_root / relative

    # ----------------------------------------------------------------------
    @classmethod
    def GetGlobalSkillPath(
        cls,
        skill_name: str,
        operating_system: OperatingSystem | None = None,
    ) -> Path | None:
        """Return the global skill file for `skill_name` as an absolute path, or `None` if skills are unsupported."""

        cls._ValidateSkillName(skill_name)

        operating_system = operating_system or cls.GetOperatingSystem()

        path = cls._GetGlobalSkillPath(skill_name, operating_system)
        if path is None:
            return None

        return Path(os.path.expandvars(str(path))).expanduser()

    # ----------------------------------------------------------------------
    @classmethod
    def GetProjectSkillPath(cls, skill_name: str, project_root: Path) -> Path | None:
        """Return the project skill file for `skill_name` under `project_root`, or `None` if unsupported."""

        cls._ValidateSkillName(skill_name)

        relative = cls._GetProjectSkillPath(skill_name)
        if relative is None:
            return None

        return project_root / relative

    # ----------------------------------------------------------------------
    # |
    # |  Abstract Methods (implemented by derived classes)
    # |
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _GetGlobalConfigurationFilename(operating_system: OperatingSystem) -> Path:
        """Return the raw, unexpanded global configuration filename for `operating_system`."""

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _GetProjectConfigurationName() -> str:
        """Return the project configuration filename, relative to a project's root directory."""

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _GetGlobalSkillsRoot(operating_system: OperatingSystem) -> Path | None:
        """Return the unexpanded global skills root directory, or `None` if skills are unsupported."""

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _GetProjectSkillsRoot() -> Path | None:
        """Return the project skills root directory (relative to a project's root), or `None` if unsupported."""

    # ----------------------------------------------------------------------
    @classmethod
    @abstractmethod
    def _GetGlobalSkillPath(
        cls,
        skill_name: str,
        operating_system: OperatingSystem,
    ) -> Path | None:
        """Return the unexpanded global skill path for `skill_name`, or `None` if unsupported."""

    # ----------------------------------------------------------------------
    @classmethod
    @abstractmethod
    def _GetProjectSkillPath(cls, skill_name: str) -> Path | None:
        """Return the project skill path for `skill_name` (relative to a project's root), or `None` if unsupported."""

    # ----------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ----------------------------------------------------------------------
    @staticmethod
    def _ValidateSkillName(skill_name: str) -> None:
        """Raise an exception if `skill_name` is invalid."""

        if (
            not skill_name
            or os.path.isabs(skill_name)  # noqa: PTH117
            or skill_name in {".", ".."}
            or "/" in skill_name
            or "\\" in skill_name
        ):
            msg = f"Invalid skill name '{skill_name}'."
            raise ValueError(msg)
