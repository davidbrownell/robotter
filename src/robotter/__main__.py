# noqa: D100
from enum import StrEnum
from pathlib import Path  # noqa: TC003
from typing import Annotated

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
from robotter.agents.Agent import Agent  # noqa: TC001
from robotter.agents.ClaudeCode import ClaudeCode
from robotter.agents.GitHubCopilot import GitHubCopilot
from robotter.agents.Grok import Grok
from robotter.agents.OpenAICodex import OpenAICodex
from robotter.agents.OpenCode import OpenCode


# ----------------------------------------------------------------------
class AgentType(StrEnum):
    """The AI agents whose configuration locations can be rendered to."""

    ClaudeCode = "claude-code"
    GitHubCopilot = "github-copilot"
    Grok = "grok"
    OpenAICodex = "openai-codex"
    OpenCode = "opencode"


# ----------------------------------------------------------------------
_AGENTS: dict[AgentType, type[Agent]] = {
    AgentType.ClaudeCode: ClaudeCode,
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
        Path,
        typer.Argument(
            exists=True,
            dir_okay=False,
            resolve_path=True,
            help="Template file to render.",
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

        with dm.Nested(f"Rendering '{agent.name}'...") as nested_dm:
            if output_dir is None:
                RenderGlobal(nested_dm, template, agent_instance)
            else:
                RenderLocal(nested_dm, template, agent_instance, output_dir)


# ----------------------------------------------------------------------
@app.command("render_skill", no_args_is_help=True)
def RenderSkill(
    template: Annotated[
        Path,
        typer.Argument(
            exists=True,
            dir_okay=False,
            resolve_path=True,
            help="Skill template file to render.",
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
    verbose: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--verbose", help="Write verbose information to the terminal."),
    ] = False,
    debug: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--debug", help="Write debug information to the terminal."),
    ] = False,
) -> None:
    """Render a skill template to the skill location of an AI agent."""

    with DoneManager.CreateCommandLine(
        flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        agent_instance = _AGENTS[agent]()

        with dm.Nested(f"Rendering skill '{agent.name}'...") as nested_dm:
            if output_dir is None:
                RenderGlobalSkill(nested_dm, template, agent_instance)
            else:
                RenderLocalSkill(nested_dm, template, agent_instance, output_dir)


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
