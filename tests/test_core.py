from copy import deepcopy
from pathlib import Path
import unittest

from outbox_lab.core import replay_outbox
from outbox_lab.fixture_check import check


class OutboxTests(unittest.TestCase):
    def test_failed_transaction_rolls_back_both_tables(self):
        result = replay_outbox({"events": [{"action": "commit", "id": "a", "value": 1, "fail": True}]})
        self.assertEqual(result, {"results": [{"action": "commit", "id": "a", "outcome": "rolled_back"}], "records": [], "outbox": []})
        with self.assertRaises(ValueError):
            replay_outbox({"events": [{"action": "commit", "id": "a", "value": 1, "fail": True}, {"action": "send", "id": "a"}]})

    def test_retries_and_duplicate_sends_preserve_one_record(self):
        result = replay_outbox({"events": [{"action": "commit", "id": "a", "value": None}, {"action": "send", "id": "a", "succeed": False}, {"action": "send", "id": "a"}, {"action": "send", "id": "a"}]})
        self.assertEqual(result["records"], [{"id": "a", "value": None}])
        self.assertEqual(result["outbox"], [{"id": "a", "status": "sent", "attempts": 2}])
        self.assertEqual(result["results"][-1]["outcome"], "duplicate")

    def test_commits_are_idempotent_only_for_the_same_value(self):
        result = replay_outbox({"events": [{"action": "commit", "id": "a", "value": {"b": 2, "a": 1}}, {"action": "commit", "id": "a", "value": {"a": 1, "b": 2}}]})
        self.assertEqual(result["results"][-1]["outcome"], "duplicate")
        with self.assertRaises(ValueError):
            replay_outbox({"events": [{"action": "commit", "id": "a", "value": 1}, {"action": "commit", "id": "a", "value": 2}]})

    def test_input_is_not_modified_and_unicode_ids_round_trip(self):
        data = {"events": [{"action": "commit", "id": " café ", "value": [1, {"x": "日本語"}]}]}
        original = deepcopy(data)
        result = replay_outbox(data)
        self.assertEqual(data, original)
        self.assertEqual(result["records"][0]["id"], "café")

    def test_invalid_flags_values_and_fields_are_rejected(self):
        cases = [{"events": [{"action": "commit", "id": "a", "value": 1, "fail": 1}]},
                 {"events": [{"action": "commit", "id": "a", "value": float("nan")}]},
                 {"events": [{"action": "commit", "id": "a", "value": 1, "extra": True}]}]
        for data in cases:
            with self.subTest(data=data), self.assertRaises(ValueError):
                replay_outbox(data)

    def test_complete_fixture_corpus(self):
        self.assertGreaterEqual(check(Path(__file__).resolve().parents[1] / "fixtures/cases.jsonl", replay_outbox), 350)


if __name__ == "__main__":
    unittest.main()
