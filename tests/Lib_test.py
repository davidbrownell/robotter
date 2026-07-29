"""Unit tests for robotter.Lib"""

from collections.abc import Iterator
from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock

import pytest

import robotter.Lib as lib_module

from robotter.agents.Agent import Agent, OperatingSystem
from robotter.Lib import (
    BrowseGlobal,
    BrowseGlobalSkills,
    BrowseLocalSkills,
    EditGlobal,
    EditGlobalSkill,
    EditLocal,
    EditLocalSkill,
    RenderGlobal,
    RenderGlobalSkill,
    RenderLocal,
    RenderLocalSkill,
)


# ----------------------------------------------------------------------
def _MakeAgent(
    *,
    project_paths: tuple[str, ...] = (),
    global_paths: tuple[str, ...] = (),
    global_skill_template: str | None = None,
    project_skill_template: str | None = None,
    global_skills_root: str | None = None,
    project_skills_root: str | None = None,
) -> Agent:
    """Create an `Agent` whose configuration paths are exactly the ones provided.

    The skill templates, when provided, are ``str.format``-style patterns containing a
    ``{skill_name}`` placeholder; a value of `None` models an agent that does not support
    skills. The skills-root values are plain paths (no placeholder); a value of `None`
    models an agent that does not support skills.
    """

    class _StubAgent(Agent):
        name = "Stub"

        @staticmethod
        def _EnumGlobalConfigurationPaths(operating_system: OperatingSystem) -> Iterator[Path]:  # noqa: ARG004
            for path in global_paths:
                yield Path(path)

        @staticmethod
        def _EnumProjectConfigurationNames() -> Iterator[str]:
            yield from project_paths

        @staticmethod
        def _GetGlobalSkillsRoot(operating_system: OperatingSystem) -> Path | None:  # noqa: ARG004
            if global_skills_root is None:
                return None
            return Path(global_skills_root)

        @staticmethod
        def _GetProjectSkillsRoot() -> Path | None:
            if project_skills_root is None:
                return None
            return Path(project_skills_root)

        @staticmethod
        def _GetGlobalSkillPath(skill_name: str, operating_system: OperatingSystem) -> Path | None:  # noqa: ARG004
            if global_skill_template is None:
                return None
            return Path(global_skill_template.format(skill_name=skill_name))

        @staticmethod
        def _GetProjectSkillPath(skill_name: str) -> Path | None:
            if project_skill_template is None:
                return None
            return Path(project_skill_template.format(skill_name=skill_name))

    return _StubAgent()


# ----------------------------------------------------------------------
@pytest.fixture
def template(tmp_path: Path):
    """Factory fixture that writes a template file and returns its path."""

    def _create(content: str) -> Path:
        file = tmp_path / "template.md"
        file.write_text(content, encoding="utf-8")
        return file

    return _create


# ----------------------------------------------------------------------
class TestRenderLocal:
    # ----------------------------------------------------------------------
    def test_writes_rendered_content(self, template, tmp_path: Path):
        agent = _MakeAgent(project_paths=("CONFIG.md",))
        output_dir = tmp_path / "out"

        RenderLocal(template("Hello, world!"), agent, output_dir)

        assert (output_dir / "CONFIG.md").read_text(encoding="utf-8") == "Hello, world!"

    # ----------------------------------------------------------------------
    def test_renders_jinja2(self, template, tmp_path: Path):
        agent = _MakeAgent(project_paths=("CONFIG.md",))
        output_dir = tmp_path / "out"

        RenderLocal(template("Value: {{ 1 + 2 }}"), agent, output_dir)

        assert (output_dir / "CONFIG.md").read_text(encoding="utf-8") == "Value: 3"

    # ----------------------------------------------------------------------
    def test_preserves_frontmatter(self, template, tmp_path: Path):
        agent = _MakeAgent(project_paths=("CONFIG.md",))
        output_dir = tmp_path / "out"

        RenderLocal(
            template(
                dedent("""\
                ---
                title: My Title
                ---
                Body: {{ 2 * 3 }}""")
            ),
            agent,
            output_dir,
        )

        assert (output_dir / "CONFIG.md").read_text(encoding="utf-8") == dedent("""\
            ---
            title: My Title
            ---
            Body: 6""")

    # ----------------------------------------------------------------------
    def test_creates_parent_directories(self, template, tmp_path: Path):
        agent = _MakeAgent(project_paths=("nested/dir/CONFIG.md",))
        output_dir = tmp_path / "out"

        RenderLocal(template("content"), agent, output_dir)

        assert (output_dir / "nested" / "dir" / "CONFIG.md").read_text(encoding="utf-8") == "content"

    # ----------------------------------------------------------------------
    def test_writes_to_every_project_path(self, template, tmp_path: Path):
        agent = _MakeAgent(project_paths=("A.md", "sub/B.md"))
        output_dir = tmp_path / "out"

        RenderLocal(template("shared"), agent, output_dir)

        assert (output_dir / "A.md").read_text(encoding="utf-8") == "shared"
        assert (output_dir / "sub" / "B.md").read_text(encoding="utf-8") == "shared"

    # ----------------------------------------------------------------------
    def test_encodes_as_utf8(self, template, tmp_path: Path):
        agent = _MakeAgent(project_paths=("CONFIG.md",))
        output_dir = tmp_path / "out"

        RenderLocal(template("café — naïve — 日本語"), agent, output_dir)

        written = output_dir / "CONFIG.md"
        assert written.read_bytes() == "café — naïve — 日本語".encode()

    # ----------------------------------------------------------------------
    def test_no_project_paths_writes_nothing(self, template, tmp_path: Path):
        agent = _MakeAgent(project_paths=())
        output_dir = tmp_path / "out"

        RenderLocal(template("content"), agent, output_dir)

        assert not output_dir.exists()


# ----------------------------------------------------------------------
class TestRenderGlobal:
    # ----------------------------------------------------------------------
    def test_writes_rendered_content(self, template, tmp_path: Path):
        target = tmp_path / "global" / "CONFIG.md"
        agent = _MakeAgent(global_paths=(str(target),))

        RenderGlobal(template("Value: {{ 3 + 4 }}"), agent)

        assert target.read_text(encoding="utf-8") == "Value: 7"

    # ----------------------------------------------------------------------
    def test_preserves_frontmatter(self, template, tmp_path: Path):
        target = tmp_path / "CONFIG.md"
        agent = _MakeAgent(global_paths=(str(target),))

        RenderGlobal(
            template(
                dedent("""\
                ---
                key: value
                ---
                Body""")
            ),
            agent,
        )

        assert target.read_text(encoding="utf-8") == dedent("""\
            ---
            key: value
            ---
            Body""")

    # ----------------------------------------------------------------------
    def test_expands_environment_variables(self, template, tmp_path: Path, monkeypatch):
        # The global path templates are expanded, so an env-var reference resolves.
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeAgent(global_paths=("~/CONFIG.md",))

        RenderGlobal(template("content"), agent)

        assert (tmp_path / "CONFIG.md").read_text(encoding="utf-8") == "content"

    # ----------------------------------------------------------------------
    def test_writes_to_every_global_path(self, template, tmp_path: Path):
        target_a = tmp_path / "a" / "CONFIG.md"
        target_b = tmp_path / "b" / "CONFIG.md"
        agent = _MakeAgent(global_paths=(str(target_a), str(target_b)))

        RenderGlobal(template("shared"), agent)

        assert target_a.read_text(encoding="utf-8") == "shared"
        assert target_b.read_text(encoding="utf-8") == "shared"


# ----------------------------------------------------------------------
class TestRenderLocalSkill:
    # ----------------------------------------------------------------------
    def test_writes_to_skill_path_named_by_frontmatter(self, template, tmp_path: Path):
        agent = _MakeAgent(project_skill_template="skills/{skill_name}/SKILL.md")
        output_dir = tmp_path / "out"

        RenderLocalSkill(
            template(
                dedent("""\
                ---
                name: my-skill
                ---
                Body: {{ 2 + 2 }}""")
            ),
            agent,
            output_dir,
        )

        assert (output_dir / "skills" / "my-skill" / "SKILL.md").read_text(encoding="utf-8") == dedent("""\
            ---
            name: my-skill
            ---
            Body: 4""")

    # ----------------------------------------------------------------------
    def test_unsupported_agent_raises(self, template, tmp_path: Path):
        agent = _MakeAgent(project_skill_template=None)
        output_dir = tmp_path / "out"

        with pytest.raises(ValueError, match="does not support skills"):
            RenderLocalSkill(
                template(
                    dedent("""\
                    ---
                    name: my-skill
                    ---
                    Body""")
                ),
                agent,
                output_dir,
            )

        assert not output_dir.exists()

    # ----------------------------------------------------------------------
    def test_missing_frontmatter_raises(self, template, tmp_path: Path):
        agent = _MakeAgent(project_skill_template="skills/{skill_name}/SKILL.md")
        output_dir = tmp_path / "out"

        with pytest.raises(ValueError, match="does not have frontmatter"):
            RenderLocalSkill(template("Body without frontmatter"), agent, output_dir)

    # ----------------------------------------------------------------------
    def test_missing_name_attribute_raises(self, template, tmp_path: Path):
        agent = _MakeAgent(project_skill_template="skills/{skill_name}/SKILL.md")
        output_dir = tmp_path / "out"

        with pytest.raises(ValueError, match="does not have a 'name' frontmatter attribute"):
            RenderLocalSkill(
                template(
                    dedent("""\
                    ---
                    description: no name here
                    ---
                    Body""")
                ),
                agent,
                output_dir,
            )


# ----------------------------------------------------------------------
class TestRenderGlobalSkill:
    # ----------------------------------------------------------------------
    def test_writes_to_skill_path_named_by_frontmatter(self, template, tmp_path: Path, monkeypatch):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeAgent(global_skill_template="~/skills/{skill_name}/SKILL.md")

        RenderGlobalSkill(
            template(
                dedent("""\
                ---
                name: my-skill
                ---
                Body: {{ 1 + 1 }}""")
            ),
            agent,
        )

        assert (tmp_path / "skills" / "my-skill" / "SKILL.md").read_text(encoding="utf-8") == dedent("""\
            ---
            name: my-skill
            ---
            Body: 2""")

    # ----------------------------------------------------------------------
    def test_unsupported_agent_raises(self, template, tmp_path: Path, monkeypatch):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeAgent(global_skill_template=None)

        with pytest.raises(ValueError, match="does not support skills"):
            RenderGlobalSkill(
                template(
                    dedent("""\
                    ---
                    name: my-skill
                    ---
                    Body""")
                ),
                agent,
            )

        assert list(tmp_path.iterdir()) == [tmp_path / "template.md"]

    # ----------------------------------------------------------------------
    def test_missing_frontmatter_raises(self, template):
        agent = _MakeAgent(global_skill_template="~/skills/{skill_name}/SKILL.md")

        with pytest.raises(ValueError, match="does not have frontmatter"):
            RenderGlobalSkill(template("Body without frontmatter"), agent)

    # ----------------------------------------------------------------------
    def test_missing_name_attribute_raises(self, template):
        agent = _MakeAgent(global_skill_template="~/skills/{skill_name}/SKILL.md")

        with pytest.raises(ValueError, match="does not have a 'name' frontmatter attribute"):
            RenderGlobalSkill(
                template(
                    dedent("""\
                    ---
                    description: no name here
                    ---
                    Body""")
                ),
                agent,
            )


# ----------------------------------------------------------------------
@pytest.fixture
def launcher(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, MagicMock]:
    """Patch the operating-system launch boundaries so tests never spawn a real editor.

    An `$EDITOR` value is provided so, by default, the launcher takes the subprocess
    path (and never invokes the operating-system default handler). Returns the
    `subprocess.run` and `os.startfile` spies.
    """

    run_spy = MagicMock()
    startfile_spy = MagicMock()

    monkeypatch.setenv("VISUAL", "")
    monkeypatch.setenv("EDITOR", "my-editor")
    monkeypatch.setattr(lib_module.subprocess, "run", run_spy)
    monkeypatch.setattr(lib_module.os, "startfile", startfile_spy, raising=False)

    return run_spy, startfile_spy


# ----------------------------------------------------------------------
class TestEditLocal:
    # ----------------------------------------------------------------------
    def test_launches_editor_on_project_file(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, _startfile_spy = launcher
        agent = _MakeAgent(project_paths=("CONFIG.md",))
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        (output_dir / "CONFIG.md").write_text("content", encoding="utf-8")

        EditLocal(agent, output_dir)

        run_spy.assert_called_once_with(["my-editor", str(output_dir / "CONFIG.md")], check=True)

    # ----------------------------------------------------------------------
    def test_launches_editor_on_first_path_only(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, _startfile_spy = launcher
        agent = _MakeAgent(project_paths=("A.md", "B.md"))
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        (output_dir / "A.md").write_text("a", encoding="utf-8")
        (output_dir / "B.md").write_text("b", encoding="utf-8")

        EditLocal(agent, output_dir)

        run_spy.assert_called_once_with(["my-editor", str(output_dir / "A.md")], check=True)

    # ----------------------------------------------------------------------
    def test_missing_file_raises(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(project_paths=("CONFIG.md",))
        output_dir = tmp_path / "out"

        with pytest.raises(FileNotFoundError):
            EditLocal(agent, output_dir)

        run_spy.assert_not_called()
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_directory_path_raises(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(project_paths=("CONFIG.md",))
        output_dir = tmp_path / "out"
        (output_dir / "CONFIG.md").mkdir(parents=True)

        with pytest.raises(FileNotFoundError):
            EditLocal(agent, output_dir)

        run_spy.assert_not_called()
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_no_project_paths_raises(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(project_paths=())

        with pytest.raises(ValueError, match="does not define any configuration locations"):
            EditLocal(agent, tmp_path)

        run_spy.assert_not_called()
        startfile_spy.assert_not_called()


# ----------------------------------------------------------------------
class TestEditGlobal:
    # ----------------------------------------------------------------------
    def test_uses_editor_env_var(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        target = tmp_path / "CONFIG.md"
        target.write_text("content", encoding="utf-8")
        agent = _MakeAgent(global_paths=(str(target),))

        EditGlobal(agent)

        run_spy.assert_called_once_with(["my-editor", str(target)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_prefers_visual_env_var(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, _startfile_spy = launcher
        monkeypatch.setenv("VISUAL", "visual-editor")
        target = tmp_path / "CONFIG.md"
        target.write_text("content", encoding="utf-8")
        agent = _MakeAgent(global_paths=(str(target),))

        EditGlobal(agent)

        run_spy.assert_called_once_with(["visual-editor", str(target)], check=True)

    # ----------------------------------------------------------------------
    def test_windows_default_handler(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.delenv("EDITOR", raising=False)
        monkeypatch.setattr(lib_module.sys, "platform", "win32")
        target = tmp_path / "CONFIG.md"
        target.write_text("content", encoding="utf-8")
        agent = _MakeAgent(global_paths=(str(target),))

        EditGlobal(agent)

        startfile_spy.assert_called_once_with(target)
        run_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_macos_default_handler(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.delenv("EDITOR", raising=False)
        monkeypatch.setattr(lib_module.sys, "platform", "darwin")
        target = tmp_path / "CONFIG.md"
        target.write_text("content", encoding="utf-8")
        agent = _MakeAgent(global_paths=(str(target),))

        EditGlobal(agent)

        run_spy.assert_called_once_with(["open", str(target)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_linux_default_handler(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.delenv("EDITOR", raising=False)
        monkeypatch.setattr(lib_module.sys, "platform", "linux")
        target = tmp_path / "CONFIG.md"
        target.write_text("content", encoding="utf-8")
        agent = _MakeAgent(global_paths=(str(target),))

        EditGlobal(agent)

        run_spy.assert_called_once_with(["xdg-open", str(target)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_file_raises(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(global_paths=(str(tmp_path / "CONFIG.md"),))

        with pytest.raises(FileNotFoundError):
            EditGlobal(agent)

        run_spy.assert_not_called()
        startfile_spy.assert_not_called()


# ----------------------------------------------------------------------
class TestEditLocalSkill:
    # ----------------------------------------------------------------------
    def test_launches_editor_on_project_skill(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, _startfile_spy = launcher
        agent = _MakeAgent(project_skill_template="skills/{skill_name}/SKILL.md")
        output_dir = tmp_path / "out"
        skill_path = output_dir / "skills" / "my-skill" / "SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text("content", encoding="utf-8")

        EditLocalSkill("my-skill", agent, output_dir)

        run_spy.assert_called_once_with(["my-editor", str(skill_path)], check=True)

    # ----------------------------------------------------------------------
    def test_unsupported_agent_raises(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(project_skill_template=None)

        with pytest.raises(ValueError, match="does not support skills"):
            EditLocalSkill("my-skill", agent, tmp_path / "out")

        run_spy.assert_not_called()
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_file_raises(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(project_skill_template="skills/{skill_name}/SKILL.md")

        with pytest.raises(FileNotFoundError, match="skill file"):
            EditLocalSkill("my-skill", agent, tmp_path / "out")

        run_spy.assert_not_called()
        startfile_spy.assert_not_called()


# ----------------------------------------------------------------------
class TestEditGlobalSkill:
    # ----------------------------------------------------------------------
    def test_launches_editor_on_global_skill(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))
        agent = _MakeAgent(global_skill_template="~/skills/{skill_name}/SKILL.md")
        skill_path = tmp_path / "skills" / "my-skill" / "SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text("content", encoding="utf-8")

        EditGlobalSkill("my-skill", agent)

        run_spy.assert_called_once_with(["my-editor", str(skill_path)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_unsupported_agent_raises(
        self,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(global_skill_template=None)

        with pytest.raises(ValueError, match="does not support skills"):
            EditGlobalSkill("my-skill", agent)

        run_spy.assert_not_called()
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_file_raises(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))
        agent = _MakeAgent(global_skill_template="~/skills/{skill_name}/SKILL.md")

        with pytest.raises(FileNotFoundError, match="skill file"):
            EditGlobalSkill("my-skill", agent)

        run_spy.assert_not_called()
        startfile_spy.assert_not_called()


# ----------------------------------------------------------------------
class TestBrowseGlobal:
    # ----------------------------------------------------------------------
    def test_windows_opens_configuration_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "win32")
        target = tmp_path / "config" / "CONFIG.md"
        target.parent.mkdir()
        agent = _MakeAgent(global_paths=(str(target),))

        BrowseGlobal(agent)

        startfile_spy.assert_called_once_with(target.parent)
        run_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_macos_opens_configuration_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "darwin")
        target = tmp_path / "config" / "CONFIG.md"
        target.parent.mkdir()
        agent = _MakeAgent(global_paths=(str(target),))

        BrowseGlobal(agent)

        run_spy.assert_called_once_with(["open", str(target.parent)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_linux_opens_configuration_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "linux")
        target = tmp_path / "config" / "CONFIG.md"
        target.parent.mkdir()
        agent = _MakeAgent(global_paths=(str(target),))

        BrowseGlobal(agent)

        run_spy.assert_called_once_with(["xdg-open", str(target.parent)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_directory_raises(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(global_paths=(str(tmp_path / "config" / "CONFIG.md"),))

        with pytest.raises(FileNotFoundError):
            BrowseGlobal(agent)

        run_spy.assert_not_called()
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_no_global_paths_raises(
        self,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(global_paths=())

        with pytest.raises(ValueError, match="does not define any configuration locations"):
            BrowseGlobal(agent)

        run_spy.assert_not_called()
        startfile_spy.assert_not_called()


# ----------------------------------------------------------------------
class TestBrowseGlobalSkills:
    # ----------------------------------------------------------------------
    def test_windows_opens_skills_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "win32")
        skills_root = tmp_path / "skills"
        skills_root.mkdir()
        agent = _MakeAgent(global_skills_root=str(skills_root))

        BrowseGlobalSkills(agent)

        startfile_spy.assert_called_once_with(skills_root)
        run_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_macos_opens_skills_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "darwin")
        skills_root = tmp_path / "skills"
        skills_root.mkdir()
        agent = _MakeAgent(global_skills_root=str(skills_root))

        BrowseGlobalSkills(agent)

        run_spy.assert_called_once_with(["open", str(skills_root)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_linux_opens_skills_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "linux")
        skills_root = tmp_path / "skills"
        skills_root.mkdir()
        agent = _MakeAgent(global_skills_root=str(skills_root))

        BrowseGlobalSkills(agent)

        run_spy.assert_called_once_with(["xdg-open", str(skills_root)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_unsupported_agent_raises(
        self,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(global_skills_root=None)

        with pytest.raises(ValueError, match="does not support skills"):
            BrowseGlobalSkills(agent)

        run_spy.assert_not_called()
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_directory_raises(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(global_skills_root=str(tmp_path / "skills"))

        with pytest.raises(FileNotFoundError, match="skills directory"):
            BrowseGlobalSkills(agent)

        run_spy.assert_not_called()
        startfile_spy.assert_not_called()


# ----------------------------------------------------------------------
class TestBrowseLocalSkills:
    # ----------------------------------------------------------------------
    def test_windows_opens_skills_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "win32")
        agent = _MakeAgent(project_skills_root="skills")
        output_dir = tmp_path / "out"
        (output_dir / "skills").mkdir(parents=True)

        BrowseLocalSkills(agent, output_dir)

        startfile_spy.assert_called_once_with(output_dir / "skills")
        run_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_linux_opens_skills_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "linux")
        agent = _MakeAgent(project_skills_root="skills")
        output_dir = tmp_path / "out"
        (output_dir / "skills").mkdir(parents=True)

        BrowseLocalSkills(agent, output_dir)

        run_spy.assert_called_once_with(["xdg-open", str(output_dir / "skills")], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_unsupported_agent_raises(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(project_skills_root=None)

        with pytest.raises(ValueError, match="does not support skills"):
            BrowseLocalSkills(agent, tmp_path / "out")

        run_spy.assert_not_called()
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_directory_raises(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(project_skills_root="skills")

        with pytest.raises(FileNotFoundError, match="skills directory"):
            BrowseLocalSkills(agent, tmp_path / "out")

        run_spy.assert_not_called()
        startfile_spy.assert_not_called()
