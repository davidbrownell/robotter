# noqa: D100
from enum import StrEnum
from pathlib import Path  # noqa: TC003
from typing import Annotated

import typer

from dbrownell_Common.Streams.DoneManager import DoneManager, Flags as DoneManagerFlags
from typer.core import TyperGroup

from robotter.Lib import RenderGlobal, RenderLocal
from robotter.agents.Agent import Agent  # noqa: TC001
from robotter.agents.ClaudeCode import ClaudeCode
from robotter.agents.GitHubCopilot import GitHubCopilot
from robotter.agents.OpenAICodex import OpenAICodex
from robotter.agents.OpenCode import OpenCode


# ----------------------------------------------------------------------
class AgentType(StrEnum):
    """The AI agents whose configuration locations can be rendered to."""

    ClaudeCode = "claude-code"
    GitHubCopilot = "github-copilot"
    OpenAICodex = "openai-codex"
    OpenCode = "opencode"


# ----------------------------------------------------------------------
_AGENTS: dict[AgentType, type[Agent]] = {
    AgentType.ClaudeCode: ClaudeCode,
    AgentType.GitHubCopilot: GitHubCopilot,
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
@app.command("EntryPoint", no_args_is_help=True)
def EntryPoint(
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

        with dm.Nested(f"Rendering '{agent.name}'..."):
            if output_dir is None:
                RenderGlobal(template, agent_instance)
            else:
                RenderLocal(template, agent_instance, output_dir)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()  # pragma: no cover
