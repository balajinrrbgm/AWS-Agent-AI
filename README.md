# Healthcare AI Agent

A comprehensive healthcare AI agent system using Amazon Bedrock, SageMaker AI, and Bedrock AgentCore for intelligent medical consultations and health analysis.

## 🏗️ Architecture Overview

This project demonstrates a production-ready healthcare AI system built with:

- **Frontend**: React 18 + TypeScript + Material-UI
- **Backend**: Python FastAPI with AWS SDK
- **AI Services**: Amazon Bedrock (Claude 3 Sonnet) + SageMaker AI
- **Infrastructure**: AWS CDK for Infrastructure as Code
- **Database**: DynamoDB for patient data
- **Security**: JWT authentication, data encryption, HIPAA compliance

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- AWS CLI configured
- Docker (optional)

### Development Setup

1. **Clone and setup**:
```bash
git clone https://github.com/balajinrrbgm/AWS-Agent-AI.git
cd AWS-Agent-AI
```

2. **Backend Setup**:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Configure your AWS credentials
python main.py
```

3. **Frontend Setup**:
```bash
cd frontend
npm install
npm start
```

4. **Infrastructure Deployment**:
```bash
cd infrastructure
npm install
npm run deploy
```

## 📁 Project Structure

```
AWS-Agent-AI/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agents/         # AI agents (Bedrock, SageMaker)
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── tests/              # Backend tests
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API services
│   │   ├── types/          # TypeScript types
│   │   └── utils/          # Utilities
│   └── package.json
├── infrastructure/         # AWS CDK infrastructure
├── docs/                   # Documentation
├── scripts/                # Deployment scripts
└── docker-compose.yml      # Local development
```

## 🎯 Features

### AI-Powered Healthcare Services
- **Medical Consultations**: Natural language interactions with Claude 3 Sonnet
- **Symptom Analysis**: ML-powered symptom assessment using SageMaker
- **Risk Assessment**: Predictive health analytics
- **Multi-Agent Orchestration**: Bedrock AgentCore coordination

### Healthcare Management
- **Patient Profiles**: Comprehensive health records
- **Appointment Scheduling**: Intelligent scheduling system
- **Health Insights**: Personalized recommendations
- **Document Processing**: Medical document analysis with Textract

### Enterprise Features
- **HIPAA Compliance**: End-to-end encryption and audit logs
- **Scalable Architecture**: Microservices with auto-scaling
- **Multi-tenant**: Support for healthcare organizations
- **Real-time**: WebSocket connections for live consultations

## 🔧 Configuration

### Environment Variables

Backend (.env):
```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Database
DYNAMODB_TABLE_PREFIX=healthcare-ai

# Security
JWT_SECRET_KEY=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key
```

Frontend (.env):
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## 🚀 Deployment

### Production Deployment
```bash
# Deploy infrastructure
cd infrastructure
npm run deploy:prod

# Deploy backend
cd backend
./scripts/deploy.sh

# Deploy frontend
cd frontend
npm run build
aws s3 sync build/ s3://your-frontend-bucket
```

### Docker Deployment
```bash
docker-compose up -d
```

## 📊 Monitoring & Observability

- **CloudWatch**: Application logs and metrics
- **X-Ray**: Distributed tracing
- **Custom Dashboards**: Health metrics and usage analytics
- **Alerts**: Automated alerting for critical issues

## 🔒 Security

- **Authentication**: JWT with refresh tokens
- **Authorization**: Role-based access control
- **Data Encryption**: At rest and in transit
- **API Security**: Rate limiting, input validation
- **HIPAA Compliance**: Audit logs, data governance

## 📚 Documentation

- [API Documentation](./docs/api.md)
- [Deployment Guide](./docs/deployment.md)
- [Architecture Guide](./docs/architecture.md)
- [Security Guide](./docs/security.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, email support@healthcareai.com or join our [Discord](https://discord.gg/healthcareai).

## 🚀 AWS Services Used

- Amazon Bedrock (Claude 3 Sonnet)
- Amazon SageMaker AI
- Amazon DynamoDB
- Amazon S3
- Amazon API Gateway
- AWS Lambda
- Amazon Cognito
- Amazon EventBridge
- AWS Step Functions
- Amazon CloudWatch
- Amazon Textract
- Amazon Comprehend Medical
- Amazon CloudFront
- AWS IAM
- AWS KMS
- Amazon VPC
- AWS Systems Manager

---

Built with ❤️ for the AWS AI Agent Global Hackathon 2025