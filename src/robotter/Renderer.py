"""Functionality for parsing and rendering templates using Jinja2."""

from typing import NewType, TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from jinja2 import Environment


# ----------------------------------------------------------------------
RenderedTemplate = NewType("RenderedTemplate", str)
"""A string produced by rendering a template through Jinja2."""


# ----------------------------------------------------------------------
class RenderError(Exception):
    """Error encountered while rendering a template file.

    Jinja2 errors do not identify the file that produced them, and a file rendered via
    `include_configuration` is not the file named on the command line. Associating the filename with
    the error is what makes the failure actionable.
    """

    # ----------------------------------------------------------------------
    def __init__(self, filename: Path, ex: Exception) -> None:
        # Forward both arguments so `self.args` mirrors the signature; Exception reconstructs
        # instances from `args` when copied or pickled.
        super().__init__(filename, ex)

        self.filename = filename

    # ----------------------------------------------------------------------
    def __str__(self) -> str:
        filename, ex = self.args

        return f"An error was encountered while rendering '{filename}': {ex}"


# ----------------------------------------------------------------------
def Parse(
    env: Environment,
    content: Path,
) -> tuple[
    str | None,  # Frontmatter
    RenderedTemplate,
]:
    """Parse the contents of a file, separating frontmatter from the main content and rendering it using Jinja2."""

    # ----------------------------------------------------------------------
    def IncludeConfiguration(relative_path: str) -> str:
        """Include and render another configuration file, returning only the rendered content (no frontmatter)."""

        _, rendered = Parse(env, content.parent / relative_path)

        return rendered

    # ----------------------------------------------------------------------

    env.globals["include_configuration"] = IncludeConfiguration  # ty: ignore[invalid-assignment]

    try:
        raw_content = content.read_text(encoding="utf-8")

        if raw_content.startswith("---"):
            min_valid_frontmatter_parts = 3
            parts = raw_content.split("---", 2)

            if len(parts) >= min_valid_frontmatter_parts:
                frontmatter = parts[1].strip()
                main_content = parts[2].strip()
            else:
                frontmatter = None
                main_content = raw_content.strip()
        else:
            frontmatter = None
            main_content = raw_content.strip()

        rendered_content = RenderedTemplate(env.from_string(main_content).render())
    except RenderError:
        # An included file has already been associated with its own filename; attributing it to the
        # including file as well would misidentify where the error occurred.
        raise
    except Exception as ex:
        raise RenderError(content, ex) from ex

    return frontmatter, rendered_content
