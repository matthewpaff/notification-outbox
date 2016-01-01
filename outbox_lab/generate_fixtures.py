"""Original outbox event traces with independently specified expected outcomes."""


def commit(key, value, fail=False):
    return {"action": "commit", "id": key, "value": value, "fail": fail}


def send(key, succeed=True):
    return {"action": "send", "id": key, "succeed": succeed}


def outcome(action, key, value):
    return {"action": action, "id": key, "outcome": value}


def make_case(index):
    key, kind = "notice-{}".format(index), index % 12
    value = {"sample": index, "topic": "notification"}
    if kind == 0:
        events, description = [{"action": "unknown", "id": key}], "reject unsupported outbox actions"
    elif kind == 1:
        events, description = [{"action": "commit", "id": key}], "reject commits without a record value"
    elif kind == 2:
        events = [{"action": "commit", "id": key, "value": value, "fail": "yes"}]
        description = "reject non-boolean transaction failure flags"
    elif kind == 3:
        events, description = [send(key)], "reject sends for uncommitted record IDs"
    elif kind == 4:
        events = [commit(key, value), commit(key, {"sample": index + 1})]
        description = "reject conflicting duplicate record IDs"
    elif kind == 5:
        events = [commit(key, value, True)]
        expected = {"results": [outcome("commit", key, "rolled_back")], "records": [], "outbox": []}
        description = "roll back record writes when the outbox transaction fails"
    else:
        records = [{"id": key, "value": value}]
        attempts = 1
        if kind == 6:
            events = [commit(key, value), send(key)]
            results = [outcome("commit", key, "stored"), outcome("send", key, "sent")]
            description = "commit a record and mark its outbox entry sent"
        elif kind == 7:
            events = [commit(key, value), commit(key, value), send(key)]
            results = [outcome("commit", key, "stored"), outcome("commit", key, "duplicate"), outcome("send", key, "sent")]
            description = "deduplicate identical record commits"
        elif kind == 8:
            events = [commit(key, value), send(key, False), send(key)]
            results = [outcome("commit", key, "stored"), outcome("send", key, "retry"), outcome("send", key, "sent")]
            attempts = 2
            description = "retry a failed outbox send without duplicating the record"
        elif kind == 9:
            events = [commit(key, value), send(key), send(key)]
            results = [outcome("commit", key, "stored"), outcome("send", key, "sent"), outcome("send", key, "duplicate")]
            description = "deduplicate sends after successful delivery marking"
        elif kind == 10:
            events = [commit(key, value, True), commit(key, value), send(key)]
            results = [outcome("commit", key, "rolled_back"), outcome("commit", key, "stored"), outcome("send", key, "sent")]
            description = "reuse an ID after a rolled-back transaction"
        else:
            other = key + "-b"
            events = [commit(other, index + 1), commit(key, value), send(key)]
            results = [outcome("commit", other, "stored"), outcome("commit", key, "stored"), outcome("send", key, "sent")]
            records += [{"id": other, "value": index + 1}]
            description = "keep independent outbox records in deterministic ID order"
        entries = [{"id": key, "status": "sent", "attempts": attempts}]
        if kind == 11:
            entries.append({"id": other, "status": "pending", "attempts": 0})
        expected = {"results": results, "records": records, "outbox": entries}
    case = {"id": "outbox-{:04d}".format(index), "description": description, "input": {"events": events}}
    case.update({"expected_error": True} if kind < 5 else {"expected": expected})
    return case
