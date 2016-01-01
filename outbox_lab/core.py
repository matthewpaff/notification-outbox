"""Replay an in-memory SQLite outbox; no messages are actually delivered."""
from contextlib import closing
import json
import sqlite3


class RollbackRequested(Exception):
    """Explicit test event representing a failure inside the transaction."""


def replay_outbox(data):
    if not isinstance(data, dict) or set(data) != {"events"} or not isinstance(data["events"], list) or len(data["events"]) > 1000:
        raise ValueError("Supply exactly events, a list of at most 1000 actions")
    results = []
    with closing(sqlite3.connect(":memory:")) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript("""CREATE TABLE records(id TEXT PRIMARY KEY, body TEXT NOT NULL);
            CREATE TABLE outbox(id TEXT PRIMARY KEY REFERENCES records(id),
                status TEXT NOT NULL, attempts INTEGER NOT NULL);""")
        for event in data["events"]:
            if not isinstance(event, dict):
                raise ValueError("Each event must be an object")
            action, key = event.get("action"), event.get("id")
            if action not in ("commit", "send") or not isinstance(key, str) or not 1 <= len(key.strip()) <= 80:
                raise ValueError("Use commit/send and a nonblank ID of at most 80 characters")
            key = key.strip()
            allowed = {"action", "id", "value", "fail"} if action == "commit" else {"action", "id", "succeed"}
            required = {"action", "id", "value"} if action == "commit" else {"action", "id"}
            if not required <= set(event) <= allowed:
                raise ValueError("Unexpected or missing event fields")
            if action == "commit":
                fail = event.get("fail", False)
                if type(fail) is not bool:
                    raise ValueError("fail must be true or false")
                try:
                    body = json.dumps(event["value"], sort_keys=True, separators=(",", ":"), allow_nan=False)
                except (TypeError, ValueError, RecursionError) as error:
                    raise ValueError("value must be JSON-serializable") from error
                existing = db.execute("SELECT body FROM records WHERE id=?", (key,)).fetchone()
                if existing:
                    if existing["body"] != body:
                        raise ValueError("An existing ID cannot be committed with a different value")
                    outcome = "duplicate"
                else:
                    try:
                        with db:
                            db.execute("INSERT INTO records VALUES(?,?)", (key, body))
                            if fail:
                                raise RollbackRequested()
                            db.execute("INSERT INTO outbox VALUES(?,'pending',0)", (key,))
                    except RollbackRequested:
                        outcome = "rolled_back"
                    else:
                        outcome = "stored"
            else:
                succeed = event.get("succeed", True)
                if type(succeed) is not bool:
                    raise ValueError("succeed must be true or false")
                item = db.execute("SELECT status FROM outbox WHERE id=?", (key,)).fetchone()
                if item is None:
                    raise ValueError("Cannot send an ID that has not been committed")
                if item["status"] == "sent":
                    outcome = "duplicate"
                else:
                    with db:
                        db.execute("UPDATE outbox SET attempts=attempts+1,status=? WHERE id=?",
                                   ("sent" if succeed else "pending", key))
                    outcome = "sent" if succeed else "retry"
            results.append({"action": action, "id": key, "outcome": outcome})
        businesses = [{"id": row["id"], "value": json.loads(row["body"])}
                      for row in db.execute("SELECT * FROM records ORDER BY id")]
        outbox = [dict(row) for row in db.execute("SELECT * FROM outbox ORDER BY id")]
    return {"results": results, "records": businesses, "outbox": outbox}
