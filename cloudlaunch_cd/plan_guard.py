"""Reject any Terraform plan beyond one new, approved EC2 instance.

Never blindly apply a plan when resource actions include delete, update or replace.
"""
import argparse
import json
import sys
from pathlib import Path


def validate_plan(plan):
    changes = plan.get('resource_changes', [])
    mutations = [x for x in changes if x.get('change', {}).get('actions') != ['no-op']]
    if len(mutations) != 1:
        raise ValueError('Expected exactly one resource create; got ' + str(len(mutations)))
    change = mutations[0]
    if change.get('address') != 'aws_instance.server':
        raise ValueError('Unexpected resource: ' + str(change.get('address')))
    if change.get('change', {}).get('actions') != ['create']:
        raise ValueError('Only an EC2 creation is permitted; updates/replacements/deletes blocked')
    return {'decision': 'CREATE_ONLY_PLAN', 'resource': 'aws_instance.server'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plan_json')
    args = parser.parse_args()
    try:
        print(json.dumps(validate_plan(json.loads(Path(args.plan_json).read_text())), indent=2))
    except Exception as e:
        print(json.dumps({'decision': 'BLOCKED_PLAN', 'reason': str(e)}))
        sys.exit(4)

if __name__ == '__main__':
    main()
