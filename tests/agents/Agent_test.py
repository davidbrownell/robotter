"""Unit tests for robotter.agents.Agent"""

import re
import sys

from pathlib import Path
from typing import ClassVar

import pytest

from robotter.agents.Agent import Agent, OperatingSystem


# ----------------------------------------------------------------------
class _StubAgent(Agent):
    """A minimal concrete `Agent` used to exercise base-class behavior."""

    name: ClassVar[str] = "Stub Agent"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetGlobalConfigurationFilename(operating_system):
        return Path("config")

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetProjectConfigurationName():
        return "config"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetGlobalSkillsRoot(operating_system):
        return Path("skills")

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetProjectSkillsRoot():
        return Path("skills")

    # ----------------------------------------------------------------------
    @classmethod
    def _GetGlobalSkillPath(cls, skill_name, operating_system):
        return Path("skills") / skill_name

    # ----------------------------------------------------------------------
    @classmethod
    def _GetProjectSkillPath(cls, skill_name):
        return Path("skills") / skill_name


# ----------------------------------------------------------------------
class TestAgentBase:
    # ----------------------------------------------------------------------
    def test_cannot_instantiate_abstract_base(self):
        with pytest.raises(TypeError):
            Agent()  # pyright: ignore[reportAbstractUsage]

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        ("platform", "expected"),
        [
            ("win32", OperatingSystem.Windows),
            ("win", OperatingSystem.Windows),
            ("darwin", OperatingSystem.MacOS),
            ("linux", OperatingSystem.Linux),
            ("freebsd", OperatingSystem.Linux),
        ],
    )
    def test_get_operating_system(self, platform, expected, monkeypatch):
        monkeypatch.setattr(sys, "platform", platform)
        assert Agent.GetOperatingSystem() == expected


# ----------------------------------------------------------------------
class TestValidateSkillName:
    """Exercise skill-name validation through the public skill-path methods."""

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "skill_name",
        [
            "",
            ".",
            "..",
            "a/b",
            "a\\b",
            "/absolute",
            "\\absolute",
            "sub/dir/skill",
            "..\\escape",
        ],
    )
    def test_global_skill_path_rejects_invalid_name(self, skill_name):
        with pytest.raises(ValueError, match=re.escape(f"Invalid skill name '{skill_name}'.")):
            _StubAgent.GetGlobalSkillPath(skill_name)

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "skill_name",
        [
            "",
            ".",
            "..",
            "a/b",
            "a\\b",
            "/absolute",
            "\\absolute",
            "sub/dir/skill",
            "..\\escape",
        ],
    )
    def test_project_skill_path_rejects_invalid_name(self, skill_name, tmp_path):
        with pytest.raises(ValueError, match=re.escape(f"Invalid skill name '{skill_name}'.")):
            _StubAgent.GetProjectSkillPath(skill_name, tmp_path)

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "skill_name",
        ["my-skill", "my_skill", "skill.name", "Skill123", "...leading-dots"],
    )
    def test_global_skill_path_accepts_valid_name(self, skill_name):
        assert _StubAgent.GetGlobalSkillPath(skill_name) == Path("skills") / skill_name

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "skill_name",
        ["my-skill", "my_skill", "skill.name", "Skill123", "...leading-dots"],
    )
    def test_project_skill_path_accepts_valid_name(self, skill_name, tmp_path):
        assert _StubAgent.GetProjectSkillPath(skill_name, tmp_path) == tmp_path / "skills" / skill_name


# ----------------------------------------------------------------------
class _NestedSkillAgent(_StubAgent):
    """An `Agent` that gives each skill its own directory beneath the skills root."""

    # ----------------------------------------------------------------------
    @classmethod
    def _GetGlobalSkillPath(cls, skill_name, operating_system):
        return Path("skills") / skill_name / "SKILL.md"

    # ----------------------------------------------------------------------
    @classmethod
    def _GetProjectSkillPath(cls, skill_name):
        return Path("skills") / skill_name / "SKILL.md"


# ----------------------------------------------------------------------
class _NoSkillsAgent(_StubAgent):
    """An `Agent` that does not support skills at all."""

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetGlobalSkillsRoot(operating_system):
        return None

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetProjectSkillsRoot():
        return None

    # ----------------------------------------------------------------------
    @classmethod
    def _GetGlobalSkillPath(cls, skill_name, operating_system):
        return None

    # ----------------------------------------------------------------------
    @classmethod
    def _GetProjectSkillPath(cls, skill_name):
        return None


# ----------------------------------------------------------------------
class TestGetSkillDirectory:
    # ----------------------------------------------------------------------
    def test_nested_layout_returns_the_skills_own_directory(self, tmp_path):
        assert _NestedSkillAgent.GetGlobalSkillDirectory("my-skill") == Path("skills") / "my-skill"
        assert (
            _NestedSkillAgent.GetProjectSkillDirectory("my-skill", tmp_path)
            == tmp_path / "skills" / "my-skill"
        )

    # ----------------------------------------------------------------------
    def test_flat_layout_owns_no_directory(self, tmp_path):
        # `_StubAgent` stores a skill as `skills/<name>`, so the only enclosing directory is the
        # skills root shared by every skill.
        assert _StubAgent.GetGlobalSkillDirectory("my-skill") is None
        assert _StubAgent.GetProjectSkillDirectory("my-skill", tmp_path) is None

    # ----------------------------------------------------------------------
    def test_unsupported_agent_owns_no_directory(self, tmp_path):
        assert _NoSkillsAgent.GetGlobalSkillDirectory("my-skill") is None
        assert _NoSkillsAgent.GetProjectSkillDirectory("my-skill", tmp_path) is None

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize("skill_name", ["..", "", "sub/skill"])
    def test_rejects_invalid_name(self, skill_name, tmp_path):
        with pytest.raises(ValueError, match=re.escape(f"Invalid skill name '{skill_name}'.")):
            _NestedSkillAgent.GetGlobalSkillDirectory(skill_name)

        with pytest.raises(ValueError, match=re.escape(f"Invalid skill name '{skill_name}'.")):
            _NestedSkillAgent.GetProjectSkillDirectory(skill_name, tmp_path)
