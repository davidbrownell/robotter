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
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Iterator


# ----------------------------------------------------------------------
class OperatingSystem(Enum):
    """Operating systems whose configuration-path conventions differ."""

    Windows = auto()
    MacOS = auto()
    Linux = auto()


# ----------------------------------------------------------------------
class Agent(ABC):
    r"""Abstract base class describing where an AI agent reads its configuration.

    Two scopes of configuration are modeled:

      - Global (a.k.a. user-level): applies to the user across every project. These
        locations are absolute and operating-system-specific (for example,
        `%USERPROFILE%\\.claude\\CLAUDE.md` on Windows versus `~/.claude/CLAUDE.md`
        on Linux and macOS).

      - Project: applies within a single project and is expressed relative to the
        project's root directory (for example, a file named `CLAUDE.md`).

    Derived classes provide the agent-specific paths and filenames; this base class
    handles operating-system selection and environment-variable / home-directory
    expansion, returning configuration locations as `pathlib.Path` instances.
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
    def GetGlobalConfigurationPaths(cls, operating_system: OperatingSystem | None = None) -> list[Path]:
        """Return the current operating system's global configuration paths as fully-expanded, absolute paths."""

        operating_system = operating_system or cls.GetOperatingSystem()

        return [
            Path(os.path.expandvars(path)).expanduser()
            for path in cls._EnumGlobalConfigurationPaths(operating_system)
        ]

    # ----------------------------------------------------------------------
    @classmethod
    def GetProjectConfigurationPaths(cls, project_root: Path) -> list[Path]:
        """Return the project configuration paths resolved against `project_root`."""

        return [project_root / path for path in cls._EnumProjectConfigurationPaths()]

    # ----------------------------------------------------------------------
    # |
    # |  Abstract Methods (implemented by derived classes)
    # |
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _EnumGlobalConfigurationPaths(
        operating_system: OperatingSystem,
    ) -> Iterator[str]:
        """Enumerate the raw, unexpanded global configuration path templates for `operating_system`."""

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _EnumProjectConfigurationPaths() -> Iterator[str]:
        """Enumerate the project configuration path(s), each relative to a project's root directory."""
