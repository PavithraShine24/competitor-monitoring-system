from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.monitoring import _article_changes


def article(**overrides):
    values = {
        "title": "Original title",
        "content": "Original article content.",
        "author": "A. Writer",
        "meta_description": "Original description",
        "published_at": datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc),
        "modified_at": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_whitespace_only_changes_are_ignored():
    updates, changed_fields = _article_changes(article(), {"title": " Original   title ", "content": "Original\narticle content. "})
    assert updates == {}
    assert changed_fields == []


def test_title_and_content_changes_are_reported():
    updates, changed_fields = _article_changes(article(), {"title": "Updated title", "content": "Updated article content."})
    assert changed_fields == ["title", "content"]
    assert updates == {"title": "Updated title", "content": "Updated article content."}


def test_missing_extracted_fields_do_not_overwrite_existing_values():
    updates, changed_fields = _article_changes(article(), {"title": "Original title", "content": ""})
    assert updates == {}
    assert changed_fields == []
