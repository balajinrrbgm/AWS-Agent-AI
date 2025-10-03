# 🚀 Healthcare AI Agent - Deployment Guide

## 🎯 Quick Start for AWS AI Agent Hackathon

This guide will help you deploy the complete Healthcare AI Agent solution to win the AWS AI Agent Global Hackathon!

## 📋 Prerequisites

### AWS Account Setup
1. **AWS Account** with administrative privileges
2. **AWS CLI** installed and configured
3. **Node.js** 18+ and **Python** 3.9+
4. **Docker** (optional for local development)

### Required AWS Services Access
- Amazon Bedrock (Claude/Llama2 models)
- Amazon SageMaker
- AWS Lambda
- Amazon DynamoDB
- Amazon S3
- Amazon API Gateway
- Amazon Cognito
- Amazon EventBridge
- AWS Step Functions

## 🛠️ Installation Steps

### 1. Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/your-username/healthcare-ai-agent.git
cd healthcare-ai-agent

# Create virtual environment for backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install

# Setup infrastructure
cd ../infrastructure
npm install
```

### 2. Environment Configuration

Create `.env` files in both backend and frontend directories:

**Backend `.env`:**
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Database
PATIENTS_TABLE=healthcare-patients
SESSIONS_TABLE=healthcare-sessions
APPOINTMENTS_TABLE=healthcare-appointments
METRICS_TABLE=healthcare-metrics

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1

# SageMaker Configuration
SAGEMAKER_SYMPTOM_ENDPOINT=healthcare-symptom-analyzer
SAGEMAKER_RISK_ENDPOINT=healthcare-risk-predictor

# Security
JWT_SECRET=your-super-secret-jwt-key
ENCRYPTION_KEY=your-encryption-key
```

**Frontend `.env`:**
```bash
REACT_APP_API_BASE_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
REACT_APP_AWS_REGION=us-east-1
REACT_APP_USER_POOL_ID=us-east-1_xxxxxxxxx
REACT_APP_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Deploy AWS Infrastructure

```bash
cd infrastructure

# Install AWS CDK globally (if not already installed)
npm install -g aws-cdk

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy all infrastructure
cdk deploy --all

# Note the outputs (API Gateway URL, Cognito Pool IDs, etc.)
```

### 4. Deploy SageMaker Models

```bash
# Navigate to ML models directory
cd ../ml-models

# Deploy symptom analysis model
python deploy_symptom_model.py

# Deploy risk prediction model
python deploy_risk_model.py

# Verify endpoints are active
aws sagemaker describe-endpoint --endpoint-name healthcare-symptom-analyzer
aws sagemaker describe-endpoint --endpoint-name healthcare-risk-predictor
```

### 5. Deploy Backend API

```bash
cd ../backend

# Package Lambda function
zip -r healthcare-api.zip . -x "*.git*" "*.env*" "__pycache__/*" "*.pyc"

# Deploy to Lambda (using AWS CLI)
aws lambda update-function-code \
  --function-name healthcare-ai-api \
  --zip-file fileb://healthcare-api.zip

# Or use SAM for more advanced deployment
# sam build
# sam deploy --guided
```

### 6. Build and Deploy Frontend

```bash
cd ../frontend

# Build React application
npm run build

# Deploy to S3 (replace with your bucket name)
aws s3 sync build/ s3://your-frontend-bucket --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

## 🧪 Testing the Deployment

### 1. Health Check
```bash
# Test API health
curl https://your-api-url/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-09-26T...",
  "version": "1.0.0",
  "services": {
    "bedrock": "operational",
    "sagemaker": "operational",
    "dynamodb": "operational"
  }
}
```

### 2. Frontend Access
1. Navigate to your CloudFront URL or S3 website endpoint
2. Register a new user account
3. Test the chat interface with sample medical queries

### 3. API Testing
```bash
# Test authentication
curl -X POST https://your-api-url/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'

# Test medical consultation
curl -X POST https://your-api-url/consultation/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "session_id": "test-session",
    "content": "I have a headache and mild fever",
    "timestamp": "2025-09-26T10:00:00Z",
    "message_type": "user"
  }'
```

## 🎨 Demo Data Setup

### 1. Create Sample Patients
```bash
cd backend
python scripts/create_demo_data.py
```

### 2. Load Medical Knowledge Base
```bash
python scripts/load_medical_knowledge.py
```

## 📊 Monitoring and Logging

### CloudWatch Logs
- Lambda function logs: `/aws/lambda/healthcare-ai-api`
- API Gateway logs: `/aws/apigateway/healthcare-ai-api`

### CloudWatch Metrics
- API response times
- Error rates
- SageMaker endpoint utilization
- DynamoDB performance

### X-Ray Tracing
Enable X-Ray tracing for end-to-end request monitoring.

## 🔧 Troubleshooting

### Common Issues

**1. Bedrock Access Denied**
```bash
# Enable Bedrock model access in AWS Console
# Go to Bedrock > Model access > Manage model access
# Enable Claude and other required models
```

**2. SageMaker Endpoint Not Found**
```bash
# Check endpoint status
aws sagemaker describe-endpoint --endpoint-name healthcare-symptom-analyzer

# Redeploy if needed
python ml-models/deploy_symptom_model.py
```

**3. CORS Issues**
- Check API Gateway CORS configuration
- Verify frontend environment variables

**4. Lambda Timeout**
- Increase Lambda timeout in CDK stack
- Optimize function performance

## 🏆 Hackathon Demo Script

### Demo Flow (10-15 minutes)

1. **Introduction** (2 min)
   - Problem statement
   - Solution overview
   - Architecture highlights

2. **Live Demo** (8 min)
   - User registration and login
   - Medical consultation chat
   - Symptom analysis with ML
   - Risk assessment dashboard
   - Appointment scheduling
   - Document processing

3. **Technical Deep Dive** (3 min)
   - AWS services integration
   - AI/ML capabilities
   - Scalability and security

4. **Business Impact** (2 min)
   - Market opportunity
   - Cost savings
   - Future roadmap

### Sample Demo Queries

```
1. "I've been having chest pain and shortness of breath for the past hour"
   → Shows emergency detection and escalation

2. "I have a mild headache and feel tired"
   → Demonstrates symptom analysis and recommendations

3. "Can you check if my medications interact with each other?"
   → Shows medication analysis capabilities

4. "I want to schedule a checkup with a cardiologist"
   → Demonstrates appointment scheduling

5. "Analyze my recent blood test results"
   → Shows document processing with Textract/Comprehend Medical
```

## 🚀 Scaling for Production

### Performance Optimization
- Use Lambda Provisioned Concurrency
- Implement DynamoDB auto-scaling
- Add Redis caching layer
- Optimize SageMaker endpoints

### Security Enhancements
- Enable WAF for API Gateway
- Implement advanced Cognito features
- Add encryption at rest/transit
- Set up VPC endpoints

### Monitoring & Alerting
- CloudWatch dashboards
- SNS alerts for critical issues
- Cost monitoring and optimization
- Performance baselines

## 📈 Success Metrics

Track these KPIs for your hackathon presentation:
- **Response time**: < 2 seconds for 90% of queries
- **Accuracy**: > 90% for symptom analysis
- **Uptime**: 99.9% availability
- **Cost**: < $0.10 per consultation
- **User satisfaction**: > 4.5/5 rating

## 🎉 Going Live Checklist

- [ ] All AWS services deployed and configured
- [ ] Frontend accessible via CloudFront
- [ ] API Gateway endpoints responding
- [ ] Bedrock models enabled and accessible
- [ ] SageMaker endpoints deployed and healthy
- [ ] DynamoDB tables created and accessible
- [ ] Cognito user pool configured
- [ ] CloudWatch monitoring enabled
- [ ] Demo data loaded
- [ ] Test scenarios validated
- [ ] Presentation materials ready

## 🆘 Support & Resources

### AWS Documentation
- [Amazon Bedrock User Guide](https://docs.aws.amazon.com/bedrock/)
- [SageMaker Developer Guide](https://docs.aws.amazon.com/sagemaker/)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)

### Community Support
- AWS re:Post forums
- Stack Overflow
- GitHub Issues

### Emergency Contacts
- Team Lead: [Your Contact]
- AWS Support: [Your Support Plan]

---

**🏆 Ready to win the AWS AI Agent Global Hackathon? Deploy this solution and showcase the future of healthcare AI!**

*Remember: This is a demo/hackathon solution. For production use, additional security, compliance (HIPAA), and performance optimizations are required.*