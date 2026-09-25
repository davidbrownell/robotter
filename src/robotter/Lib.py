"""High-level operations that render templates into agent configuration locations."""

import os
import subprocess
import sys

from typing import TYPE_CHECKING

import yaml

from jinja2 import Environment

from robotter.Renderer import GetOutputPath, IsTemplate, Parse

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from dbrownell_Common.Streams.DoneManager import DoneManager

    from robotter.agents.Agent import Agent


# ----------------------------------------------------------------------
def RenderGlobal(dm: DoneManager, template: Path, agent: Agent) -> None:
    """Render `template` and write the result to `agent`'s global configuration file."""

    _Render(dm, template, agent.GetGlobalConfigurationFilename())


# ----------------------------------------------------------------------
def RenderLocal(dm: DoneManager, template: Path, agent: Agent, output_dir: Path) -> None:
    """Render `template` and write the result to `agent`'s project configuration file under `output_dir`."""

    _Render(dm, template, agent.GetProjectConfigurationFilename(output_dir))


# ----------------------------------------------------------------------
def RenderGlobalSkill(dm: DoneManager, template: Path, agent: Agent) -> None:
    """Render the skill `template` (a file or a directory) to `agent`'s global skill location."""

    _RenderSkill(
        dm,
        template,
        agent,
        agent.GetGlobalSkillPath,
        agent.GetGlobalSkillDirectory,
    )


# ----------------------------------------------------------------------
def RenderLocalSkill(dm: DoneManager, template: Path, agent: Agent, output_dir: Path) -> None:
    """Render the skill `template` (a file or a directory) to `agent`'s project skill location under `output_dir`."""

    _RenderSkill(
        dm,
        template,
        agent,
        lambda skill_name: agent.GetProjectSkillPath(skill_name, output_dir),
        lambda skill_name: agent.GetProjectSkillDirectory(skill_name, output_dir),
    )


# ----------------------------------------------------------------------
def EditGlobal(dm: DoneManager, agent: Agent) -> None:
    """Launch an editor on `agent`'s global (user-level) configuration file."""

    _EditFile(dm, agent.GetGlobalConfigurationFilename())


# ----------------------------------------------------------------------
def EditLocal(dm: DoneManager, agent: Agent, output_dir: Path) -> None:
    """Launch an editor on `agent`'s project configuration file under `output_dir`."""

    _EditFile(dm, agent.GetProjectConfigurationFilename(output_dir))


# ----------------------------------------------------------------------
def EditGlobalSkill(dm: DoneManager, skill_name: str, agent: Agent) -> None:
    """Launch an editor on `agent`'s global (user-level) skill file for `skill_name`."""

    path = agent.GetGlobalSkillPath(skill_name)
    if path is None:
        dm.WriteError(_SkillsUnsupportedMessage(agent))
        return

    _EditFile(dm, path, "skill file")


# ----------------------------------------------------------------------
def EditLocalSkill(dm: DoneManager, skill_name: str, agent: Agent, output_dir: Path) -> None:
    """Launch an editor on `agent`'s project skill file for `skill_name` under `output_dir`."""

    path = agent.GetProjectSkillPath(skill_name, output_dir)
    if path is None:
        dm.WriteError(_SkillsUnsupportedMessage(agent))
        return

    _EditFile(dm, path, "skill file")


# ----------------------------------------------------------------------
def BrowseGlobal(dm: DoneManager, agent: Agent) -> None:
    """Open the directory containing `agent`'s global (user-level) configuration file in a file browser."""

    filename = agent.GetGlobalConfigurationFilename()

    _BrowseDirectory(dm, filename.parent, "configuration directory")


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
def _Render(dm: DoneManager, template: Path, path: Path) -> None:
    """Render `template` and write the result to `path`."""

    _, content = _RenderContent(template)

    _WriteFile(dm, path, content)


# ----------------------------------------------------------------------
def _RenderSkill(
    dm: DoneManager,
    template: Path,
    agent: Agent,
    get_skill_path: Callable[[str], Path | None],
    get_skill_directory: Callable[[str], Path | None],
) -> None:
    """Render a skill template file or directory to the location produced by `get_skill_path`."""

    if template.is_dir():
        _RenderSkillDirectory(dm, template, agent, get_skill_path, get_skill_directory)
        return

    frontmatter, content = _RenderContent(template)

    skill_name = _ExtractSkillName(dm, template, frontmatter)
    if skill_name is None:
        return

    path = _ResolveSkillPath(dm, skill_name, agent, get_skill_path)
    if path is None:
        return

    _WriteFile(dm, path, content)


# ----------------------------------------------------------------------
def _RenderSkillDirectory(
    dm: DoneManager,
    template: Path,
    agent: Agent,
    get_skill_path: Callable[[str], Path | None],
    get_skill_directory: Callable[[str], Path | None],
) -> None:
    """Render every file under the `template` directory into a skill directory named after `template`."""

    # The directory name identifies the skill, so frontmatter is not consulted for it. Resolving
    # the skill's own file locates the destination, ensuring the name is validated exactly as it is
    # for a single-file template rather than being joined onto the skills root unchecked.
    skill_path = _ResolveSkillPath(dm, template.name, agent, get_skill_path)
    if skill_path is None:
        return

    # The agent decides which directory a skill owns. Deriving it here (for example, from the
    # skill file's parent) would write into the shared skills root for agents that store a skill
    # as a single file, letting one skill overwrite another's.
    destination_root = get_skill_directory(template.name)
    if destination_root is None:
        dm.WriteError(
            f"The '{agent.name}' agent stores each skill as a single file, so it cannot render the skill template directory '{template}'.",
        )
        return

    # `Path` comparisons fold case on Windows but not on POSIX, so sorting the paths themselves
    # would order the writes differently per platform. Sorting on the relative path's parts keeps
    # the order stable everywhere.
    sources = sorted(
        (
            (source, GetOutputPath(source.relative_to(template)))
            for source in template.rglob("*")
            if source.is_file()
        ),
        key=lambda item: (item[1].parts, item[0].relative_to(template).parts),
    )

    if not sources:
        dm.WriteError(f"The skill template directory '{template}' is empty.")
        return

    sources_by_output: dict[Path, list[Path]] = {}

    for source, output in sources:
        sources_by_output.setdefault(output, []).append(source)

    # Removing template suffixes can make a file's output collide with a directory produced by
    # other files (`scripts.jinja` alongside `scripts/run.py`).
    output_directories = {parent for output in sources_by_output for parent in output.parents}

    for output, output_sources in sources_by_output.items():
        if len(output_sources) > 1:
            dm.WriteError(
                f"The skill template directory '{template}' contains multiple files that render to '{output.as_posix()}': "
                + ", ".join(f"'{source.relative_to(template).as_posix()}'" for source in output_sources)
                + ".",
            )
            return

        if output in output_directories:
            dm.WriteError(
                f"The skill template directory '{template}' contains '{output_sources[0].relative_to(template).as_posix()}', which renders to '{output.as_posix()}', but '{output.as_posix()}' is also a directory.",
            )
            return

    if skill_path not in {destination_root / output for output in sources_by_output}:
        dm.WriteError(
            f"The skill template directory '{template}' does not contain '{skill_path.name}'.",
        )
        return

    # Render everything before writing anything so that a malformed template does not leave a
    # partially installed skill behind. Writes themselves are not staged, so a failure while
    # writing (a permission error, a full disk) can still leave the skill incomplete.
    destinations = [(destination_root / output, _RenderSkillSource(source)) for source, output in sources]

    for destination, content in destinations:
        _WriteFile(dm, destination, content)


# ----------------------------------------------------------------------
def _RenderSkillSource(source: Path) -> str | bytes:
    """Render `source` as a template, or return its raw bytes when it is not a template."""

    # Skill directories carry supporting assets (images, scripts, data files) alongside their
    # templates. Reading those as text would corrupt them (leading `---` is consumed as
    # frontmatter, whitespace is stripped) or fail outright, so they are copied byte for byte.
    if not IsTemplate(source):
        return source.read_bytes()

    _, content = _RenderContent(source)

    return content


# ----------------------------------------------------------------------
def _ResolveSkillPath(
    dm: DoneManager,
    skill_name: str,
    agent: Agent,
    get_skill_path: Callable[[str], Path | None],
) -> Path | None:
    """Return the skill file for `skill_name`, or `None` (after writing an error) if it cannot be resolved."""

    try:
        path = get_skill_path(skill_name)
    except ValueError as ex:
        dm.WriteError(str(ex))
        return None

    if path is None:
        dm.WriteError(_SkillsUnsupportedMessage(agent))
        return None

    return path


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
def _WriteFile(dm: DoneManager, path: Path, content: str | bytes) -> None:
    """Write `content` to `path`, creating parent directories as needed."""

    with dm.Nested(f"Writing '{path}'..."):
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")


# ----------------------------------------------------------------------
def _EditFile(dm: DoneManager, path: Path, file_label: str = "configuration file") -> None:
    """Launch an editor on `path`."""

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
