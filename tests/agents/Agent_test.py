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
