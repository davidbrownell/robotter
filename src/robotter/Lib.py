"""High-level operations that render templates into agent configuration locations."""

import os
import subprocess
import sys

from typing import NoReturn, TYPE_CHECKING

import yaml

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
def RenderGlobalSkill(template: Path, agent: Agent) -> None:
    """Render the skill `template` and write it to `agent`'s global skill location.

    The skill name is taken from the template's frontmatter `name` attribute. Raises
    `ValueError` if `agent` does not support skills.
    """

    frontmatter, content = _RenderContent(template)
    skill_name = _ExtractSkillName(template, frontmatter)

    path = agent.GetGlobalSkillPath(skill_name)
    if path is None:
        _RaiseSkillsUnsupported(agent)

    _WriteFile(path, content)


# ----------------------------------------------------------------------
def RenderLocalSkill(template: Path, agent: Agent, output_dir: Path) -> None:
    """Render the skill `template` and write it to `agent`'s project skill location under `output_dir`.

    The skill name is taken from the template's frontmatter `name` attribute. Raises
    `ValueError` if `agent` does not support skills.
    """

    frontmatter, content = _RenderContent(template)
    skill_name = _ExtractSkillName(template, frontmatter)

    path = agent.GetProjectSkillPath(skill_name, output_dir)
    if path is None:
        _RaiseSkillsUnsupported(agent)

    _WriteFile(path, content)


# ----------------------------------------------------------------------
def EditGlobal(agent: Agent) -> None:
    """Launch an editor on `agent`'s global (user-level) configuration file."""

    _EditFile(agent.GetGlobalConfigurationPaths())


# ----------------------------------------------------------------------
def EditLocal(agent: Agent, output_dir: Path) -> None:
    """Launch an editor on `agent`'s project configuration file under `output_dir`."""

    _EditFile(agent.GetProjectConfigurationPaths(output_dir))


# ----------------------------------------------------------------------
def EditGlobalSkill(skill_name: str, agent: Agent) -> None:
    """Launch an editor on `agent`'s global (user-level) skill file for `skill_name`."""

    path = agent.GetGlobalSkillPath(skill_name)
    if path is None:
        _RaiseSkillsUnsupported(agent)

    _EditFile([path], "skill file")


# ----------------------------------------------------------------------
def EditLocalSkill(skill_name: str, agent: Agent, output_dir: Path) -> None:
    """Launch an editor on `agent`'s project skill file for `skill_name` under `output_dir`."""

    path = agent.GetProjectSkillPath(skill_name, output_dir)
    if path is None:
        _RaiseSkillsUnsupported(agent)

    _EditFile([path], "skill file")


# ----------------------------------------------------------------------
def BrowseGlobal(agent: Agent) -> None:
    """Open the directory containing `agent`'s global (user-level) configuration file in a file browser."""

    paths = agent.GetGlobalConfigurationPaths()

    if not paths:
        msg = "The agent does not define any configuration locations."
        raise ValueError(msg)

    _BrowseDirectory(paths[0].parent, "configuration directory")


# ----------------------------------------------------------------------
def BrowseGlobalSkills(agent: Agent) -> None:
    """Open `agent`'s global (user-level) skills directory in a file browser."""

    directory = agent.GetGlobalSkillsRoot()
    if directory is None:
        _RaiseSkillsUnsupported(agent)

    _BrowseDirectory(directory, "skills directory")


# ----------------------------------------------------------------------
def BrowseLocalSkills(agent: Agent, output_dir: Path) -> None:
    """Open `agent`'s project skills directory under `output_dir` in a file browser."""

    directory = agent.GetProjectSkillsRoot(output_dir)
    if directory is None:
        _RaiseSkillsUnsupported(agent)

    _BrowseDirectory(directory, "skills directory")


# ----------------------------------------------------------------------
# |
# |  Private Functions
# |
# ----------------------------------------------------------------------
def _Render(template: Path, paths: list[Path]) -> None:
    """Render `template` and write the result to each path in `paths`."""

    _, content = _RenderContent(template)

    for path in paths:
        _WriteFile(path, content)


# ----------------------------------------------------------------------
def _RenderContent(template: Path) -> tuple[str | None, str]:
    """Render `template`, returning its frontmatter (or `None`) and the full content to be written."""

    # Configuration files are plain text/markdown, so HTML autoescaping is intentionally disabled.
    frontmatter, rendered = Parse(Environment(autoescape=False), template)  # noqa: S701

    content = rendered if frontmatter is None else f"---\n{frontmatter}\n---\n{rendered}"

    return frontmatter, content


# ----------------------------------------------------------------------
def _ExtractSkillName(template: Path, frontmatter: str | None) -> str:
    """Return the `name` attribute from `frontmatter`, raising `ValueError` if it is missing."""

    if frontmatter is None:
        msg = f"The skill template '{template}' does not have frontmatter."
        raise ValueError(msg)

    parsed = yaml.safe_load(frontmatter)

    if not isinstance(parsed, dict) or "name" not in parsed:
        msg = f"The skill template '{template}' does not have a 'name' frontmatter attribute."
        raise ValueError(msg)

    return str(parsed["name"])


# ----------------------------------------------------------------------
def _BrowseDirectory(directory: Path, directory_label: str = "configuration directory") -> None:
    """Open `directory` in the operating system's default file browser.

    `directory_label` names the kind of directory for error messages. Raises
    `FileNotFoundError` if `directory` does not exist.
    """

    if not directory.is_dir():
        msg = f"The {directory_label} '{directory}' does not exist."
        raise FileNotFoundError(msg)

    if sys.platform.startswith("win"):
        os.startfile(directory)  # type: ignore[attr-defined]  # noqa: S606
    elif sys.platform == "darwin":
        subprocess.run(["open", str(directory)], check=True)  # noqa: S603, S607
    else:
        subprocess.run(["xdg-open", str(directory)], check=True)  # noqa: S603, S607


# ----------------------------------------------------------------------
def _RaiseSkillsUnsupported(agent: Agent) -> NoReturn:
    """Raise `ValueError` indicating that `agent` does not support skills."""

    msg = f"The '{agent.name}' agent does not support skills."
    raise ValueError(msg)


# ----------------------------------------------------------------------
def _WriteFile(path: Path, content: str) -> None:
    """Write `content` to `path`, creating parent directories as needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ----------------------------------------------------------------------
def _EditFile(paths: list[Path], file_label: str = "configuration file") -> None:
    """Launch an editor on the first path in `paths`.

    `file_label` names the kind of file for error messages. The editor is honored from
    `$VISUAL`/`$EDITOR` and otherwise falls back to the operating system's default handler.
    """

    if not paths:
        msg = "The agent does not define any configuration locations."
        raise ValueError(msg)

    path = paths[0]

    if not path.is_file():
        msg = f"The {file_label} '{path}' does not exist."
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
