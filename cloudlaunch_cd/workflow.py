"""Validate, inspect existing EC2, and prepare an isolated Terraform deployment.

This checks one configured AWS account + region. It NEVER creates AWS resources.
Boto3 is imported only by the CLI, so tests require no AWS credentials.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

REQUIRED = ('request_id', 'employee_id', 'project_id', 'task_id', 'workload',
            'environment', 'region', 'instance_type', 'ami_id')
ALLOWED_TYPES = {'t3.micro', 't3.small', 't3.medium'}
ALLOWED_ENVIRONMENTS = {'dev', 'test', 'prod'}
ALLOWED_REGIONS = {'us-east-1', 'us-east-2'}
IDENTIFIER = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,62}$')
AMI = re.compile(r'^ami-[0-9a-f]{8,17}$')

class GateBlocked(Exception):
    def __init__(self, reason, instances=None):
        super().__init__(reason)
        self.reason = reason
        self.instances = instances or []


def validate(data):
    if not isinstance(data, dict) or set(data) != set(REQUIRED):
        raise ValueError('Request must contain exactly: ' + ', '.join(REQUIRED))
    result = {}
    for field in REQUIRED:
        val = data[field]
        if not isinstance(val, str) or not val.strip():
            raise ValueError(field + ' must be a nonempty string')
        result[field] = val.strip()
    for field in ('request_id', 'employee_id', 'project_id', 'task_id', 'workload'):
        if not IDENTIFIER.fullmatch(result[field]):
            raise ValueError('Invalid ' + field)
    if result['environment'] not in ALLOWED_ENVIRONMENTS:
        raise ValueError('Unsupported environment')
    if result['region'] not in ALLOWED_REGIONS:
        raise ValueError('Unsupported region')
    if result['instance_type'] not in ALLOWED_TYPES:
        raise ValueError('Unsupported instance type')
    if not AMI.fullmatch(result['ami_id']):
        raise ValueError('Invalid AMI ID')
    return result


def identity(data):
    data = validate(data)
    # Business identity must not include employee, request, instance size or AMI.
    return '|'.join(data[x].casefold() for x in
                    ('project_id', 'task_id', 'workload', 'environment', 'region'))


def state_key(data):
    """Identical business purpose maps to the same Terraform state key."""
    digest = hashlib.sha256(identity(data).encode()).hexdigest()[:24]
    return 'cloudlaunch/requests/' + digest + '/terraform.tfstate'


def tags(data):
    d = validate(data)
    return {
        'ManagedBy': 'CloudLaunch',
        'ProjectID': d['project_id'].casefold(),
        'TaskID': d['task_id'].casefold(),
        'Workload': d['workload'].casefold(),
        'Environment': d['environment'],
        'BusinessKey': hashlib.sha256(identity(d).encode()).hexdigest()[:24],
        'RequestID': d['request_id'],
        'RequestedBy': d['employee_id'],
    }


def inspect_instances(ec2, data):
    """Find tag-identical business servers, including stopped ones; never writes.

    Uses a broad project tag search rather than exact four-tag AWS filtering so
    case inconsistencies on existing tags can be handled in Python.
    """
    d = validate(data)
    result = []
    pager = ec2.get_paginator('describe_instances')
    pages = pager.paginate(Filters=[{
        'Name': 'instance-state-name',
        'Values': ['pending', 'running', 'stopping', 'stopped', 'shutting-down'],
    }])
    for page in pages:
        for reservation in page.get('Reservations', []):
            for inst in reservation.get('Instances', []):
                existing = {t['Key'].lower(): str(t['Value']).strip().casefold()
                            for t in inst.get('Tags', [])}
                # Require business identity; do not treat technical similarity as proof.
                if all(existing.get(tag.lower()) == d[field].casefold() for tag, field in (
                    ('ProjectID', 'project_id'), ('TaskID', 'task_id'),
                    ('Workload', 'workload'), ('Environment', 'environment'))):
                    result.append({
                        'instance_id': inst['InstanceId'],
                        'state': inst.get('State', {}).get('Name', 'unknown'),
                        'instance_type': inst.get('InstanceType', 'unknown'),
                        'image_id': inst.get('ImageId', 'unknown'),
                        'region': d['region'],
                        'tags': {t['Key']: t['Value'] for t in inst.get('Tags', [])},
                    })
    return result


def check_existing(ec2, data):
    """Fail closed on AWS API errors; report candidates with instance details."""
    try:
        matches = inspect_instances(ec2, data)
    except Exception as ex:
        raise GateBlocked('AWS_INVENTORY_UNAVAILABLE: ' + type(ex).__name__) from ex
    if matches:
        raise GateBlocked('ALREADY_PROVISIONED', matches)
    return {'decision': 'NO_BUSINESS_MATCH_FOUND', 'state_key': state_key(data)}


def prepare(data, output_dir):
    """Write Terraform variable file and backend config, no credentials or state."""
    d = validate(data)
    bucket = os.environ.get('CLOUDLAUNCH_STATE_BUCKET', '')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{2,62}', bucket):
        raise ValueError('Set CLOUDLAUNCH_STATE_BUCKET to an existing private S3 state bucket')
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    variables = {k: d[k] for k in ('request_id', 'employee_id', 'project_id',
                 'task_id', 'workload', 'environment', 'region', 'instance_type', 'ami_id')}
    (target / 'deployment.auto.tfvars.json').write_text(json.dumps(variables, indent=2) + '\n')
    # backend.hcl contains nonsecret infrastructure identifiers, but is kept outside Git.
    backend = '\n'.join((
        'bucket = "' + bucket + '"',
        'key = "' + state_key(d) + '"',
        'region = "' + os.environ.get('CLOUDLAUNCH_STATE_REGION', 'us-east-1') + '"',
        'encrypt = true',
        'use_lockfile = true',
        '',
    ))
    (target / 'backend.hcl').write_text(backend)
    return {'decision': 'CONFIG_PREPARED', 'state_key': state_key(d),
            'variables_file': str(target / 'deployment.auto.tfvars.json')}


def cli():
    parser = argparse.ArgumentParser(description='CloudLaunch standalone EC2 workflow')
    parser.add_argument('command', choices=('validate', 'check-aws', 'prepare'))
    parser.add_argument('--file', required=True)
    parser.add_argument('--output-dir', default='.cloudlaunch-runtime')
    args = parser.parse_args()
    try:
        data = validate(json.loads(Path(args.file).read_text()))
        if args.command == 'validate':
            answer = {'decision': 'VALID_REQUEST', 'business_key': identity(data),
                      'state_key': state_key(data)}
        elif args.command == 'prepare':
            answer = prepare(data, args.output_dir)
        else:
            import boto3
            sess = boto3.Session()
            ec2 = sess.client('ec2', region_name=data['region'])
            account = sess.client('sts').get_caller_identity()['Account']
            answer = check_existing(ec2, data)
            answer['aws_account'] = account
            answer['region'] = data['region']
        print(json.dumps(answer, indent=2))
    except GateBlocked as exc:
        print(json.dumps({'decision': 'BLOCKED', 'reason': exc.reason,
                          'existing_instances': exc.instances}, indent=2))
        sys.exit(3)
    except Exception as exc:
        print(json.dumps({'decision': 'ERROR', 'error': type(exc).__name__,
                          'detail': str(exc)}, indent=2))
        sys.exit(2)

if __name__ == '__main__':
    cli()
