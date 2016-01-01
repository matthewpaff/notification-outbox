"""Print original generated cases; this command does not create Git commits."""
import argparse
import json

from outbox_lab.generate_fixtures import make_case


def main():
    parser = argparse.ArgumentParser(description="Print generated validation cases as JSONL.")
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.count <= 10000:
        parser.error("Count must be between 1 and 10000")
    for index in range(args.count):
        print(json.dumps(make_case(index), ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
