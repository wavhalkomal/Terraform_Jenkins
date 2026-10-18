import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cloudlaunch.requests import submit_request, list_records, duplicate_report

BASE = dict(employee_id="rahul", project_id="PAY-2026", task_id="TASK-450",
            workload="payment-api", environment="dev", region="us-east-1", instance_type="t3.micro")

class DuplicateRequestsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "requests.sqlite3"

    def tearDown(self):
        self.temp.cleanup()

    def test_same_task_two_employees_keep_independent_requests(self):
        first = submit_request(self.db, BASE, "click-1")
        second = submit_request(self.db, {**BASE, "employee_id": "priya"}, "click-2")
        self.assertNotEqual(first["request_id"], second["request_id"])
        self.assertEqual(second["action"], "POTENTIAL_DUPLICATE")
        self.assertEqual(len(list_records(self.db)), 2)
        self.assertEqual({x["status"] for x in list_records(self.db)}, {"DUPLICATE_REVIEW"})
        self.assertEqual({x["employee_id"] for x in duplicate_report(self.db)[0]["employees"]}, {"rahul", "priya"})

    def test_repeated_submission_returns_same_request(self):
        first = submit_request(self.db, BASE, "same-click")
        second = submit_request(self.db, BASE, "same-click")
        self.assertEqual(first["request_id"], second["request_id"])
        self.assertEqual(second["action"], "RETRIED_SAME_REQUEST")

    def test_different_task_is_independent(self):
        submit_request(self.db, BASE, "a")
        submit_request(self.db, {**BASE, "task_id": "TASK-451"}, "b")
        self.assertEqual(len(duplicate_report(self.db)), 0)

    def test_size_conflict_flags_possible_duplicate(self):
        submit_request(self.db, BASE, "a")
        result = submit_request(self.db, {**BASE, "employee_id": "priya", "instance_type": "t3.small"}, "b")
        self.assertEqual(result["status"], "DUPLICATE_REVIEW")

    def test_token_must_not_be_reused_for_other_payload(self):
        submit_request(self.db, BASE, "a")
        with self.assertRaisesRegex(ValueError, "Idempotency"):
            submit_request(self.db, {**BASE, "task_id": "TASK-451"}, "a")

    def test_hundred_concurrent_people_remain_independent(self):
        def send(i):
            return submit_request(self.db, {**BASE, "employee_id": "person-" + str(i)}, "click-" + str(i))
        with ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(send, range(100)))
        self.assertEqual(len({r["request_id"] for r in results}), 100)
        self.assertEqual(len(list_records(self.db)), 100)
        self.assertEqual(duplicate_report(self.db)[0]["request_count"], 100)
        self.assertEqual(len([r for r in results if r["action"] == "REQUEST_RECORDED"]), 1)

    def test_unsupported_region_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported region"):
            submit_request(self.db, {**BASE, "region": "invalid"}, "a")

    def test_case_and_whitespace_normalized(self):
        submit_request(self.db, BASE, "a")
        request = {**BASE, "employee_id": "priya", "project_id": " PAY-2026 ",
                   "task_id": "task-450", "workload": "PAYMENT-API"}
        self.assertEqual(submit_request(self.db, request, "b")["action"], "POTENTIAL_DUPLICATE")
