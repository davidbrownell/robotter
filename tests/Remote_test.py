"""Unit tests for robotter.Remote"""

import io
import json

from email.message import Message
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import FileHandler, FTPHandler, Request

import pytest

import robotter.Remote as remote_module

from robotter.Remote import Download, IsUrl


# ----------------------------------------------------------------------
class _FakeOpener:
    """Serves canned responses in place of network requests."""

    responses: dict[str, bytes] = {}
    requests: list[tuple[str, list[tuple[str, str]]]] = []
    handlers: list[type] = []

    # ----------------------------------------------------------------------
    def add_handler(self, handler: object) -> None:
        _FakeOpener.handlers.append(type(handler))

    # ----------------------------------------------------------------------
    def open(self, request: Request, timeout: float) -> io.BytesIO:  # noqa: ARG002
        url = request.full_url

        # Only unredirected headers are recorded, as those are the only ones withheld from redirects.
        _FakeOpener.requests.append((url, list(request.unredirected_hdrs.items())))

        if url not in _FakeOpener.responses:
            raise HTTPError(url, 404, "Not Found", Message(), None)

        return io.BytesIO(_FakeOpener.responses[url])


# ----------------------------------------------------------------------
@pytest.fixture
def opener(monkeypatch: pytest.MonkeyPatch) -> type[_FakeOpener]:
    monkeypatch.setattr(_FakeOpener, "responses", {})
    monkeypatch.setattr(_FakeOpener, "requests", [])
    monkeypatch.setattr(_FakeOpener, "handlers", [])
    monkeypatch.setattr(remote_module, "OpenerDirector", _FakeOpener)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    return _FakeOpener


# ----------------------------------------------------------------------
_API = "https://api.github.com/repos/owner/repo/contents"


# ----------------------------------------------------------------------
def _File(name: str, download_url: str) -> dict[str, str]:
    return {"type": "file", "name": name, "download_url": download_url, "url": f"{_API}/{name}"}


# ----------------------------------------------------------------------
class TestIsUrl:
    # ----------------------------------------------------------------------
    @pytest.mark.parametrize("value", ["http://example.com/a.md", "https://github.com/owner/repo"])
    def test_http_urls(self, value: str):
        assert IsUrl(value) is True

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "value", ["template.md", "C:\\templates\\a.md", "file:///a.md", "ftp://host/a.md"]
    )
    def test_non_http_values(self, value: str):
        assert IsUrl(value) is False


# ----------------------------------------------------------------------
class TestDownload:
    # ----------------------------------------------------------------------
    def test_generic_url_downloads_file_named_by_url(self, opener, tmp_path: Path):
        opener.responses["https://example.com/dir/my%20file.md"] = b"content"

        result = Download("https://example.com/dir/my%20file.md", tmp_path)

        assert result == tmp_path / "my file.md"
        assert result.read_bytes() == b"content"

    # ----------------------------------------------------------------------
    def test_generic_url_without_path_raises(self, opener, tmp_path: Path):
        with pytest.raises(ValueError, match=r"^The URL 'https://example.com/' does not name a file\.$"):
            Download("https://example.com/", tmp_path)

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        ("url", "name"),
        [
            ("https://example.com/a/..%2F..%2Fevil.md", "../../evil.md"),
            ("https://example.com/a/%2Fevil.md", "/evil.md"),
            ("https://example.com/a/../evil.md", ".."),
            ("https://github.com/owner/repo/blob/main/..%2Fevil.md", "../evil.md"),
        ],
    )
    def test_url_with_invalid_name_raises(self, opener, tmp_path: Path, url: str, name: str):
        with pytest.raises(ValueError) as ex:
            Download(url, tmp_path)

        assert str(ex.value) == f"'{name}' is not a valid file or directory name."
        assert opener.requests == []

    # ----------------------------------------------------------------------
    def test_response_exceeding_maximum_size_raises(self, opener, tmp_path: Path):
        opener.responses["https://example.com/a.md"] = b"x" * (10 * 1024 * 1024 + 1)

        with pytest.raises(ValueError) as ex:
            Download("https://example.com/a.md", tmp_path)

        assert str(ex.value) == "'https://example.com/a.md' exceeds the maximum size of 10485760 bytes."
        assert not (tmp_path / "a.md").exists()

    # ----------------------------------------------------------------------
    def test_github_blob_downloads_file(self, opener, tmp_path: Path):
        opener.responses[f"{_API}/skills/SKILL.md?ref=main"] = json.dumps(
            _File("SKILL.md", "https://raw.githubusercontent.com/owner/repo/main/skills/SKILL.md"),
        ).encode()
        opener.responses["https://raw.githubusercontent.com/owner/repo/main/skills/SKILL.md"] = b"skill"

        result = Download("https://github.com/owner/repo/blob/main/skills/SKILL.md", tmp_path)

        assert result == tmp_path / "SKILL.md"
        assert result.read_bytes() == b"skill"

    # ----------------------------------------------------------------------
    def test_github_tree_downloads_directory_recursively(self, opener, tmp_path: Path):
        opener.responses[f"{_API}/skills/review?ref=main"] = json.dumps(
            [
                _File("SKILL.md", "https://raw/SKILL.md"),
                {"type": "dir", "name": "scripts", "url": f"{_API}/skills/review/scripts?ref=main"},
            ],
        ).encode()
        opener.responses[f"{_API}/skills/review/scripts?ref=main"] = json.dumps(
            [_File("run.py", "https://raw/run.py")],
        ).encode()
        opener.responses["https://raw/SKILL.md"] = b"skill"
        opener.responses["https://raw/run.py"] = b"script"

        result = Download("https://github.com/owner/repo/tree/main/skills/review", tmp_path)

        assert result == tmp_path / "review"
        assert (result / "SKILL.md").read_bytes() == b"skill"
        assert (result / "scripts" / "run.py").read_bytes() == b"script"

    # ----------------------------------------------------------------------
    def test_github_repository_root_is_named_after_repository(self, opener, tmp_path: Path):
        opener.responses[f"{_API}/?ref=main"] = json.dumps(
            [_File("SKILL.md", "https://raw/SKILL.md")]
        ).encode()
        opener.responses["https://raw/SKILL.md"] = b"skill"

        result = Download("https://github.com/owner/repo/tree/main", tmp_path)

        assert result == tmp_path / "repo"
        assert (result / "SKILL.md").read_bytes() == b"skill"

    # ----------------------------------------------------------------------
    def test_github_ref_containing_slashes(self, opener, tmp_path: Path):
        opener.responses[f"{_API}/SKILL.md?ref=feature%2Fx"] = json.dumps(
            _File("SKILL.md", "https://raw/SKILL.md"),
        ).encode()
        opener.responses["https://raw/SKILL.md"] = b"skill"

        result = Download("https://github.com/owner/repo/blob/feature/x/SKILL.md", tmp_path)

        assert result.read_bytes() == b"skill"
        assert [url for url, _ in opener.requests] == [
            f"{_API}/x/SKILL.md?ref=feature",
            f"{_API}/SKILL.md?ref=feature%2Fx",
            "https://raw/SKILL.md",
        ]

    # ----------------------------------------------------------------------
    def test_github_ref_containing_slashes_without_path_is_named_after_repository(
        self, opener, tmp_path: Path
    ):
        opener.responses[f"{_API}/?ref=feature%2Fx"] = json.dumps(
            [_File("SKILL.md", "https://raw/SKILL.md")]
        ).encode()
        opener.responses["https://raw/SKILL.md"] = b"skill"

        result = Download("https://github.com/owner/repo/tree/feature/x", tmp_path)

        assert result == tmp_path / "repo"
        assert (result / "SKILL.md").read_bytes() == b"skill"

    # ----------------------------------------------------------------------
    def test_github_owner_and_repo_are_quoted(self, opener, tmp_path: Path):
        github_url = "https://github.com/own%3Fer/re%23po/blob/main/a.md"

        opener.responses["https://api.github.com/repos/own%3Fer/re%23po/contents/a.md?ref=main"] = json.dumps(
            _File("a.md", "https://raw/a.md")
        ).encode()
        opener.responses["https://raw/a.md"] = b"a"

        result = Download(github_url, tmp_path)

        assert result.read_bytes() == b"a"

    # ----------------------------------------------------------------------
    def test_github_entry_with_invalid_name_raises(self, opener, tmp_path: Path):
        opener.responses[f"{_API}/skills?ref=main"] = json.dumps([_File("..", "https://raw/evil")]).encode()

        with pytest.raises(ValueError) as ex:
            Download("https://github.com/owner/repo/tree/main/skills", tmp_path)

        assert str(ex.value) == "'..' is not a valid file or directory name."
        assert [url for url, _ in opener.requests] == [f"{_API}/skills?ref=main"]

    # ----------------------------------------------------------------------
    def test_github_not_found_raises(self, opener, tmp_path: Path):
        with pytest.raises(
            ValueError,
            match=r"^The GitHub URL 'https://github.com/owner/repo/blob/main/a.md' could not be found\.$",
        ):
            Download("https://github.com/owner/repo/blob/main/a.md", tmp_path)

    # ----------------------------------------------------------------------
    def test_github_errors_other_than_not_found_are_raised(self, opener, tmp_path: Path, monkeypatch):
        def Open(self, url: str, timeout: float):  # noqa: ARG001
            raise HTTPError(url, 403, "Forbidden", Message(), None)

        monkeypatch.setattr(_FakeOpener, "open", Open)

        with pytest.raises(HTTPError) as ex:
            Download("https://github.com/owner/repo/blob/main/a.md", tmp_path)

        assert ex.value.code == 403

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "url",
        [
            "https://github.com/owner/repo",
            "https://github.com/owner/repo/tree",
            "https://github.com/owner/repo/issues/1",
        ],
    )
    def test_github_url_outside_repository_contents_raises(self, opener, tmp_path: Path, url: str):
        with pytest.raises(ValueError) as ex:
            Download(url, tmp_path)

        assert str(ex.value) == (
            f"The GitHub URL '{url}' does not reference a file or directory within a repository."
        )

    # ----------------------------------------------------------------------
    def test_github_unsupported_content_type_raises(self, opener, tmp_path: Path):
        opener.responses[f"{_API}/link?ref=main"] = json.dumps({"type": "symlink", "name": "link"}).encode()

        with pytest.raises(ValueError, match=r"^'link' is a symlink, which cannot be downloaded\.$"):
            Download("https://github.com/owner/repo/blob/main/link", tmp_path)

    # ----------------------------------------------------------------------
    def test_github_token_is_sent_to_github(self, opener, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "secret")

        opener.responses[f"{_API}/a.md?ref=main"] = json.dumps(
            _File("a.md", "https://raw.githubusercontent.com/owner/repo/main/a.md"),
        ).encode()
        opener.responses["https://raw.githubusercontent.com/owner/repo/main/a.md"] = b"a"

        Download("https://github.com/owner/repo/blob/main/a.md", tmp_path)

        assert [headers for _, headers in opener.requests] == [
            [("Authorization", "Bearer secret")],
            [("Authorization", "Bearer secret")],
        ]

    # ----------------------------------------------------------------------
    def test_github_token_is_not_sent_elsewhere(self, opener, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "secret")
        opener.responses["https://example.com/a.md"] = b"a"

        Download("https://example.com/a.md", tmp_path)

        assert opener.requests == [("https://example.com/a.md", [])]

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "url", ["http://api.github.com/a.md", "http://raw.githubusercontent.com/owner/repo/main/a.md"]
    )
    def test_github_token_is_not_sent_without_https(self, opener, tmp_path: Path, monkeypatch, url: str):
        monkeypatch.setenv("GITHUB_TOKEN", "secret")
        opener.responses[url] = b"a"

        Download(url, tmp_path)

        assert opener.requests == [(url, [])]

    # ----------------------------------------------------------------------
    def test_github_directory_exceeding_maximum_entries_raises(self, opener, tmp_path: Path):
        # The directory itself is the first entry, so its 500th file exceeds the 500 entry limit.
        opener.responses[f"{_API}/skills?ref=main"] = json.dumps(
            [_File(f"{index}.md", f"https://raw/{index}.md") for index in range(500)],
        ).encode()

        for index in range(500):
            opener.responses[f"https://raw/{index}.md"] = b"a"

        with pytest.raises(ValueError) as ex:
            Download("https://github.com/owner/repo/tree/main/skills", tmp_path)

        assert str(ex.value) == (
            "The download exceeds the maximum of 500 files and directories or 52428800 bytes."
        )
        assert (tmp_path / "skills" / "498.md").is_file()
        assert not (tmp_path / "skills" / "499.md").exists()

    # ----------------------------------------------------------------------
    def test_github_directory_exceeding_maximum_size_raises(self, opener, tmp_path: Path):
        opener.responses[f"{_API}/skills?ref=main"] = json.dumps(
            [
                _File("0.md", "https://raw/large.md"),
                {"type": "dir", "name": "nested", "url": f"{_API}/skills/nested?ref=main"},
            ],
        ).encode()
        opener.responses[f"{_API}/skills/nested?ref=main"] = json.dumps(
            [_File(f"{index}.md", "https://raw/large.md") for index in range(1, 6)],
        ).encode()
        opener.responses["https://raw/large.md"] = b"x" * (10 * 1024 * 1024)

        with pytest.raises(ValueError) as ex:
            Download("https://github.com/owner/repo/tree/main/skills", tmp_path)

        assert str(ex.value) == (
            "The download exceeds the maximum of 500 files and directories or 52428800 bytes."
        )
        assert (tmp_path / "skills" / "nested" / "4.md").is_file()
        assert not (tmp_path / "skills" / "nested" / "5.md").exists()

    # ----------------------------------------------------------------------
    def test_only_web_urls_can_be_opened(self, opener, tmp_path: Path):
        opener.responses["https://example.com/a.md"] = b"a"

        Download("https://example.com/a.md", tmp_path)

        assert opener.handlers
        assert FileHandler not in opener.handlers
        assert FTPHandler not in opener.handlers
