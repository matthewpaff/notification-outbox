"""JSON command interface for an original learning tool."""
import argparse
import json
import sys

from .core import replay_outbox
from .fixture_check import check


def main(argv=None):
    parser = argparse.ArgumentParser(description='Replay an in-memory SQLite transactional outbox with rollback, idempotent commits, and delivery marking.')
    parser.add_argument("path", nargs="?", default="-", help="UTF-8 JSON file or - for stdin")
    parser.add_argument("--check-fixtures", metavar="JSONL")
    args = parser.parse_args(argv)
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        if args.check_fixtures:
            if args.path != "-":
                parser.error("Use --check-fixtures alone")
            print("Verified {} generated fixtures.".format(check(args.check_fixtures, replay_outbox)))
        else:
            if args.path == "-":
                data = json.load(sys.stdin)
            else:
                with open(args.path, encoding="utf-8-sig") as handle:
                    data = json.load(handle)
            print(json.dumps(replay_outbox(data), ensure_ascii=True, indent=2))
        return 0
    except (ValueError, RecursionError) as error:
        print("error: " + str(error), file=sys.stderr)
        return 2
    except OSError as error:
        print("error: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
