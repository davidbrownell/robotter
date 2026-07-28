**Project:**
[![License](https://img.shields.io/github/license/davidbrownell/robotter?color=dark-green)](https://github.com/davidbrownell/robotter/blob/master/LICENSE)

**Package:**
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/robotter?color=dark-green)](https://pypi.org/project/robotter/)
[![PyPI - Version](https://img.shields.io/pypi/v/robotter?color=dark-green)](https://pypi.org/project/robotter/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/robotter)](https://pypistats.org/packages/robotter)

**Development:**
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![ty](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ty/main/assets/badge/v0.json)](https://github.com/astral-sh/ty)
[![pytest](https://img.shields.io/badge/pytest-enabled-brightgreen)](https://docs.pytest.org/)
[![CI](https://github.com/davidbrownell/robotter/actions/workflows/CICD.yml/badge.svg)](https://github.com/davidbrownell/robotter/actions/workflows/CICD.yml)
[![Code Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/davidbrownell/f15146b1b8fdc0a5d45ac0eb786a84f7/raw/robotter_code_coverage.json)](https://github.com/davidbrownell/robotter/actions)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/y/davidbrownell/robotter?color=dark-green)](https://github.com/davidbrownell/robotter/commits/main/)

<!-- Content above this delimiter will be copied to the generated README.md file. DO NOT REMOVE THIS COMMENT, as it will cause regeneration to fail. -->

## Contents
- [Overview](#overview)
  - [Rendering a template](#how-to-use-robotter)
  - [Editing an agent's configuration](#editing-an-agents-configuration)
  - [Browsing an agent's global configuration](#browsing-an-agents-global-configuration)
- [Installation](#installation)
- [Development](#development)
- [Additional Information](#additional-information)
- [License](#license)

## Overview
`robotter` composes GenAI "dotfiles" (the instruction/configuration files read by AI coding agents) from a single source template.

Different agents read their configuration from different locations under different filenames. `robotter` renders one [Jinja2](https://jinja.palletsprojects.com/) template and writes the result to the appropriate location(s) for a target agent, at either global (user-level) or project scope:

| Agent | Value | Project Configuration | Global Configuration |
| --- | --- | --- | --- |
| Claude Code | `claude-code` | `CLAUDE.md` | `~/.claude/CLAUDE.md` |
| GitHub Copilot | `github-copilot` | `.github/copilot-instructions.md` | `<VS Code user>/prompts` |
| OpenAI Codex | `openai-codex` | `AGENTS.md` | `~/.codex/AGENTS.md` |
| OpenCode | `opencode` | `AGENTS.md` | `~/.config/opencode/AGENTS.md` |

Templates may include optional [YAML](https://yaml.org/) frontmatter (preserved in the rendered output) and may compose other templates via the `include_configuration("<relative path>")` function, letting you maintain shared content once and assemble agent-specific files from it.

### How to use `robotter`
Render a template to an agent's configuration location(s):

```shell
uvx robotter render <template> <agent> [<dir>] [--verbose] [--debug]
```

| Argument / Option | Description |
| --- | --- |
| `<template>` | Path to the template file to render. |
| `<agent>` | Target agent: `claude-code`, `github-copilot`, `openai-codex`, or `opencode`. |
| `<dir>` | Render project-level configuration under this directory. When omitted, global (user-level) configuration is rendered. |
| `--verbose` | Write verbose information to the terminal. |
| `--debug` | Write debug information to the terminal. |

**Examples**

Render `instructions.md` to the current user's global Claude Code configuration:

```shell
uvx robotter render instructions.md claude-code
```

Render `instructions.md` to the project-level OpenCode configuration under `./my-project`:

```shell
uvx robotter render instructions.md opencode ./my-project
```

### Editing an agent's configuration
Open an agent's rendered configuration file in an editor:

```shell
uvx robotter edit <agent> [<dir>] [--verbose] [--debug]
```

| Argument / Option | Description |
| --- | --- |
| `<agent>` | Target agent: `claude-code`, `github-copilot`, `openai-codex`, or `opencode`. |
| `<dir>` | Edit project-level configuration under this directory. When omitted, global (user-level) configuration is edited. |
| `--verbose` | Write verbose information to the terminal. |
| `--debug` | Write debug information to the terminal. |

The configuration file must already exist (for example, produced by a prior `render`); `edit` fails if it does not. The editor is selected from the `VISUAL` or `EDITOR` environment variable when set, otherwise the operating system's default handler for the file is used.

**Examples**

Edit the current user's global Claude Code configuration:

```shell
uvx robotter edit claude-code
```

Edit the project-level OpenCode configuration under `./my-project`:

```shell
uvx robotter edit opencode ./my-project
```

### Browsing an agent's global configuration
Open an agent's global (user-level) configuration directory in a file browser:

```shell
uvx robotter browse <agent> [--verbose] [--debug]
```

| Argument / Option | Description |
| --- | --- |
| `<agent>` | Target agent: `claude-code`, `github-copilot`, `openai-codex`, or `opencode`. |
| `--verbose` | Write verbose information to the terminal. |
| `--debug` | Write debug information to the terminal. |

The directory is opened using the operating system's default file browser. The directory must already exist (for example, produced by a prior `render`); `browse` fails if it does not.

**Example**

Browse the current user's global Claude Code configuration directory:

```shell
uvx robotter browse claude-code
```

### Example Configuration
A configuration file is a [Jinja2](https://jinja.palletsprojects.com/) template with optional [YAML](https://yaml.org/) frontmatter. Use the `include_configuration("<relative path>")` function to compose shared content from another configuration file, letting you maintain that content once and reuse it across multiple templates.

The following `instructions.md` template includes a shared `shared/coding-standards.md` file:

```jinja
---
description: Instructions for AI coding agents
---
# Project Instructions

## Overview
This project composes GenAI dotfiles from a single source template.

## Coding Standards
{{ include_configuration("shared/coding-standards.md") }}
```

The included `shared/coding-standards.md` file (its frontmatter, if any, is ignored when included):

```markdown
- Prefer clarity over cleverness.
- Write tests for all new functionality.
- Document public interfaces.
```

The path passed to `include_configuration` is resolved relative to the file that contains the call, so a template in one directory can include a file located in a subdirectory (`"shared/coding-standards.md"`) or a parent directory (`"../coding-standards.md"`). Included files may themselves call `include_configuration`, allowing configuration to be composed from arbitrarily nested fragments.

Rendering the `instructions.md` template above produces the following output (the frontmatter is preserved; the `include_configuration` call is replaced with the rendered content of the included file):

```markdown
---
description: Instructions for AI coding agents
---
# Project Instructions

## Overview
This project composes GenAI dotfiles from a single source template.

## Coding Standards
- Prefer clarity over cleverness.
- Write tests for all new functionality.
- Document public interfaces.
```

<!-- Content below this delimiter will be copied to the generated README.md file. DO NOT REMOVE THIS COMMENT, as it will cause regeneration to fail. -->

## Installation
Note that it isn't necessary to install `robotter` when running via `uvx`.

| Installation Method | Command |
| --- | --- |
| Via [uv](https://github.com/astral-sh/uv) | `uv add robotter` |
| Via [pip](https://pip.pypa.io/en/stable/) | `pip install robotter` |

### Verifying Signed Artifacts
Artifacts are signed and verified using [py-minisign](https://github.com/x13a/py-minisign) and the public key in the file `./minisign_key.pub`.

To verify that an artifact is valid, visit [the latest release](https://github.com/davidbrownell/robotter/releases/latest) and download the `.minisign` signature file that corresponds to the artifact, then run the following command, replacing `<filename>` with the name of the artifact to be verified:

```shell
uv run --with py-minisign python -c "import minisign; minisign.PublicKey.from_file('minisign_key.pub').verify_file('<filename>'); print('The file has been verified.')"
```

## Development
Please visit [Contributing](https://github.com/davidbrownell/robotter/blob/main/CONTRIBUTING.md) and [Development](https://github.com/davidbrownell/robotter/blob/main/DEVELOPMENT.md) for information on contributing to this project.

## Additional Information
Additional information can be found at these locations.

| Title | Document | Description |
| --- | --- | --- |
| Code of Conduct | [CODE_OF_CONDUCT.md](https://github.com/davidbrownell/robotter/blob/main/CODE_OF_CONDUCT.md) | Information about the norms, rules, and responsibilities we adhere to when participating in this open source community. |
| Contributing | [CONTRIBUTING.md](https://github.com/davidbrownell/robotter/blob/main/CONTRIBUTING.md) | Information about contributing to this project. |
| Development | [DEVELOPMENT.md](https://github.com/davidbrownell/robotter/blob/main/DEVELOPMENT.md) | Information about development activities involved in making changes to this project. |
| Governance | [GOVERNANCE.md](https://github.com/davidbrownell/robotter/blob/main/GOVERNANCE.md) | Information about how this project is governed. |
| Maintainers | [MAINTAINERS.md](https://github.com/davidbrownell/robotter/blob/main/MAINTAINERS.md) | Information about individuals who maintain this project. |
| Security | [SECURITY.md](https://github.com/davidbrownell/robotter/blob/main/SECURITY.md) | Information about how to privately report security issues associated with this project. |

## License
`robotter` is licensed under the <a href="https://choosealicense.com/licenses/MIT/" target="_blank">MIT</a> license.
