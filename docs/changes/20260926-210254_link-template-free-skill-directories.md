---
type: Change
title: Fix stale links in skill directories that contain no templates
description: Global rendering installs a skill directory without templates as a single symbolic link to its source directory, so files added to or removed from the source are reflected.
tags: [rendering, skills, symlinks]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T21:02:54Z }
sources:
  - id: lib
    resource: src/robotter/Lib.py
    title: Skill directory rendering and symbolic link creation
  - id: tests
    resource: tests/Lib_test.py
    title: Skill directory linking tests
  - id: readme
    resource: README.md
    title: User-facing documentation
---

# Summary

Fixes a bug introduced by `20260925-203358_link-non-template-files`. When rendering globally, a skill directory that contains no `.jinja`/`.jinja2` templates is now installed as one symbolic link to the source directory rather than as a directory of per-file links.[^lib] Any existing skill directory at the destination is replaced.

# Motivation

Linking non-template files was intended to make source changes take effect without rendering again. Per-file links only achieved that for edits to existing files: files added to or removed from the source were not reflected until the skill was rendered again. Without templates, the rendered skill is identical to its source, so linking the directory itself restores the intended behavior.

# Changes

- `_RenderSkillDirectory` links the whole directory when linking is allowed and no file is a template.[^lib]
- A destination directory left as a link by a previous render is unlinked before templates are written, so rendered files are never written into the source.[^lib]
- `_LinkFile` renamed to `_LinkPath` and extended to link directories:[^lib]
  - Directory links are created with `target_is_directory=True`, required on Windows.
  - An existing link or directory at the destination is removed before the new link is moved into place; a file link never replaces a directory, so directory contents are not deleted by a mismatched link.
  - Replacing a real directory that contains the source is refused with an error, since removing it would delete the source. A link to such a directory is replaced safely.
- The link failure message now reads "enable 'copy' to copy it instead" to cover both files and directories.[^lib]
- Tests cover linking, replacement of existing directories and links, transitions between linked and rendered directories, the containing-directory guard, and link failure.[^tests]
- README documents the directory-linking behavior.[^readme]

# Compatibility

Behavior change for existing users: re-rendering a template-free skill globally replaces the previously installed directory (including any files added to it by hand) with a symbolic link. Project-level rendering and `--copy` are unaffected.

[^lib]: Skill directory rendering and symbolic link creation
[^tests]: Skill directory linking tests
[^readme]: User-facing documentation
