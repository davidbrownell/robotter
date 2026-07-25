"""Functionality for parsing and rendering templates using Jinja2."""

from typing import NewType, TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from jinja2 import Environment


# ----------------------------------------------------------------------
RenderedTemplate = NewType("RenderedTemplate", str)
"""A string that has been rendered by Jinja2. This type is used to indicate that the content has been processed and is ready for use."""


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

    # Register the include_configuration function in the environment
    env.globals["include_configuration"] = IncludeConfiguration  # ty: ignore[invalid-assignment]

    # Read the content of the file
    raw_content = content.read_text()

    # Split the content into frontmatter and main content
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

    return frontmatter, rendered_content
