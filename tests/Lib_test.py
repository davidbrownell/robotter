"""Unit tests for robotter.Lib"""

from collections.abc import Iterator
from pathlib import Path
from textwrap import dedent

import pytest

from robotter.agents.Agent import Agent, OperatingSystem
from robotter.Lib import RenderGlobal, RenderLocal


# ----------------------------------------------------------------------
def _MakeAgent(
    *,
    project_paths: tuple[str, ...] = (),
    global_paths: tuple[str, ...] = (),
) -> Agent:
    """Create an `Agent` whose configuration paths are exactly the ones provided."""

    class _StubAgent(Agent):
        name = "Stub"

        @staticmethod
        def _EnumGlobalConfigurationPaths(operating_system: OperatingSystem) -> Iterator[str]:  # noqa: ARG004
            yield from global_paths

        @staticmethod
        def _EnumProjectConfigurationNames() -> Iterator[str]:
            yield from project_paths

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
