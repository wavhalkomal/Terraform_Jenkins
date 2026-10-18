#!/usr/bin/env bash
set -euo pipefail

INSTANCE_ID="${1:?Usage: post_deployment_check.sh INSTANCE_ID}"
AWS_REGION="${AWS_REGION:-us-east-1}"
EXPECTED_TYPE="${EXPECTED_TYPE:-t2.micro}"
EXPECTED_NAME="${EXPECTED_NAME:-TF-Instance}"

printf '\n=== EC2 post-deployment verification ===\n'
printf 'Instance: %s | Region: %s\n' "$INSTANCE_ID" "$AWS_REGION"

# AWS waiters poll until the state is reached or fail after their retry limit.
echo '[1/5] Waiting for EC2 running state...'
aws ec2 wait instance-running --region "$AWS_REGION" --instance-ids "$INSTANCE_ID"
echo '[2/5] Waiting for both AWS EC2 status checks...'
aws ec2 wait instance-status-ok --region "$AWS_REGION" --instance-ids "$INSTANCE_ID"

# Query each attribute separately to avoid ambiguity in CLI text formatting.
echo '[3/5] Fetching EC2 attributes...'
get_field() {
  aws ec2 describe-instances \
    --region "$AWS_REGION" --instance-ids "$INSTANCE_ID" \
    --query "$1" --output text
}
STATE=$(get_field 'Reservations[0].Instances[0].State.Name')
TYPE=$(get_field 'Reservations[0].Instances[0].InstanceType')
NAME=$(get_field 'Reservations[0].Instances[0].Tags[?Key==`Name`].Value | [0]')
AZ=$(get_field 'Reservations[0].Instances[0].Placement.AvailabilityZone')
PUBLIC_IP=$(get_field 'Reservations[0].Instances[0].PublicIpAddress')

check() {
  local description="$1" actual="$2" expected="$3"
  if [[ "$actual" != "$expected" ]]; then
    printf 'FAIL: %s: expected %s, got %s\n' "$description" "$expected" "$actual" >&2
    exit 1
  fi
  printf 'PASS: %s = %s\n' "$description" "$actual"
}

echo '[4/5] Checking expected configuration...'
check 'Instance state' "$STATE" 'running'
check 'Instance type' "$TYPE" "$EXPECTED_TYPE"
check 'Name tag' "$NAME" "$EXPECTED_NAME"
[[ "$AZ" == "$AWS_REGION"[a-z] ]] || {
  printf 'FAIL: Availability zone %s does not belong to region %s\n' "$AZ" "$AWS_REGION" >&2
  exit 1
}
printf 'PASS: Availability zone = %s\n' "$AZ"

echo '[5/5] Summary'
printf 'PASS: EC2 %s verified in %s (public IP: %s)\n' "$INSTANCE_ID" "$AWS_REGION" "$PUBLIC_IP"
# Note: AWS health checks do not verify OS configuration or application health.
