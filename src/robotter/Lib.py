"""High-level operations that render templates into agent configuration locations."""

from typing import TYPE_CHECKING

from jinja2 import Environment

from robotter.Renderer import Parse

if TYPE_CHECKING:
    from pathlib import Path

    from robotter.agents.Agent import Agent


# ----------------------------------------------------------------------
def RenderGlobal(template: Path, agent: Agent) -> None:
    """Render `template` and write the result to each of `agent`'s global configuration paths."""

    _Render(template, agent.GetGlobalConfigurationPaths())


# ----------------------------------------------------------------------
def RenderLocal(template: Path, agent: Agent, output_dir: Path) -> None:
    """Render `template` and write the result to each of `agent`'s project configuration paths under `output_dir`."""

    _Render(template, agent.GetProjectConfigurationPaths(output_dir))


# ----------------------------------------------------------------------
# |
# |  Private Functions
# |
# ----------------------------------------------------------------------
def _Render(template: Path, paths: list[Path]) -> None:
    """Render `template` and write the result to each path in `paths`."""

    # Configuration files are plain text/markdown, so HTML autoescaping is intentionally disabled.
    frontmatter, rendered = Parse(Environment(autoescape=False), template)  # noqa: S701

    content = rendered if frontmatter is None else f"---\n{frontmatter}\n---\n{rendered}"

    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
