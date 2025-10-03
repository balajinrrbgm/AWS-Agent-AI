# Healthcare AI Agent - Complete AWS Deployment Guide
## Region: eu-central-1

## 🚀 Quick Start - AWS Credentials Issue Resolution

### The Error You're Seeing:
```
An error occurred (InvalidClientTokenId) when calling the GetCallerIdentity operation: The security token included in the request is invalid.
```

### Solutions:

#### Option 1: Get New AWS Credentials
1. **AWS Console Method:**
   - Go to AWS Console → IAM → Users → Your User → Security Credentials
   - Create new Access Key
   - Copy Access Key ID and Secret Access Key

2. **Configure AWS CLI:**
   ```powershell
   aws configure
   # Enter: AWS Access Key ID
   # Enter: AWS Secret Access Key  
   # Enter: eu-central-1
   # Enter: json
   ```

#### Option 2: Use Environment Variables
```powershell
$env:AWS_ACCESS_KEY_ID='your-new-access-key-id'
$env:AWS_SECRET_ACCESS_KEY='your-new-secret-access-key'
$env:AWS_DEFAULT_REGION='eu-central-1'
```

#### Option 3: Manual Deployment (Recommended for now)
Since credentials are problematic, let's deploy manually via AWS Console.

---

## 📋 Complete Manual Deployment Steps

### Prerequisites Checklist
- [ ] AWS Account with appropriate permissions
- [ ] Access to eu-central-1 region
- [ ] Healthcare AI Agent code ready (✅ Done)
- [ ] Deployment package created (✅ Done: healthcare-ai-lambda.zip)

### Step 1: Deploy Lambda Function

1. **Go to AWS Lambda Console:**
   ```
   https://eu-central-1.console.aws.amazon.com/lambda/
   ```

2. **Create Function:**
   - Click "Create function"
   - Choose "Author from scratch"
   - Function name: `healthcare-ai-agent`
   - Runtime: `Python 3.11`
   - Architecture: `x86_64`
   - Click "Create function"

3. **Upload Code:**
   - In the Code tab, click "Upload from" → ".zip file"
   - Upload `healthcare-ai-lambda.zip` (created by deployment script)
   - Handler: `lambda_handler.lambda_handler`
   - Timeout: 30 seconds
   - Memory: 512 MB

4. **Environment Variables:**
   ```
   ENVIRONMENT=production
   AWS_REGION=eu-central-1
   ```

5. **Test Lambda:**
   - Create test event with:
   ```json
   {
     "httpMethod": "GET",
     "path": "/health",
     "headers": {},
     "body": null
   }
   ```

### Step 2: Create API Gateway

1. **Go to API Gateway Console:**
   ```
   https://eu-central-1.console.aws.amazon.com/apigateway/
   ```

2. **Create REST API:**
   - Click "Create API"
   - Choose "REST API" → "Build"
   - API name: `Healthcare AI Agent API`
   - Endpoint Type: Regional
   - Click "Create API"

3. **Create Resources and Methods:**

   **Root Resource (/):**
   - Method: GET
   - Integration type: Lambda Function
   - Lambda Function: healthcare-ai-agent
   - Use Lambda Proxy integration: ✅

   **Health Endpoint (/health):**
   - Create Resource: `/health`
   - Method: GET
   - Integration: Lambda Function (healthcare-ai-agent)
   - Use Lambda Proxy integration: ✅

   **API Endpoints (/api/v1):**
   - Create Resource: `/api`
   - Create Resource under `/api`: `/v1`
   - Create Resource under `/v1`: `/query`
   - Method: POST
   - Integration: Lambda Function (healthcare-ai-agent)

   **Patients Endpoint (/api/v1/patients):**
   - Create Resource under `/v1`: `/patients`
   - Method: GET
   - Integration: Lambda Function (healthcare-ai-agent)

4. **Enable CORS:**
   - Select each resource
   - Actions → Enable CORS
   - Access-Control-Allow-Origin: `*`
   - Access-Control-Allow-Headers: `Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token`
   - Access-Control-Allow-Methods: `GET,POST,PUT,DELETE,OPTIONS`

5. **Deploy API:**
   - Actions → Deploy API
   - Deployment stage: `prod`
   - Stage description: `Production deployment`
   - Click "Deploy"

### Step 3: Configure Lambda Permissions

1. **Lambda Console → Functions → healthcare-ai-agent → Configuration → Permissions**
2. **Resource-based policy → Add permission:**
   - Service: API Gateway
   - Source ARN: `arn:aws:execute-api:eu-central-1:ACCOUNT-ID:API-ID/*/*`

### Step 4: Frontend Deployment (S3 + CloudFront)

1. **Create S3 Bucket:**
   ```
   https://eu-central-1.console.aws.amazon.com/s3/
   ```
   - Bucket name: `healthcare-ai-frontend-bucket-unique-name`
   - Region: eu-central-1
   - Uncheck "Block all public access"
   - Enable static website hosting

2. **Upload Frontend:**
   - Upload contents of `frontend/build/` folder
   - Set index document: `index.html`
   - Set error document: `index.html`

3. **Create CloudFront Distribution:**
   ```
   https://console.aws.amazon.com/cloudfront/
   ```
   - Origin Domain: S3 bucket website endpoint
   - Viewer Protocol Policy: Redirect HTTP to HTTPS
   - Allowed HTTP Methods: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
   - Cache Policy: CachingDisabled (for API calls)

### Step 5: Update Frontend Configuration

1. **Update API URL in Frontend:**
   - File: `frontend/src/hooks/useHealthAPI.ts`
   - Update `API_BASE_URL` to your API Gateway URL:
   ```typescript
   const API_BASE_URL = 'https://YOUR-API-ID.execute-api.eu-central-1.amazonaws.com/prod';
   ```

2. **Rebuild and Redeploy Frontend:**
   ```powershell
   cd frontend
   npm run build
   # Upload new build folder to S3
   ```

---

## 🔧 Testing Your Deployment

### Test Backend API:
```bash
curl https://YOUR-API-ID.execute-api.eu-central-1.amazonaws.com/prod/health
```

Expected Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-27T18:30:00Z",
  "service": "healthcare-ai-agent"
}
```

### Test Chat API:
```bash
curl -X POST https://YOUR-API-ID.execute-api.eu-central-1.amazonaws.com/prod/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "content": "I have a headache",
    "timestamp": "2025-09-27T18:30:00Z",
    "message_type": "user"
  }'
```

---

## 🎯 Production Enhancements

### Security:
- [ ] Enable API Gateway authentication (Cognito/API Keys)
- [ ] Configure WAF for API protection
- [ ] Use AWS Secrets Manager for sensitive data
- [ ] Enable CloudTrail logging

### Performance:
- [ ] Configure Lambda provisioned concurrency
- [ ] Set up CloudWatch alarms
- [ ] Enable X-Ray tracing
- [ ] Configure API Gateway caching

### Monitoring:
- [ ] CloudWatch dashboards
- [ ] Lambda insights
- [ ] API Gateway access logs
- [ ] Custom metrics

---

## 🚨 Troubleshooting

### Common Issues:

1. **Lambda Timeout:**
   - Increase timeout in Lambda configuration
   - Check CloudWatch logs

2. **CORS Errors:**
   - Verify CORS configuration in API Gateway
   - Check preflight OPTIONS requests

3. **Permission Errors:**
   - Verify Lambda execution role
   - Check API Gateway resource policies

4. **Frontend Not Loading:**
   - Check S3 bucket policy
   - Verify CloudFront distribution settings

---

## 📞 Support

### AWS Resources:
- [Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)

### Healthcare AI Agent:
- Local Testing: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000`

---

## ✅ Deployment Checklist

### Pre-deployment:
- [ ] AWS credentials configured
- [ ] Lambda package created (healthcare-ai-lambda.zip)
- [ ] Frontend built (npm run build)

### Lambda Deployment:
- [ ] Function created
- [ ] Code uploaded
- [ ] Handler configured
- [ ] Environment variables set
- [ ] Test executed successfully

### API Gateway:
- [ ] REST API created
- [ ] Resources and methods configured
- [ ] CORS enabled
- [ ] API deployed to prod stage
- [ ] Lambda permissions added

### Frontend:
- [ ] S3 bucket created
- [ ] Static website hosting enabled
- [ ] Files uploaded
- [ ] CloudFront distribution created
- [ ] API URL updated in frontend

### Testing:
- [ ] Health endpoint responds
- [ ] Chat API works
- [ ] Frontend loads
- [ ] End-to-end functionality verified

---

**Current Status:** 
- ✅ Backend code ready
- ✅ Frontend built and working
- ✅ Deployment package created
- ⚠️ AWS credentials need fixing
- 🎯 Ready for manual deployment

**Next Steps:**
1. Fix AWS credentials OR
2. Proceed with manual deployment following this guide