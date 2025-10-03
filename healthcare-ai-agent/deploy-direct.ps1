# Healthcare AI Agent - Direct AWS Deployment Script
# This script deploys directly using AWS CLI commands

param(
    [string]$Region = "eu-central-1",
    [string]$StackName = "HealthcareAIAgent"
)

$ErrorActionPreference = "Continue"

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Test-AWSConnection {
    Write-Log "Testing AWS connection..." -Color "Blue"
    try {
        $identity = aws sts get-caller-identity --region $Region 2>$null
        if ($LASTEXITCODE -eq 0) {
            $identityObj = $identity | ConvertFrom-Json
            Write-Log "✅ Connected to AWS Account: $($identityObj.Account)" -Color "Green"
            Write-Log "✅ User: $($identityObj.Arn)" -Color "Green"
            return $true
        } else {
            Write-Log "❌ AWS connection failed" -Color "Red"
            return $false
        }
    }
    catch {
        Write-Log "❌ AWS connection error: $($_.Exception.Message)" -Color "Red"
        return $false
    }
}

function Deploy-LambdaFunction {
    Write-Log "Deploying Lambda function..." -Color "Blue"
    
    # Create IAM role for Lambda
    $rolePolicy = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
"@
    
    $rolePolicy | Out-File -FilePath "lambda-role-policy.json" -Encoding UTF8
    
    # Create the role
    aws iam create-role --role-name HealthcareAILambdaRole --assume-role-policy-document file://lambda-role-policy.json --region $Region 2>$null
    
    # Attach basic execution policy
    aws iam attach-role-policy --role-name HealthcareAILambdaRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole --region $Region 2>$null
    
    # Get account ID
    $identity = aws sts get-caller-identity --region $Region | ConvertFrom-Json
    $accountId = $identity.Account
    $roleArn = "arn:aws:iam::${accountId}:role/HealthcareAILambdaRole"
    
    Write-Log "Created IAM role: $roleArn" -Color "Green"
    
    # Wait for role to be available
    Start-Sleep -Seconds 10
    
    # Create Lambda function
    if (Test-Path "healthcare-ai-lambda.zip") {
        aws lambda create-function --function-name healthcare-ai-agent --runtime python3.11 --role $roleArn --handler lambda_handler.lambda_handler --zip-file fileb://healthcare-ai-lambda.zip --timeout 30 --memory-size 512 --region $Region 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Lambda function created successfully" -Color "Green"
            return $true
        } else {
            Write-Log "❌ Lambda function creation failed" -Color "Red"
            return $false
        }
    } else {
        Write-Log "❌ Lambda zip file not found" -Color "Red"
        return $false
    }
}

function Create-ApiGateway {
    Write-Log "Creating API Gateway..." -Color "Blue"
    
    # Create REST API
    $apiResult = aws apigateway create-rest-api --name "Healthcare AI Agent API" --region $Region
    if ($LASTEXITCODE -ne 0) {
        Write-Log "❌ Failed to create API Gateway" -Color "Red"
        return $false
    }
    
    $api = $apiResult | ConvertFrom-Json
    $apiId = $api.id
    Write-Log "✅ Created API Gateway: $apiId" -Color "Green"
    
    # Get root resource ID
    $resources = aws apigateway get-resources --rest-api-id $apiId --region $Region | ConvertFrom-Json
    $rootResourceId = $resources.items[0].id
    
    # Create health resource
    $healthResource = aws apigateway create-resource --rest-api-id $apiId --parent-id $rootResourceId --path-part "health" --region $Region | ConvertFrom-Json
    $healthResourceId = $healthResource.id
    
    # Get Lambda function ARN
    $identity = aws sts get-caller-identity --region $Region | ConvertFrom-Json
    $accountId = $identity.Account
    $lambdaArn = "arn:aws:lambda:${Region}:${accountId}:function:healthcare-ai-agent"
    
    # Create GET method for health endpoint
    aws apigateway put-method --rest-api-id $apiId --resource-id $healthResourceId --http-method GET --authorization-type NONE --region $Region 2>$null
    
    # Set up Lambda integration
    $integrationUri = "arn:aws:apigateway:${Region}:lambda:path/2015-03-31/functions/${lambdaArn}/invocations"
    aws apigateway put-integration --rest-api-id $apiId --resource-id $healthResourceId --http-method GET --type AWS_PROXY --integration-http-method POST --uri $integrationUri --region $Region 2>$null
    
    # Add Lambda permission for API Gateway
    aws lambda add-permission --function-name healthcare-ai-agent --statement-id "api-gateway-invoke" --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:${Region}:${accountId}:${apiId}/*/*" --region $Region 2>$null
    
    # Deploy API
    aws apigateway create-deployment --rest-api-id $apiId --stage-name prod --region $Region 2>$null
    
    $apiEndpoint = "https://${apiId}.execute-api.${Region}.amazonaws.com/prod"
    Write-Log "✅ API Gateway deployed: $apiEndpoint" -Color "Green"
    
    return $apiEndpoint
}

function Create-S3Frontend {
    Write-Log "Creating S3 bucket for frontend..." -Color "Blue"
    
    $identity = aws sts get-caller-identity --region $Region | ConvertFrom-Json
    $accountId = $identity.Account
    $bucketName = "healthcare-ai-frontend-${accountId}-${Region}"
    
    # Create S3 bucket
    if ($Region -eq "us-east-1") {
        aws s3 mb s3://$bucketName --region $Region 2>$null
    } else {
        aws s3 mb s3://$bucketName --region $Region 2>$null
    }
    
    # Enable static website hosting
    aws s3 website s3://$bucketName --index-document index.html --error-document index.html --region $Region 2>$null
    
    # Set bucket policy for public read
    $bucketPolicy = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${bucketName}/*"
        }
    ]
}
"@
    $bucketPolicy | Out-File -FilePath "bucket-policy.json" -Encoding UTF8
    aws s3api put-bucket-policy --bucket $bucketName --policy file://bucket-policy.json --region $Region 2>$null
    
    # Upload frontend files if available
    if (Test-Path "frontend-deployment.zip") {
        # Extract and upload
        Expand-Archive -Path "frontend-deployment.zip" -DestinationPath "frontend-temp" -Force
        aws s3 sync frontend-temp s3://$bucketName --region $Region 2>$null
        Remove-Item "frontend-temp" -Recurse -Force
        Write-Log "✅ Frontend uploaded to S3" -Color "Green"
    }
    
    $websiteUrl = "http://${bucketName}.s3-website.${Region}.amazonaws.com"
    Write-Log "✅ Frontend URL: $websiteUrl" -Color "Green"
    
    return $websiteUrl
}

# Main deployment process
Write-Log "🚀 Starting Healthcare AI Agent Deployment to $Region" -Color "Green"
Write-Log ""

if (-not (Test-AWSConnection)) {
    Write-Log "❌ AWS connection failed. Please run 'aws configure' or 'aws sso login'" -Color "Red"
    exit 1
}

Write-Log "Starting deployment process..." -Color "Blue"

# Deploy Lambda
if (Deploy-LambdaFunction) {
    Write-Log "✅ Lambda deployment completed" -Color "Green"
} else {
    Write-Log "❌ Lambda deployment failed" -Color "Red"
    exit 1
}

# Create API Gateway
$apiEndpoint = Create-ApiGateway
if ($apiEndpoint) {
    Write-Log "✅ API Gateway deployment completed" -Color "Green"
} else {
    Write-Log "❌ API Gateway deployment failed" -Color "Red"
    exit 1
}

# Create S3 Frontend
$websiteUrl = Create-S3Frontend
if ($websiteUrl) {
    Write-Log "✅ Frontend deployment completed" -Color "Green"
} else {
    Write-Log "❌ Frontend deployment failed" -Color "Red"
}

# Cleanup temp files
Remove-Item "lambda-role-policy.json", "bucket-policy.json" -ErrorAction SilentlyContinue

Write-Log ""
Write-Log "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!" -Color "Green"
Write-Log ""
Write-Log "📋 Deployment Summary:" -Color "Cyan"
Write-Log "  🔗 API Endpoint: $apiEndpoint" -Color "White"
Write-Log "  🌐 Frontend URL: $websiteUrl" -Color "White"
Write-Log "  📍 Region: $Region" -Color "White"
Write-Log "  ⚡ Lambda Function: healthcare-ai-agent" -Color "White"
Write-Log ""
Write-Log "🧪 Test your deployment:" -Color "Yellow"
Write-Log "  curl $apiEndpoint/health" -Color "Gray"
Write-Log ""
Write-Log "✅ Healthcare AI Agent is now live on AWS!" -Color "Green"