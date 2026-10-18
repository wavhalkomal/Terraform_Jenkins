import unittest
from cloudlaunch.aws_inventory import find_existing_ec2, preflight_decision

REQUEST = dict(employee_id="rahul", project_id="PAY-2026", task_id="TASK-450",
               workload="payment-api", environment="dev", region="us-east-1", instance_type="t3.micro")

class FakePaginator:
    def __init__(self, pages):
        self.pages = pages
        self.filters = None
    def paginate(self, **kwargs):
        self.filters = kwargs["Filters"]
        yield from self.pages

class FakeEC2:
    def __init__(self, pages):
        self.paginator = FakePaginator(pages)
    def get_paginator(self, name):
        assert name == "describe_instances"
        return self.paginator

class BrokenEC2:
    def get_paginator(self, name):
        raise RuntimeError("AWS is unreachable")

class InventoryTests(unittest.TestCase):
    def test_matches_existing_server(self):
        ec2 = FakeEC2([{"Reservations": [{"Instances": [{
            "InstanceId": "i-existing", "InstanceType": "t3.micro",
            "State": {"Name": "running"},
            "Tags": [{"Key": "ProjectID", "Value": "pay-2026"}]
        }]}]}])
        result = preflight_decision(ec2, REQUEST)
        self.assertEqual(result["decision"], "REVIEW_EXISTING_INFRA")
        self.assertEqual(result["matches"][0]["instance_id"], "i-existing")
        self.assertTrue(result["matches"][0]["same_instance_type"])
        self.assertIn({"Name": "tag:TaskID", "Values": ["task-450"]}, ec2.paginator.filters)

    def test_different_instance_size_still_flags_match(self):
        ec2 = FakeEC2([{"Reservations": [{"Instances": [{
            "InstanceId": "i-other", "InstanceType": "t3.small",
            "State": {"Name": "stopped"}
        }]}]}])
        match = preflight_decision(ec2, REQUEST)
        self.assertEqual(match["decision"], "REVIEW_EXISTING_INFRA")
        self.assertFalse(match["matches"][0]["same_instance_type"])

    def test_empty_result(self):
        result = preflight_decision(FakeEC2([{"Reservations": []}]), REQUEST)
        self.assertEqual(result["decision"], "NO_TAGGED_MATCH_FOUND")

    def test_aws_failure_blocks(self):
        result = preflight_decision(BrokenEC2(), REQUEST)
        self.assertEqual(result["decision"], "BLOCKED_INVENTORY_UNAVAILABLE")

    def test_multiple_pages(self):
        ec2 = FakeEC2([{"Reservations": []}, {"Reservations": [{"Instances": [{
            "InstanceId": "i-page-two", "InstanceType": "t3.micro"
        }]}]}])
        self.assertEqual(len(find_existing_ec2(ec2, REQUEST)), 1)
