#!/usr/bin/env python3
"""AWS CDK app entry point for ChaosSec infrastructure."""

import os
import aws_cdk as cdk
from chaossec_stack import ChaosSecStack


app = cdk.App()

# Get environment configuration
env = cdk.Environment(
    account=os.environ.get('AWS_ACCOUNT_ID', os.environ.get('CDK_DEFAULT_ACCOUNT')),
    region=os.environ.get('AWS_REGION', os.environ.get('CDK_DEFAULT_REGION', 'us-east-1'))
)

# Create ChaosSec stack
ChaosSecStack(
    app,
    "ChaosSecStack",
    env=env,
    description="ChaosSec: Autonomous Chaos & Security Agent for AWS"
)

app.synth()

