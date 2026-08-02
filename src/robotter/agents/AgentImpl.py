"""Default implementation of the skill-path methods shared by most AI agents."""

from pathlib import Path
from typing import ClassVar, override

from robotter.agents.Agent import Agent, OperatingSystem


# ----------------------------------------------------------------------
class AgentImpl(Agent):
    """`Agent` specialization providing the defaults shared by most AI agents.

    The project configuration filename defaults to the final component of the global
    filename, and skills are located by joining an agent's skills root with the skill's
    name and the shared skill filename. Derived classes therefore only supply their
    configuration filenames and skills roots, overriding a method only where the layout
    differs.
    """

    # The filename that defines a skill within its own directory beneath a skills root.
    _SKILL_FILENAME: ClassVar[str] = "SKILL.md"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetHomeRoot(operating_system: OperatingSystem) -> Path:
        """Return the unexpanded root of the user's home directory for `operating_system`."""

        if operating_system == OperatingSystem.Windows:
            return Path("%USERPROFILE%")

        return Path("~")

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetProjectConfigurationName(cls) -> str:
        return cls._GetGlobalConfigurationFilename(cls.GetOperatingSystem()).name

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetGlobalSkillPath(
        cls,
        skill_name: str,
        operating_system: OperatingSystem,
    ) -> Path | None:
        root = cls._GetGlobalSkillsRoot(operating_system)
        if root is None:
            return None  # pragma: no cover

        return root / skill_name / cls._SKILL_FILENAME

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetProjectSkillPath(cls, skill_name: str) -> Path | None:
        root = cls._GetProjectSkillsRoot()
        if root is None:
            return None  # pragma: no cover

        return root / skill_name / cls._SKILL_FILENAME
