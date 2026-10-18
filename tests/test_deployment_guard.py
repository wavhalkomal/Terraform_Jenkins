import tempfile
import unittest
from pathlib import Path
from cloudlaunch.requests import submit_request
from cloudlaunch.review import review_request
from cloudlaunch.deployment_guard import reserve_after_preflight, reservation_report, audit_report

BASE = dict(employee_id="rahul", project_id="PAY-2026", task_id="TASK-450",
            workload="payment-api", environment="dev", region="us-east-1", instance_type="t3.micro")

class FakeEmptyAWS:
    def get_paginator(self, name):
        class Paginator:
            def paginate(self, **kwargs):
                return iter([{"Reservations": []}])
        return Paginator()

class FakeExistingAWS:
    def get_paginator(self, name):
        class Paginator:
            def paginate(self, **kwargs):
                return iter([{"Reservations":[{"Instances":[{
                    "InstanceId": "i-found", "InstanceType": "t3.micro",
                    "State":{"Name":"running"}}]}]}])
        return Paginator()

class FakeBrokenAWS:
    def get_paginator(self, name):
        raise RuntimeError("offline")

class DeploymentGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "guard.sqlite3"
    def tearDown(self):
        self.tmp.cleanup()
    def _approved(self):
        r = submit_request(self.db, BASE, "click-1")
        review_request(self.db, r["request_id"], "approve", "admin-demo", "single server")
        return r["request_id"]
    def test_approved_request_can_reserve_but_cannot_apply(self):
        rid = self._approved()
        answer = reserve_after_preflight(self.db, rid, FakeEmptyAWS())
        self.assertEqual(answer["decision"], "RESERVED_FOR_REVIEW")
        self.assertFalse(answer["terraform_apply_allowed"])
        self.assertEqual(len(reservation_report(self.db)), 1)
        self.assertEqual(audit_report(self.db)[0]["event"], "RESERVATION_CREATED")
    def test_unreviewed_request_blocked(self):
        rid = submit_request(self.db, BASE, "click-1")["request_id"]
        self.assertEqual(reserve_after_preflight(self.db, rid, FakeEmptyAWS())["decision"], "BLOCKED_NOT_APPROVED")
    def test_aws_candidate_blocks(self):
        rid = self._approved()
        self.assertEqual(reserve_after_preflight(self.db, rid, FakeExistingAWS())["decision"], "BLOCKED_AWS_CHECK")
        self.assertEqual(reservation_report(self.db), [])
    def test_aws_error_blocks(self):
        rid = self._approved()
        self.assertEqual(reserve_after_preflight(self.db, rid, FakeBrokenAWS())["decision"], "BLOCKED_AWS_CHECK")
    def test_repeat_reservation_blocked(self):
        rid = self._approved()
        reserve_after_preflight(self.db, rid, FakeEmptyAWS())
        self.assertEqual(reserve_after_preflight(self.db, rid, FakeEmptyAWS())["decision"], "BLOCKED_ALREADY_RESERVED")
    def test_new_employee_creates_duplicate_and_blocks_reservation(self):
        rid = self._approved()
        submit_request(self.db, {**BASE, "employee_id": "priya"}, "click-2")
        self.assertEqual(reserve_after_preflight(self.db, rid, FakeEmptyAWS())["decision"], "BLOCKED_DUPLICATE_REQUESTS")
