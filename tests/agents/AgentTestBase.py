"""Shared test scaffolding for concrete `Agent` implementations.

This module's name intentionally does not match pytest's test-file pattern, so it is
imported by the per-agent test modules rather than collected as a test module itself.
"""

from pathlib import Path

import pytest

from robotter.agents.Agent import Agent, OperatingSystem


# ----------------------------------------------------------------------
class AgentTestBase:
    """Base class for a concrete `Agent` implementation's test suite.

    Subclasses (named ``Test...`` so pytest collects them) assign the class attributes
    below; the inherited test methods then exercise the associated agent. Because this
    class is not named ``Test...``, pytest does not collect it on its own.
    """

    # Assigned by subclasses.
    agent_type: type[Agent]
    expected_name: str
    global_templates: dict[OperatingSystem, list[str]]
    project_paths: list[str]

    # ----------------------------------------------------------------------
    def test_name(self):
        assert self.agent_type.name == self.expected_name
        assert self.agent_type().name == self.expected_name

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "operating_system",
        [OperatingSystem.Windows, OperatingSystem.MacOS, OperatingSystem.Linux],
    )
    def test_enum_global_configuration_paths(self, operating_system):
        templates = list(self.agent_type._EnumGlobalConfigurationPaths(operating_system))

        assert templates == self.global_templates[operating_system]

    # ----------------------------------------------------------------------
    def test_enum_project_configuration_paths(self):
        assert list(self.agent_type._EnumProjectConfigurationPaths()) == self.project_paths

    # ----------------------------------------------------------------------
    def test_get_global_configuration_paths(self, tmp_path, monkeypatch):
        # Point every "home" location at the temporary directory so nothing on the real
        # machine is referenced, regardless of which OS the test is running on.
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        paths = self.agent_type().GetGlobalConfigurationPaths()

        # Only the current operating system's templates are resolved.
        assert len(paths) == len(self.global_templates[Agent.GetOperatingSystem()])

        for path in paths:
            assert isinstance(path, Path)
            assert path.is_absolute()
            # All environment variables and '~' references have been expanded.
            assert "~" not in str(path)
            assert "%" not in str(path)
            # Everything resolves beneath the redirected home directory.
            assert path.is_relative_to(tmp_path)

    # ----------------------------------------------------------------------
    def test_get_project_configuration_paths(self, tmp_path):
        paths = self.agent_type().GetProjectConfigurationPaths(tmp_path)

        assert paths == [tmp_path / relative for relative in self.project_paths]

        for path in paths:
            assert isinstance(path, Path)
            assert path.is_absolute()
