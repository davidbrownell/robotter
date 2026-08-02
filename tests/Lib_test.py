"""Unit tests for robotter.Lib"""

from collections.abc import Callable, Iterator
from pathlib import Path
from textwrap import dedent
from typing import cast
from unittest.mock import MagicMock

import pytest

from dbrownell_Common.Streams.DoneManager import DoneManager
from dbrownell_Common.TestHelpers.StreamTestHelpers import GenerateDoneManagerAndContent

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
    project_path: str = "",
    global_path: str = "",
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
        def _GetGlobalConfigurationFilename(operating_system: OperatingSystem) -> Path:  # noqa: ARG004
            return Path(global_path)

        @staticmethod
        def _GetProjectConfigurationName() -> str:
            return project_path

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
@pytest.fixture
def dm() -> Iterator[DoneManager]:
    """Provide a `DoneManager` whose captured output is discarded.

    Tests that assert on the captured output drive `GenerateDoneManagerAndContent`
    directly instead of using this fixture.
    """

    generator = GenerateDoneManagerAndContent()
    yield cast(DoneManager, next(generator))

    # Finalize the underlying DoneManager context.
    for _ in generator:
        pass


# ----------------------------------------------------------------------
class TestRenderLocal:
    # ----------------------------------------------------------------------
    def test_writes_rendered_content(self, template, tmp_path: Path, dm: DoneManager):
        agent = _MakeAgent(project_path="CONFIG.md")
        output_dir = tmp_path / "out"

        RenderLocal(dm, template("Hello, world!"), agent, output_dir)

        assert (output_dir / "CONFIG.md").read_text(encoding="utf-8") == "Hello, world!"

    # ----------------------------------------------------------------------
    def test_renders_jinja2(self, template, tmp_path: Path, dm: DoneManager):
        agent = _MakeAgent(project_path="CONFIG.md")
        output_dir = tmp_path / "out"

        RenderLocal(dm, template("Value: {{ 1 + 2 }}"), agent, output_dir)

        assert (output_dir / "CONFIG.md").read_text(encoding="utf-8") == "Value: 3"

    # ----------------------------------------------------------------------
    def test_preserves_frontmatter(self, template, tmp_path: Path, dm: DoneManager):
        agent = _MakeAgent(project_path="CONFIG.md")
        output_dir = tmp_path / "out"

        RenderLocal(
            dm,
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
    def test_creates_parent_directories(self, template, tmp_path: Path, dm: DoneManager):
        agent = _MakeAgent(project_path="nested/dir/CONFIG.md")
        output_dir = tmp_path / "out"

        RenderLocal(dm, template("content"), agent, output_dir)

        assert (output_dir / "nested" / "dir" / "CONFIG.md").read_text(encoding="utf-8") == "content"

    # ----------------------------------------------------------------------
    def test_encodes_as_utf8(self, template, tmp_path: Path, dm: DoneManager):
        agent = _MakeAgent(project_path="CONFIG.md")
        output_dir = tmp_path / "out"

        RenderLocal(dm, template("café — naïve — 日本語"), agent, output_dir)

        written = output_dir / "CONFIG.md"
        assert written.read_bytes() == "café — naïve — 日本語".encode()

    # ----------------------------------------------------------------------
    def test_writes_the_written_file_to_the_done_manager(self, template, tmp_path: Path):
        agent = _MakeAgent(project_path="sub/CONFIG.md")
        output_dir = tmp_path / "out"

        generator = GenerateDoneManagerAndContent()
        dm = cast(DoneManager, next(generator))

        RenderLocal(dm, template("shared"), agent, output_dir)

        content = cast(str, next(generator))

        assert content == dedent(f"""\
            Heading...
              Writing '{output_dir / "sub" / "CONFIG.md"}'...DONE! (0, <scrubbed duration>)
            DONE! (0, <scrubbed duration>)
            """)


# ----------------------------------------------------------------------
class TestRenderGlobal:
    # ----------------------------------------------------------------------
    def test_writes_rendered_content(self, template, tmp_path: Path, dm: DoneManager):
        target = tmp_path / "global" / "CONFIG.md"
        agent = _MakeAgent(global_path=str(target))

        RenderGlobal(dm, template("Value: {{ 3 + 4 }}"), agent)

        assert target.read_text(encoding="utf-8") == "Value: 7"

    # ----------------------------------------------------------------------
    def test_preserves_frontmatter(self, template, tmp_path: Path, dm: DoneManager):
        target = tmp_path / "CONFIG.md"
        agent = _MakeAgent(global_path=str(target))

        RenderGlobal(
            dm,
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
    def test_expands_environment_variables(self, template, tmp_path: Path, monkeypatch, dm: DoneManager):
        # The global path template is expanded, so an env-var reference resolves.
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeAgent(global_path="~/CONFIG.md")

        RenderGlobal(dm, template("content"), agent)

        assert (tmp_path / "CONFIG.md").read_text(encoding="utf-8") == "content"


# ----------------------------------------------------------------------
class TestRenderLocalSkill:
    # ----------------------------------------------------------------------
    def test_writes_to_skill_path_named_by_frontmatter(self, template, tmp_path: Path, dm: DoneManager):
        agent = _MakeAgent(project_skill_template="skills/{skill_name}/SKILL.md")
        output_dir = tmp_path / "out"

        RenderLocalSkill(
            dm,
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
    def test_unsupported_agent_writes_error(self, template, tmp_path: Path):
        agent = _MakeAgent(project_skill_template=None)
        output_dir = tmp_path / "out"

        generator = GenerateDoneManagerAndContent()
        dm = cast(DoneManager, next(generator))

        RenderLocalSkill(
            dm,
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

        content = cast(str, next(generator))

        assert content == dedent("""\
            Heading...
              ERROR: The 'Stub' agent does not support skills.
            DONE! (-1, <scrubbed duration>)
            """)
        assert not output_dir.exists()

    # ----------------------------------------------------------------------
    def test_missing_frontmatter_writes_error(self, template, tmp_path: Path):
        agent = _MakeAgent(project_skill_template="skills/{skill_name}/SKILL.md")
        output_dir = tmp_path / "out"
        template_path = template("Body without frontmatter")

        content = _RunCapturingContent(lambda dm: RenderLocalSkill(dm, template_path, agent, output_dir))

        assert content == _ExpectedError(f"The skill template '{template_path}' does not have frontmatter.")
        assert not output_dir.exists()

    # ----------------------------------------------------------------------
    def test_missing_name_attribute_writes_error(self, template, tmp_path: Path):
        agent = _MakeAgent(project_skill_template="skills/{skill_name}/SKILL.md")
        output_dir = tmp_path / "out"
        template_path = template(
            dedent("""\
                ---
                description: no name here
                ---
                Body""")
        )

        content = _RunCapturingContent(lambda dm: RenderLocalSkill(dm, template_path, agent, output_dir))

        assert content == _ExpectedError(
            f"The skill template '{template_path}' does not have a 'name' frontmatter attribute."
        )
        assert not output_dir.exists()


# ----------------------------------------------------------------------
class TestRenderGlobalSkill:
    # ----------------------------------------------------------------------
    def test_writes_to_skill_path_named_by_frontmatter(
        self, template, tmp_path: Path, monkeypatch, dm: DoneManager
    ):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeAgent(global_skill_template="~/skills/{skill_name}/SKILL.md")

        RenderGlobalSkill(
            dm,
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
    def test_unsupported_agent_writes_error(self, template, tmp_path: Path, monkeypatch):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeAgent(global_skill_template=None)

        generator = GenerateDoneManagerAndContent()
        dm = cast(DoneManager, next(generator))

        RenderGlobalSkill(
            dm,
            template(
                dedent("""\
                ---
                name: my-skill
                ---
                Body""")
            ),
            agent,
        )

        content = cast(str, next(generator))

        assert content == dedent("""\
            Heading...
              ERROR: The 'Stub' agent does not support skills.
            DONE! (-1, <scrubbed duration>)
            """)
        assert list(tmp_path.iterdir()) == [tmp_path / "template.md"]

    # ----------------------------------------------------------------------
    def test_missing_frontmatter_writes_error(self, template):
        agent = _MakeAgent(global_skill_template="~/skills/{skill_name}/SKILL.md")
        template_path = template("Body without frontmatter")

        content = _RunCapturingContent(lambda dm: RenderGlobalSkill(dm, template_path, agent))

        assert content == _ExpectedError(f"The skill template '{template_path}' does not have frontmatter.")

    # ----------------------------------------------------------------------
    def test_missing_name_attribute_writes_error(self, template):
        agent = _MakeAgent(global_skill_template="~/skills/{skill_name}/SKILL.md")
        template_path = template(
            dedent("""\
                ---
                description: no name here
                ---
                Body""")
        )

        content = _RunCapturingContent(lambda dm: RenderGlobalSkill(dm, template_path, agent))

        assert content == _ExpectedError(
            f"The skill template '{template_path}' does not have a 'name' frontmatter attribute."
        )


# ----------------------------------------------------------------------
def _RunCapturingContent(func: Callable[[DoneManager], None]) -> str:
    """Invoke `func` with a fresh `DoneManager` and return the captured, scrubbed output."""

    generator = GenerateDoneManagerAndContent()
    dm = cast(DoneManager, next(generator))

    func(dm)

    return cast(str, next(generator))


# ----------------------------------------------------------------------
def _ExpectedError(message: str) -> str:
    """Return the captured output expected when `message` is written as an error."""

    return dedent(f"""\
        Heading...
          ERROR: {message}
        DONE! (-1, <scrubbed duration>)
        """)


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
        dm: DoneManager,
    ):
        run_spy, _startfile_spy = launcher
        agent = _MakeAgent(project_path="CONFIG.md")
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        (output_dir / "CONFIG.md").write_text("content", encoding="utf-8")

        EditLocal(dm, agent, output_dir)

        run_spy.assert_called_once_with(["my-editor", str(output_dir / "CONFIG.md")], check=True)

    # ----------------------------------------------------------------------
    def test_missing_file_writes_error(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(project_path="CONFIG.md")
        output_dir = tmp_path / "out"

        content = _RunCapturingContent(lambda dm: EditLocal(dm, agent, output_dir))

        assert content == _ExpectedError(
            f"The configuration file '{output_dir / 'CONFIG.md'}' does not exist."
        )
        run_spy.assert_not_called()
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_directory_path_writes_error(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(project_path="CONFIG.md")
        output_dir = tmp_path / "out"
        (output_dir / "CONFIG.md").mkdir(parents=True)

        content = _RunCapturingContent(lambda dm: EditLocal(dm, agent, output_dir))

        assert content == _ExpectedError(
            f"The configuration file '{output_dir / 'CONFIG.md'}' does not exist."
        )
        run_spy.assert_not_called()
        startfile_spy.assert_not_called()


# ----------------------------------------------------------------------
class TestEditGlobal:
    # ----------------------------------------------------------------------
    def test_uses_editor_env_var(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
        dm: DoneManager,
    ):
        run_spy, startfile_spy = launcher
        target = tmp_path / "CONFIG.md"
        target.write_text("content", encoding="utf-8")
        agent = _MakeAgent(global_path=str(target))

        EditGlobal(dm, agent)

        run_spy.assert_called_once_with(["my-editor", str(target)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_prefers_visual_env_var(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
        dm: DoneManager,
    ):
        run_spy, _startfile_spy = launcher
        monkeypatch.setenv("VISUAL", "visual-editor")
        target = tmp_path / "CONFIG.md"
        target.write_text("content", encoding="utf-8")
        agent = _MakeAgent(global_path=str(target))

        EditGlobal(dm, agent)

        run_spy.assert_called_once_with(["visual-editor", str(target)], check=True)

    # ----------------------------------------------------------------------
    def test_windows_default_handler(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
        dm: DoneManager,
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.delenv("EDITOR", raising=False)
        monkeypatch.setattr(lib_module.sys, "platform", "win32")
        target = tmp_path / "CONFIG.md"
        target.write_text("content", encoding="utf-8")
        agent = _MakeAgent(global_path=str(target))

        EditGlobal(dm, agent)

        startfile_spy.assert_called_once_with(target)
        run_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_macos_default_handler(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
        dm: DoneManager,
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.delenv("EDITOR", raising=False)
        monkeypatch.setattr(lib_module.sys, "platform", "darwin")
        target = tmp_path / "CONFIG.md"
        target.write_text("content", encoding="utf-8")
        agent = _MakeAgent(global_path=str(target))

        EditGlobal(dm, agent)

        run_spy.assert_called_once_with(["open", str(target)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_linux_default_handler(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
        dm: DoneManager,
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.delenv("EDITOR", raising=False)
        monkeypatch.setattr(lib_module.sys, "platform", "linux")
        target = tmp_path / "CONFIG.md"
        target.write_text("content", encoding="utf-8")
        agent = _MakeAgent(global_path=str(target))

        EditGlobal(dm, agent)

        run_spy.assert_called_once_with(["xdg-open", str(target)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_file_writes_error(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        target = tmp_path / "CONFIG.md"
        agent = _MakeAgent(global_path=str(target))

        content = _RunCapturingContent(lambda dm: EditGlobal(dm, agent))

        assert content == _ExpectedError(f"The configuration file '{target}' does not exist.")
        run_spy.assert_not_called()
        startfile_spy.assert_not_called()


# ----------------------------------------------------------------------
class TestEditLocalSkill:
    # ----------------------------------------------------------------------
    def test_launches_editor_on_project_skill(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
        dm: DoneManager,
    ):
        run_spy, _startfile_spy = launcher
        agent = _MakeAgent(project_skill_template="skills/{skill_name}/SKILL.md")
        output_dir = tmp_path / "out"
        skill_path = output_dir / "skills" / "my-skill" / "SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text("content", encoding="utf-8")

        EditLocalSkill(dm, "my-skill", agent, output_dir)

        run_spy.assert_called_once_with(["my-editor", str(skill_path)], check=True)

    # ----------------------------------------------------------------------
    def test_unsupported_agent_writes_error(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(project_skill_template=None)

        content = _RunCapturingContent(lambda dm: EditLocalSkill(dm, "my-skill", agent, tmp_path / "out"))

        assert content == _ExpectedError("The 'Stub' agent does not support skills.")
        run_spy.assert_not_called()
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_file_writes_error(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(project_skill_template="skills/{skill_name}/SKILL.md")
        output_dir = tmp_path / "out"

        content = _RunCapturingContent(lambda dm: EditLocalSkill(dm, "my-skill", agent, output_dir))

        assert content == _ExpectedError(
            f"The skill file '{output_dir / 'skills' / 'my-skill' / 'SKILL.md'}' does not exist."
        )
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
        dm: DoneManager,
    ):
        run_spy, startfile_spy = launcher
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))
        agent = _MakeAgent(global_skill_template="~/skills/{skill_name}/SKILL.md")
        skill_path = tmp_path / "skills" / "my-skill" / "SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text("content", encoding="utf-8")

        EditGlobalSkill(dm, "my-skill", agent)

        run_spy.assert_called_once_with(["my-editor", str(skill_path)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_unsupported_agent_writes_error(
        self,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(global_skill_template=None)

        content = _RunCapturingContent(lambda dm: EditGlobalSkill(dm, "my-skill", agent))

        assert content == _ExpectedError("The 'Stub' agent does not support skills.")
        run_spy.assert_not_called()
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_file_writes_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))
        agent = _MakeAgent(global_skill_template="~/skills/{skill_name}/SKILL.md")

        content = _RunCapturingContent(lambda dm: EditGlobalSkill(dm, "my-skill", agent))

        assert content == _ExpectedError(
            f"The skill file '{tmp_path / 'skills' / 'my-skill' / 'SKILL.md'}' does not exist."
        )
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
        dm: DoneManager,
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "win32")
        target = tmp_path / "config" / "CONFIG.md"
        target.parent.mkdir()
        agent = _MakeAgent(global_path=str(target))

        BrowseGlobal(dm, agent)

        startfile_spy.assert_called_once_with(target.parent)
        run_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_macos_opens_configuration_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
        dm: DoneManager,
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "darwin")
        target = tmp_path / "config" / "CONFIG.md"
        target.parent.mkdir()
        agent = _MakeAgent(global_path=str(target))

        BrowseGlobal(dm, agent)

        run_spy.assert_called_once_with(["open", str(target.parent)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_linux_opens_configuration_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
        dm: DoneManager,
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "linux")
        target = tmp_path / "config" / "CONFIG.md"
        target.parent.mkdir()
        agent = _MakeAgent(global_path=str(target))

        BrowseGlobal(dm, agent)

        run_spy.assert_called_once_with(["xdg-open", str(target.parent)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_directory_writes_error(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(global_path=str(tmp_path / "config" / "CONFIG.md"))

        content = _RunCapturingContent(lambda dm: BrowseGlobal(dm, agent))

        assert content == _ExpectedError(
            f"The configuration directory '{tmp_path / 'config'}' does not exist."
        )
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
        dm: DoneManager,
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "win32")
        skills_root = tmp_path / "skills"
        skills_root.mkdir()
        agent = _MakeAgent(global_skills_root=str(skills_root))

        BrowseGlobalSkills(dm, agent)

        startfile_spy.assert_called_once_with(skills_root)
        run_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_macos_opens_skills_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
        dm: DoneManager,
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "darwin")
        skills_root = tmp_path / "skills"
        skills_root.mkdir()
        agent = _MakeAgent(global_skills_root=str(skills_root))

        BrowseGlobalSkills(dm, agent)

        run_spy.assert_called_once_with(["open", str(skills_root)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_linux_opens_skills_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
        dm: DoneManager,
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "linux")
        skills_root = tmp_path / "skills"
        skills_root.mkdir()
        agent = _MakeAgent(global_skills_root=str(skills_root))

        BrowseGlobalSkills(dm, agent)

        run_spy.assert_called_once_with(["xdg-open", str(skills_root)], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_unsupported_agent_writes_error(
        self,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(global_skills_root=None)

        content = _RunCapturingContent(lambda dm: BrowseGlobalSkills(dm, agent))

        assert content == _ExpectedError("The 'Stub' agent does not support skills.")
        run_spy.assert_not_called()
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_directory_writes_error(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        skills_root = tmp_path / "skills"
        agent = _MakeAgent(global_skills_root=str(skills_root))

        content = _RunCapturingContent(lambda dm: BrowseGlobalSkills(dm, agent))

        assert content == _ExpectedError(f"The skills directory '{skills_root}' does not exist.")
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
        dm: DoneManager,
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "win32")
        agent = _MakeAgent(project_skills_root="skills")
        output_dir = tmp_path / "out"
        (output_dir / "skills").mkdir(parents=True)

        BrowseLocalSkills(dm, agent, output_dir)

        startfile_spy.assert_called_once_with(output_dir / "skills")
        run_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_linux_opens_skills_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        launcher: tuple[MagicMock, MagicMock],
        dm: DoneManager,
    ):
        run_spy, startfile_spy = launcher
        monkeypatch.setattr(lib_module.sys, "platform", "linux")
        agent = _MakeAgent(project_skills_root="skills")
        output_dir = tmp_path / "out"
        (output_dir / "skills").mkdir(parents=True)

        BrowseLocalSkills(dm, agent, output_dir)

        run_spy.assert_called_once_with(["xdg-open", str(output_dir / "skills")], check=True)
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_unsupported_agent_writes_error(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(project_skills_root=None)

        content = _RunCapturingContent(lambda dm: BrowseLocalSkills(dm, agent, tmp_path / "out"))

        assert content == _ExpectedError("The 'Stub' agent does not support skills.")
        run_spy.assert_not_called()
        startfile_spy.assert_not_called()

    # ----------------------------------------------------------------------
    def test_missing_directory_writes_error(
        self,
        tmp_path: Path,
        launcher: tuple[MagicMock, MagicMock],
    ):
        run_spy, startfile_spy = launcher
        agent = _MakeAgent(project_skills_root="skills")
        output_dir = tmp_path / "out"

        content = _RunCapturingContent(lambda dm: BrowseLocalSkills(dm, agent, output_dir))

        assert content == _ExpectedError(f"The skills directory '{output_dir / 'skills'}' does not exist.")
        run_spy.assert_not_called()
        startfile_spy.assert_not_called()
