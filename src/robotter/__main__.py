# noqa: D100
import tempfile

from contextlib import contextmanager
from enum import StrEnum
from pathlib import Path
from typing import Annotated, TYPE_CHECKING

import typer

from dbrownell_Common.Streams.DoneManager import DoneManager, Flags as DoneManagerFlags
from typer.core import TyperGroup

from robotter import __version__
from robotter.Lib import (
    BrowseGlobal,
    BrowseGlobalSkills,
    BrowseLocalSkills,
    EditGlobal,
    EditGlobalSkill,
    EditLocal,
    EditLocalSkill,
    RenderGlobal,
    RenderGlobalSkill,
    RenderLocal,
    RenderLocalSkill,
)
from robotter.Remote import Download, IsUrl
from robotter.agents.Agent import Agent  # noqa: TC001
from robotter.agents.ClaudeCode import ClaudeCode
from robotter.agents.Cline import Cline
from robotter.agents.Cursor import Cursor
from robotter.agents.GeminiCLI import GeminiCLI
from robotter.agents.GitHubCopilot import GitHubCopilot
from robotter.agents.Grok import Grok
from robotter.agents.OpenAICodex import OpenAICodex
from robotter.agents.OpenCode import OpenCode

if TYPE_CHECKING:
    from collections.abc import Iterator


# ----------------------------------------------------------------------
class AgentType(StrEnum):
    """The AI agents whose configuration locations can be rendered to."""

    ClaudeCode = "claude-code"
    Cline = "cline"
    Cursor = "cursor"
    GeminiCLI = "gemini-cli"
    GitHubCopilot = "github-copilot"
    Grok = "grok"
    OpenAICodex = "openai-codex"
    OpenCode = "opencode"


# ----------------------------------------------------------------------
_AGENTS: dict[AgentType, type[Agent]] = {
    AgentType.ClaudeCode: ClaudeCode,
    AgentType.Cline: Cline,
    AgentType.Cursor: Cursor,
    AgentType.GeminiCLI: GeminiCLI,
    AgentType.GitHubCopilot: GitHubCopilot,
    AgentType.Grok: Grok,
    AgentType.OpenAICodex: OpenAICodex,
    AgentType.OpenCode: OpenCode,
}


# ----------------------------------------------------------------------
class NaturalOrderGrouper(TyperGroup):  # noqa: D101
    # ----------------------------------------------------------------------
    def list_commands(self, *args, **kwargs) -> list[str]:  # noqa: ARG002, D102
        return list(self.commands.keys())  # pragma: no cover


# ----------------------------------------------------------------------
def _ValidateTemplate(value: str) -> str:
    """Resolve a local template path, leaving URLs to be downloaded later."""

    if IsUrl(value):
        return value

    path = Path(value).resolve()

    if not path.exists():
        msg = f"'{value}' does not exist."
        raise typer.BadParameter(msg)

    return str(path)


# ----------------------------------------------------------------------
@contextmanager
def _ResolveTemplate(dm: DoneManager, template: str) -> Iterator[Path | None]:
    """Yield the local path of `template`, or `None` (after writing an error) if it could not be downloaded."""

    if not IsUrl(template):
        yield Path(template)
        return

    # Downloads are discarded after rendering, which is why remote templates are always copied
    # rather than linked.
    with tempfile.TemporaryDirectory() as temp_dir:
        path: Path | None = None

        with dm.Nested(f"Downloading '{template}'...") as nested_dm:
            try:
                path = Download(template, Path(temp_dir))
            except Exception as ex:
                nested_dm.WriteError(f"'{template}' could not be downloaded: {ex}")

        yield path


# ----------------------------------------------------------------------
app = typer.Typer(
    cls=NaturalOrderGrouper,
    help=__doc__,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=False,
)


# ----------------------------------------------------------------------
@app.command("render", no_args_is_help=True)
def Render(
    template: Annotated[
        str,
        typer.Argument(
            callback=_ValidateTemplate,
            help="Template file to render, as a path or URL.",
        ),
    ],
    agent: Annotated[
        AgentType,
        typer.Argument(
            help="Agent to render configuration for.",
        ),
    ],
    output_dir: Annotated[
        Path | None,
        typer.Argument(
            file_okay=False,
            resolve_path=True,
            help="Render project-level configuration under this directory. When omitted, global (user-level) configuration is rendered.",
        ),
    ] = None,
    copy: Annotated[  # noqa: FBT002
        bool,
        typer.Option(
            "--copy",
            help="Copy non-template files instead of creating symbolic links when rendering globally. Project-level rendering always copies.",
        ),
    ] = False,
    verbose: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--verbose", help="Write verbose information to the terminal."),
    ] = False,
    debug: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--debug", help="Write debug information to the terminal."),
    ] = False,
) -> None:
    """Render a template to the configuration locations of an AI agent."""

    with DoneManager.CreateCommandLine(
        flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        agent_instance = _AGENTS[agent]()

        with (
            dm.Nested(f"Rendering '{agent.name}'...") as nested_dm,
            _ResolveTemplate(nested_dm, template) as template_path,
        ):
            if template_path is None:
                return

            if template_path.is_dir():
                nested_dm.WriteError(f"The template '{template}' is a directory.")
                return

            if output_dir is None:
                RenderGlobal(nested_dm, template_path, agent_instance, copy=copy or IsUrl(template))
            else:
                RenderLocal(nested_dm, template_path, agent_instance, output_dir)


# ----------------------------------------------------------------------
@app.command("render_skill", no_args_is_help=True)
def RenderSkill(
    template: Annotated[
        str,
        typer.Argument(
            callback=_ValidateTemplate,
            help="Skill template file to render, or a directory whose files are each rendered into a skill named after the directory, as a path or URL (including a GitHub directory URL).",
        ),
    ],
    agent: Annotated[
        AgentType,
        typer.Argument(
            help="Agent to render the skill for.",
        ),
    ],
    output_dir: Annotated[
        Path | None,
        typer.Argument(
            file_okay=False,
            resolve_path=True,
            help="Render the project-level skill under this directory. When omitted, the global (user-level) skill is rendered.",
        ),
    ] = None,
    copy: Annotated[  # noqa: FBT002
        bool,
        typer.Option(
            "--copy",
            help="Copy non-template files instead of creating symbolic links when rendering globally. Project-level rendering always copies.",
        ),
    ] = False,
    verbose: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--verbose", help="Write verbose information to the terminal."),
    ] = False,
    debug: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--debug", help="Write debug information to the terminal."),
    ] = False,
) -> None:
    """Render a skill template file or directory to the skill location of an AI agent."""

    with DoneManager.CreateCommandLine(
        flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        agent_instance = _AGENTS[agent]()

        with (
            dm.Nested(f"Rendering skill '{agent.name}'...") as nested_dm,
            _ResolveTemplate(nested_dm, template) as template_path,
        ):
            if template_path is None:
                return

            if output_dir is None:
                RenderGlobalSkill(nested_dm, template_path, agent_instance, copy=copy or IsUrl(template))
            else:
                RenderLocalSkill(nested_dm, template_path, agent_instance, output_dir)


# ----------------------------------------------------------------------
@app.command("edit", no_args_is_help=True)
def Edit(
    agent: Annotated[
        AgentType,
        typer.Argument(
            help="Agent whose configuration file should be edited.",
        ),
    ],
    output_dir: Annotated[
        Path | None,
        typer.Argument(
            file_okay=False,
            resolve_path=True,
            help="Edit project-level configuration under this directory. When omitted, global (user-level) configuration is edited.",
        ),
    ] = None,
    verbose: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--verbose", help="Write verbose information to the terminal."),
    ] = False,
    debug: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--debug", help="Write debug information to the terminal."),
    ] = False,
) -> None:
    """Launch an AI agent's configuration file in an editor."""

    with DoneManager.CreateCommandLine(
        flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        agent_instance = _AGENTS[agent]()

        with dm.Nested(f"Editing '{agent.name}'...") as nested_dm:
            if output_dir is None:
                EditGlobal(nested_dm, agent_instance)
            else:
                EditLocal(nested_dm, agent_instance, output_dir)


# ----------------------------------------------------------------------
@app.command("edit_skill", no_args_is_help=True)
def EditSkill(
    skill_name: Annotated[
        str,
        typer.Argument(
            help="Name of the skill to edit.",
        ),
    ],
    agent: Annotated[
        AgentType,
        typer.Argument(
            help="Agent whose skill file should be edited.",
        ),
    ],
    output_dir: Annotated[
        Path | None,
        typer.Argument(
            file_okay=False,
            resolve_path=True,
            help="Edit the project-level skill under this directory. When omitted, the global (user-level) skill is edited.",
        ),
    ] = None,
    verbose: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--verbose", help="Write verbose information to the terminal."),
    ] = False,
    debug: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--debug", help="Write debug information to the terminal."),
    ] = False,
) -> None:
    """Launch an AI agent's skill file in an editor."""

    with DoneManager.CreateCommandLine(
        flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        agent_instance = _AGENTS[agent]()

        with dm.Nested(f"Editing skill '{agent.name}'...") as nested_dm:
            if output_dir is None:
                EditGlobalSkill(nested_dm, skill_name, agent_instance)
            else:
                EditLocalSkill(nested_dm, skill_name, agent_instance, output_dir)


# ----------------------------------------------------------------------
@app.command("browse", no_args_is_help=True)
def Browse(
    agent: Annotated[
        AgentType,
        typer.Argument(
            help="Agent whose global configuration directory should be opened.",
        ),
    ],
    verbose: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--verbose", help="Write verbose information to the terminal."),
    ] = False,
    debug: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--debug", help="Write debug information to the terminal."),
    ] = False,
) -> None:
    """Open an AI agent's global configuration directory in a file browser."""

    with DoneManager.CreateCommandLine(
        flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        agent_instance = _AGENTS[agent]()

        with dm.Nested(f"Browsing '{agent.name}'...") as nested_dm:
            BrowseGlobal(nested_dm, agent_instance)


# ----------------------------------------------------------------------
@app.command("browse_skills", no_args_is_help=True)
def BrowseSkills(
    agent: Annotated[
        AgentType,
        typer.Argument(
            help="Agent whose skills directory should be opened.",
        ),
    ],
    output_dir: Annotated[
        Path | None,
        typer.Argument(
            file_okay=False,
            resolve_path=True,
            help="Browse the project-level skills directory under this directory. When omitted, the global (user-level) skills directory is browsed.",
        ),
    ] = None,
    verbose: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--verbose", help="Write verbose information to the terminal."),
    ] = False,
    debug: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--debug", help="Write debug information to the terminal."),
    ] = False,
) -> None:
    """Open an AI agent's skills directory in a file browser."""

    with DoneManager.CreateCommandLine(
        flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        agent_instance = _AGENTS[agent]()

        with dm.Nested(f"Browsing skills '{agent.name}'...") as nested_dm:
            if output_dir is None:
                BrowseGlobalSkills(nested_dm, agent_instance)
            else:
                BrowseLocalSkills(nested_dm, agent_instance, output_dir)


# ----------------------------------------------------------------------
@app.command("version")
def Version() -> None:
    """Print the version."""

    typer.echo(__version__)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()  # pragma: no cover
