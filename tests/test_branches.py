from github_to_sqlite import utils
import sqlite_utils


def ref(name, sha="abc", pull=None, default=False):
    return {
        "name": name,
        "default": default,
        "target": {
            "oid": sha,
            "committedDate": "2026-08-18T14:49:54Z",
            "messageHeadline": "do the thing",
            "author": {"name": "Thomas", "user": {"login": "thomas5788"}},
        },
        "associatedPullRequests": {
            "nodes": [{"number": pull, "state": "MERGED", "url": "u"}] if pull else []
        },
    }


def test_save_branches_keeps_head_and_pull_request():
    db = sqlite_utils.Database(memory=True)
    assert utils.save_branches(db, 100, [ref("master", default=True), ref("fix/x", pull=7)]) == 2
    rows = {row["name"]: row for row in db["branches"].rows}
    assert rows["master"]["default"] == 1
    assert rows["master"]["author"] == "thomas5788"
    assert rows["fix/x"]["pull_request"] == 7
    assert rows["fix/x"]["pull_request_state"] == "MERGED"


def test_deleted_branch_disappears():
    db = sqlite_utils.Database(memory=True)
    utils.save_branches(db, 100, [ref("master", default=True), ref("fix/x")])
    utils.save_branches(db, 100, [ref("master", default=True)])
    assert [row["name"] for row in db["branches"].rows] == ["master"]


def test_other_repos_are_left_alone():
    db = sqlite_utils.Database(memory=True)
    utils.save_branches(db, 100, [ref("master", default=True)])
    utils.save_branches(db, 200, [ref("main", default=True)])
    utils.save_branches(db, 100, [ref("master", default=True)])
    assert db["branches"].count == 2


def test_author_falls_back_to_the_commit_name():
    db = sqlite_utils.Database(memory=True)
    anonymous = ref("fix/y")
    anonymous["target"]["author"] = {"name": "Роман", "user": None}
    utils.save_branches(db, 100, [anonymous])
    assert db["branches"].get("100:fix/y")["author"] == "Роман"
