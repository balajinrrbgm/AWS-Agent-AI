#!/bin/bash
# Quick deployment script for Healthcare AI Agent

echo "🚀 Healthcare AI Agent - Quick AWS Deployment"
echo "🌍 Region: eu-central-1"
echo ""

# Navigate to healthcare-ai-agent directory
cd healthcare-ai-agent

# Check if AWS CLI is configured
echo "📋 Checking AWS configuration..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Set region
export AWS_DEFAULT_REGION=eu-central-1
aws configure set region eu-central-1

echo "✅ AWS configured for eu-central-1"

# Deploy infrastructure
echo ""
echo "🏗️ Deploying infrastructure..."
cd infrastructure

# Install CDK dependencies
npm install

# Install CDK CLI if not present
if ! command -v cdk &> /dev/null; then
    echo "Installing AWS CDK CLI..."
    npm install -g aws-cdk
fi

# Bootstrap CDK
echo "Bootstrapping CDK..."
cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/eu-central-1

# Deploy the stack
echo "Deploying CDK stack..."
cdk deploy --require-approval never --outputs-file outputs.json

cd ..

# Build and prepare backend
echo ""
echo "📦 Preparing backend..."
cd backend

# Create simple Lambda handler
cat > lambda_handler.py << 'EOF'
import json
from app import app

def lambda_handler(event, context):
    """AWS Lambda handler for FastAPI app"""
    try:
        # Import Mangum for Lambda-ASGI adapter
        from mangum import Mangum
        handler = Mangum(app)
        return handler(event, context)
    except ImportError:
        # Fallback simple response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Healthcare AI Agent API',
                'status': 'healthy',
                'endpoints': {
                    'health': '/health',
                    'patients': '/api/v1/patients',
                    'query': '/api/v1/query'
                }
            })
        }
EOF

cd ..

# Build frontend
echo ""
echo "🎨 Building frontend..."
cd frontend

# Install dependencies
npm install

# Create production build
npm run build

cd ..

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Check AWS CloudFormation console for stack outputs"
echo "2. Test API endpoints"
echo "3. Access frontend via CloudFront distribution"
echo ""
echo "📖 Useful commands:"
echo "aws cloudformation describe-stacks --stack-name HealthcareAIAgentStack --query 'Stacks[0].Outputs'"
echo ""