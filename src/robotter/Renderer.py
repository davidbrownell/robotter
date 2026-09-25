"""Functionality for parsing and rendering templates using Jinja2."""

from typing import NewType, TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from jinja2 import Environment


# ----------------------------------------------------------------------
ParsedContent = NewType("ParsedContent", str)
"""Content produced by `Parse`: rendered through Jinja2 for templates, verbatim otherwise."""


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
# Template suffixes may appear anywhere in a filename (`SKILL.jinja.md`) so that the remaining
# suffixes continue to describe the rendered file's type.
_TEMPLATE_SUFFIXES: frozenset[str] = frozenset({".jinja", ".jinja2"})


# ----------------------------------------------------------------------
def IsTemplate(path: Path) -> bool:
    """Return True if `path` names a Jinja2 template."""

    return any(suffix.lower() in _TEMPLATE_SUFFIXES for suffix in path.suffixes)


# ----------------------------------------------------------------------
def GetOutputPath(path: Path) -> Path:
    """Return `path` with any template suffixes removed from its filename."""

    suffixes = path.suffixes
    stem = path.name[: len(path.name) - len("".join(suffixes))]

    return path.with_name(
        stem + "".join(suffix for suffix in suffixes if suffix.lower() not in _TEMPLATE_SUFFIXES),
    )


# ----------------------------------------------------------------------
def Parse(
    env: Environment,
    content: Path,
) -> tuple[
    str | None,  # Frontmatter
    ParsedContent,
]:
    """Parse the contents of a file, separating frontmatter from the main content and rendering it using Jinja2 if it is a template."""

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

        parsed_content = ParsedContent(
            env.from_string(main_content).render() if IsTemplate(content) else main_content,
        )
    except RenderError:
        # An included file has already been associated with its own filename; attributing it to the
        # including file as well would misidentify where the error occurred.
        raise
    except Exception as ex:
        raise RenderError(content, ex) from ex

    return frontmatter, parsed_content
