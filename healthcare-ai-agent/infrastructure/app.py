#!/usr/bin/env python3
"""
Healthcare AI Agent CDK App
Entry point for deploying AWS infrastructure
"""

import os
from aws_cdk import App, Environment
from lib.simple_healthcare_stack import HealthcareAIAgentStack

# Create CDK app
app = App()

# Get AWS account and region from environment or use defaults
account = os.environ.get('CDK_DEFAULT_ACCOUNT')
region = "eu-central-1"  # Fixed region

# Environment configuration
env = Environment(account=account, region=region)

# Deploy the main stack
HealthcareAIAgentStack(
    app, 
    "HealthcareAIAgentStack",
    env=env,
    description="Healthcare AI Agent infrastructure with Lambda, API Gateway, and S3"
)

# Synthesize the app
app.synth()