"""Shared test scaffolding for concrete `Agent` implementations.

This module's name intentionally does not match pytest's test-file pattern, so it is
imported by the per-agent test modules rather than collected as a test module itself.
"""

import os
import re

from pathlib import Path

import pytest

from robotter.agents.Agent import Agent, OperatingSystem


# ----------------------------------------------------------------------
def _TemplateToPath(template: str) -> Path:
    """Build a `Path` from a `template` by concatenating its components.

    The template may use either separator (`/` or `\\`); splitting here rather than
    passing the raw string to `Path` means the comparison does not depend on the
    separators the host operating system happens to recognize.
    """

    first, *rest = re.split(r"[\\/]", template)

    path = Path(first)
    for component in rest:
        path = path / component

    return path


# ----------------------------------------------------------------------
def _ExpandTemplate(template: str) -> Path:
    """Expand a `template` the same way the production code does: concatenate its components, then expand."""

    return Path(os.path.expandvars(str(_TemplateToPath(template)))).expanduser()


# ----------------------------------------------------------------------
class AgentTestBase:
    """Base class for a concrete `Agent` implementation's test suite.

    Subclasses (named ``Test...`` so pytest collects them) assign the class attributes
    below; the inherited test methods then exercise the associated agent. Because this
    class is not named ``Test...``, pytest does not collect it on its own.
    """

    # A skill name used to exercise the skill-path methods.
    _SKILL_NAME = "my-skill"

    # Assigned by subclasses.
    agent_type: type[Agent]
    expected_name: str
    global_template: dict[OperatingSystem, str]
    project_path: str

    # Skill path templates keyed by operating system for the skill named `_SKILL_NAME`, or
    # `None` for every operating system if the agent does not support skills.
    global_skill_templates: dict[OperatingSystem, str | None]

    # The project-relative skill path for the skill named `_SKILL_NAME`, or `None` if the
    # agent does not support skills.
    project_skill_path: str | None

    # Skills root directory templates keyed by operating system, or `None` for every
    # operating system if the agent does not support skills.
    global_skills_root_templates: dict[OperatingSystem, str | None]

    # The project-relative skills root directory, or `None` if the agent does not support skills.
    project_skills_root: str | None

    # ----------------------------------------------------------------------
    def test_name(self):
        assert self.agent_type.name == self.expected_name
        assert self.agent_type().name == self.expected_name

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "operating_system",
        [OperatingSystem.Windows, OperatingSystem.MacOS, OperatingSystem.Linux],
    )
    def test_get_global_configuration_filename_raw(self, operating_system):
        filename = self.agent_type._GetGlobalConfigurationFilename(operating_system)

        assert filename == _TemplateToPath(self.global_template[operating_system])

    # ----------------------------------------------------------------------
    def test_get_project_configuration_name_raw(self):
        assert self.agent_type._GetProjectConfigurationName() == self.project_path

    # ----------------------------------------------------------------------
    def test_get_global_configuration_filename(self, tmp_path, monkeypatch):
        # Point every "home" location at the temporary directory so nothing on the real
        # machine is referenced, regardless of which OS the test is running on.
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        path = self.agent_type().GetGlobalConfigurationFilename()

        # Only the current operating system's template is resolved.
        assert isinstance(path, Path)
        assert path.is_absolute()
        # All environment variables and '~' references have been expanded.
        assert "~" not in str(path)
        assert "%" not in str(path)
        # Everything resolves beneath the redirected home directory.
        assert path.is_relative_to(tmp_path)

    # ----------------------------------------------------------------------
    def test_get_project_configuration_filename(self, tmp_path):
        path = self.agent_type().GetProjectConfigurationFilename(tmp_path)

        assert path == tmp_path / self.project_path
        assert isinstance(path, Path)
        assert path.is_absolute()

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "operating_system",
        [OperatingSystem.Windows, OperatingSystem.MacOS, OperatingSystem.Linux],
    )
    def test_get_global_skill_path(self, operating_system, tmp_path, monkeypatch):
        # Point every "home" location at the temporary directory so nothing on the real
        # machine is referenced, regardless of which OS the test is running on.
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        path = self.agent_type().GetGlobalSkillPath(self._SKILL_NAME, operating_system)

        expected_template = self.global_skill_templates[operating_system]

        if expected_template is None:
            assert path is None
            return

        assert path == _ExpandTemplate(expected_template)
        assert path is not None

        # Windows environment variables (for example, `%USERPROFILE%`) are only expanded
        # when running on Windows, so the fully-expanded assertions below can only hold
        # when the requested operating system matches the one running the test.
        if operating_system != Agent.GetOperatingSystem():
            return

        assert path.is_absolute()
        # All environment variables and '~' references have been expanded.
        assert "~" not in str(path)
        assert "%" not in str(path)
        assert path.is_relative_to(tmp_path)

    # ----------------------------------------------------------------------
    def test_get_global_skill_path_defaults_to_current_operating_system(self, tmp_path, monkeypatch):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        path = self.agent_type().GetGlobalSkillPath(self._SKILL_NAME)

        expected_template = self.global_skill_templates[Agent.GetOperatingSystem()]

        if expected_template is None:
            assert path is None
        else:
            assert path == _ExpandTemplate(expected_template)

    # ----------------------------------------------------------------------
    def test_get_project_skill_path(self, tmp_path):
        path = self.agent_type().GetProjectSkillPath(self._SKILL_NAME, tmp_path)

        if self.project_skill_path is None:
            assert path is None
            return

        assert path == tmp_path / self.project_skill_path
        assert path is not None
        assert path.is_absolute()

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "operating_system",
        [OperatingSystem.Windows, OperatingSystem.MacOS, OperatingSystem.Linux],
    )
    def test_get_global_skills_root(self, operating_system, tmp_path, monkeypatch):
        # Point every "home" location at the temporary directory so nothing on the real
        # machine is referenced, regardless of which OS the test is running on.
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        path = self.agent_type().GetGlobalSkillsRoot(operating_system)

        expected_template = self.global_skills_root_templates[operating_system]

        if expected_template is None:
            assert path is None
            return

        assert path == _ExpandTemplate(expected_template)
        assert path is not None

        # Windows environment variables (for example, `%USERPROFILE%`) are only expanded
        # when running on Windows, so the fully-expanded assertions below can only hold
        # when the requested operating system matches the one running the test.
        if operating_system != Agent.GetOperatingSystem():
            return

        assert path.is_absolute()
        # All environment variables and '~' references have been expanded.
        assert "~" not in str(path)
        assert "%" not in str(path)
        assert path.is_relative_to(tmp_path)

    # ----------------------------------------------------------------------
    def test_get_global_skills_root_defaults_to_current_operating_system(self, tmp_path, monkeypatch):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        path = self.agent_type().GetGlobalSkillsRoot()

        expected_template = self.global_skills_root_templates[Agent.GetOperatingSystem()]

        if expected_template is None:
            assert path is None
        else:
            assert path == _ExpandTemplate(expected_template)

    # ----------------------------------------------------------------------
    def test_get_project_skills_root(self, tmp_path):
        path = self.agent_type().GetProjectSkillsRoot(tmp_path)

        if self.project_skills_root is None:
            assert path is None
            return

        assert path == tmp_path / self.project_skills_root
        assert path is not None
        assert path.is_absolute()
