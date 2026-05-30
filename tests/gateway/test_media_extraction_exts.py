"""Tests for MEDIA:<path> document extension coverage.

Bug #35474: ``.md`` / ``.markdown`` were missing from the outbound
``extract_media()`` regex, so ``MEDIA:/tmp/test.md`` and
``MEDIA:/tmp/test.markdown`` were not extracted as deliverable paths.
"""
from __future__ import annotations

from gateway.platforms.base import BasePlatformAdapter


def test_extract_media_includes_md_and_markdown_document_paths() -> None:
    """MEDIA: with .md and .markdown extensions must be extracted as document paths."""
    content = (
        "Here is a markdown report:\n"
        "MEDIA:/tmp/test.md\n"
        "MEDIA:/tmp/test.markdown\n"
        "Enjoy!"
    )
    media, cleaned = BasePlatformAdapter.extract_media(content)

    paths = [path for path, _is_voice in media]
    assert "/tmp/test.md" in paths
    assert "/tmp/test.markdown" in paths

    is_voice_flags = [is_voice for _path, is_voice in media]
    assert not any(is_voice_flags), "Markdown documents must not be treated as voice"

    assert "MEDIA:/tmp/test.md" not in cleaned
    assert "MEDIA:/tmp/test.markdown" not in cleaned
