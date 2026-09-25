---
type: Change
title: Require a `.jinja`/`.jinja2` extension for templates
description: Only files whose names include a `.jinja` or `.jinja2` extension are rendered as Jinja2 templates; all other files are written verbatim.
tags: [rendering, templates, skills, jinja]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-25T19:34:21Z }
sources:
  - id: renderer
    resource: src/robotter/Renderer.py
    title: Template detection and output path derivation
  - id: lib
    resource: src/robotter/Lib.py
    title: Skill directory rendering
  - id: readme
    resource: README.md
    title: User-facing documentation
---

# Summary

Jinja2 rendering is now opt-in per file, keyed on a `.jinja` or `.jinja2` extension that may appear anywhere in the filename (`SKILL.jinja.md`, `instructions.jinja2.md`).[^renderer] Files without one are written verbatim, so content such as `{{ ... }}` survives unchanged. Frontmatter handling is unaffected.

# Motivation

Previously, every single-file template was rendered through Jinja2, and skill directories rendered every `.md`/`.markdown` file. Markdown content that legitimately contains Jinja-like syntax (examples of templating, other tools' placeholder syntax) was mangled or failed to render, and there was no way to opt out. An explicit extension makes the author's intent visible in the filename and leaves the remaining suffixes to describe the rendered file's type.

# Changes

- `Renderer.IsTemplate(path)`: returns `True` when any suffix of `path` is `.jinja` or `.jinja2` (case-insensitive).[^renderer]
- `Renderer.GetOutputPath(path)`: strips template suffixes from the filename (`SKILL.jinja.md` → `SKILL.md`).[^renderer]
- `Renderer.Parse`: renders the main content through Jinja2 only when the file is a template; otherwise returns the stripped content as-is.[^renderer]
- `Renderer.RenderedTemplate` renamed to `Renderer.ParsedContent`, since `Parse` no longer always renders its content.[^renderer]
- Skill directory rendering:[^lib]
  - Output paths are derived via `GetOutputPath`.
  - The `.md`/`.markdown` suffix list was removed; non-template files are copied byte for byte.
  - A top-level `SKILL.md` may come from `SKILL.md` or a template such as `SKILL.jinja.md`.
  - Rendering fails, writing nothing, when multiple source files produce the same output filename (for example, `SKILL.md` and `SKILL.jinja.md`), or when a file's output name matches a directory (for example, `scripts.jinja` and `scripts/run.py`).
- README examples renamed to `*.jinja.md` and the template rule documented.[^readme]

# Compatibility

Behavior change for existing users: templates named without a `.jinja`/`.jinja2` extension are no longer rendered, so `include_configuration(...)` calls and other Jinja constructs in them are emitted literally. Rename such files (for example, `instructions.md` → `instructions.jinja.md`) to restore rendering.

API change: code that references `Renderer.RenderedTemplate` must use `Renderer.ParsedContent` instead.

[^renderer]: Template detection and output path derivation
[^lib]: Skill directory rendering
[^readme]: User-facing documentation
