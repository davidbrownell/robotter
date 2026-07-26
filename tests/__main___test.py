"""Unit tests for robotter.__main__"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from typer.testing import CliRunner

import robotter.__main__ as main_module

from robotter.__main__ import AgentType, app
from robotter.agents.ClaudeCode import ClaudeCode
from robotter.agents.GitHubCopilot import GitHubCopilot
from robotter.agents.OpenAICodex import OpenAICodex
from robotter.agents.OpenCode import OpenCode

runner = CliRunner()


# ----------------------------------------------------------------------
@pytest.fixture
def template(tmp_path: Path) -> Path:
    """Write a template file and return its path."""

    file = tmp_path / "template.md"
    file.write_text("Value: {{ 1 + 2 }}", encoding="utf-8")
    return file


# ----------------------------------------------------------------------
@pytest.fixture
def render_spies(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, MagicMock]:
    """Replace the render functions so tests never write to real configuration locations."""

    render_global = MagicMock()
    render_local = MagicMock()

    monkeypatch.setattr(main_module, "RenderGlobal", render_global)
    monkeypatch.setattr(main_module, "RenderLocal", render_local)

    return render_global, render_local


# ----------------------------------------------------------------------
class TestDispatch:
    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        ("agent_type", "agent_cls"),
        [
            (AgentType.ClaudeCode, ClaudeCode),
            (AgentType.GitHubCopilot, GitHubCopilot),
            (AgentType.OpenAICodex, OpenAICodex),
            (AgentType.OpenCode, OpenCode),
        ],
    )
    def test_selects_the_requested_agent(
        self,
        agent_type: AgentType,
        agent_cls: type,
        template: Path,
        render_spies: tuple[MagicMock, MagicMock],
    ):
        render_global, render_local = render_spies

        result = runner.invoke(app, [str(template), agent_type.value])

        assert result.exit_code == 0, result.output
        render_global.assert_called_once()
        render_local.assert_not_called()
        assert isinstance(render_global.call_args.args[1], agent_cls)

    # ----------------------------------------------------------------------
    def test_no_output_dir_renders_global(
        self,
        template: Path,
        render_spies: tuple[MagicMock, MagicMock],
    ):
        render_global, render_local = render_spies

        result = runner.invoke(app, [str(template), AgentType.ClaudeCode.value])

        assert result.exit_code == 0, result.output
        render_global.assert_called_once()
        render_local.assert_not_called()

        passed_template = render_global.call_args.args[0]
        assert Path(passed_template).resolve() == template.resolve()

    # ----------------------------------------------------------------------
    def test_output_dir_renders_local(
        self,
        template: Path,
        tmp_path: Path,
        render_spies: tuple[MagicMock, MagicMock],
    ):
        render_global, render_local = render_spies
        output_dir = tmp_path / "out"

        result = runner.invoke(
            app,
            [str(template), AgentType.ClaudeCode.value, "--output-dir", str(output_dir)],
        )

        assert result.exit_code == 0, result.output
        render_local.assert_called_once()
        render_global.assert_not_called()

        passed_template, _agent, passed_output_dir = render_local.call_args.args
        assert Path(passed_template).resolve() == template.resolve()
        assert Path(passed_output_dir).resolve() == output_dir.resolve()


# ----------------------------------------------------------------------
class TestErrors:
    # ----------------------------------------------------------------------
    def test_missing_template_fails(
        self,
        tmp_path: Path,
        render_spies: tuple[MagicMock, MagicMock],
    ):
        render_global, render_local = render_spies

        result = runner.invoke(app, [str(tmp_path / "does_not_exist.md"), AgentType.ClaudeCode.value])

        assert result.exit_code != 0
        render_global.assert_not_called()
        render_local.assert_not_called()

    # ----------------------------------------------------------------------
    def test_directory_template_fails(
        self,
        tmp_path: Path,
        render_spies: tuple[MagicMock, MagicMock],
    ):
        render_global, render_local = render_spies

        result = runner.invoke(app, [str(tmp_path), AgentType.ClaudeCode.value])

        assert result.exit_code != 0
        render_global.assert_not_called()
        render_local.assert_not_called()

    # ----------------------------------------------------------------------
    def test_unknown_agent_fails(
        self,
        template: Path,
        render_spies: tuple[MagicMock, MagicMock],
    ):
        render_global, render_local = render_spies

        result = runner.invoke(app, [str(template), "not-an-agent"])

        assert result.exit_code != 0
        render_global.assert_not_called()
        render_local.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_agent_fails(
        self,
        template: Path,
        render_spies: tuple[MagicMock, MagicMock],
    ):
        render_global, render_local = render_spies

        result = runner.invoke(app, [str(template)])

        assert result.exit_code != 0
        render_global.assert_not_called()
        render_local.assert_not_called()


# ----------------------------------------------------------------------
class TestIntegration:
    """End-to-end tests that write only into a temporary directory (never a real config location)."""

    # ----------------------------------------------------------------------
    def test_local_render_writes_project_file(self, template: Path, tmp_path: Path):
        output_dir = tmp_path / "out"

        result = runner.invoke(
            app,
            [str(template), AgentType.ClaudeCode.value, "--output-dir", str(output_dir)],
        )

        assert result.exit_code == 0, result.output
        assert (output_dir / "CLAUDE.md").read_text(encoding="utf-8") == "Value: 3"
