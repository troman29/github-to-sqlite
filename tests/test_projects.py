from github_to_sqlite import utils
import json
import sqlite_utils


ITEM = {
    "id": "PVTI_1",
    "type": "ISSUE",
    "createdAt": "2026-08-01T10:00:00Z",
    "updatedAt": "2026-08-02T10:00:00Z",
    "fieldValues": {
        "nodes": [
            {},
            {"text": "Fix the thing", "field": {"name": "Title"}},
            {"name": "In review", "field": {"name": "Status"}},
            {"number": 3.0, "field": {"name": "Estimate"}},
            {"date": "2026-08-09", "field": {"name": "Due"}},
            {"users": {"nodes": [{"login": "troman29"}, {"login": "thomas5788"}]}, "field": {"name": "Assignees"}},
        ]
    },
    "content": {
        "number": 42,
        "title": "Fix the thing",
        "url": "https://github.com/windbit/issues/issues/42",
        "state": "OPEN",
        "repository": {"nameWithOwner": "windbit/issues"},
    },
}

DRAFT = {
    "id": "PVTI_2",
    "type": "DRAFT_ISSUE",
    "createdAt": "2026-08-03T10:00:00Z",
    "updatedAt": "2026-08-03T10:00:00Z",
    "fieldValues": {"nodes": [{"text": "Think about it", "field": {"name": "Title"}}]},
    "content": {"title": "Think about it"},
}

PROJECT = {
    "id": "PVT_1",
    "number": 3,
    "title": "Agentek",
    "url": "https://github.com/orgs/windbit/projects/3",
    "closed": False,
    "public": False,
    "createdAt": "2026-01-01T00:00:00Z",
    "updatedAt": "2026-08-03T10:00:00Z",
}


def test_field_values_reads_every_value_type():
    assert utils.field_values(ITEM["fieldValues"]["nodes"]) == {
        "Title": "Fix the thing",
        "Status": "In review",
        "Estimate": 3.0,
        "Due": "2026-08-09",
        "Assignees": "troman29, thomas5788",
    }


def test_save_project_items():
    db = sqlite_utils.Database(memory=True)
    project_id = utils.save_project(db, "windbit", PROJECT)
    assert utils.save_project_items(db, project_id, [ITEM, DRAFT]) == 2
    rows = {row["id"]: row for row in db["project_items"].rows}
    assert rows["PVTI_1"]["status"] == "In review"
    assert rows["PVTI_1"]["repo"] == "windbit/issues"
    assert rows["PVTI_1"]["number"] == 42
    assert json.loads(rows["PVTI_1"]["fields"])["Estimate"] == 3.0
    # у черновика нет ни репозитория, ни номера — заголовок берётся из поля Title
    assert rows["PVTI_2"]["title"] == "Think about it"
    assert rows["PVTI_2"]["repo"] is None
    assert db["projects"].get(project_id)["title"] == "Agentek"


def test_item_removed_from_the_board_disappears():
    db = sqlite_utils.Database(memory=True)
    project_id = utils.save_project(db, "windbit", PROJECT)
    utils.save_project_items(db, project_id, [ITEM, DRAFT])
    utils.save_project_items(db, project_id, [ITEM])
    assert [row["id"] for row in db["project_items"].rows] == ["PVTI_1"]


def test_items_are_replaced_not_duplicated():
    db = sqlite_utils.Database(memory=True)
    project_id = utils.save_project(db, "windbit", PROJECT)
    utils.save_project_items(db, project_id, [ITEM])
    moved = {**ITEM, "fieldValues": {"nodes": [{"name": "Done", "field": {"name": "Status"}}]}}
    utils.save_project_items(db, project_id, [moved])
    assert db["project_items"].count == 1
    assert db["project_items"].get("PVTI_1")["status"] == "Done"
