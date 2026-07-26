"""Unit tests for robotter.agents.Agent"""

import sys

import pytest

from robotter.agents.Agent import Agent, OperatingSystem


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
