"""Unit tests for robotter.Renderer"""

from pathlib import Path
from textwrap import dedent

import pytest
from jinja2 import Environment

from robotter.Renderer import Parse


# ----------------------------------------------------------------------
@pytest.fixture
def env() -> Environment:
    return Environment()


# ----------------------------------------------------------------------
@pytest.fixture
def tmp_file(tmp_path: Path):
    """Factory fixture for creating temporary files with content."""

    def _create(content: str) -> Path:
        file = tmp_path / "test_file.txt"
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
            included_file = tmp_path / "included.txt"
            included_file.write_text("Included content")

            main_file = tmp_path / "main.txt"
            main_file.write_text("Before {{ include_configuration('included.txt') }} After")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "Before Included content After"

        # ----------------------------------------------------------------------
        def test_include_file_with_frontmatter_ignores_frontmatter(self, env: Environment, tmp_path: Path):
            included_file = tmp_path / "included.txt"
            included_file.write_text(
                dedent("""\
                ---
                title: Should Be Ignored
                ---
                Only this content""")
            )

            main_file = tmp_path / "main.txt"
            main_file.write_text("{{ include_configuration('included.txt') }}")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "Only this content"

        # ----------------------------------------------------------------------
        def test_include_file_in_subdirectory(self, env: Environment, tmp_path: Path):
            subdir = tmp_path / "subdir"
            subdir.mkdir()

            included_file = subdir / "nested.txt"
            included_file.write_text("Nested content")

            main_file = tmp_path / "main.txt"
            main_file.write_text("{{ include_configuration('subdir/nested.txt') }}")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "Nested content"

        # ----------------------------------------------------------------------
        def test_include_file_with_jinja2_template(self, env: Environment, tmp_path: Path):
            included_file = tmp_path / "included.txt"
            included_file.write_text("Result: {{ 2 * 3 }}")

            main_file = tmp_path / "main.txt"
            main_file.write_text("{{ include_configuration('included.txt') }}")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "Result: 6"

        # ----------------------------------------------------------------------
        def test_nested_include_configuration(self, env: Environment, tmp_path: Path):
            level2_file = tmp_path / "level2.txt"
            level2_file.write_text("Level 2")

            level1_file = tmp_path / "level1.txt"
            level1_file.write_text("[{{ include_configuration('level2.txt') }}]")

            main_file = tmp_path / "main.txt"
            main_file.write_text("Main: {{ include_configuration('level1.txt') }}")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "Main: [Level 2]"

        # ----------------------------------------------------------------------
        def test_include_relative_from_subdirectory(self, env: Environment, tmp_path: Path):
            subdir = tmp_path / "subdir"
            subdir.mkdir()

            sibling_file = subdir / "sibling.txt"
            sibling_file.write_text("Sibling content")

            main_file = subdir / "main.txt"
            main_file.write_text("{{ include_configuration('sibling.txt') }}")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "Sibling content"

        # ----------------------------------------------------------------------
        def test_include_parent_directory_file(self, env: Environment, tmp_path: Path):
            parent_file = tmp_path / "parent.txt"
            parent_file.write_text("Parent content")

            subdir = tmp_path / "subdir"
            subdir.mkdir()

            main_file = subdir / "main.txt"
            main_file.write_text("{{ include_configuration('../parent.txt') }}")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "Parent content"

        # ----------------------------------------------------------------------
        def test_multiple_includes_in_same_file(self, env: Environment, tmp_path: Path):
            file_a = tmp_path / "a.txt"
            file_a.write_text("A")

            file_b = tmp_path / "b.txt"
            file_b.write_text("B")

            main_file = tmp_path / "main.txt"
            main_file.write_text("{{ include_configuration('a.txt') }}-{{ include_configuration('b.txt') }}")

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter is None
            assert rendered == "A-B"

        # ----------------------------------------------------------------------
        def test_include_nonexistent_file_raises_error(self, env: Environment, tmp_path: Path):
            main_file = tmp_path / "main.txt"
            main_file.write_text("{{ include_configuration('does_not_exist.txt') }}")

            with pytest.raises(FileNotFoundError):
                Parse(env, main_file)

        # ----------------------------------------------------------------------
        def test_include_with_main_file_having_frontmatter(self, env: Environment, tmp_path: Path):
            included_file = tmp_path / "included.txt"
            included_file.write_text("Included")

            main_file = tmp_path / "main.txt"
            main_file.write_text(
                dedent("""\
                ---
                main: frontmatter
                ---
                Content: {{ include_configuration('included.txt') }}""")
            )

            frontmatter, rendered = Parse(env, main_file)

            assert frontmatter == "main: frontmatter"
            assert rendered == "Content: Included"
