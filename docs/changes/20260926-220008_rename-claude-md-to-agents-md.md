---
type: Change
title: Rename the repository instructions file to AGENTS.md
description: The repository's agent instructions move from CLAUDE.md to AGENTS.md and are updated to version 0.8.0 of the python_development instructions.
tags: [configuration, agents]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T22:00:08Z }
sources:
  - id: agents
    resource: AGENTS.md
    title: Repository agent instructions
---

# Summary

The repository's agent instructions file is renamed from `CLAUDE.md` to `AGENTS.md` and regenerated from version 0.8.0 of the `python_development` instructions.[^agents]

# Motivation

robotter renders agent instructions to `AGENTS.md` for all supported agents, including Claude Code. The repository's own instructions file now follows the same convention and picks up the latest instruction content.

# Changes

- `CLAUDE.md` removed; `AGENTS.md` added.[^agents]
- Version header changed from `Version: 0.6.0` to `python_development Version: 0.8.0`.[^agents]
- "SOLID" expanded to "SOLID design principles".[^agents]
- New "General" section under "Python Development" requiring `python`-related tasks to run via `uv`.[^agents]

# Compatibility

Tools that read only `CLAUDE.md` from the repository root no longer find project instructions.

[^agents]: Repository agent instructions
