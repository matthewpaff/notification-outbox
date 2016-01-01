"""Check expected values or expected validation errors in synthetic JSONL data."""
import json


def check(path, evaluate):
    count, seen = 0, set()
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            try:
                case = json.loads(line)
                if case["id"] in seen:
                    raise ValueError("Duplicate fixture ID")
                seen.add(case["id"])
                try:
                    result = evaluate(case["input"])
                except ValueError:
                    if not case.get("expected_error", False):
                        raise
                else:
                    if case.get("expected_error", False) or result != case["expected"]:
                        raise ValueError("Unexpected result")
            except (ValueError, KeyError, TypeError) as error:
                raise ValueError("Fixture line {}: {}".format(number, error)) from error
            count += 1
    if count == 0:
        raise ValueError("Fixture file is empty")
    return count
