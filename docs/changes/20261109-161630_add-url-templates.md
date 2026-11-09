---
type: Change
title: Render templates referenced by URL
description: The render and render_skill commands accept an http(s) URL, including GitHub file and directory URLs, in place of a local template path.
tags: [feature, templates, remote]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-11-09T16:16:30Z }
sources:
  - id: remote
    resource: src/robotter/Remote.py
    title: URL detection and download of templates
  - id: main
    resource: src/robotter/__main__.py
    title: Command-line entry point
  - id: readme
    resource: README.md
    title: User documentation
  - id: tests
    resource: tests/Remote_test.py
    title: Tests for remote template download
---

# Summary

`robotter render` and `robotter render_skill` accept an `http`/`https` URL as `<template>`. GitHub file (`/blob/`) and directory (`/tree/`) URLs are downloaded through the GitHub contents API; any other URL is downloaded as a single file.[^remote] The download is placed in a temporary directory and rendered with the existing local rendering logic.[^main]

# Motivation

Templates and skills are commonly kept in a shared repository. Rendering them previously required cloning that repository first; referencing the template by URL removes that step and allows a skill directory hosted on GitHub to be installed with one command.[^readme]

# Changes

- New `Remote` module providing `IsUrl` and `Download`.[^remote]
- GitHub refs containing slashes are resolved by trying the shortest ref that GitHub recognizes.[^remote]
- `GITHUB_TOKEN`, when set, is sent to `api.github.com` and `raw.githubusercontent.com` over https only, as an unredirected header, to access private repositories and raise the API rate limit.[^remote]
- Downloads are restricted to http(s) handlers, limited to 10 MB per file and to 500 entries / 50 MB per directory, and reject names that are not a single path component.[^remote]
- The `<template>` argument changes from a `Path` to a `str` validated by a callback, so URLs bypass the local existence check.[^main]
- Downloaded templates are always copied rather than symlinked, since the download is discarded after rendering.[^main]
- `render` reports an error when the resolved template is a directory.[^main]
- README documents URL templates and adds a GitHub skill-directory example.[^readme]
- Tests cover URL detection, GitHub and generic downloads, limits, token handling, and the CLI paths.[^tests]

# Compatibility

Local template paths behave as before. `include_configuration` within a downloaded template can only reach files within the downloaded file or directory.[^readme]

[^remote]: URL detection and download of templates
[^main]: Command-line entry point
[^readme]: User documentation
[^tests]: Tests for remote template download
