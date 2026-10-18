import unittest
from cloudlaunch_cd.plan_guard import validate_plan

class PlanGuardTests(unittest.TestCase):
    def test_one_ec2_create_passes(self):
        self.assertEqual(validate_plan({'resource_changes': [
            {'address': 'aws_instance.server', 'change': {'actions': ['create']}}
        ]})['decision'], 'CREATE_ONLY_PLAN')
    def test_existing_resource_noop_blocks(self):
        with self.assertRaises(ValueError):
            validate_plan({'resource_changes': [
                {'address': 'aws_instance.server', 'change': {'actions': ['no-op']}}
            ]})
    def test_ec2_replace_blocks(self):
        with self.assertRaises(ValueError):
            validate_plan({'resource_changes': [
                {'address': 'aws_instance.server', 'change': {'actions': ['delete', 'create']}}
            ]})
    def test_second_resource_blocks(self):
        with self.assertRaises(ValueError):
            validate_plan({'resource_changes': [
                {'address': 'aws_instance.server', 'change': {'actions': ['create']}},
                {'address': 'aws_s3_bucket.bad', 'change': {'actions': ['create']}}
            ]})
