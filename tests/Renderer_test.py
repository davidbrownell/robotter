"""Unit tests for robotter.Renderer"""

import copy

from pathlib import Path
from textwrap import dedent

import pytest
from jinja2 import Environment

from robotter.Renderer import GetOutputPath, IsTemplate, Parse, RenderError


# ----------------------------------------------------------------------
@pytest.fixture
def env() -> Environment:
    return Environment()


# ----------------------------------------------------------------------
@pytest.fixture
def tmp_file(tmp_path: Path):
    """Factory fixture for creating temporary files with content."""

    def _create(content: str) -> Path:
        file = tmp_path / "test_file.jinja.txt"
        file.write_text(content)
        return file

    return _create


# ----------------------------------------------------------------------
class TestParse:
    # ----------------------------------------------------------------------
    def test_content_without_frontmatter(self, env: Environment, tmp_file):
        content = "Hello, world!"
        file = tmp_file(content)

        frontmatter, rendered = Parse(env, file)

        assert frontmatter is None
        assert rendered == "Hello, world!"
        assert isinstance(rendered, str)

    # ----------------------------------------------------------------------
    def test_content_with_frontmatter(self, env: Environment, tmp_file):
        content = dedent("""\
            ---
            title: My Title
            author: Test Author
            ---
            Main content here.""")
        file = tmp_file(content)

        frontmatter, rendered = Parse(env, file)

        assert frontmatter == dedent("""\
            title: My Title
            author: Test Author""")
        assert rendered == "Main content here."

    # ----------------------------------------------------------------------
    def test_frontmatter_is_stripped(self, env: Environment, tmp_file):
        content = dedent("""\
            ---
               spaced content
            ---
            body""")
        file = tmp_file(content)

        frontmatter, rendered = Parse(env, file)

        assert frontmatter == "spaced content"
        assert rendered == "body"

    # ----------------------------------------------------------------------
    def test_content_starting_with_dashes_but_no_closing(self, env: Environment, tmp_file):
        content = dedent("""\
            ---
            not really frontmatter because no closing dashes""")
        file = tmp_file(content)

        frontmatter, rendered = Parse(env, file)

        assert frontmatter is None
        assert rendered == dedent("""\
            ---
            not really frontmatter because no closing dashes""")

    # ----------------------------------------------------------------------
    def test_jinja2_template_rendering(self, env: Environment, tmp_file):
        content = "Value: {{ 1 + 2 }}"
        file = tmp_file(content)

        frontmatter, rendered = Parse(env, file)

        assert frontmatter is None
        assert rendered == "Value: 3"

    # ----------------------------------------------------------------------
    def test_jinja2_template_in_content_with_frontmatter(self, env: Environment, tmp_file):
        content = dedent("""\
            ---
            key: value
            ---
            Sum: {{ 5 + 5 }}""")
        file = tmp_file(content)

        frontmatter, rendered = Parse(env, file)

        assert frontmatter == "key: value"
        assert rendered == "Sum: 10"

    # ----------------------------------------------------------------------
    def test_frontmatter_not_rendered_as_jinja2(self, env: Environment, tmp_file):
        content = dedent("""\
            ---
            template: {{ not_rendered }}
            ---
            Body content""")
        file = tmp_file(content)

        frontmatter, rendered = Parse(env, file)

        assert frontmatter == "template: {{ not_rendered }}"
        assert rendered == "Body content"

    # ----------------------------------------------------------------------
    def test_empty_frontmatter(self, env: Environment, tmp_file):
        content = dedent("""\
            ---
            ---
            Content after empty frontmatter""")
        file = tmp_file(content)

        frontmatter, rendered = Parse(env, file)

        assert frontmatter == ""
        assert rendered == "Content after empty frontmatter"

    # ----------------------------------------------------------------------
    def test_empty_content_after_frontmatter(self, env: Environment, tmp_file):
        content = dedent("""\
            ---
            only: frontmatter
            ---
            """)
        file = tmp_file(content)

        frontmatter, rendered = Parse(env, file)

        assert frontmatter == "only: frontmatter"
        assert rendered == ""

    # ----------------------------------------------------------------------
    def test_multiple_triple_dashes_in_content(self, env: Environment, tmp_file):
        content = dedent("""\
            ---
            frontmatter
            ---
            content with --- dashes --- inside""")
        file = tmp_file(content)

        frontmatter, rendered = Parse(env, file)

        assert frontmatter == "frontmatter"
        assert rendered == "content with --- dashes --- inside"

    # ----------------------------------------------------------------------
    def test_return_type_is_rendered_template(self, env: Environment, tmp_file):
        content = "simple content"
        file = tmp_file(content)

        _, rendered = Parse(env, file)

        assert isinstance(rendered, str)

    # ----------------------------------------------------------------------
    def test_whitespace_only_content(self, env: Environment, tmp_file):
        content = dedent("""\

            \t
               """)
        file = tmp_file(content)

        frontmatter, rendered = Parse(env, file)

        assert frontmatter is None
        assert rendered == ""

    # ----------------------------------------------------------------------
    def test_jinja2_control_structures(self, env: Environment, tmp_file):
        content = "{% for i in range(3) %}{{ i }}{% endfor %}"
        file = tmp_file(content)

        frontmatter, rendered = Parse(env, file)

        assert frontmatter is None
        assert rendered == "012"

    # ----------------------------------------------------------------------
    class TestIncludeConfiguration:
        # ----------------------------------------------------------------------
        def test_include_simple_file(self, env: Environment, tmp_path: Path):
            included_file = tmp_path / "included.jinja.txt"
            included_file.write_text("Included content")

            main_file = tmp_path / "main.jinja.txt"
            main_file.write_text("Before {{ include_configuration('included.jinja.txt') }} After")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "Before Included content After"

        # ----------------------------------------------------------------------
        def test_include_file_with_frontmatter_ignores_frontmatter(self, env: Environment, tmp_path: Path):
            included_file = tmp_path / "included.jinja.txt"
            included_file.write_text(
                dedent("""\
                ---
                title: Should Be Ignored
                ---
                Only this content""")
            )

            main_file = tmp_path / "main.jinja.txt"
            main_file.write_text("{{ include_configuration('included.jinja.txt') }}")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "Only this content"

        # ----------------------------------------------------------------------
        def test_include_file_in_subdirectory(self, env: Environment, tmp_path: Path):
            subdir = tmp_path / "subdir"
            subdir.mkdir()

            included_file = subdir / "nested.jinja.txt"
            included_file.write_text("Nested content")

            main_file = tmp_path / "main.jinja.txt"
            main_file.write_text("{{ include_configuration('subdir/nested.jinja.txt') }}")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "Nested content"

        # ----------------------------------------------------------------------
        def test_include_file_with_jinja2_template(self, env: Environment, tmp_path: Path):
            included_file = tmp_path / "included.jinja.txt"
            included_file.write_text("Result: {{ 2 * 3 }}")

            main_file = tmp_path / "main.jinja.txt"
            main_file.write_text("{{ include_configuration('included.jinja.txt') }}")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "Result: 6"

        # ----------------------------------------------------------------------
        def test_nested_include_configuration(self, env: Environment, tmp_path: Path):
            level2_file = tmp_path / "level2.jinja.txt"
            level2_file.write_text("Level 2")

            level1_file = tmp_path / "level1.jinja.txt"
            level1_file.write_text("[{{ include_configuration('level2.jinja.txt') }}]")

            main_file = tmp_path / "main.jinja.txt"
            main_file.write_text("Main: {{ include_configuration('level1.jinja.txt') }}")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "Main: [Level 2]"

        # ----------------------------------------------------------------------
        def test_include_relative_from_subdirectory(self, env: Environment, tmp_path: Path):
            subdir = tmp_path / "subdir"
            subdir.mkdir()

            sibling_file = subdir / "sibling.jinja.txt"
            sibling_file.write_text("Sibling content")

            main_file = subdir / "main.jinja.txt"
            main_file.write_text("{{ include_configuration('sibling.jinja.txt') }}")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "Sibling content"

        # ----------------------------------------------------------------------
        def test_include_parent_directory_file(self, env: Environment, tmp_path: Path):
            parent_file = tmp_path / "parent.jinja.txt"
            parent_file.write_text("Parent content")

            subdir = tmp_path / "subdir"
            subdir.mkdir()

            main_file = subdir / "main.jinja.txt"
            main_file.write_text("{{ include_configuration('../parent.jinja.txt') }}")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "Parent content"

        # ----------------------------------------------------------------------
        def test_multiple_includes_in_same_file(self, env: Environment, tmp_path: Path):
            file_a = tmp_path / "a.jinja.txt"
            file_a.write_text("A")

            file_b = tmp_path / "b.jinja.txt"
            file_b.write_text("B")

            main_file = tmp_path / "main.jinja.txt"
            main_file.write_text(
                "{{ include_configuration('a.jinja.txt') }}-{{ include_configuration('b.jinja.txt') }}"
            )

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "A-B"

        # ----------------------------------------------------------------------
        def test_include_nonexistent_file_raises_error(self, env: Environment, tmp_path: Path):
            main_file = tmp_path / "main.jinja.txt"
            main_file.write_text("{{ include_configuration('does_not_exist.jinja.txt') }}")

            with pytest.raises(RenderError) as exc_info:
                Parse(env, main_file)

            assert exc_info.value.filename == tmp_path / "does_not_exist.jinja.txt"
            assert isinstance(exc_info.value.__cause__, FileNotFoundError)

        # ----------------------------------------------------------------------
        def test_include_with_main_file_having_frontmatter(self, env: Environment, tmp_path: Path):
            included_file = tmp_path / "included.jinja.txt"
            included_file.write_text("Included")

            main_file = tmp_path / "main.jinja.txt"
            main_file.write_text(
                dedent("""\
                ---
                main: frontmatter
                ---
                Content: {{ include_configuration('included.jinja.txt') }}""")
            )

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter == "main: frontmatter"
            assert rendered == "Content: Included"


# ----------------------------------------------------------------------
class TestRenderError:
    # ----------------------------------------------------------------------
    def test_syntax_error_includes_filename(self, env: Environment, tmp_file):
        file = tmp_file("Hello {% bogus %}")

        with pytest.raises(RenderError) as exc_info:
            Parse(env, file)

        assert (
            str(exc_info.value)
            == f"An error was encountered while rendering '{file}': Encountered unknown tag 'bogus'."
        )
        assert exc_info.value.filename == file

    # ----------------------------------------------------------------------
    def test_runtime_error_includes_filename(self, env: Environment, tmp_file):
        file = tmp_file("{{ 1 / 0 }}")

        with pytest.raises(RenderError) as exc_info:
            Parse(env, file)

        assert str(exc_info.value) == f"An error was encountered while rendering '{file}': division by zero"
        assert exc_info.value.filename == file

    # ----------------------------------------------------------------------
    def test_missing_file_includes_filename(self, env: Environment, tmp_path: Path):
        file = tmp_path / "does_not_exist.jinja.txt"

        with pytest.raises(RenderError) as exc_info:
            Parse(env, file)

        assert exc_info.value.filename == file

    # ----------------------------------------------------------------------
    def test_original_exception_is_preserved(self, env: Environment, tmp_file):
        file = tmp_file("{{ 1 / 0 }}")

        with pytest.raises(RenderError) as exc_info:
            Parse(env, file)

        assert isinstance(exc_info.value.__cause__, ZeroDivisionError)

    # ----------------------------------------------------------------------
    def test_error_survives_copy(self, env: Environment, tmp_file):
        file = tmp_file("{{ 1 / 0 }}")

        with pytest.raises(RenderError) as exc_info:
            Parse(env, file)

        duplicate = copy.copy(exc_info.value)

        assert duplicate.filename == file
        assert str(duplicate) == f"An error was encountered while rendering '{file}': division by zero"

    # ----------------------------------------------------------------------
    def test_error_identifies_included_file_not_including_file(self, env: Environment, tmp_path: Path):
        included_file = tmp_path / "included.jinja.txt"
        included_file.write_text("Inner {% bogus %}")

        main_file = tmp_path / "main.jinja.txt"
        main_file.write_text("Outer {{ include_configuration('included.jinja.txt') }}")

        with pytest.raises(RenderError) as exc_info:
            Parse(env, main_file)

        assert (
            str(exc_info.value)
            == f"An error was encountered while rendering '{included_file}': Encountered unknown tag 'bogus'."
        )
        assert exc_info.value.filename == included_file

    # ----------------------------------------------------------------------
    def test_error_identifies_deeply_nested_included_file(self, env: Environment, tmp_path: Path):
        level2_file = tmp_path / "level2.jinja.txt"
        level2_file.write_text("{% bogus %}")

        level1_file = tmp_path / "level1.jinja.txt"
        level1_file.write_text("{{ include_configuration('level2.jinja.txt') }}")

        main_file = tmp_path / "main.jinja.txt"
        main_file.write_text("{{ include_configuration('level1.jinja.txt') }}")

        with pytest.raises(RenderError) as exc_info:
            Parse(env, main_file)

        assert exc_info.value.filename == level2_file


# ----------------------------------------------------------------------
class TestParseNonTemplate:
    # ----------------------------------------------------------------------
    def test_content_is_not_rendered(self, env: Environment, tmp_path: Path):
        file = tmp_path / "file.md"
        file.write_text("Value: {{ 1 + 2 }} {% bogus %}")

        frontmatter, rendered = Parse(env, file)

        assert frontmatter is None
        assert rendered == "Value: {{ 1 + 2 }} {% bogus %}"

    # ----------------------------------------------------------------------
    def test_frontmatter_is_separated(self, env: Environment, tmp_path: Path):
        file = tmp_path / "file.md"
        file.write_text(
            dedent("""\
                ---
                name: value
                ---
                Content: {{ 1 + 2 }}"""),
        )

        frontmatter, rendered = Parse(env, file)

        assert frontmatter == "name: value"
        assert rendered == "Content: {{ 1 + 2 }}"

    # ----------------------------------------------------------------------
    def test_template_includes_non_template_verbatim(self, env: Environment, tmp_path: Path):
        included_file = tmp_path / "included.md"
        included_file.write_text(
            dedent("""\
                ---
                ignored: true
                ---
                Included {{ 1 + 1 }}"""),
        )

        main_file = tmp_path / "main.jinja.md"
        main_file.write_text("{{ 1 + 2 }}: {{ include_configuration('included.md') }}")

        _, rendered = Parse(env, main_file)

        assert rendered == "3: Included {{ 1 + 1 }}"


# ----------------------------------------------------------------------
class TestIsTemplate:
    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "filename",
        ["foo.jinja", "foo.jinja2", "foo.jinja.txt", "foo.jinja2.md", "foo.bar.jinja.md", "FOO.JINJA.md"],
    )
    def test_templates(self, filename: str):
        assert IsTemplate(Path("dir") / filename) is True

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "filename",
        ["foo", "foo.md", "jinja.md", "foo.jinjax", "foo-jinja.md", ".jinja"],
    )
    def test_non_templates(self, filename: str):
        assert IsTemplate(Path("dir") / filename) is False

    # ----------------------------------------------------------------------
    def test_directory_name_is_ignored(self):
        assert IsTemplate(Path("dir.jinja") / "foo.md") is False


# ----------------------------------------------------------------------
class TestGetOutputPath:
    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("SKILL.jinja.md", "SKILL.md"),
            ("run.jinja2.py", "run.py"),
            ("notes.jinja", "notes"),
            ("notes.jinja2", "notes"),
            ("foo.bar.jinja.md", "foo.bar.md"),
            ("FOO.JINJA.md", "FOO.md"),
            ("foo.md", "foo.md"),
            ("foo", "foo"),
        ],
    )
    def test_filename(self, filename: str, expected: str):
        assert GetOutputPath(Path("dir") / filename) == Path("dir") / expected

    # ----------------------------------------------------------------------
    def test_directory_name_is_preserved(self):
        assert GetOutputPath(Path("dir.jinja") / "foo.jinja.md") == Path("dir.jinja") / "foo.md"
