# Notification Outbox

Replay an in-memory SQLite transactional outbox with rollback, idempotent commits, and delivery marking.

Uses Python 3.10+ and its standard library only. No package installation, virtual
environment, external server, Redis, Celery, or network access is required.

## Run

```console
python -m outbox_lab --help
python -m outbox_lab examples/sample.json
python -m outbox_lab --check-fixtures fixtures/cases.jsonl
python generate_fixtures.py --count 20
python -m unittest discover -s tests -v
```

Run from this directory. The optional path defaults to `-`, which reads JSON from
stdin. Output is JSON or a fixture-check summary. Exit codes are 0 success,
1 file failure, and 2 invalid input. Examples and fixtures contain generated data.

Input is exactly an events list of at most 1000 objects. commit requires action, id, and value, with optional boolean fail to simulate a transaction failure after the record insert; both tables roll back. Identical repeated commits are duplicates; conflicting values for an existing ID fail. send accepts optional boolean succeed; failed sends leave the entry pending and count an attempt, successful sends mark it sent, and later sends are deduplicated without another attempt. IDs are trimmed nonblank strings of at most 80 characters. Output includes event outcomes, records, and outbox rows in ID order. Data exists only during the replay. This does not contact a broker, send notifications, persist between runs, or guarantee production exactly-once delivery.

## Learning focus

The modeled 2016 reliable-notification learning themes: an atomic business write/outbox entry, retries, and duplicate handling. This is an independent concept exercise based on the modeled
roadmap. It makes no claim to be employer-owned or period-authentic production code.

## Structure

- `outbox_lab/core.py`: validated parsing, storage, or state transitions.
- `outbox_lab/cli.py`: JSON command interface.
- `outbox_lab/generate_fixtures.py`: original deterministic validation cases.
- `outbox_lab/fixture_check.py`: expected-output/error checks.
- `fixtures/cases.jsonl`: 367 generated cases, with explicit descriptions.
- `tests/`: independently selected boundaries and the complete corpus check.

Branches `feature/core`, `feature/cli`, `data/fixtures`, and `docs/usage` retain
snapshots; `main` contains the complete tool. Dates and provenance are also recorded
in TIMELINE.json. Many data cases share a scenario; they are not separate features.

Keep changes focused, use actual dates for new work, and add a regression test
for changed behavior. Licensed under [MIT](LICENSE).

[History and provenance](HISTORY.md).
