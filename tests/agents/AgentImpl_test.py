"""Unit tests for robotter.agents.AgentImpl"""

from pathlib import Path
from typing import ClassVar

import pytest

from robotter.agents.Agent import OperatingSystem
from robotter.agents.AgentImpl import AgentImpl


# ----------------------------------------------------------------------
class _StubAgent(AgentImpl):
    """Concrete `AgentImpl` that supplies skills roots so the inherited skill-path derivation can be exercised."""

    name: ClassVar[str] = "Stub Agent"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetGlobalConfigurationFilename(operating_system):
        return Path("config")

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetGlobalSkillsRoot(operating_system):
        return Path("global") / "skills"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetProjectSkillsRoot():
        return Path("project") / "skills"


# ----------------------------------------------------------------------
class TestGetGlobalSkillPath:
    """`AgentImpl` derives the global skill path from its global skills root."""

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "operating_system",
        [OperatingSystem.Windows, OperatingSystem.MacOS, OperatingSystem.Linux],
    )
    def test_derives_path_from_global_skills_root(self, operating_system):
        path = _StubAgent.GetGlobalSkillPath("my-skill", operating_system)

        assert path == Path("global") / "skills" / "my-skill" / "SKILL.md"


# ----------------------------------------------------------------------
class TestGetProjectSkillPath:
    """`AgentImpl` derives the project skill path from its project skills root."""

    # ----------------------------------------------------------------------
    def test_derives_path_from_project_skills_root(self, tmp_path):
        path = _StubAgent.GetProjectSkillPath("my-skill", tmp_path)

        assert path == tmp_path / "project" / "skills" / "my-skill" / "SKILL.md"
