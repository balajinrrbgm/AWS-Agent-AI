# Healthcare AI Agent - Enhanced AWS Deployment Script
# Handles credential validation and provides alternatives

param(
    [string]$Region = "eu-central-1",
    [string]$StackName = "HealthcareAIAgentStack",
    [switch]$SkipAWSValidation = $false,
    [switch]$LocalOnly = $false
)

$ErrorActionPreference = "Continue"

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Test-AWSCredentials {
    Write-Log "Validating AWS credentials..." -Color "Blue"
    
    try {
        # Check if AWS CLI is installed
        $null = aws --version 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Log "AWS CLI not found. Please install AWS CLI first." -Color "Red"
            return $false
        }
        
        # Check credentials configuration
        $configList = aws configure list 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Log "AWS CLI configuration issue." -Color "Red"
            return $false
        }
        
        Write-Log "AWS CLI Configuration:" -Color "Yellow"
        Write-Host $configList
        
        # Test credentials by calling STS
        $stsResult = aws sts get-caller-identity 2>$null
        if ($LASTEXITCODE -eq 0 -and $stsResult) {
            $identity = $stsResult | ConvertFrom-Json
            Write-Log "AWS Credentials: VALID" -Color "Green"
            Write-Log "Account: $($identity.Account)" -Color "White"
            Write-Log "User/Role: $($identity.Arn)" -Color "White"
            return $true
        } else {
            Write-Log "AWS Credentials: INVALID or EXPIRED" -Color "Red"
            Write-Log "Error: Security token is invalid or expired" -Color "Red"
            return $false
        }
    }
    catch {
        Write-Log "Error checking AWS credentials: $($_.Exception.Message)" -Color "Red"
        return $false
    }
}

function Show-CredentialFix {
    Write-Log "" 
    Write-Log "CREDENTIAL ISSUES DETECTED" -Color "Red"
    Write-Log "Your AWS credentials are configured but invalid/expired." -Color "Yellow"
    Write-Log ""
    Write-Log "SOLUTIONS:" -Color "Cyan"
    Write-Log ""
    Write-Log "Option 1: Reconfigure AWS CLI" -Color "Green"
    Write-Log "  aws configure" -Color "White"
    Write-Log "  Enter new/valid AWS Access Key ID and Secret Access Key" -Color "Gray"
    Write-Log ""
    Write-Log "Option 2: Use AWS SSO (if your organization uses it)" -Color "Green"
    Write-Log "  aws configure sso" -Color "White"
    Write-Log ""
    Write-Log "Option 3: Set environment variables" -Color "Green"
    Write-Log "  `$env:AWS_ACCESS_KEY_ID='your-access-key'" -Color "White"
    Write-Log "  `$env:AWS_SECRET_ACCESS_KEY='your-secret-key'" -Color "White"
    Write-Log "  `$env:AWS_DEFAULT_REGION='eu-central-1'" -Color "White"
    Write-Log ""
    Write-Log "Option 4: Manual deployment via AWS Console" -Color "Green"
    Write-Log "  See manual deployment instructions below" -Color "Gray"
}

function Deploy-LocalDevelopment {
    Write-Log "" 
    Write-Log "LOCAL DEVELOPMENT DEPLOYMENT" -Color "Green"
    Write-Log ""
    
    # Check if backend is running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Log "Backend Status: RUNNING" -Color "Green"
            Write-Log "Backend URL: http://localhost:8000" -Color "White"
            Write-Log "API Documentation: http://localhost:8000/docs" -Color "White"
        }
    }
    catch {
        Write-Log "Backend Status: NOT RUNNING" -Color "Yellow"
        Write-Log "To start backend: cd backend && python app.py" -Color "White"
    }
    
    # Check frontend
    if (Test-Path "frontend/build") {
        Write-Log "Frontend Status: BUILT" -Color "Green"
        Write-Log "To serve frontend: cd frontend && npm start" -Color "White"
    } else {
        Write-Log "Frontend Status: NOT BUILT" -Color "Yellow"
        Write-Log "To build frontend: cd frontend && npm run build" -Color "White"
    }
}

function Show-ManualDeployment {
    Write-Log ""
    Write-Log "MANUAL AWS DEPLOYMENT INSTRUCTIONS" -Color "Cyan"
    Write-Log "Region: $Region" -Color "White"
    Write-Log ""
    
    Write-Log "Step 1: Deploy Lambda Function" -Color "Yellow"
    Write-Log "1. Go to: https://$Region.console.aws.amazon.com/lambda/" -Color "White"
    Write-Log "2. Click 'Create function'" -Color "White"
    Write-Log "3. Choose 'Author from scratch'" -Color "White"
    Write-Log "4. Function name: healthcare-ai-agent" -Color "White"
    Write-Log "5. Runtime: Python 3.11" -Color "White"
    Write-Log "6. Click 'Create function'" -Color "White"
    Write-Log "7. Copy code from backend/lambda_handler.py and paste in editor" -Color "White"
    Write-Log "8. Handler: lambda_handler.lambda_handler" -Color "White"
    Write-Log "9. Click 'Deploy'" -Color "White"
    Write-Log ""
    
    Write-Log "Step 2: Create API Gateway" -Color "Yellow"
    Write-Log "1. Go to: https://$Region.console.aws.amazon.com/apigateway/" -Color "White"
    Write-Log "2. Click 'Create API' -> REST API -> Build" -Color "White"
    Write-Log "3. API name: Healthcare AI Agent API" -Color "White"
    Write-Log "4. Create resources and methods:" -Color "White"
    Write-Log "   - GET / -> Lambda function" -Color "Gray"
    Write-Log "   - GET /health -> Lambda function" -Color "Gray"
    Write-Log "   - POST /api/v1/query -> Lambda function" -Color "Gray"
    Write-Log "   - GET /api/v1/patients -> Lambda function" -Color "Gray"
    Write-Log "5. Enable CORS on all methods" -Color "White"
    Write-Log "6. Deploy API to 'prod' stage" -Color "White"
    Write-Log ""
    
    Write-Log "Step 3: Test Deployment" -Color "Yellow"
    Write-Log "After deployment, test with:" -Color "White"
    Write-Log "curl https://[api-id].execute-api.$Region.amazonaws.com/prod/health" -Color "Gray"
}

function Build-DeploymentPackage {
    Write-Log "Creating deployment package..." -Color "Blue"
    
    if (Test-Path "backend") {
        $packageDir = "aws-deployment-package"
        if (Test-Path $packageDir) {
            Remove-Item $packageDir -Recurse -Force
        }
        
        New-Item -ItemType Directory -Path $packageDir -Force | Out-Null
        
        # Copy Lambda handler
        Copy-Item "backend/lambda_handler.py" $packageDir -Force
        Copy-Item "backend/app.py" $packageDir -Force
        
        # Create zip file
        Compress-Archive -Path "$packageDir/*" -DestinationPath "healthcare-ai-lambda.zip" -Force
        
        $zipSize = (Get-Item "healthcare-ai-lambda.zip").Length / 1KB
        Write-Log "Deployment package created: healthcare-ai-lambda.zip ($([math]::Round($zipSize, 2)) KB)" -Color "Green"
        
        Remove-Item $packageDir -Recurse -Force
    }
}

# Main deployment logic
function Start-EnhancedDeployment {
    Write-Log "Healthcare AI Agent - Enhanced Deployment" -Color "Green"
    Write-Log "Target Region: $Region" -Color "White"
    Write-Log ""
    
    # Skip AWS validation if requested
    if ($SkipAWSValidation) {
        Write-Log "Skipping AWS credential validation (as requested)" -Color "Yellow"
        $awsValid = $false
    } else {
        $awsValid = Test-AWSCredentials
    }
    
    if ($LocalOnly) {
        Deploy-LocalDevelopment
        return
    }
    
    if ($awsValid) {
        Write-Log ""
        Write-Log "AWS CREDENTIALS VALID - PROCEEDING WITH AUTOMATED DEPLOYMENT" -Color "Green"
        Write-Log ""
        
        # Set region
        aws configure set region $Region
        
        try {
            # CDK deployment
            if (Test-Path "infrastructure") {
                Set-Location "infrastructure"
                
                Write-Log "Installing CDK dependencies..." -Color "Blue"
                npm install
                
                Write-Log "Bootstrapping CDK..." -Color "Blue"
                $identity = aws sts get-caller-identity | ConvertFrom-Json
                cdk bootstrap "aws://$($identity.Account)/$Region"
                
                Write-Log "Deploying infrastructure..." -Color "Blue" 
                cdk deploy --require-approval never
                
                Set-Location ".."
                Write-Log "Infrastructure deployment completed!" -Color "Green"
            }
        }
        catch {
            Write-Log "Automated deployment failed: $($_.Exception.Message)" -Color "Red"
            Write-Log "Falling back to manual deployment instructions..." -Color "Yellow"
            Show-ManualDeployment
        }
    } else {
        Show-CredentialFix
        Build-DeploymentPackage
        Show-ManualDeployment
    }
    
    Deploy-LocalDevelopment
    
    Write-Log ""
    Write-Log "DEPLOYMENT SUMMARY" -Color "Cyan"
    Write-Log "✅ Lambda handler ready: backend/lambda_handler.py" -Color "Green"
    Write-Log "✅ Deployment package: healthcare-ai-lambda.zip" -Color "Green"
    Write-Log "✅ Local development: http://localhost:8000" -Color "Green"
    Write-Log "⚠️  AWS deployment: Manual steps required" -Color "Yellow"
}

# Execute deployment
Start-EnhancedDeployment