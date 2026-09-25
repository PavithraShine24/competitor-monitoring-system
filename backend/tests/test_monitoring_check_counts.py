from types import SimpleNamespace

from app.api.articles import _updated_counts_by_check


def count_for_check(rows, check_id):
    return _updated_counts_by_check(rows).get(check_id, 0)


def test_check_with_no_updates_has_zero_updated_articles():
    assert count_for_check([], 10) == 0


def test_check_with_one_updated_event_has_one_updated_article():
    assert count_for_check([(10, 1)], 10) == 1


def test_check_with_multiple_updated_events_counts_only_that_check():
    rows = [(10, 2), (11, 4), (10, 3)]
    assert count_for_check(rows, 10) == 3
    assert count_for_check(rows, 11) == 4


def test_new_article_count_remains_separate():
    check = SimpleNamespace(new_articles_found=2, updated_articles=count_for_check([(10, 1)], 10))
    assert check.new_articles_found == 2
    assert check.updated_articles == 1