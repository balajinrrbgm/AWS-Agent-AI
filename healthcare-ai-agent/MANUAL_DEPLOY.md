# Healthcare AI Agent - Manual Deployment Guide for eu-central-1

## 📋 Quick Deployment Steps

Since AWS credentials need to be properly configured, here's a manual deployment approach:

### Step 1: Configure AWS Credentials

You need valid AWS credentials. Please run:

```powershell
aws configure
```

And enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region name: `eu-central-1`
- Default output format: `json`

### Step 2: Alternative Local Development

For now, let's run the application locally and then deploy manually:

#### Start Local Backend
```powershell
cd backend
python app.py
```

#### Start Local Frontend (in another terminal)
```powershell
cd frontend
npm install
npm start
```

### Step 3: Manual AWS Deployment (when credentials are ready)

#### Deploy Backend to AWS Lambda
1. Create deployment package:
```powershell
cd backend
mkdir deployment
cp *.py deployment/
pip install -r requirements.txt -t deployment/
cd deployment
Compress-Archive -Path * -DestinationPath ../backend.zip
```

2. Create Lambda function via AWS Console:
   - Runtime: Python 3.11
   - Region: eu-central-1
   - Handler: app.lambda_handler
   - Upload: backend.zip

#### Deploy Frontend to S3
1. Build frontend:
```powershell
cd frontend
npm run build
```

2. Create S3 bucket via AWS Console:
   - Region: eu-central-1
   - Name: healthcare-ai-frontend-[your-suffix]
   - Enable static website hosting
   - Upload build/ folder contents

#### Create API Gateway
1. Create REST API in AWS Console
2. Connect to Lambda function
3. Enable CORS
4. Deploy to stage

### Step 4: Current Local Access

**Backend API**: http://localhost:8000
**Frontend**: http://localhost:3000

### Available Endpoints (Local)
- GET /health - Health check
- GET /api/v1/patients - List patients
- POST /api/v1/query - AI query processing

## 🔧 AWS Services Required for Full Deployment

When ready to deploy to AWS:

1. **Lambda** - Serverless compute
2. **API Gateway** - REST API
3. **S3** - Static hosting & storage
4. **CloudFront** - CDN (optional)
5. **DynamoDB** - Database (optional)
6. **Cognito** - Authentication (optional)

## 🌍 Region: eu-central-1 (Frankfurt)

All resources will be deployed to the Frankfurt region for optimal European performance.

---

**Next**: Configure AWS credentials and run deployment script, or use local development environment.