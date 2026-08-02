"""High-level operations that render templates into agent configuration locations."""

import os
import subprocess
import sys

from typing import TYPE_CHECKING

import yaml

from jinja2 import Environment

from robotter.Renderer import Parse

if TYPE_CHECKING:
    from pathlib import Path

    from dbrownell_Common.Streams.DoneManager import DoneManager

    from robotter.agents.Agent import Agent


# ----------------------------------------------------------------------
def RenderGlobal(dm: DoneManager, template: Path, agent: Agent) -> None:
    """Render `template` and write the result to each of `agent`'s global configuration paths."""

    _Render(dm, template, agent.GetGlobalConfigurationPaths())


# ----------------------------------------------------------------------
def RenderLocal(dm: DoneManager, template: Path, agent: Agent, output_dir: Path) -> None:
    """Render `template` and write the result to each of `agent`'s project configuration paths under `output_dir`."""

    _Render(dm, template, agent.GetProjectConfigurationPaths(output_dir))


# ----------------------------------------------------------------------
def RenderGlobalSkill(dm: DoneManager, template: Path, agent: Agent) -> None:
    """Render the skill `template` and write it to `agent`'s global skill location."""

    frontmatter, content = _RenderContent(template)
    skill_name = _ExtractSkillName(dm, template, frontmatter)
    if skill_name is None:
        return

    path = agent.GetGlobalSkillPath(skill_name)
    if path is None:
        dm.WriteError(_SkillsUnsupportedMessage(agent))
        return

    _WriteFile(dm, path, content)


# ----------------------------------------------------------------------
def RenderLocalSkill(dm: DoneManager, template: Path, agent: Agent, output_dir: Path) -> None:
    """Render the skill `template` and write it to `agent`'s project skill location under `output_dir`."""

    frontmatter, content = _RenderContent(template)
    skill_name = _ExtractSkillName(dm, template, frontmatter)
    if skill_name is None:
        return

    path = agent.GetProjectSkillPath(skill_name, output_dir)
    if path is None:
        dm.WriteError(_SkillsUnsupportedMessage(agent))
        return

    _WriteFile(dm, path, content)


# ----------------------------------------------------------------------
def EditGlobal(dm: DoneManager, agent: Agent) -> None:
    """Launch an editor on `agent`'s global (user-level) configuration file."""

    _EditFile(dm, agent.GetGlobalConfigurationPaths())


# ----------------------------------------------------------------------
def EditLocal(dm: DoneManager, agent: Agent, output_dir: Path) -> None:
    """Launch an editor on `agent`'s project configuration file under `output_dir`."""

    _EditFile(dm, agent.GetProjectConfigurationPaths(output_dir))


# ----------------------------------------------------------------------
def EditGlobalSkill(dm: DoneManager, skill_name: str, agent: Agent) -> None:
    """Launch an editor on `agent`'s global (user-level) skill file for `skill_name`."""

    path = agent.GetGlobalSkillPath(skill_name)
    if path is None:
        dm.WriteError(_SkillsUnsupportedMessage(agent))
        return

    _EditFile(dm, [path], "skill file")


# ----------------------------------------------------------------------
def EditLocalSkill(dm: DoneManager, skill_name: str, agent: Agent, output_dir: Path) -> None:
    """Launch an editor on `agent`'s project skill file for `skill_name` under `output_dir`."""

    path = agent.GetProjectSkillPath(skill_name, output_dir)
    if path is None:
        dm.WriteError(_SkillsUnsupportedMessage(agent))
        return

    _EditFile(dm, [path], "skill file")


# ----------------------------------------------------------------------
def BrowseGlobal(dm: DoneManager, agent: Agent) -> None:
    """Open the directory containing `agent`'s global (user-level) configuration file in a file browser."""

    paths = agent.GetGlobalConfigurationPaths()

    if not paths:
        dm.WriteError("The agent does not define any configuration locations.")
        return

    _BrowseDirectory(dm, paths[0].parent, "configuration directory")


# ----------------------------------------------------------------------
def BrowseGlobalSkills(dm: DoneManager, agent: Agent) -> None:
    """Open `agent`'s global (user-level) skills directory in a file browser."""

    directory = agent.GetGlobalSkillsRoot()
    if directory is None:
        dm.WriteError(_SkillsUnsupportedMessage(agent))
        return

    _BrowseDirectory(dm, directory, "skills directory")


# ----------------------------------------------------------------------
def BrowseLocalSkills(dm: DoneManager, agent: Agent, output_dir: Path) -> None:
    """Open `agent`'s project skills directory under `output_dir` in a file browser."""

    directory = agent.GetProjectSkillsRoot(output_dir)
    if directory is None:
        dm.WriteError(_SkillsUnsupportedMessage(agent))
        return

    _BrowseDirectory(dm, directory, "skills directory")


# ----------------------------------------------------------------------
# |
# |  Private Functions
# |
# ----------------------------------------------------------------------
def _Render(dm: DoneManager, template: Path, paths: list[Path]) -> None:
    """Render `template` and write the result to each path in `paths`."""

    _, content = _RenderContent(template)

    for path in paths:
        _WriteFile(dm, path, content)


# ----------------------------------------------------------------------
def _RenderContent(template: Path) -> tuple[str | None, str]:
    """Render `template`, returning its frontmatter (or `None`) and the full content to be written."""

    # Configuration files are plain text/markdown, so HTML autoescaping is intentionally disabled.
    frontmatter, rendered = Parse(Environment(autoescape=False), template)  # noqa: S701

    content = rendered if frontmatter is None else f"---\n{frontmatter}\n---\n{rendered}"

    return frontmatter, content


# ----------------------------------------------------------------------
def _ExtractSkillName(dm: DoneManager, template: Path, frontmatter: str | None) -> str | None:
    """Return the `name` attribute from `frontmatter`, or `None` (after writing an error) if it is missing."""

    if frontmatter is None:
        dm.WriteError(f"The skill template '{template}' does not have frontmatter.")
        return None

    parsed = yaml.safe_load(frontmatter)

    if not isinstance(parsed, dict) or "name" not in parsed:
        dm.WriteError(f"The skill template '{template}' does not have a 'name' frontmatter attribute.")
        return None

    return str(parsed["name"])


# ----------------------------------------------------------------------
def _BrowseDirectory(
    dm: DoneManager,
    directory: Path,
    directory_label: str = "configuration directory",
) -> None:
    """Open `directory` in the operating system's default file browser."""

    if not directory.is_dir():
        dm.WriteError(f"The {directory_label} '{directory}' does not exist.")
        return

    with dm.Nested(f"Opening '{directory}'..."):
        if sys.platform.startswith("win"):
            os.startfile(directory)  # type: ignore[attr-defined]  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.run(["open", str(directory)], check=True)  # noqa: S603, S607
        else:
            subprocess.run(["xdg-open", str(directory)], check=True)  # noqa: S603, S607


# ----------------------------------------------------------------------
def _SkillsUnsupportedMessage(agent: Agent) -> str:
    """Return the message describing that `agent` does not support skills."""

    return f"The '{agent.name}' agent does not support skills."


# ----------------------------------------------------------------------
def _WriteFile(dm: DoneManager, path: Path, content: str) -> None:
    """Write `content` to `path`, creating parent directories as needed."""

    with dm.Nested(f"Writing '{path}'..."):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


# ----------------------------------------------------------------------
def _EditFile(dm: DoneManager, paths: list[Path], file_label: str = "configuration file") -> None:
    """Launch an editor on the first path in `paths`."""

    if not paths:
        dm.WriteError("The agent does not define any configuration locations.")
        return

    path = paths[0]

    if not path.is_file():
        dm.WriteError(f"The {file_label} '{path}' does not exist.")
        return

    with dm.Nested(f"Editing '{path}'..."):
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
        if editor:
            subprocess.run([editor, str(path)], check=True)  # noqa: S603
        elif sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=True)  # noqa: S603, S607
        else:
            subprocess.run(["xdg-open", str(path)], check=True)  # noqa: S603, S607
