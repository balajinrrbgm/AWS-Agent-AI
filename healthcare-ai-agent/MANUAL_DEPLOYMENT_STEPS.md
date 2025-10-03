# 🚀 Healthcare AI Agent - Manual AWS Console Deployment
## Ready for eu-central-1 region

Since we're experiencing AWS CLI credential issues, here's the **guaranteed manual deployment** process using the AWS Console:

## 📦 Files Ready for Deployment

- ✅ `healthcare-ai-lambda.zip` (2.8 KB) - Lambda function
- ✅ `frontend-deployment.zip` (575 KB) - React frontend
- ✅ All deployment documentation

## 🎯 Step-by-Step Manual Deployment

### Step 1: Deploy Lambda Function

1. **Open AWS Lambda Console:**
   - Go to: https://eu-central-1.console.aws.amazon.com/lambda/home?region=eu-central-1
   - Click "Create function"

2. **Configure Function:**
   - Choose "Author from scratch"
   - Function name: `healthcare-ai-agent`
   - Runtime: `Python 3.11`
   - Architecture: `x86_64`
   - Click "Create function"

3. **Upload Code:**
   - In the Code tab, click "Upload from" → ".zip file"
   - Select `healthcare-ai-lambda.zip`
   - Click "Save"

4. **Configure Settings:**
   - Handler: `lambda_handler.lambda_handler`
   - Timeout: 30 seconds
   - Memory: 512 MB
   - Environment variables:
     - `ENVIRONMENT` = `production`
     - `AWS_REGION` = `eu-central-1`

5. **Test Lambda:**
   - Click "Test"
   - Create new test event:
   ```json
   {
     "httpMethod": "GET",
     "path": "/health",
     "headers": {},
     "body": null
   }
   ```
   - Run test - should return success

### Step 2: Create API Gateway

1. **Open API Gateway Console:**
   - Go to: https://eu-central-1.console.aws.amazon.com/apigateway/home?region=eu-central-1
   - Click "Create API"

2. **Create REST API:**
   - Choose "REST API" → "Build"
   - API name: `Healthcare AI Agent API`
   - Endpoint Type: Regional
   - Click "Create API"

3. **Create Resources:**

   **Root Method (/):**
   - Select the root resource "/"
   - Actions → Create Method → GET
   - Integration type: Lambda Function
   - Use Lambda Proxy integration: ✅ Check
   - Lambda Function: `healthcare-ai-agent`
   - Click "Save"
   - Click "OK" to add permission

   **Health Resource (/health):**
   - Actions → Create Resource
   - Resource Name: `health`
   - Resource Path: `/health`
   - Click "Create Resource"
   - Select `/health` resource
   - Actions → Create Method → GET
   - Integration: Lambda Function (healthcare-ai-agent)
   - Use Lambda Proxy integration: ✅ Check
   - Click "Save" and "OK"

4. **Enable CORS:**
   - Select each resource (`/` and `/health`)
   - Actions → Enable CORS
   - Access-Control-Allow-Origin: `*`
   - Access-Control-Allow-Headers: `Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token`
   - Access-Control-Allow-Methods: Select all
   - Click "Enable CORS and replace existing CORS headers"

5. **Deploy API:**
   - Actions → Deploy API
   - Deployment stage: [New Stage]
   - Stage name: `prod`
   - Click "Deploy"
   - **Note the Invoke URL** - you'll need this!

### Step 3: Deploy Frontend to S3

1. **Create S3 Bucket:**
   - Go to: https://s3.console.aws.amazon.com/s3/home?region=eu-central-1
   - Click "Create bucket"
   - Bucket name: `healthcare-ai-frontend-[your-account-id]-eu-central-1`
   - Region: EU (Frankfurt) eu-central-1
   - **Uncheck** "Block all public access"
   - Click "Create bucket"

2. **Enable Static Website Hosting:**
   - Click on your bucket
   - Properties tab → Static website hosting
   - Enable static website hosting
   - Index document: `index.html`
   - Error document: `index.html`
   - Click "Save changes"

3. **Upload Frontend Files:**
   - Extract `frontend-deployment.zip` to a folder
   - Objects tab → Upload
   - Add all files from the extracted folder
   - Click "Upload"

4. **Set Bucket Policy:**
   - Permissions tab → Bucket Policy
   - Add this policy (replace BUCKET-NAME):
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Sid": "PublicReadGetObject",
               "Effect": "Allow",
               "Principal": "*",
               "Action": "s3:GetObject",
               "Resource": "arn:aws:s3:::BUCKET-NAME/*"
           }
       ]
   }
   ```
   - Click "Save changes"

### Step 4: Update Frontend API URL

1. **Get API Gateway URL:**
   - From Step 2, copy the Invoke URL (e.g., `https://abc123.execute-api.eu-central-1.amazonaws.com/prod`)

2. **Update Frontend Configuration:**
   - Extract `frontend-deployment.zip`
   - Find the file containing API configuration
   - Update the API base URL to your API Gateway URL
   - Re-zip and re-upload to S3

### Step 5: Test Your Deployment

1. **Test API Endpoint:**
   ```bash
   curl https://YOUR-API-ID.execute-api.eu-central-1.amazonaws.com/prod/health
   ```

2. **Test Frontend:**
   - Visit your S3 website URL: `http://BUCKET-NAME.s3-website.eu-central-1.amazonaws.com`

## 🎉 Success!

Your Healthcare AI Agent should now be fully deployed and accessible:

- **API**: `https://YOUR-API-ID.execute-api.eu-central-1.amazonaws.com/prod`
- **Frontend**: `http://BUCKET-NAME.s3-website.eu-central-1.amazonaws.com`

## 🔧 Troubleshooting

- **Lambda errors**: Check CloudWatch logs
- **CORS issues**: Verify CORS configuration in API Gateway
- **Frontend not loading**: Check S3 bucket policy and static website hosting
- **API not responding**: Verify Lambda permissions for API Gateway

---

**All files are ready for deployment! Follow these steps to get your Healthcare AI Agent running on AWS eu-central-1.** 🚀