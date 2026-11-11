"""Check that relative Markdown links point at files that exist.

The root docs, documentation tree, and component READMEs are part of the
repository's navigation contract, so a stale link should fail CI like a broken
import. External URLs and in-page anchors are intentionally not fetched or
validated.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import unquote

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

COMPONENT_READMES = [
    ROOT / "api/README.md",
    ROOT / "dashboard/README.md",
    *sorted((ROOT / "src").rglob("README.md")),
]
MARKDOWN_FILES = sorted(
    {
        *ROOT.glob("*.md"),
        *(ROOT / ".github").rglob("*.md"),
        *DOCS.rglob("*.md"),
        *COMPONENT_READMES,
    }
)

FENCE = re.compile(r"^\s*(`{3,}|~{3,})([^\n]*)$")
INLINE_CODE = re.compile(r"`[^`\n]*`")
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:")


def _local_target(raw: str) -> str | None:
    target = raw.strip()
    if not target:
        return None
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    target = unquote(target.split("#", 1)[0])
    if not target or target.startswith(EXTERNAL_PREFIXES):
        return None
    return target


def _without_fenced_code(text: str) -> str:
    """Skip backtick/tilde fences, including longer fences containing shorter ones."""
    prose = []
    fence = None
    for line in text.splitlines(keepends=True):
        match = FENCE.match(line)
        if fence is not None:
            if (
                match
                and match[1][0] == fence[0]
                and len(match[1]) >= len(fence)
                and not match[2].strip()
            ):
                fence = None
        elif match:
            fence = match[1]
        else:
            prose.append(line)
    return "".join(prose)


def _relative_targets(markdown_file: Path) -> Iterator[tuple[str, str]]:
    text = _without_fenced_code(markdown_file.read_text(encoding="utf-8"))
    text = INLINE_CODE.sub("", text)
    for raw in LINK.findall(text):
        target = _local_target(raw)
        if target is not None:
            yield raw, target


def _broken_links(markdown_file: Path, *, root: Path = ROOT) -> list[str]:
    broken = []
    for raw, target in _relative_targets(markdown_file):
        resolved = (markdown_file.parent / target).resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            broken.append(f"{raw} escapes the repository")
            continue
        if not resolved.exists():
            broken.append(raw)
    return broken


@pytest.mark.parametrize("markdown_file", MARKDOWN_FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_relative_links_resolve(markdown_file: Path) -> None:
    broken = _broken_links(markdown_file)
    assert not broken, f"broken relative links in {markdown_file.relative_to(ROOT)}: {broken}"


def test_documentation_is_reachable_from_index():
    """Follow Markdown file links; every docs page must have a discoverable route."""
    documents = set(MARKDOWN_FILES)
    pending = [DOCS / "README.md"]
    reachable = set()
    while pending:
        document = pending.pop()
        if document in reachable:
            continue
        reachable.add(document)
        for _, target in _relative_targets(document):
            resolved = (document.parent / target).resolve()
            if resolved in documents and resolved not in reachable:
                pending.append(resolved)
    missing = sorted(
        str(path.relative_to(ROOT)) for path in DOCS.rglob("*.md") if path not in reachable
    )
    assert not missing, f"link these documents from the index or a linked guide: {missing}"


@pytest.mark.parametrize(
    "text, expected",
    [
        ("[missing](missing.md)", ["missing.md"]),
        ("[`code-labelled missing`](missing.md)", ["missing.md"]),
        ("![missing image](missing.png)", ["missing.png"]),
        ("[existing](existing.md#heading)", []),
        ('[titled](existing.md "a title")', []),
        ('[spaces](<file with spaces.md> "a title")', []),
        ("[encoded](file%20with%20spaces.md)", []),
        ("[encoded hash](file%23name.md)", []),
        ("[escape](../outside.md)", ["../outside.md escapes the repository"]),
        ("[remote](https://example.invalid/missing.md) [anchor](#missing)", []),
        ("`[literal](missing.md)`", []),
        ("```markdown\n[example](missing.md)\n```\n", []),
        ("~~~markdown\n[example](missing.md)\n~~~\n", []),
        ("````markdown\n```\n[example](missing.md)\n```\n````\n", []),
        ("~~~\n[example](missing.md)\n~~~~\n[real](missing.md)", ["missing.md"]),
        ("~~~markdown\n[unclosed literal](missing.md)\n", []),
        ("[empty]( )", []),
    ],
)
def test_link_checker_handles_prose_and_code(tmp_path, text, expected):
    document = tmp_path / "README.md"
    document.write_text(text, encoding="utf-8")
    for filename in ("existing.md", "file with spaces.md", "file#name.md"):
        (tmp_path / filename).write_text("# Example\n", encoding="utf-8")
    assert _broken_links(document, root=tmp_path) == expected
