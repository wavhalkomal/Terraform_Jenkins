import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from cloudlaunch.requests import submit_request, list_records

BASE = dict(employee_id="rahul", project_id="PAY-2026", task_id="TASK-450",
            workload="payment-api", environment="dev", region="us-east-1", instance_type="t3.micro")

class DuplicateRequestsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "requests.sqlite3"

    def tearDown(self):
        self.temp.cleanup()

    def test_same_task_two_employees_one_deployment(self):
        first = submit_request(self.db, BASE, "click-1")
        second = submit_request(self.db, {**BASE, "employee_id": "priya"}, "click-2")
        self.assertNotEqual(first["request_id"], second["request_id"])
        self.assertEqual(first["deployment_id"], second["deployment_id"])
        self.assertEqual(second["action"], "LINKED_TO_EXISTING")
        self.assertEqual(list_records(self.db)[0]["request_count"], 2)

    def test_duplicate_browser_retry(self):
        first = submit_request(self.db, BASE, "same-click")
        second = submit_request(self.db, BASE, "same-click")
        self.assertEqual(first["request_id"], second["request_id"])
        self.assertEqual(second["action"], "RETRIED_SAME_REQUEST")

    def test_different_task(self):
        a = submit_request(self.db, BASE, "a")
        b = submit_request(self.db, {**BASE, "task_id": "TASK-451"}, "b")
        self.assertNotEqual(a["deployment_id"], b["deployment_id"])

    def test_conflicting_instance_size(self):
        submit_request(self.db, BASE, "a")
        with self.assertRaisesRegex(ValueError, "administrator review"):
            submit_request(self.db, {**BASE, "employee_id": "priya", "instance_type": "t3.small"}, "b")

    def test_key_reuse_for_other_request_rejected(self):
        submit_request(self.db, BASE, "a")
        with self.assertRaisesRegex(ValueError, "Idempotency key"):
            submit_request(self.db, {**BASE, "task_id": "TASK-451"}, "a")

    def test_simultaneous_submissions(self):
        def run(employee):
            return submit_request(self.db, {**BASE, "employee_id": employee}, employee + "-click")
        with ThreadPoolExecutor(max_workers=2) as pool:
            a, b = list(pool.map(run, ("rahul", "priya")))
        self.assertEqual(a["deployment_id"], b["deployment_id"])
        self.assertEqual(list_records(self.db)[0]["request_count"], 2)

    def test_unsupported_region(self):
        with self.assertRaisesRegex(ValueError, "Unsupported region"):
            submit_request(self.db, {**BASE, "region": "invalid-region"}, "a")
