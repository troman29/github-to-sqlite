from click.testing import CliRunner
from github_to_sqlite import cli
import json
import sqlite_utils


USER = {"id": 7, "login": "troman29", "type": "User", "site_admin": False}
REPO = {
    "id": 100,
    "node_id": "R_1",
    "name": "issues",
    "full_name": "windbit/issues",
    "private": True,
    "owner": USER,
    "html_url": "https://github.com/windbit/issues",
    "description": None,
    "fork": False,
    "license": None,
    "default_branch": "main",
}


def issue(number=5, title="Board is slow", state="open"):
    return {
        "id": 900 + number,
        "node_id": "I_{}".format(number),
        "number": number,
        "title": title,
        "user": USER,
        "labels": [],
        "state": state,
        "locked": False,
        "assignee": None,
        "assignees": [],
        "milestone": None,
        "comments": 0,
        "created_at": "2026-08-01T10:00:00Z",
        "updated_at": "2026-08-02T10:00:00Z",
        "closed_at": None,
        "body": "…",
    }


def run(tmp_path, event, payload):
    db_path = str(tmp_path / "github.db")
    result = CliRunner().invoke(
        cli.cli, ["webhook", db_path, "--event", event], input=json.dumps(payload)
    )
    return result, sqlite_utils.Database(db_path)


def test_issue_event_is_saved_without_the_api(tmp_path):
    result, db = run(tmp_path, "issues", {"action": "opened", "issue": issue(), "repository": REPO})
    assert result.exit_code == 0, result.output
    row = db["issues"].get(905)
    assert row["title"] == "Board is slow"
    assert row["repo"] == REPO["id"]
    assert db["repos"].get(REPO["id"])["full_name"] == "windbit/issues"


def test_second_delivery_updates_the_same_row(tmp_path):
    db_path = str(tmp_path / "github.db")
    for payload in (
        {"action": "opened", "issue": issue(), "repository": REPO},
        {"action": "closed", "issue": issue(state="closed"), "repository": REPO},
    ):
        CliRunner().invoke(cli.cli, ["webhook", db_path, "--event", "issues"], input=json.dumps(payload))
    db = sqlite_utils.Database(db_path)
    assert db["issues"].count == 1
    assert db["issues"].get(905)["state"] == "closed"



def test_unknown_event_fails_loudly(tmp_path):
    result, _ = run(tmp_path, "star", {"repository": REPO})
    assert result.exit_code != 0
    assert "nothing to save" in result.output


def test_payload_without_repository_fails(tmp_path):
    result, _ = run(tmp_path, "issues", {"issue": issue()})
    assert result.exit_code != 0
    assert "no repository" in result.output
