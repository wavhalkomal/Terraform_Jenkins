import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from cloudlaunch_cd.workflow import validate, identity, state_key, tags, inspect_instances, check_existing, GateBlocked, prepare

REQ = dict(request_id='REQ-1001', employee_id='rahul', project_id='pay-2026',
           task_id='task-450', workload='payment-api', environment='dev',
           region='us-east-1', instance_type='t3.micro', ami_id='ami-05fa00d4c63e32376')

class MockEC2:
    def __init__(self, instances=None, fail=False):
        self.instances = instances or []
        self.fail = fail
    def get_paginator(self, name):
        if self.fail:
            raise RuntimeError('AWS unavailable')
        items = self.instances
        class Pager:
            def paginate(self, **kwargs):
                return iter([{'Reservations': [{'Instances': items}]}])
        return Pager()

def instance(request=REQ):
    return {'InstanceId': 'i-existing', 'State': {'Name': 'running'},
            'ImageId': request['ami_id'], 'InstanceType': request['instance_type'],
            'Tags': [{'Key': k, 'Value': v} for k, v in tags(request).items()]}

class CloudLaunchCDTests(unittest.TestCase):
    def test_unique_state_by_business_purpose(self):
        other = {**REQ, 'employee_id': 'priya', 'request_id': 'REQ-1002',
                 'instance_type': 't3.small'}
        self.assertEqual(state_key(REQ), state_key(other))
    def test_independent_project_has_different_state(self):
        self.assertNotEqual(state_key(REQ), state_key({**REQ, 'task_id': 'task-451'}))
    def test_detect_existing_with_different_request_and_size(self):
        other = {**REQ, 'employee_id': 'priya', 'request_id': 'REQ-1002',
                 'instance_type': 't3.small'}
        with self.assertRaises(GateBlocked) as captured:
            check_existing(MockEC2([instance(REQ)]), other)
        self.assertEqual(captured.exception.reason, 'ALREADY_PROVISIONED')
        self.assertEqual(captured.exception.instances[0]['instance_id'], 'i-existing')
    def test_detect_stopped_instance(self):
        value = instance()
        value['State']['Name'] = 'stopped'
        with self.assertRaises(GateBlocked):
            check_existing(MockEC2([value]), REQ)
    def test_unrelated_project_not_duplicate(self):
        other = {**REQ, 'task_id': 'task-451'}
        self.assertEqual(check_existing(MockEC2([instance(other)]), REQ)['decision'],
                         'NO_BUSINESS_MATCH_FOUND')
    def test_aws_failure_fails_closed(self):
        with self.assertRaises(GateBlocked) as c:
            check_existing(MockEC2(fail=True), REQ)
        self.assertIn('UNAVAILABLE', c.exception.reason)
    def test_empty_inventory(self):
        self.assertEqual(check_existing(MockEC2(), REQ)['decision'], 'NO_BUSINESS_MATCH_FOUND')
    def test_validate_rejects_bad_region(self):
        with self.assertRaises(ValueError):
            validate({**REQ, 'region': 'eu-central-1'})
    def test_prepare_isolated_backend_configs(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'CLOUDLAUNCH_STATE_BUCKET': 'example-state-bucket'}):
            result = prepare(REQ, tmp)
            self.assertEqual(result['state_key'], state_key(REQ))
            self.assertIn(state_key(REQ), (Path(tmp) / 'backend.hcl').read_text())
            self.assertEqual(json.loads((Path(tmp) / 'deployment.auto.tfvars.json').read_text())['request_id'], 'REQ-1001')
    def test_business_identity_normalizes_case(self):
        self.assertEqual(identity(REQ), identity({**REQ, 'project_id': 'PAY-2026'}))
