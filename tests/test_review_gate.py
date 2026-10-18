import tempfile
import unittest
from pathlib import Path
from cloudlaunch.requests import submit_request, list_records
from cloudlaunch.review import review_request
from cloudlaunch.gate import evaluate_gate

BASE = dict(employee_id="rahul", project_id="PAY-2026", task_id="TASK-450",
            workload="payment-api", environment="dev", region="us-east-1",
            instance_type="t3.micro")

class EmptyEC2:
    def get_paginator(self, name):
        class P:
            def paginate(self, **kwargs):
                return iter([{"Reservations": []}])
        return P()

class ExistingEC2:
    def get_paginator(self, name):
        class P:
            def paginate(self, **kwargs):
                return iter([{"Reservations": [{"Instances": [{
                    "InstanceId": "i-previous", "InstanceType": "t3.micro",
                    "State": {"Name": "running"}, "Tags": []
                }]}]}])
        return P()

class BrokenEC2:
    def get_paginator(self, name):
        raise RuntimeError("cannot check AWS")

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "review.sqlite3"
    def tearDown(self):
        self.tmp.cleanup()
    def test_admin_rejects_duplicate_then_approves_one(self):
        a = submit_request(self.db, BASE, "click-a")
        b = submit_request(self.db, {**BASE, "employee_id": "priya"}, "click-b")
        with self.assertRaisesRegex(ValueError, "matching requests"):
            review_request(self.db, a["request_id"], "approve", "admin", "requested by team")
        rejected = review_request(self.db, b["request_id"], "reject", "admin", "duplicate of Rahul")
        self.assertEqual(rejected["status"], "REJECTED")
        approved = review_request(self.db, a["request_id"], "approve", "admin", "single server needed")
        self.assertEqual(approved["status"], "APPROVED")
        self.assertFalse(approved["deployment_authorized"])
        self.assertEqual(evaluate_gate(self.db, a["request_id"], EmptyEC2())["decision"], "PASS_PRELIMINARY")
    def test_cannot_gate_unreviewed(self):
        a = submit_request(self.db, BASE, "click-a")
        self.assertEqual(evaluate_gate(self.db, a["request_id"], EmptyEC2())["decision"], "BLOCKED_NOT_APPROVED")
    def test_matching_aws_instance_blocks(self):
        a = submit_request(self.db, BASE, "click-a")
        review_request(self.db, a["request_id"], "approve", "admin", "one machine")
        self.assertEqual(evaluate_gate(self.db, a["request_id"], ExistingEC2())["decision"], "BLOCKED_AWS_CHECK")
    def test_unavailable_aws_blocks(self):
        a = submit_request(self.db, BASE, "click-a")
        review_request(self.db, a["request_id"], "approve", "admin", "one machine")
        self.assertEqual(evaluate_gate(self.db, a["request_id"], BrokenEC2())["decision"], "BLOCKED_AWS_CHECK")
    def test_unknown_request_blocks(self):
        self.assertEqual(evaluate_gate(self.db, "REQ-not-there", EmptyEC2())["decision"], "BLOCKED_UNKNOWN_REQUEST")
    def test_invalid_review_action(self):
        a = submit_request(self.db, BASE, "click-a")
        with self.assertRaises(ValueError):
            review_request(self.db, a["request_id"], "delete", "admin", "test")
