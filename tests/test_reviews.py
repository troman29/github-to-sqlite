from github_to_sqlite import utils
import sqlite_utils


def db_with_pull_request():
    db = sqlite_utils.Database(memory=True)
    db["repos"].create({"id": int}, pk="id")
    db["repos"].insert({"id": 100})
    db["pull_requests"].create({"id": int, "repo": int, "number": int}, pk="id")
    db["pull_requests"].insert({"id": 555, "repo": 100, "number": 42})
    return db


def review(database_id=1, state="APPROVED"):
    return {
        "databaseId": database_id,
        "state": state,
        "body": "выглядит хорошо",
        "author": {"login": "troman29"},
        "submittedAt": "2026-08-19T10:00:00Z",
        "commit": {"oid": "abc"},
        "url": "https://github.com/windbit/x/pull/42#pullrequestreview-1",
    }


def inline_comment(comment_id=9):
    return {
        "id": comment_id,
        "pull_request_review_id": 1,
        "pull_request_url": "https://api.github.com/repos/windbit/x/pulls/42",
        "user": {"login": "thomas5788"},
        "path": "backend/app.py",
        "line": 17,
        "body": "тут падает на пустом списке",
        "created_at": "2026-08-19T10:05:00Z",
        "updated_at": "2026-08-19T10:05:00Z",
        "html_url": "https://github.com/windbit/x/pull/42#discussion_r9",
        "in_reply_to_id": None,
    }


def test_review_lands_on_its_pull_request():
    db = db_with_pull_request()
    assert utils.save_reviews(db, 100, [(42, review())]) == 1
    row = db["reviews"].get(1)
    assert row["pull_request"] == 555
    assert row["state"] == "APPROVED"
    assert row["author"] == "troman29"


def test_review_of_an_unknown_pull_request_still_saved():
    # PR может быть ещё не синхронизирован — вердикт всё равно нужен, просто без внешнего ключа
    db = db_with_pull_request()
    utils.save_reviews(db, 100, [(999, review(database_id=2))])
    assert db["reviews"].get(2)["pull_request"] is None
    assert db["reviews"].get(2)["number"] == 999


def test_inline_comment_resolves_its_pull_request():
    db = db_with_pull_request()
    assert utils.save_review_comments(db, 100, [inline_comment()]) == 1
    row = db["review_comments"].get(9)
    assert row["pull_request"] == 555
    assert row["path"] == "backend/app.py"
    assert row["line"] == 17
    assert row["review"] == 1


def test_second_delivery_of_the_same_review_updates_it():
    db = db_with_pull_request()
    utils.save_reviews(db, 100, [(42, review(state="COMMENTED"))])
    utils.save_reviews(db, 100, [(42, review(state="APPROVED"))])
    assert db["reviews"].count == 1
    assert db["reviews"].get(1)["state"] == "APPROVED"
