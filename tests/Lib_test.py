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

from robotter.Renderer import RenderError
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

        @classmethod
        def _GetGlobalSkillPath(cls, skill_name: str, operating_system: OperatingSystem) -> Path | None:  # noqa: ARG003
            if global_skill_template is None:
                return None
            return Path(global_skill_template.format(skill_name=skill_name))

        @classmethod
        def _GetProjectSkillPath(cls, skill_name: str) -> Path | None:
            if project_skill_template is None:
                return None
            return Path(project_skill_template.format(skill_name=skill_name))

    return _StubAgent()


# ----------------------------------------------------------------------
@pytest.fixture
def template(tmp_path: Path):
    """Factory fixture that writes a template file and returns its path."""

    def _create(content: str) -> Path:
        file = tmp_path / "template.jinja.md"
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
@pytest.fixture
def symlinks(tmp_path: Path) -> None:
    """Skip the test when the host cannot create symbolic links (for example, Windows without Developer Mode)."""

    probe = tmp_path / ".symlink-probe"

    try:
        probe.symlink_to(tmp_path)
    except OSError:
        pytest.skip("Symbolic links cannot be created on this host.")

    probe.unlink()


# ----------------------------------------------------------------------
@pytest.fixture
def symlink_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every attempt to create a symbolic link fail."""

    def _Raise(*args, **kwargs) -> None:  # noqa: ARG001
        msg = "Symbolic links are unavailable."
        raise OSError(msg)

    monkeypatch.setattr(Path, "symlink_to", _Raise)


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
    def test_does_not_render_non_template(self, tmp_path: Path, dm: DoneManager):
        agent = _MakeAgent(project_path="CONFIG.md")
        output_dir = tmp_path / "out"

        file = tmp_path / "template.md"
        file.write_text("Value: {{ 1 + 2 }}", encoding="utf-8")

        RenderLocal(dm, file, agent, output_dir)

        assert (output_dir / "CONFIG.md").read_text(encoding="utf-8") == "Value: {{ 1 + 2 }}"

    # ----------------------------------------------------------------------
    def test_copies_non_template_byte_for_byte(self, tmp_path: Path, dm: DoneManager):
        agent = _MakeAgent(project_path="CONFIG.md")
        output_dir = tmp_path / "out"

        # Leading and trailing whitespace and the frontmatter's blank lines would be normalized if
        # the file were parsed.
        payload = b"---\n\nkey: value\n\n---\n\nBody\n\n"

        file = tmp_path / "template.md"
        file.write_bytes(payload)

        RenderLocal(dm, file, agent, output_dir)

        written = output_dir / "CONFIG.md"

        assert not written.is_symlink()
        assert written.read_bytes() == payload

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
    def test_writes_template_as_file(self, template, tmp_path: Path, dm: DoneManager):
        target = tmp_path / "global" / "CONFIG.md"
        agent = _MakeAgent(global_path=str(target))

        RenderGlobal(dm, template("Value: {{ 3 + 4 }}"), agent)

        assert not target.is_symlink()
        assert target.read_text(encoding="utf-8") == "Value: 7"

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_links_non_template(self, tmp_path: Path, dm: DoneManager):
        target = tmp_path / "global" / "CONFIG.mdc"
        agent = _MakeAgent(global_path=str(target))

        source = tmp_path / "instructions.md"
        source.write_text("Value: {{ 1 + 2 }}\n", encoding="utf-8")

        RenderGlobal(dm, source, agent)

        assert target.is_symlink()
        assert target.resolve() == source.resolve()
        assert target.read_text(encoding="utf-8") == "Value: {{ 1 + 2 }}\n"

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_writes_the_linked_file_to_the_done_manager(self, tmp_path: Path):
        target = tmp_path / "global" / "CONFIG.md"
        agent = _MakeAgent(global_path=str(target))

        source = tmp_path / "instructions.md"
        source.write_text("Body", encoding="utf-8")

        content = _RunCapturingContent(lambda dm: RenderGlobal(dm, source, agent))

        assert content == dedent(f"""\
            Heading...
              Linking '{target}' to '{source.resolve()}'...DONE! (0, <scrubbed duration>)
            DONE! (0, <scrubbed duration>)
            """)

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_replaces_existing_file_with_link(self, tmp_path: Path, dm: DoneManager):
        target = tmp_path / "global" / "CONFIG.md"
        target.parent.mkdir()
        target.write_text("previous", encoding="utf-8")

        agent = _MakeAgent(global_path=str(target))

        source = tmp_path / "instructions.md"
        source.write_text("Body", encoding="utf-8")

        RenderGlobal(dm, source, agent)
        RenderGlobal(dm, source, agent)

        assert target.is_symlink()
        assert target.read_text(encoding="utf-8") == "Body"
        assert sorted(path.name for path in target.parent.iterdir()) == ["CONFIG.md"]

    # ----------------------------------------------------------------------
    def test_copy_writes_non_template_byte_for_byte(self, tmp_path: Path, dm: DoneManager):
        target = tmp_path / "global" / "CONFIG.md"
        agent = _MakeAgent(global_path=str(target))

        payload = b"---\n\nkey: value\n\n---\n\nBody\n\n"

        source = tmp_path / "instructions.md"
        source.write_bytes(payload)

        RenderGlobal(dm, source, agent, copy=True)

        assert not target.is_symlink()
        assert target.read_bytes() == payload

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_copy_replaces_link_without_modifying_its_source(self, tmp_path: Path, dm: DoneManager):
        target = tmp_path / "global" / "CONFIG.md"
        agent = _MakeAgent(global_path=str(target))

        source = tmp_path / "instructions.md"
        source.write_text("Original", encoding="utf-8")

        RenderGlobal(dm, source, agent)

        replacement = tmp_path / "replacement.md"
        replacement.write_text("Replacement", encoding="utf-8")

        RenderGlobal(dm, replacement, agent, copy=True)

        assert not target.is_symlink()
        assert target.read_text(encoding="utf-8") == "Replacement"
        assert source.read_text(encoding="utf-8") == "Original"

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_template_replaces_link_without_modifying_its_source(
        self, template, tmp_path: Path, dm: DoneManager
    ):
        target = tmp_path / "global" / "CONFIG.md"
        agent = _MakeAgent(global_path=str(target))

        source = tmp_path / "instructions.md"
        source.write_text("Original", encoding="utf-8")

        RenderGlobal(dm, source, agent)
        RenderGlobal(dm, template("Value: {{ 3 + 4 }}"), agent)

        assert not target.is_symlink()
        assert target.read_text(encoding="utf-8") == "Value: 7"
        assert source.read_text(encoding="utf-8") == "Original"

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlink_failure")
    def test_link_failure_writes_error_and_preserves_existing_file(self, tmp_path: Path):
        target = tmp_path / "global" / "CONFIG.md"
        target.parent.mkdir()
        target.write_text("previous", encoding="utf-8")

        agent = _MakeAgent(global_path=str(target))

        source = tmp_path / "instructions.md"
        source.write_text("Body", encoding="utf-8")

        content = _RunCapturingContent(lambda dm: RenderGlobal(dm, source, agent))

        assert content == dedent(f"""\
            Heading...
              Linking '{target}' to '{source.resolve()}'...
                ERROR: A symbolic link to '{source.resolve()}' could not be created at '{target}' (Symbolic links are unavailable.); enable 'copy' to copy it instead.
              DONE! (-1, <scrubbed duration>)
            DONE! (-1, <scrubbed duration>)
            """)
        assert not target.is_symlink()
        assert target.read_text(encoding="utf-8") == "previous"
        assert sorted(path.name for path in target.parent.iterdir()) == ["CONFIG.md"]

    # ----------------------------------------------------------------------
    def test_rendering_source_onto_itself_preserves_it(self, tmp_path: Path, dm: DoneManager):
        source = tmp_path / "CONFIG.md"
        source.write_text("Body", encoding="utf-8")

        agent = _MakeAgent(global_path=str(source))

        RenderGlobal(dm, source, agent)

        assert not source.is_symlink()
        assert source.read_text(encoding="utf-8") == "Body"
        assert sorted(path.name for path in tmp_path.iterdir()) == ["CONFIG.md"]

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_replaces_stale_temporary_link(self, tmp_path: Path, dm: DoneManager):
        target = tmp_path / "global" / "CONFIG.md"
        target.parent.mkdir()
        target.with_name(".CONFIG.md.robotter-link").write_text("stale", encoding="utf-8")

        agent = _MakeAgent(global_path=str(target))

        source = tmp_path / "instructions.md"
        source.write_text("Body", encoding="utf-8")

        RenderGlobal(dm, source, agent)

        assert target.is_symlink()
        assert target.read_text(encoding="utf-8") == "Body"
        assert sorted(path.name for path in target.parent.iterdir()) == ["CONFIG.md"]

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_move_failure_removes_temporary_link(self, tmp_path: Path, monkeypatch, dm: DoneManager):
        target = tmp_path / "global" / "CONFIG.md"
        target.parent.mkdir()
        target.write_text("previous", encoding="utf-8")

        agent = _MakeAgent(global_path=str(target))

        source = tmp_path / "instructions.md"
        source.write_text("Body", encoding="utf-8")

        def _Raise(*args, **kwargs) -> None:  # noqa: ARG001
            msg = "The link cannot be moved."
            raise OSError(msg)

        monkeypatch.setattr(Path, "replace", _Raise)

        with pytest.raises(OSError, match="The link cannot be moved."):
            RenderGlobal(dm, source, agent)

        assert target.read_text(encoding="utf-8") == "previous"
        assert sorted(path.name for path in target.parent.iterdir()) == ["CONFIG.md"]


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
    def test_non_template_is_named_by_frontmatter(self, tmp_path: Path, dm: DoneManager):
        agent = _MakeAgent(project_skill_template="skills/{skill_name}/SKILL.md")
        output_dir = tmp_path / "out"

        file = tmp_path / "SKILL.md"
        file.write_text(
            dedent("""                ---
                name: my-skill
                ---
                Body: {{ 2 + 2 }}"""),
            encoding="utf-8",
        )

        RenderLocalSkill(dm, file, agent, output_dir)

        assert (output_dir / "skills" / "my-skill" / "SKILL.md").read_text(encoding="utf-8") == dedent("""            ---
            name: my-skill
            ---
            Body: {{ 2 + 2 }}""")

    # ----------------------------------------------------------------------
    def test_copies_non_template_byte_for_byte(self, tmp_path: Path, dm: DoneManager):
        agent = _MakeAgent(project_skill_template="skills/{skill_name}/SKILL.md")
        output_dir = tmp_path / "out"

        payload = b"---\nname: my-skill\n\n---\n\nBody\n\n"

        file = tmp_path / "SKILL.md"
        file.write_bytes(payload)

        RenderLocalSkill(dm, file, agent, output_dir)

        written = output_dir / "skills" / "my-skill" / "SKILL.md"

        assert not written.is_symlink()
        assert written.read_bytes() == payload

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

        written = tmp_path / "skills" / "my-skill" / "SKILL.md"

        assert not written.is_symlink()
        assert written.read_text(encoding="utf-8") == dedent("""\
            ---
            name: my-skill
            ---
            Body: 2""")

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_links_non_template(self, tmp_path: Path, monkeypatch, dm: DoneManager):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeAgent(global_skill_template="~/skills/{skill_name}/SKILL.md")

        source = tmp_path / "review_skill.md"
        source.write_text("---\nname: my-skill\n---\nBody\n", encoding="utf-8")

        RenderGlobalSkill(dm, source, agent)

        written = tmp_path / "skills" / "my-skill" / "SKILL.md"

        assert written.is_symlink()
        assert written.resolve() == source.resolve()

    # ----------------------------------------------------------------------
    def test_copy_writes_non_template_byte_for_byte(self, tmp_path: Path, monkeypatch, dm: DoneManager):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeAgent(global_skill_template="~/skills/{skill_name}/SKILL.md")

        payload = b"---\nname: my-skill\n---\nBody\n"

        source = tmp_path / "review_skill.md"
        source.write_bytes(payload)

        RenderGlobalSkill(dm, source, agent, copy=True)

        written = tmp_path / "skills" / "my-skill" / "SKILL.md"

        assert not written.is_symlink()
        assert written.read_bytes() == payload

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlink_failure")
    def test_link_failure_writes_error(self, tmp_path: Path, monkeypatch):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeAgent(global_skill_template="~/skills/{skill_name}/SKILL.md")

        source = tmp_path / "review_skill.md"
        source.write_text("---\nname: my-skill\n---\nBody\n", encoding="utf-8")

        content = _RunCapturingContent(lambda dm: RenderGlobalSkill(dm, source, agent))

        written = tmp_path / "skills" / "my-skill" / "SKILL.md"

        assert content == dedent(f"""\
            Heading...
              Linking '{written}' to '{source.resolve()}'...
                ERROR: A symbolic link to '{source.resolve()}' could not be created at '{written}' (Symbolic links are unavailable.); enable 'copy' to copy it instead.
              DONE! (-1, <scrubbed duration>)
            DONE! (-1, <scrubbed duration>)
            """)
        assert list(written.parent.iterdir()) == []

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
        assert list(tmp_path.iterdir()) == [tmp_path / "template.jinja.md"]

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
def _MakeNestedSkillAgent(*, supports_skills: bool = True) -> Agent:
    """Create an `Agent` that stores each skill in its own directory beneath a skills root.

    This is the layout every shipped agent uses, and the only one for which a skill owns a
    directory that supporting files can be written into.
    """

    if not supports_skills:
        return _MakeAgent()

    return _MakeAgent(
        global_skill_template="~/skills/{skill_name}/SKILL.md",
        project_skill_template="skills/{skill_name}/SKILL.md",
        global_skills_root="~/skills",
        project_skills_root="skills",
    )


# ----------------------------------------------------------------------
@pytest.fixture
def skill_dir(tmp_path: Path):
    """Factory fixture that writes files into a skill template directory and returns its path."""

    def _create(files: dict[str, str], skill_name: str = "my-skill") -> Path:
        root = tmp_path / "templates" / skill_name

        for relative_path, content in files.items():
            file = root / relative_path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(content, encoding="utf-8")

        return root

    return _create


# ----------------------------------------------------------------------
class TestRenderLocalSkillDirectory:
    # ----------------------------------------------------------------------
    def test_writes_every_file_under_skill_named_by_directory(
        self, skill_dir, tmp_path: Path, dm: DoneManager
    ):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        RenderLocalSkill(dm, skill_dir({"SKILL.md": "Body", "reference.md": "Reference"}), agent, output_dir)

        destination = output_dir / "skills" / "my-skill"

        assert destination.joinpath("SKILL.md").read_text(encoding="utf-8") == "Body"
        assert destination.joinpath("reference.md").read_text(encoding="utf-8") == "Reference"

    # ----------------------------------------------------------------------
    def test_renders_template_files(self, skill_dir, tmp_path: Path, dm: DoneManager):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        RenderLocalSkill(
            dm,
            skill_dir(
                {"SKILL.jinja.md": "Body: {{ 2 + 2 }}", "reference.jinja2.md": "Reference: {{ 3 * 3 }}"}
            ),
            agent,
            output_dir,
        )

        destination = output_dir / "skills" / "my-skill"

        assert destination.joinpath("SKILL.md").read_text(encoding="utf-8") == "Body: 4"
        assert destination.joinpath("reference.md").read_text(encoding="utf-8") == "Reference: 9"

    # ----------------------------------------------------------------------
    def test_preserves_frontmatter_of_each_file(self, skill_dir, tmp_path: Path, dm: DoneManager):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        RenderLocalSkill(
            dm,
            skill_dir(
                {
                    "SKILL.jinja.md": dedent("""\
                        ---
                        name: ignored-name
                        ---
                        Body: {{ 1 + 1 }}"""),
                },
            ),
            agent,
            output_dir,
        )

        assert (output_dir / "skills" / "my-skill" / "SKILL.md").read_text(encoding="utf-8") == dedent("""\
            ---
            name: ignored-name
            ---
            Body: 2""")

    # ----------------------------------------------------------------------
    def test_preserves_nested_directory_structure(self, skill_dir, tmp_path: Path, dm: DoneManager):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        RenderLocalSkill(
            dm,
            skill_dir({"SKILL.md": "Body", "scripts/run.py": "value = {{ 5 }}"}),
            agent,
            output_dir,
        )

        destination = output_dir / "skills" / "my-skill"

        assert destination.joinpath("SKILL.md").read_text(encoding="utf-8") == "Body"

        # `run.py` is not a template, so its Jinja-like content is preserved verbatim.
        assert destination.joinpath("scripts", "run.py").read_text(encoding="utf-8") == "value = {{ 5 }}"

    # ----------------------------------------------------------------------
    def test_directory_name_determines_skill_name(self, skill_dir, tmp_path: Path, dm: DoneManager):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        RenderLocalSkill(
            dm,
            skill_dir(
                {
                    "SKILL.md": dedent("""\
                        ---
                        name: frontmatter-name
                        ---
                        Body"""),
                },
                skill_name="directory-name",
            ),
            agent,
            output_dir,
        )

        assert (output_dir / "skills" / "directory-name" / "SKILL.md").is_file()
        assert not (output_dir / "skills" / "frontmatter-name").exists()

    # ----------------------------------------------------------------------
    def test_writes_each_written_file_to_the_done_manager(self, skill_dir, tmp_path: Path):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"
        template_path = skill_dir({"SKILL.md": "Body", "reference.md": "Reference"})

        content = _RunCapturingContent(lambda dm: RenderLocalSkill(dm, template_path, agent, output_dir))

        destination = output_dir / "skills" / "my-skill"

        assert content == dedent(f"""\
            Heading...
              Writing '{destination / "SKILL.md"}'...DONE! (0, <scrubbed duration>)
              Writing '{destination / "reference.md"}'...DONE! (0, <scrubbed duration>)
            DONE! (0, <scrubbed duration>)
            """)

    # ----------------------------------------------------------------------
    def test_writes_files_in_output_path_order(self, skill_dir, tmp_path: Path):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        # `b-c` sorts before `b.jinja` but after its output `b`, so ordering by source path would
        # write `b-c` first.
        template_path = skill_dir({"SKILL.md": "Body", "b.jinja": "B", "b-c": "C"})

        content = _RunCapturingContent(lambda dm: RenderLocalSkill(dm, template_path, agent, output_dir))

        destination = output_dir / "skills" / "my-skill"

        assert content == dedent(f"""\
            Heading...
              Writing '{destination / "SKILL.md"}'...DONE! (0, <scrubbed duration>)
              Writing '{destination / "b"}'...DONE! (0, <scrubbed duration>)
              Writing '{destination / "b-c"}'...DONE! (0, <scrubbed duration>)
            DONE! (0, <scrubbed duration>)
            """)

    # ----------------------------------------------------------------------
    def test_unsupported_agent_writes_error(self, skill_dir, tmp_path: Path):
        agent = _MakeNestedSkillAgent(supports_skills=False)
        output_dir = tmp_path / "out"
        template_path = skill_dir({"SKILL.md": "Body"})

        content = _RunCapturingContent(lambda dm: RenderLocalSkill(dm, template_path, agent, output_dir))

        assert content == _ExpectedError("The 'Stub' agent does not support skills.")
        assert not output_dir.exists()

    # ----------------------------------------------------------------------
    def test_empty_directory_writes_error(self, tmp_path: Path):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"
        template_path = tmp_path / "templates" / "my-skill"
        template_path.mkdir(parents=True)

        content = _RunCapturingContent(lambda dm: RenderLocalSkill(dm, template_path, agent, output_dir))

        assert content == _ExpectedError(f"The skill template directory '{template_path}' is empty.")
        assert not output_dir.exists()

    # ----------------------------------------------------------------------
    def test_invalid_directory_name_writes_error(self, tmp_path: Path):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        templates = tmp_path / "templates"
        templates.mkdir(parents=True)
        (tmp_path / "escaped.md").write_text("Escaped", encoding="utf-8")

        # A directory whose name is '..' would otherwise resolve to a destination outside of the
        # agent's skills root.
        template_path = Path(str(templates)) / ".."

        content = _RunCapturingContent(lambda dm: RenderLocalSkill(dm, template_path, agent, output_dir))

        assert content == _ExpectedError("Invalid skill name '..'.")
        assert not output_dir.exists()

    # ----------------------------------------------------------------------
    def test_flat_layout_agent_writes_error(self, skill_dir, tmp_path: Path):
        # This agent stores each skill as a single file directly in the skills root, so a skill
        # owns no directory of its own; writing the template's files would put them in the root
        # shared by every skill.
        agent = _MakeAgent(
            project_skill_template="skills/{skill_name}.md",
            project_skills_root="skills",
        )
        output_dir = tmp_path / "out"
        template_path = skill_dir({"SKILL.md": "Body"})

        content = _RunCapturingContent(lambda dm: RenderLocalSkill(dm, template_path, agent, output_dir))

        assert content == _ExpectedError(
            f"The 'Stub' agent stores each skill as a single file, so it cannot render the skill template directory '{template_path}'."
        )
        assert not output_dir.exists()

    # ----------------------------------------------------------------------
    def test_missing_skill_file_writes_error(self, skill_dir, tmp_path: Path):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        # Without `SKILL.md` the installed directory is not a skill the agent can load.
        template_path = skill_dir({"reference.md": "Reference"})

        content = _RunCapturingContent(lambda dm: RenderLocalSkill(dm, template_path, agent, output_dir))

        assert content == _ExpectedError(
            f"The skill template directory '{template_path}' does not contain 'SKILL.md'."
        )
        assert not output_dir.exists()

    # ----------------------------------------------------------------------
    def test_nested_skill_file_does_not_satisfy_the_requirement(self, skill_dir, tmp_path: Path):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        # `SKILL.md` must sit at the root of the template directory; one nested beneath it lands
        # somewhere the agent does not read.
        template_path = skill_dir({"nested/SKILL.md": "Body"})

        content = _RunCapturingContent(lambda dm: RenderLocalSkill(dm, template_path, agent, output_dir))

        assert content == _ExpectedError(
            f"The skill template directory '{template_path}' does not contain 'SKILL.md'."
        )
        assert not output_dir.exists()

    # ----------------------------------------------------------------------
    def test_template_suffixes_are_removed_from_output_filenames(
        self, skill_dir, tmp_path: Path, dm: DoneManager
    ):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        # `SKILL.jinja.md` satisfies the `SKILL.md` requirement because it is written as `SKILL.md`.
        RenderLocalSkill(
            dm,
            skill_dir(
                {
                    "SKILL.jinja.md": "Body: {{ 1 + 1 }}",
                    "scripts/run.jinja2.py": "value = {{ 5 }}",
                    "notes.jinja": "Notes: {{ 2 * 3 }}",
                },
            ),
            agent,
            output_dir,
        )

        destination = output_dir / "skills" / "my-skill"

        assert sorted(
            path.relative_to(destination).as_posix() for path in destination.rglob("*") if path.is_file()
        ) == ["SKILL.md", "notes", "scripts/run.py"]
        assert destination.joinpath("SKILL.md").read_text(encoding="utf-8") == "Body: 2"
        assert destination.joinpath("scripts", "run.py").read_text(encoding="utf-8") == "value = 5"
        assert destination.joinpath("notes").read_text(encoding="utf-8") == "Notes: 6"

    # ----------------------------------------------------------------------
    def test_output_filename_collision_writes_error(self, skill_dir, tmp_path: Path):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        template_path = skill_dir(
            {
                "SKILL.md": "Body",
                "SKILL.jinja.md": "Body",
                "SKILL.jinja2.md": "Body",
                "reference.md": "Reference",
            },
        )

        content = _RunCapturingContent(lambda dm: RenderLocalSkill(dm, template_path, agent, output_dir))

        assert content == _ExpectedError(
            f"The skill template directory '{template_path}' contains multiple files that render to 'SKILL.md': 'SKILL.jinja.md', 'SKILL.jinja2.md', 'SKILL.md'."
        )
        assert not output_dir.exists()

    # ----------------------------------------------------------------------
    def test_output_file_and_directory_collision_writes_error(self, skill_dir, tmp_path: Path):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        template_path = skill_dir(
            {"SKILL.md": "Body", "scripts.jinja": "Scripts", "scripts/run.py": "run()"},
        )

        content = _RunCapturingContent(lambda dm: RenderLocalSkill(dm, template_path, agent, output_dir))

        assert content == _ExpectedError(
            f"The skill template directory '{template_path}' contains 'scripts.jinja', which renders to 'scripts', but 'scripts' is also a directory."
        )
        assert not output_dir.exists()

    # ----------------------------------------------------------------------
    def test_copies_non_template_files_verbatim(self, skill_dir, tmp_path: Path, dm: DoneManager):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        template_path = skill_dir({"SKILL.jinja.md": "Body: {{ 1 + 1 }}"})

        # Files that are not templates must survive unchanged, even when their content would
        # otherwise be consumed by Jinja or by frontmatter extraction.
        (template_path / "script.js").write_text("// {{ not_a_template }}", encoding="utf-8")
        (template_path / "data.yaml").write_text("---\nkey: value\n", encoding="utf-8")
        (template_path / "invalid.hbs").write_text("{% not_a_jinja_tag %}", encoding="utf-8")
        (template_path / "reference.md").write_text("---\nkey: value\n---\n{{ 1 + 1 }}\n", encoding="utf-8")

        RenderLocalSkill(dm, template_path, agent, output_dir)

        destination = output_dir / "skills" / "my-skill"

        assert destination.joinpath("SKILL.md").read_text(encoding="utf-8") == "Body: 2"
        assert (
            destination.joinpath("reference.md").read_text(encoding="utf-8")
            == "---\nkey: value\n---\n{{ 1 + 1 }}\n"
        )
        assert destination.joinpath("script.js").read_text(encoding="utf-8") == "// {{ not_a_template }}"
        assert destination.joinpath("data.yaml").read_text(encoding="utf-8") == "---\nkey: value\n"
        assert destination.joinpath("invalid.hbs").read_text(encoding="utf-8") == "{% not_a_jinja_tag %}"
        assert not any(path.is_symlink() for path in destination.iterdir())

    # ----------------------------------------------------------------------
    def test_copies_binary_files_byte_for_byte(self, skill_dir, tmp_path: Path, dm: DoneManager):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        template_path = skill_dir({"SKILL.md": "Body"})

        # Binary assets are not decodable as UTF-8, so rendering them would fail outright.
        payload = bytes(range(256))
        (template_path / "logo.png").write_bytes(payload)

        RenderLocalSkill(dm, template_path, agent, output_dir)

        assert (output_dir / "skills" / "my-skill" / "logo.png").read_bytes() == payload

    # ----------------------------------------------------------------------
    def test_render_failure_writes_nothing(self, skill_dir, tmp_path: Path):
        agent = _MakeNestedSkillAgent()
        output_dir = tmp_path / "out"

        # `zzz.jinja.md` sorts after `aaa.jinja.md`, so a naive implementation would write `aaa.md` before
        # failing and leave a partially installed skill behind.
        template_path = skill_dir(
            {"aaa.jinja.md": "Valid", "SKILL.md": "Body", "zzz.jinja.md": "{% not_a_jinja_tag %}"},
        )

        with pytest.raises(RenderError) as exc_info:
            _RunCapturingContent(lambda dm: RenderLocalSkill(dm, template_path, agent, output_dir))

        assert exc_info.value.filename == template_path / "zzz.jinja.md"
        assert not output_dir.exists()


# ----------------------------------------------------------------------
class TestRenderGlobalSkillDirectory:
    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_writes_every_file_under_skill_named_by_directory(
        self, skill_dir, tmp_path: Path, monkeypatch, dm: DoneManager
    ):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent()

        RenderGlobalSkill(
            dm,
            skill_dir({"SKILL.jinja.md": "Body: {{ 1 + 1 }}", "reference.md": "Reference"}),
            agent,
        )

        destination = tmp_path / "skills" / "my-skill"

        assert destination.joinpath("SKILL.md").read_text(encoding="utf-8") == "Body: 2"
        assert destination.joinpath("reference.md").read_text(encoding="utf-8") == "Reference"

    # ----------------------------------------------------------------------
    def test_unsupported_agent_writes_error(self, skill_dir, tmp_path: Path, monkeypatch):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent(supports_skills=False)
        template_path = skill_dir({"SKILL.md": "Body"})

        content = _RunCapturingContent(lambda dm: RenderGlobalSkill(dm, template_path, agent))

        assert content == _ExpectedError("The 'Stub' agent does not support skills.")
        assert not (tmp_path / "skills").exists()

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_links_non_template_files_and_writes_templates(self, skill_dir, tmp_path: Path, monkeypatch):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent()
        template_path = skill_dir(
            {"SKILL.jinja.md": "Body: {{ 1 + 1 }}", "reference.md": "Reference", "scripts/check.py": "pass"},
        )

        content = _RunCapturingContent(lambda dm: RenderGlobalSkill(dm, template_path, agent))

        destination = tmp_path / "skills" / "my-skill"
        resolved = template_path.resolve()

        # Links are created before any file is written.
        assert content == dedent(f"""\
            Heading...
              Linking '{destination / "reference.md"}' to '{resolved / "reference.md"}'...DONE! (0, <scrubbed duration>)
              Linking '{destination / "scripts" / "check.py"}' to '{resolved / "scripts" / "check.py"}'...DONE! (0, <scrubbed duration>)
              Writing '{destination / "SKILL.md"}'...DONE! (0, <scrubbed duration>)
            DONE! (0, <scrubbed duration>)
            """)

        assert not destination.joinpath("SKILL.md").is_symlink()
        assert destination.joinpath("SKILL.md").read_text(encoding="utf-8") == "Body: 2"
        assert destination.joinpath("reference.md").resolve() == resolved / "reference.md"
        assert destination.joinpath("scripts", "check.py").resolve() == resolved / "scripts" / "check.py"

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_links_directory_without_templates(self, skill_dir, tmp_path: Path, monkeypatch):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent()
        template_path = skill_dir({"SKILL.md": "Body", "scripts/check.py": "pass"})

        content = _RunCapturingContent(lambda dm: RenderGlobalSkill(dm, template_path, agent))

        destination = tmp_path / "skills" / "my-skill"
        resolved = template_path.resolve()

        assert content == dedent(f"""\
            Heading...
              Linking '{destination}' to '{resolved}'...DONE! (0, <scrubbed duration>)
            DONE! (0, <scrubbed duration>)
            """)

        assert destination.is_symlink()
        assert destination.resolve() == resolved

        # Files added to the source after rendering are visible without rendering again.
        (template_path / "reference.md").write_text("Reference", encoding="utf-8")

        assert destination.joinpath("reference.md").read_text(encoding="utf-8") == "Reference"

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_link_replaces_existing_directory(self, skill_dir, tmp_path: Path, monkeypatch, dm: DoneManager):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent()
        template_path = skill_dir({"SKILL.md": "Body"})

        destination = tmp_path / "skills" / "my-skill"
        destination.mkdir(parents=True)
        (destination / "SKILL.md").write_text("Stale", encoding="utf-8")
        (destination / "removed.md").write_text("Removed", encoding="utf-8")

        RenderGlobalSkill(dm, template_path, agent)

        assert destination.is_symlink()
        assert sorted(path.name for path in destination.iterdir()) == ["SKILL.md"]
        assert destination.joinpath("SKILL.md").read_text(encoding="utf-8") == "Body"

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_link_replaces_link_to_other_directory(
        self, skill_dir, tmp_path: Path, monkeypatch, dm: DoneManager
    ):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent()
        original = skill_dir({"SKILL.md": "Original"})

        replacement = tmp_path / "other" / "my-skill"
        replacement.mkdir(parents=True)
        (replacement / "SKILL.md").write_text("Replacement", encoding="utf-8")

        RenderGlobalSkill(dm, original, agent)
        RenderGlobalSkill(dm, replacement, agent)

        destination = tmp_path / "skills" / "my-skill"

        assert destination.resolve() == replacement.resolve()
        assert (original / "SKILL.md").read_text(encoding="utf-8") == "Original"

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_templates_replace_previously_linked_directory(
        self, skill_dir, tmp_path: Path, monkeypatch, dm: DoneManager
    ):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent()
        template_path = skill_dir({"SKILL.md": "Body"})

        RenderGlobalSkill(dm, template_path, agent)

        (template_path / "extra.jinja.md").write_text("Extra: {{ 1 + 1 }}", encoding="utf-8")

        RenderGlobalSkill(dm, template_path, agent)

        destination = tmp_path / "skills" / "my-skill"

        assert not destination.is_symlink()
        assert destination.joinpath("extra.md").read_text(encoding="utf-8") == "Extra: 2"
        assert destination.joinpath("SKILL.md").resolve() == template_path.resolve() / "SKILL.md"
        assert sorted(path.name for path in template_path.iterdir()) == ["SKILL.md", "extra.jinja.md"]

    # ----------------------------------------------------------------------
    def test_link_over_directory_containing_source_writes_error(self, tmp_path: Path, monkeypatch):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent()

        destination = tmp_path / "skills" / "my-skill"
        template_path = destination / "sources" / "my-skill"
        template_path.mkdir(parents=True)
        (template_path / "SKILL.md").write_text("Body", encoding="utf-8")

        content = _RunCapturingContent(lambda dm: RenderGlobalSkill(dm, template_path, agent))

        resolved = template_path.resolve()

        assert content == dedent(f"""\
            Heading...
              Linking '{destination}' to '{resolved}'...
                ERROR: '{destination}' cannot be replaced by a symbolic link to '{resolved}' because it contains '{resolved}'.
              DONE! (-1, <scrubbed duration>)
            DONE! (-1, <scrubbed duration>)
            """)
        assert (template_path / "SKILL.md").read_text(encoding="utf-8") == "Body"

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_link_replaces_link_to_directory_containing_source(
        self, tmp_path: Path, monkeypatch, dm: DoneManager
    ):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent()

        other = tmp_path / "other"
        template_path = other / "sources" / "my-skill"
        template_path.mkdir(parents=True)
        (template_path / "SKILL.md").write_text("Body", encoding="utf-8")

        destination = tmp_path / "skills" / "my-skill"
        destination.parent.mkdir(parents=True)
        destination.symlink_to(other, target_is_directory=True)

        RenderGlobalSkill(dm, template_path, agent)

        assert destination.resolve() == template_path.resolve()
        assert (template_path / "SKILL.md").read_text(encoding="utf-8") == "Body"

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_rendering_linked_directory_again_preserves_link(
        self, skill_dir, tmp_path: Path, monkeypatch, dm: DoneManager
    ):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent()
        template_path = skill_dir({"SKILL.md": "Body"})

        RenderGlobalSkill(dm, template_path, agent)

        content = _RunCapturingContent(lambda dm: RenderGlobalSkill(dm, template_path, agent))

        destination = tmp_path / "skills" / "my-skill"
        resolved = template_path.resolve()

        assert content == dedent(f"""\
            Heading...
              Linking '{destination}' to '{resolved}'...DONE! (0, <scrubbed duration>)
            DONE! (0, <scrubbed duration>)
            """)
        assert destination.is_symlink()
        assert destination.resolve() == resolved
        assert (template_path / "SKILL.md").read_text(encoding="utf-8") == "Body"

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlinks")
    def test_file_link_over_directory_preserves_directory(
        self, skill_dir, tmp_path: Path, monkeypatch, dm: DoneManager
    ):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent()
        template_path = skill_dir({"SKILL.jinja.md": "Body", "reference.md": "Reference"})

        existing = tmp_path / "skills" / "my-skill" / "reference.md"
        existing.mkdir(parents=True)
        (existing / "notes.md").write_text("Notes", encoding="utf-8")

        with pytest.raises(OSError):
            RenderGlobalSkill(dm, template_path, agent)

        assert (existing / "notes.md").read_text(encoding="utf-8") == "Notes"

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlink_failure")
    def test_directory_link_failure_preserves_existing_directory(
        self, skill_dir, tmp_path: Path, monkeypatch
    ):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent()
        template_path = skill_dir({"SKILL.md": "Body"})

        destination = tmp_path / "skills" / "my-skill"
        destination.mkdir(parents=True)
        (destination / "SKILL.md").write_text("Existing", encoding="utf-8")

        content = _RunCapturingContent(lambda dm: RenderGlobalSkill(dm, template_path, agent))

        resolved = template_path.resolve()

        assert content == dedent(f"""\
            Heading...
              Linking '{destination}' to '{resolved}'...
                ERROR: A symbolic link to '{resolved}' could not be created at '{destination}' (Symbolic links are unavailable.); enable 'copy' to copy it instead.
              DONE! (-1, <scrubbed duration>)
            DONE! (-1, <scrubbed duration>)
            """)
        assert (destination / "SKILL.md").read_text(encoding="utf-8") == "Existing"

    # ----------------------------------------------------------------------
    def test_copy_writes_every_file(self, skill_dir, tmp_path: Path, monkeypatch, dm: DoneManager):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent()

        RenderGlobalSkill(
            dm,
            skill_dir({"SKILL.jinja.md": "Body: {{ 1 + 1 }}", "reference.md": "Reference"}),
            agent,
            copy=True,
        )

        destination = tmp_path / "skills" / "my-skill"

        assert not destination.joinpath("SKILL.md").is_symlink()
        assert not destination.joinpath("reference.md").is_symlink()
        assert destination.joinpath("SKILL.md").read_text(encoding="utf-8") == "Body: 2"
        assert destination.joinpath("reference.md").read_text(encoding="utf-8") == "Reference"

    # ----------------------------------------------------------------------
    @pytest.mark.usefixtures("symlink_failure")
    def test_link_failure_writes_no_files(self, skill_dir, tmp_path: Path, monkeypatch):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent()
        template_path = skill_dir({"SKILL.jinja.md": "Body", "reference.md": "Reference"})

        content = _RunCapturingContent(lambda dm: RenderGlobalSkill(dm, template_path, agent))

        link = tmp_path / "skills" / "my-skill" / "reference.md"
        source = template_path.resolve() / "reference.md"

        assert content == dedent(f"""\
            Heading...
              Linking '{link}' to '{source}'...
                ERROR: A symbolic link to '{source}' could not be created at '{link}' (Symbolic links are unavailable.); enable 'copy' to copy it instead.
              DONE! (-1, <scrubbed duration>)
            DONE! (-1, <scrubbed duration>)
            """)
        assert list(link.parent.iterdir()) == []

    # ----------------------------------------------------------------------
    def test_render_failure_links_nothing(self, skill_dir, tmp_path: Path, monkeypatch):
        for var in ("HOME", "USERPROFILE", "APPDATA"):
            monkeypatch.setenv(var, str(tmp_path))

        agent = _MakeNestedSkillAgent()
        template_path = skill_dir({"SKILL.jinja.md": "{% not_a_jinja_tag %}", "reference.md": "Reference"})

        with pytest.raises(RenderError):
            _RunCapturingContent(lambda dm: RenderGlobalSkill(dm, template_path, agent))

        assert not (tmp_path / "skills").exists()


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
