"""Check that relative Markdown links point at files that exist.

The documentation index and cross-links are part of the repository's
navigation contract, so a stale link should fail CI like a broken import.
External URLs and in-page anchors are intentionally not fetched or validated.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

MARKDOWN_FILES = sorted(
    [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "CONTRIBUTING.md", *DOCS.rglob("*.md")]
)

FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]*`")
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:")


def _local_target(raw: str) -> str | None:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    target = unquote(target).split("#", 1)[0]
    if not target or target.startswith(EXTERNAL_PREFIXES):
        return None
    return target


def _broken_links(markdown_file: Path) -> list[str]:
    text = markdown_file.read_text(encoding="utf-8")
    text = FENCED_CODE.sub("", text)
    text = INLINE_CODE.sub("", text)
    broken = []
    for raw in LINK.findall(text):
        target = _local_target(raw)
        if target is None:
            continue
        resolved = (markdown_file.parent / target).resolve()
        try:
            resolved.relative_to(ROOT)
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
