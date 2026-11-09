"""Retrieval of templates referenced by URL rather than by local path."""

import json
import os

from http import HTTPStatus
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urlparse
from urllib.request import (
    HTTPDefaultErrorHandler,
    HTTPErrorProcessor,
    HTTPHandler,
    HTTPRedirectHandler,
    HTTPSHandler,
    OpenerDirector,
    Request,
)


# ----------------------------------------------------------------------
def IsUrl(value: str) -> bool:
    """Return True if `value` is an http(s) URL."""

    return urlparse(value).scheme in ("http", "https")


# ----------------------------------------------------------------------
def Download(url: str, output_dir: Path) -> Path:
    """Download the file or GitHub directory at `url` into `output_dir`, returning its local path.

    The local path keeps the remote name, since a skill directory's name identifies the skill.
    """

    parsed = urlparse(url)
    parts = [_ValidateName(unquote(part)) for part in parsed.path.split("/") if part]

    if parsed.hostname not in ("github.com", "www.github.com"):
        if not parts:
            msg = f"The URL '{url}' does not name a file."
            raise ValueError(msg)

        destination = output_dir / parts[-1]
        destination.write_bytes(_Fetch(url))

        return destination

    min_parts = 4  # owner, repo, `blob` or `tree`, ref

    if len(parts) < min_parts or parts[2] not in ("blob", "tree"):
        msg = f"The GitHub URL '{url}' does not reference a file or directory within a repository."
        raise ValueError(msg)

    owner, repo = parts[:2]
    ref_and_path = parts[3:]

    # Refs may contain slashes (`feature/x`), so the boundary between ref and path is ambiguous;
    # the shortest ref that GitHub recognizes wins.
    for index in range(1, len(ref_and_path) + 1):
        ref = "/".join(ref_and_path[:index])
        path = "/".join(ref_and_path[index:])

        try:
            content = _FetchJson(
                f"https://api.github.com/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/contents/{quote(path)}?ref={quote(ref, safe='')}",
            )
        except HTTPError as ex:
            if ex.code == HTTPStatus.NOT_FOUND:
                continue

            raise

        destination = output_dir / (ref_and_path[-1] if path else repo)

        _DownloadGitHubContent(content, destination, (0, 0))
        return destination

    msg = f"The GitHub URL '{url}' could not be found."
    raise ValueError(msg)


# ----------------------------------------------------------------------
# |
# |  Private Functions
# |
# ----------------------------------------------------------------------
_GitHubContent = dict[str, object] | list[dict[str, object]]

# Templates are text files and skills are small; anything larger is not a template.
_MAX_RESPONSE_BYTES = 10 * 1024 * 1024

# A directory URL can reference an entire repository; these bound the download as a whole, which the
# per-response limit does not.
_MAX_DOWNLOAD_ENTRIES = 500
_MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024


# ----------------------------------------------------------------------
def _ValidateName(name: str) -> str:
    # Names come from the URL or the GitHub API and become local paths; a name that is not a single
    # path component (`..`, `a/b`, `C:x`) could write outside the download directory.
    if name == ".." or Path(name).name != name:
        msg = f"'{name}' is not a valid file or directory name."
        raise ValueError(msg)

    return name


# ----------------------------------------------------------------------
def _DownloadGitHubContent(
    content: _GitHubContent,
    destination: Path,
    totals: tuple[int, int],
) -> tuple[int, int]:
    """Write `content` (a GitHub contents API response) to `destination`, returning the updated (entries, bytes) totals."""

    if isinstance(content, list):
        totals = _Tally(totals, 0)
        destination.mkdir(parents=True, exist_ok=True)

        for entry in content:
            totals = _DownloadGitHubContent(
                # Directory listings omit the contents of subdirectories.
                entry if entry["type"] == "file" else _FetchJson(str(entry["url"])),
                destination / _ValidateName(str(entry["name"])),
                totals,
            )

        return totals

    if content["type"] != "file":
        msg = f"'{destination.name}' is a {content['type']}, which cannot be downloaded."
        raise ValueError(msg)

    data = _Fetch(str(content["download_url"]))
    totals = _Tally(totals, len(data))

    destination.write_bytes(data)
    return totals


# ----------------------------------------------------------------------
def _Tally(totals: tuple[int, int], num_bytes: int) -> tuple[int, int]:
    entries, total_bytes = totals[0] + 1, totals[1] + num_bytes

    if entries > _MAX_DOWNLOAD_ENTRIES or total_bytes > _MAX_DOWNLOAD_BYTES:
        msg = f"The download exceeds the maximum of {_MAX_DOWNLOAD_ENTRIES} files and directories or {_MAX_DOWNLOAD_BYTES} bytes."
        raise ValueError(msg)

    return entries, total_bytes


# ----------------------------------------------------------------------
def _FetchJson(url: str) -> _GitHubContent:
    return json.loads(_Fetch(url))


# ----------------------------------------------------------------------
def _Fetch(url: str) -> bytes:
    # The default opener also handles `file:` and `ftp:` URLs; a template URL should never read
    # from anywhere other than the web.
    opener = OpenerDirector()

    for handler in (
        HTTPHandler(),
        HTTPSHandler(),
        HTTPRedirectHandler(),
        HTTPDefaultErrorHandler(),
        HTTPErrorProcessor(),
    ):
        opener.add_handler(handler)

    # The handlers above restrict the opener to http(s), which is the concern S310 raises.
    request = Request(url)  # noqa: S310

    # Authentication grants access to private repositories and raises GitHub's rate limit, which
    # directory downloads (one request per directory) can otherwise exhaust. The header is
    # unredirected so that a redirect to another host does not receive the token, and is limited to
    # https so that the token is never sent in cleartext.
    token = os.environ.get("GITHUB_TOKEN")
    parsed = urlparse(url)

    if (
        token
        and parsed.scheme == "https"
        and parsed.hostname in ("api.github.com", "raw.githubusercontent.com")
    ):
        request.add_unredirected_header("Authorization", f"Bearer {token}")

    with opener.open(request, timeout=60) as response:
        content = response.read(_MAX_RESPONSE_BYTES + 1)

    if len(content) > _MAX_RESPONSE_BYTES:
        msg = f"'{url}' exceeds the maximum size of {_MAX_RESPONSE_BYTES} bytes."
        raise ValueError(msg)

    return content
