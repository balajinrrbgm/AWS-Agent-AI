# Healthcare AI Agent - AWS Deployment Script (PowerShell)
# Deploys backend, frontend, and infrastructure to AWS (eu-central-1)

param(
    [string]$Region = "eu-central-1",
    [string]$StackName = "HealthcareAIAgentStack",
    [switch]$SkipPrerequisites = $false,
    [switch]$DeployOnly = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Blue = "Blue"

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Test-Prerequisites {
    Write-Log "🔍 Checking prerequisites..." -Color $Blue
    
    $allGood = $true
    
    # Check AWS CLI
    try {
        $awsVersion = aws --version 2>$null
        Write-Log "✅ AWS CLI: $awsVersion" -Color $Green
    }
    catch {
        Write-Log "❌ AWS CLI not found. Please install AWS CLI first." -Color $Red
        $allGood = $false
    }
    
    # Check AWS credentials
    try {
        $awsIdentity = aws sts get-caller-identity 2>$null | ConvertFrom-Json
        Write-Log "✅ AWS Account: $($awsIdentity.Account)" -Color $Green
    }
    catch {
        Write-Log "❌ AWS credentials not configured. Run 'aws configure' first." -Color $Red
        $allGood = $false
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version 2>$null
        Write-Log "✅ Node.js: $nodeVersion" -Color $Green
    }
    catch {
        Write-Log "❌ Node.js not found. Please install Node.js first." -Color $Red
        $allGood = $false
    }
    
    # Check Python
    try {
        $pythonVersion = python --version 2>$null
        Write-Log "✅ Python: $pythonVersion" -Color $Green
    }
    catch {
        Write-Log "❌ Python not found. Please install Python first." -Color $Red
        $allGood = $false
    }
    
    return $allGood
}

function Set-AWSRegion {
    Write-Log "🌍 Setting AWS region to $Region" -Color $Blue
    $env:AWS_DEFAULT_REGION = $Region
    aws configure set region $Region
}

function Install-CDK {
    Write-Log "🔧 Installing AWS CDK..." -Color $Blue
    try {
        $cdkVersion = cdk --version 2>$null
        Write-Log "✅ CDK already installed: $cdkVersion" -Color $Green
    }
    catch {
        Write-Log "Installing AWS CDK CLI..." -Color $Yellow
        npm install -g aws-cdk
    }
}

function New-LambdaLayer {
    Write-Log "📦 Creating Lambda layer..." -Color $Blue
    
    # Create layer directory structure
    $layerDir = "lambda-layer"
    $pythonDir = "$layerDir\python"
    
    if (Test-Path $layerDir) {
        Remove-Item $layerDir -Recurse -Force
    }
    
    New-Item -ItemType Directory -Path $layerDir -Force | Out-Null
    New-Item -ItemType Directory -Path $pythonDir -Force | Out-Null
    
    # Install dependencies
    Set-Location backend
    pip install -r requirements.txt -t "../$pythonDir" --quiet
    Set-Location ..
    
    # Create zip file
    Compress-Archive -Path "$layerDir\*" -DestinationPath "lambda-layer.zip" -Force
    
    Write-Log "✅ Lambda layer created" -Color $Green
}

function Build-Backend {
    Write-Log "📦 Preparing backend..." -Color $Blue
    
    Set-Location backend
    
    # Create deployment package
    $packageDir = "deployment-package"
    if (Test-Path $packageDir) {
        Remove-Item $packageDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $packageDir -Force | Out-Null
    
    # Copy source files
    Copy-Item "*.py" $packageDir -Force
    if (Test-Path "src") {
        Copy-Item "src" $packageDir -Recurse -Force
    }
    
    # Create deployment zip
    Set-Location $packageDir
    Compress-Archive -Path "*" -DestinationPath "../backend-deployment.zip" -Force
    Set-Location ..
    
    Set-Location ..
    Write-Log "✅ Backend prepared" -Color $Green
}

function Build-Frontend {
    Write-Log "🎨 Building frontend..." -Color $Blue
    
    Set-Location frontend
    
    # Install dependencies
    npm install --silent
    
    # Build production version
    npm run build --silent
    
    Set-Location ..
    Write-Log "✅ Frontend built successfully" -Color $Green
}

function Deploy-Infrastructure {
    Write-Log "🏗️ Deploying infrastructure..." -Color $Blue
    
    Set-Location infrastructure
    
    # Install CDK dependencies
    npm install --silent
    
    # Bootstrap CDK if needed
    Write-Log "Bootstrapping CDK..." -Color $Yellow
    try {
        cdk bootstrap "aws://unknown-account/$Region" --quiet
    }
    catch {
        Write-Log "⚠️ CDK bootstrap failed or already done" -Color $Yellow
    }
    
    # Deploy stack
    Write-Log "Deploying CDK stack..." -Color $Yellow
    cdk deploy --require-approval never --outputs-file outputs.json
    
    Set-Location ..
    Write-Log "✅ Infrastructure deployed" -Color $Green
}

function Deploy-Frontend {
    Write-Log "🌐 Deploying frontend..." -Color $Blue
    
    # Get S3 bucket from stack outputs
    try {
        $outputs = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs" | ConvertFrom-Json
        
        $s3Bucket = $null
        foreach ($output in $outputs) {
            if ($output.OutputKey -like "*bucket*" -or $output.OutputKey -like "*Bucket*") {
                $s3Bucket = $output.OutputValue
                break
            }
        }
        
        if ($s3Bucket) {
            # Sync frontend to S3
            Set-Location frontend
            aws s3 sync build/ "s3://$s3Bucket/" --delete --quiet
            Set-Location ..
            Write-Log "✅ Frontend deployed to S3: $s3Bucket" -Color $Green
        }
        else {
            Write-Log "⚠️ Could not find S3 bucket in stack outputs" -Color $Yellow
        }
    }
    catch {
        Write-Log "⚠️ Frontend deployment to S3 failed: $($_.Exception.Message)" -Color $Yellow
    }
}

function New-EnvironmentFile {
    Write-Log "📝 Creating environment configuration..." -Color $Blue
    
    try {
        $outputs = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs" | ConvertFrom-Json
        
        $apiUrl = $null
        $userPoolId = $null
        $userPoolClientId = $null
        
        foreach ($output in $outputs) {
            switch -Wildcard ($output.OutputKey) {
                "*api*" { $apiUrl = $output.OutputValue }
                "*UserPool*" { 
                    if ($output.OutputKey -notlike "*Client*") {
                        $userPoolId = $output.OutputValue
                    }
                    else {
                        $userPoolClientId = $output.OutputValue
                    }
                }
            }
        }
        
        $envContent = @"
REACT_APP_API_URL=$($apiUrl -replace 'null', 'https://your-api-gateway-url')
REACT_APP_AWS_REGION=$Region
REACT_APP_USER_POOL_ID=$($userPoolId -replace 'null', 'your-user-pool-id')
REACT_APP_USER_POOL_CLIENT_ID=$($userPoolClientId -replace 'null', 'your-user-pool-client-id')
REACT_APP_ENVIRONMENT=production
"@
        
        $envContent | Out-File -FilePath "frontend\.env.production" -Encoding UTF8
        Write-Log "✅ Environment file created" -Color $Green
    }
    catch {
        Write-Log "⚠️ Error creating environment file: $($_.Exception.Message)" -Color $Yellow
    }
}

function Show-DeploymentInfo {
    Write-Log "📋 Deployment Information:" -Color $Blue
    Write-Host "=" * 60 -ForegroundColor $Blue
    
    try {
        $outputs = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs" | ConvertFrom-Json
        
        foreach ($output in $outputs) {
            $key = $output.OutputKey
            $value = $output.OutputValue
            
            switch -Wildcard ($key) {
                "*api*" { Write-Log "🔗 API Endpoint: $value" -Color $Green }
                "*distribution*" { Write-Log "🌐 CloudFront URL: $value" -Color $Green }
                "*bucket*" { Write-Log "🪣 S3 Bucket: $value" -Color $Green }
                "*UserPool*" { Write-Log "👥 Cognito User Pool: $value" -Color $Green }
                default { Write-Log "$key : $value" -Color "White" }
            }
        }
        
        Write-Host "=" * 60 -ForegroundColor $Blue
    }
    catch {
        Write-Log "⚠️ Could not retrieve deployment information" -Color $Yellow
    }
}

# Main deployment process
function Start-Deployment {
    Write-Log "🚀 Starting Healthcare AI Agent deployment to AWS" -Color $Blue
    Write-Log "🌍 Target Region: $Region" -Color $Blue
    Write-Log "📦 Stack Name: $StackName" -Color $Blue
    
    # Check prerequisites
    if (-not $SkipPrerequisites -and -not (Test-Prerequisites)) {
        Write-Log "❌ Prerequisites not met. Exiting." -Color $Red
        exit 1
    }
    
    try {
        # Set AWS region
        Set-AWSRegion
        
        # Install CDK
        Install-CDK
        
        if (-not $DeployOnly) {
            # Create Lambda layer
            New-LambdaLayer
            
            # Build backend
            Build-Backend
            
            # Build frontend
            Build-Frontend
        }
        
        # Deploy infrastructure
        Deploy-Infrastructure
        
        # Create environment configuration
        New-EnvironmentFile
        
        if (-not $DeployOnly) {
            # Deploy frontend to S3
            Deploy-Frontend
        }
        
        # Show deployment information
        Show-DeploymentInfo
        
        Write-Log ""
        Write-Log "🎉 Deployment completed successfully!" -Color $Green
        Write-Log ""
        Write-Log "📖 Next Steps:" -Color $Blue
        Write-Log "1. Test API endpoints" -Color "White"
        Write-Log "2. Configure custom domain (optional)" -Color "White"
        Write-Log "3. Set up monitoring and alerts" -Color "White"
        Write-Log "4. Configure backup policies" -Color "White"
        Write-Log "5. Test frontend application" -Color "White"
        
    }
    catch {
        Write-Log "❌ Deployment failed: $($_.Exception.Message)" -Color $Red
        exit 1
    }
}

# Start deployment
Start-Deployment