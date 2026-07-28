"""High-level operations that render templates into agent configuration locations."""

import os
import subprocess
import sys

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
def EditGlobal(agent: Agent) -> None:
    """Launch an editor on `agent`'s global (user-level) configuration file."""

    _Edit(agent.GetGlobalConfigurationPaths())


# ----------------------------------------------------------------------
def EditLocal(agent: Agent, output_dir: Path) -> None:
    """Launch an editor on `agent`'s project configuration file under `output_dir`."""

    _Edit(agent.GetProjectConfigurationPaths(output_dir))


# ----------------------------------------------------------------------
def BrowseGlobal(agent: Agent) -> None:
    """Open the directory containing `agent`'s global (user-level) configuration file in a file browser."""

    paths = agent.GetGlobalConfigurationPaths()

    if not paths:
        msg = "The agent does not define any configuration locations."
        raise ValueError(msg)

    directory = paths[0].parent

    if not directory.is_dir():
        msg = f"The configuration directory '{directory}' does not exist."
        raise FileNotFoundError(msg)

    if sys.platform.startswith("win"):
        os.startfile(directory)  # type: ignore[attr-defined]  # noqa: S606
    elif sys.platform == "darwin":
        subprocess.run(["open", str(directory)], check=True)  # noqa: S603, S607
    else:
        subprocess.run(["xdg-open", str(directory)], check=True)  # noqa: S603, S607


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


# ----------------------------------------------------------------------
def _Edit(paths: list[Path]) -> None:
    """Launch an editor on the first path in `paths`.

    The editor is honored from `$VISUAL`/`$EDITOR` and otherwise falls back to the
    operating system's default handler.
    """

    if not paths:
        msg = "The agent does not define any configuration locations."
        raise ValueError(msg)

    path = paths[0]

    if not path.is_file():
        msg = f"The configuration file '{path}' does not exist."
        raise FileNotFoundError(msg)

    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if editor:
        subprocess.run([editor, str(path)], check=True)  # noqa: S603
    elif sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]  # noqa: S606
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=True)  # noqa: S603, S607
    else:
        subprocess.run(["xdg-open", str(path)], check=True)  # noqa: S603, S607
