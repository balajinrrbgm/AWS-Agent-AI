# Healthcare AI Agent - AWS Deployment Guide

## 🚀 Complete Deployment to AWS (eu-central-1)

This guide will help you deploy the Healthcare AI Agent to AWS using the eu-central-1 region.

## 📋 Prerequisites

### 1. AWS Account Setup
- [ ] AWS Account with appropriate permissions
- [ ] AWS CLI installed and configured
- [ ] Access to eu-central-1 region

### 2. Required Tools
- [ ] AWS CLI v2 ✅ (Installed: 2.27.57)
- [ ] Node.js (for CDK and frontend)
- [ ] Python 3.x (for backend)
- [ ] Git

### 3. AWS Credentials Configuration

**Step 1: Configure AWS CLI**
```bash
aws configure
```
Enter:
- AWS Access Key ID: `[Your AWS Access Key]`
- AWS Secret Access Key: `[Your AWS Secret Key]`
- Default region name: `eu-central-1`
- Default output format: `json`

**Step 2: Verify Configuration**
```bash
aws sts get-caller-identity
aws configure list
```

## 🏗️ Infrastructure Components

### Backend Services
- **API Gateway**: REST API endpoints
- **Lambda Functions**: Serverless compute
- **DynamoDB**: Patient data, sessions, appointments
- **Cognito**: User authentication
- **S3**: Document storage
- **Bedrock**: AI/ML services (Claude 3)
- **SageMaker**: ML model endpoints

### Frontend
- **React Application**: Modern web interface
- **CloudFront**: Global CDN
- **S3**: Static website hosting

## 🚀 Automated Deployment

### Option 1: PowerShell Script (Recommended for Windows)
```powershell
# Navigate to project directory
cd healthcare-ai-agent

# Run deployment script
.\deploy.ps1 -Region "eu-central-1"
```

### Option 2: Manual Step-by-Step Deployment

#### Step 1: Deploy Infrastructure
```bash
cd infrastructure
npm install
npm install -g aws-cdk

# Bootstrap CDK (first time only)
cdk bootstrap aws://[YOUR-ACCOUNT-ID]/eu-central-1

# Deploy infrastructure
cdk deploy --require-approval never
```

#### Step 2: Prepare Backend
```bash
cd ../backend

# Create Lambda deployment package
mkdir lambda-package
cp *.py lambda-package/
pip install -r requirements.txt -t lambda-package/

# Create deployment zip
cd lambda-package
zip -r ../backend-deployment.zip .
cd ..
```

#### Step 3: Build Frontend
```bash
cd ../frontend
npm install
npm run build
```

#### Step 4: Deploy Frontend to S3
```bash
# Get S3 bucket name from stack outputs
aws cloudformation describe-stacks --stack-name HealthcareAIAgentStack --query "Stacks[0].Outputs"

# Sync to S3 (replace with actual bucket name)
aws s3 sync build/ s3://[BUCKET-NAME]/ --delete
```

## 📊 Deployment Outputs

After successful deployment, you'll receive:

- **API Gateway URL**: `https://[api-id].execute-api.eu-central-1.amazonaws.com/prod`
- **CloudFront Distribution**: `https://[distribution-id].cloudfront.net`
- **Cognito User Pool ID**: `eu-central-1_[pool-id]`
- **S3 Bucket**: `[stack-name]-bucket-[random-suffix]`

## 🔧 Environment Configuration

### Frontend Environment Variables
Create `.env.production` in the frontend directory:
```env
REACT_APP_API_URL=https://[your-api-gateway-url]
REACT_APP_AWS_REGION=eu-central-1
REACT_APP_USER_POOL_ID=[your-user-pool-id]
REACT_APP_USER_POOL_CLIENT_ID=[your-user-pool-client-id]
REACT_APP_ENVIRONMENT=production
```

### Backend Environment Variables
The Lambda functions will automatically receive:
- DynamoDB table names
- S3 bucket name
- Cognito configuration
- AWS region settings

## 🧪 Testing Deployment

### 1. API Health Check
```bash
curl https://[your-api-gateway-url]/health
```

### 2. Frontend Access
Visit: `https://[your-cloudfront-url]`

### 3. Authentication Test
- Register a new user
- Verify email
- Login and test protected endpoints

## 🔒 Security Configuration

### 1. Cognito User Pool
- Email verification enabled
- Strong password policy
- MFA optional
- Advanced security features

### 2. API Gateway
- Cognito authorizer for protected endpoints
- CORS configured
- Rate limiting enabled
- Request/response logging

### 3. S3 Security
- Public access blocked
- Server-side encryption
- Versioning enabled
- CloudFront OAI access only

## 📈 Monitoring & Logging

### 1. CloudWatch Logs
- Lambda function logs
- API Gateway access logs
- Error logs and metrics

### 2. X-Ray Tracing
- End-to-end request tracing
- Performance monitoring
- Error detection

### 3. CloudWatch Dashboards
- API metrics
- Lambda performance
- DynamoDB metrics
- CloudFront analytics

## 🛠️ Troubleshooting

### Common Issues

**1. CDK Bootstrap Error**
```bash
# If bootstrap fails, try with explicit account ID
cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/eu-central-1
```

**2. Lambda Package Too Large**
- Use Lambda layers for dependencies
- Optimize package size
- Consider container-based deployment

**3. API Gateway CORS Issues**
- Verify CORS configuration in CDK
- Check preflight OPTIONS requests
- Validate origin headers

**4. Cognito Authentication Issues**
- Verify user pool configuration
- Check client app settings
- Validate JWT tokens

### Getting Help

**Check Stack Status**
```bash
aws cloudformation describe-stacks --stack-name HealthcareAIAgentStack
```

**View Stack Events**
```bash
aws cloudformation describe-stack-events --stack-name HealthcareAIAgentStack
```

**Check Lambda Logs**
```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/healthcare"
```

## 🗑️ Cleanup

To remove all resources:
```bash
cd infrastructure
cdk destroy --force
```

⚠️ **Warning**: This will delete all data including DynamoDB tables and S3 objects.

## 📞 Support

For deployment issues:
1. Check CloudFormation console for stack events
2. Review CloudWatch logs for errors
3. Verify AWS permissions and quotas
4. Ensure all prerequisites are met

---

## 🎯 Quick Start Commands

**Prerequisites Check:**
```bash
aws --version
node --version
python --version
aws sts get-caller-identity
```

**One-Command Deployment:**
```powershell
.\deploy.ps1 -Region "eu-central-1"
```

**Verify Deployment:**
```bash
aws cloudformation describe-stacks --stack-name HealthcareAIAgentStack --query "Stacks[0].Outputs"
```

---

*Healthcare AI Agent - Production-Ready AWS Deployment*