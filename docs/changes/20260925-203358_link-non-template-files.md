---
type: Change
title: Link non-template files when rendering globally
description: Global rendering installs non-template files as symbolic links to their sources; `--copy` restores copying, and project-level rendering always copies.
tags: [rendering, skills, symlinks, cli]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-25T20:33:58Z }
sources:
  - id: lib
    resource: src/robotter/Lib.py
    title: Output writing and symbolic link creation
  - id: main
    resource: src/robotter/__main__.py
    title: Command-line `--copy` option
  - id: readme
    resource: README.md
    title: User-facing documentation
---

# Summary

When rendering globally, a file without a `.jinja`/`.jinja2` extension is installed as a symbolic link to its source rather than copied.[^lib] Templates are still written as files, and project-level rendering always copies. `render` and `render_skill` gain a `--copy` option that copies non-template files instead of linking them.[^main]

# Motivation

Non-template files are reproduced verbatim, so a copy only goes stale: every edit to the source required rendering again before the agent saw it. Linking makes edits take effect immediately. Project-level output is typically committed to a repository, where a link to a file on the author's machine would be meaningless, so it continues to copy. `--copy` covers hosts that cannot create symbolic links (for example, Windows without Developer Mode or administrator rights).

# Changes

- `RenderGlobal` and `RenderGlobalSkill` accept a keyword-only `copy` argument (default `False`).[^lib]
- Non-template single files are reproduced byte for byte instead of being parsed and re-emitted; skill files are still parsed to read the skill name from frontmatter.[^lib]
- Links are created under a temporary name and moved into place, so an existing file survives a failed link; the temporary link is removed if the move fails.[^lib]
- A destination that already is the source (or a link to it) is left untouched rather than replaced by a link to itself.[^lib]
- A link failure writes an error suggesting copying and stops rendering.[^lib]
- Skill directories create all links before writing any template, so a host that cannot create links fails without writing files.[^lib]
- Writing a file over a link left by a previous render removes the link first, so its source is never overwritten.[^lib]
- `--copy` added to `render` and `render_skill`.[^main]
- README documents the linking behavior and `--copy`.[^readme]

# Compatibility

Behavior change for existing users: global rendering of non-template files now creates symbolic links. On hosts that cannot create them, rendering fails until `--copy` is passed.

Non-template single files are no longer normalized (leading/trailing whitespace and frontmatter formatting are preserved exactly as in the source).

[^lib]: Output writing and symbolic link creation
[^main]: Command-line `--copy` option
[^readme]: User-facing documentation
