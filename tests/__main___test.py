"""Unit tests for robotter.__main__"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from typer.testing import CliRunner

import robotter.__main__ as main_module

from robotter import __version__
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
@pytest.fixture
def render_skill_spies(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, MagicMock]:
    """Replace the skill render functions so tests never write to real skill locations."""

    render_global_skill = MagicMock()
    render_local_skill = MagicMock()

    monkeypatch.setattr(main_module, "RenderGlobalSkill", render_global_skill)
    monkeypatch.setattr(main_module, "RenderLocalSkill", render_local_skill)

    return render_global_skill, render_local_skill


# ----------------------------------------------------------------------
@pytest.fixture
def edit_spies(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, MagicMock]:
    """Replace the edit functions so tests never launch a real editor."""

    edit_global = MagicMock()
    edit_local = MagicMock()

    monkeypatch.setattr(main_module, "EditGlobal", edit_global)
    monkeypatch.setattr(main_module, "EditLocal", edit_local)

    return edit_global, edit_local


# ----------------------------------------------------------------------
@pytest.fixture
def edit_skill_spies(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, MagicMock]:
    """Replace the edit-skill functions so tests never launch a real editor."""

    edit_global_skill = MagicMock()
    edit_local_skill = MagicMock()

    monkeypatch.setattr(main_module, "EditGlobalSkill", edit_global_skill)
    monkeypatch.setattr(main_module, "EditLocalSkill", edit_local_skill)

    return edit_global_skill, edit_local_skill


# ----------------------------------------------------------------------
@pytest.fixture
def browse_spy(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace the browse function so tests never open a real file browser."""

    browse_global = MagicMock()

    monkeypatch.setattr(main_module, "BrowseGlobal", browse_global)

    return browse_global


# ----------------------------------------------------------------------
@pytest.fixture
def browse_skills_spies(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, MagicMock]:
    """Replace the browse-skills functions so tests never open a real file browser."""

    browse_global_skills = MagicMock()
    browse_local_skills = MagicMock()

    monkeypatch.setattr(main_module, "BrowseGlobalSkills", browse_global_skills)
    monkeypatch.setattr(main_module, "BrowseLocalSkills", browse_local_skills)

    return browse_global_skills, browse_local_skills


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

        result = runner.invoke(app, ["render", str(template), agent_type.value])

        assert result.exit_code == 0, result.output
        render_global.assert_called_once()
        render_local.assert_not_called()
        assert isinstance(render_global.call_args.args[2], agent_cls)

    # ----------------------------------------------------------------------
    def test_no_output_dir_renders_global(
        self,
        template: Path,
        render_spies: tuple[MagicMock, MagicMock],
    ):
        render_global, render_local = render_spies

        result = runner.invoke(app, ["render", str(template), AgentType.ClaudeCode.value])

        assert result.exit_code == 0, result.output
        render_global.assert_called_once()
        render_local.assert_not_called()

        passed_template = render_global.call_args.args[1]
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
            ["render", str(template), AgentType.ClaudeCode.value, str(output_dir)],
        )

        assert result.exit_code == 0, result.output
        render_local.assert_called_once()
        render_global.assert_not_called()

        _dm, passed_template, _agent, passed_output_dir = render_local.call_args.args
        assert Path(passed_template).resolve() == template.resolve()
        assert Path(passed_output_dir).resolve() == output_dir.resolve()


# ----------------------------------------------------------------------
class TestRenderSkillDispatch:
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
        render_skill_spies: tuple[MagicMock, MagicMock],
    ):
        render_global_skill, render_local_skill = render_skill_spies

        result = runner.invoke(app, ["render_skill", str(template), agent_type.value])

        assert result.exit_code == 0, result.output
        render_global_skill.assert_called_once()
        render_local_skill.assert_not_called()
        assert isinstance(render_global_skill.call_args.args[2], agent_cls)

    # ----------------------------------------------------------------------
    def test_no_output_dir_renders_global(
        self,
        template: Path,
        render_skill_spies: tuple[MagicMock, MagicMock],
    ):
        render_global_skill, render_local_skill = render_skill_spies

        result = runner.invoke(app, ["render_skill", str(template), AgentType.ClaudeCode.value])

        assert result.exit_code == 0, result.output
        render_global_skill.assert_called_once()
        render_local_skill.assert_not_called()

        passed_template = render_global_skill.call_args.args[1]
        assert Path(passed_template).resolve() == template.resolve()

    # ----------------------------------------------------------------------
    def test_output_dir_renders_local(
        self,
        template: Path,
        tmp_path: Path,
        render_skill_spies: tuple[MagicMock, MagicMock],
    ):
        render_global_skill, render_local_skill = render_skill_spies
        output_dir = tmp_path / "out"

        result = runner.invoke(
            app,
            ["render_skill", str(template), AgentType.ClaudeCode.value, str(output_dir)],
        )

        assert result.exit_code == 0, result.output
        render_local_skill.assert_called_once()
        render_global_skill.assert_not_called()

        _dm, passed_template, _agent, passed_output_dir = render_local_skill.call_args.args
        assert Path(passed_template).resolve() == template.resolve()
        assert Path(passed_output_dir).resolve() == output_dir.resolve()

    # ----------------------------------------------------------------------
    def test_missing_template_fails(
        self,
        tmp_path: Path,
        render_skill_spies: tuple[MagicMock, MagicMock],
    ):
        render_global_skill, render_local_skill = render_skill_spies

        result = runner.invoke(
            app, ["render_skill", str(tmp_path / "does_not_exist.md"), AgentType.ClaudeCode.value]
        )

        assert result.exit_code != 0
        render_global_skill.assert_not_called()
        render_local_skill.assert_not_called()

    # ----------------------------------------------------------------------
    def test_directory_template_fails(
        self,
        tmp_path: Path,
        render_skill_spies: tuple[MagicMock, MagicMock],
    ):
        render_global_skill, render_local_skill = render_skill_spies

        result = runner.invoke(app, ["render_skill", str(tmp_path), AgentType.ClaudeCode.value])

        assert result.exit_code != 0
        render_global_skill.assert_not_called()
        render_local_skill.assert_not_called()

    # ----------------------------------------------------------------------
    def test_unknown_agent_fails(
        self,
        template: Path,
        render_skill_spies: tuple[MagicMock, MagicMock],
    ):
        render_global_skill, render_local_skill = render_skill_spies

        result = runner.invoke(app, ["render_skill", str(template), "not-an-agent"])

        assert result.exit_code != 0
        render_global_skill.assert_not_called()
        render_local_skill.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_agent_fails(
        self,
        template: Path,
        render_skill_spies: tuple[MagicMock, MagicMock],
    ):
        render_global_skill, render_local_skill = render_skill_spies

        result = runner.invoke(app, ["render_skill", str(template)])

        assert result.exit_code != 0
        render_global_skill.assert_not_called()
        render_local_skill.assert_not_called()


# ----------------------------------------------------------------------
class TestEditDispatch:
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
        edit_spies: tuple[MagicMock, MagicMock],
    ):
        edit_global, edit_local = edit_spies

        result = runner.invoke(app, ["edit", agent_type.value])

        assert result.exit_code == 0, result.output
        edit_global.assert_called_once()
        edit_local.assert_not_called()
        assert isinstance(edit_global.call_args.args[1], agent_cls)

    # ----------------------------------------------------------------------
    def test_no_output_dir_edits_global(
        self,
        edit_spies: tuple[MagicMock, MagicMock],
    ):
        edit_global, edit_local = edit_spies

        result = runner.invoke(app, ["edit", AgentType.ClaudeCode.value])

        assert result.exit_code == 0, result.output
        edit_global.assert_called_once()
        edit_local.assert_not_called()

    # ----------------------------------------------------------------------
    def test_output_dir_edits_local(
        self,
        tmp_path: Path,
        edit_spies: tuple[MagicMock, MagicMock],
    ):
        edit_global, edit_local = edit_spies
        output_dir = tmp_path / "out"

        result = runner.invoke(app, ["edit", AgentType.ClaudeCode.value, str(output_dir)])

        assert result.exit_code == 0, result.output
        edit_local.assert_called_once()
        edit_global.assert_not_called()

        _dm, _agent, passed_output_dir = edit_local.call_args.args
        assert Path(passed_output_dir).resolve() == output_dir.resolve()

    # ----------------------------------------------------------------------
    def test_unknown_agent_fails(
        self,
        edit_spies: tuple[MagicMock, MagicMock],
    ):
        edit_global, edit_local = edit_spies

        result = runner.invoke(app, ["edit", "not-an-agent"])

        assert result.exit_code != 0
        edit_global.assert_not_called()
        edit_local.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_agent_fails(
        self,
        edit_spies: tuple[MagicMock, MagicMock],
    ):
        edit_global, edit_local = edit_spies

        result = runner.invoke(app, ["edit"])

        assert result.exit_code != 0
        edit_global.assert_not_called()
        edit_local.assert_not_called()


# ----------------------------------------------------------------------
class TestEditSkillDispatch:
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
        edit_skill_spies: tuple[MagicMock, MagicMock],
    ):
        edit_global_skill, edit_local_skill = edit_skill_spies

        result = runner.invoke(app, ["edit_skill", "my-skill", agent_type.value])

        assert result.exit_code == 0, result.output
        edit_global_skill.assert_called_once()
        edit_local_skill.assert_not_called()
        assert isinstance(edit_global_skill.call_args.args[2], agent_cls)

    # ----------------------------------------------------------------------
    def test_no_output_dir_edits_global(
        self,
        edit_skill_spies: tuple[MagicMock, MagicMock],
    ):
        edit_global_skill, edit_local_skill = edit_skill_spies

        result = runner.invoke(app, ["edit_skill", "my-skill", AgentType.ClaudeCode.value])

        assert result.exit_code == 0, result.output
        edit_global_skill.assert_called_once()
        edit_local_skill.assert_not_called()

        passed_skill_name = edit_global_skill.call_args.args[1]
        assert passed_skill_name == "my-skill"

    # ----------------------------------------------------------------------
    def test_output_dir_edits_local(
        self,
        tmp_path: Path,
        edit_skill_spies: tuple[MagicMock, MagicMock],
    ):
        edit_global_skill, edit_local_skill = edit_skill_spies
        output_dir = tmp_path / "out"

        result = runner.invoke(app, ["edit_skill", "my-skill", AgentType.ClaudeCode.value, str(output_dir)])

        assert result.exit_code == 0, result.output
        edit_local_skill.assert_called_once()
        edit_global_skill.assert_not_called()

        _dm, passed_skill_name, _agent, passed_output_dir = edit_local_skill.call_args.args
        assert passed_skill_name == "my-skill"
        assert Path(passed_output_dir).resolve() == output_dir.resolve()

    # ----------------------------------------------------------------------
    def test_unknown_agent_fails(
        self,
        edit_skill_spies: tuple[MagicMock, MagicMock],
    ):
        edit_global_skill, edit_local_skill = edit_skill_spies

        result = runner.invoke(app, ["edit_skill", "my-skill", "not-an-agent"])

        assert result.exit_code != 0
        edit_global_skill.assert_not_called()
        edit_local_skill.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_agent_fails(
        self,
        edit_skill_spies: tuple[MagicMock, MagicMock],
    ):
        edit_global_skill, edit_local_skill = edit_skill_spies

        result = runner.invoke(app, ["edit_skill", "my-skill"])

        assert result.exit_code != 0
        edit_global_skill.assert_not_called()
        edit_local_skill.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_skill_name_fails(
        self,
        edit_skill_spies: tuple[MagicMock, MagicMock],
    ):
        edit_global_skill, edit_local_skill = edit_skill_spies

        result = runner.invoke(app, ["edit_skill"])

        assert result.exit_code != 0
        edit_global_skill.assert_not_called()
        edit_local_skill.assert_not_called()


# ----------------------------------------------------------------------
class TestBrowseDispatch:
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
        browse_spy: MagicMock,
    ):
        result = runner.invoke(app, ["browse", agent_type.value])

        assert result.exit_code == 0, result.output
        browse_spy.assert_called_once()
        assert isinstance(browse_spy.call_args.args[1], agent_cls)

    # ----------------------------------------------------------------------
    def test_unknown_agent_fails(
        self,
        browse_spy: MagicMock,
    ):
        result = runner.invoke(app, ["browse", "not-an-agent"])

        assert result.exit_code != 0
        browse_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_agent_fails(
        self,
        browse_spy: MagicMock,
    ):
        result = runner.invoke(app, ["browse"])

        assert result.exit_code != 0
        browse_spy.assert_not_called()


# ----------------------------------------------------------------------
class TestBrowseSkillsDispatch:
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
        browse_skills_spies: tuple[MagicMock, MagicMock],
    ):
        browse_global_skills, browse_local_skills = browse_skills_spies

        result = runner.invoke(app, ["browse_skills", agent_type.value])

        assert result.exit_code == 0, result.output
        browse_global_skills.assert_called_once()
        browse_local_skills.assert_not_called()
        assert isinstance(browse_global_skills.call_args.args[1], agent_cls)

    # ----------------------------------------------------------------------
    def test_no_output_dir_browses_global(
        self,
        browse_skills_spies: tuple[MagicMock, MagicMock],
    ):
        browse_global_skills, browse_local_skills = browse_skills_spies

        result = runner.invoke(app, ["browse_skills", AgentType.ClaudeCode.value])

        assert result.exit_code == 0, result.output
        browse_global_skills.assert_called_once()
        browse_local_skills.assert_not_called()

    # ----------------------------------------------------------------------
    def test_output_dir_browses_local(
        self,
        tmp_path: Path,
        browse_skills_spies: tuple[MagicMock, MagicMock],
    ):
        browse_global_skills, browse_local_skills = browse_skills_spies
        output_dir = tmp_path / "out"

        result = runner.invoke(app, ["browse_skills", AgentType.ClaudeCode.value, str(output_dir)])

        assert result.exit_code == 0, result.output
        browse_local_skills.assert_called_once()
        browse_global_skills.assert_not_called()

        _dm, _agent, passed_output_dir = browse_local_skills.call_args.args
        assert Path(passed_output_dir).resolve() == output_dir.resolve()

    # ----------------------------------------------------------------------
    def test_unknown_agent_fails(
        self,
        browse_skills_spies: tuple[MagicMock, MagicMock],
    ):
        browse_global_skills, browse_local_skills = browse_skills_spies

        result = runner.invoke(app, ["browse_skills", "not-an-agent"])

        assert result.exit_code != 0
        browse_global_skills.assert_not_called()
        browse_local_skills.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_agent_fails(
        self,
        browse_skills_spies: tuple[MagicMock, MagicMock],
    ):
        browse_global_skills, browse_local_skills = browse_skills_spies

        result = runner.invoke(app, ["browse_skills"])

        assert result.exit_code != 0
        browse_global_skills.assert_not_called()
        browse_local_skills.assert_not_called()


# ----------------------------------------------------------------------
class TestVersion:
    # ----------------------------------------------------------------------
    def test_prints_the_package_version(self):
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0, result.output
        assert result.output == f"{__version__}\n"


# ----------------------------------------------------------------------
class TestErrors:
    # ----------------------------------------------------------------------
    def test_missing_template_fails(
        self,
        tmp_path: Path,
        render_spies: tuple[MagicMock, MagicMock],
    ):
        render_global, render_local = render_spies

        result = runner.invoke(
            app, ["render", str(tmp_path / "does_not_exist.md"), AgentType.ClaudeCode.value]
        )

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

        result = runner.invoke(app, ["render", str(tmp_path), AgentType.ClaudeCode.value])

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

        result = runner.invoke(app, ["render", str(template), "not-an-agent"])

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

        result = runner.invoke(app, ["render", str(template)])

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
            ["render", str(template), AgentType.ClaudeCode.value, str(output_dir)],
        )

        assert result.exit_code == 0, result.output
        assert (output_dir / "CLAUDE.md").read_text(encoding="utf-8") == "Value: 3"
