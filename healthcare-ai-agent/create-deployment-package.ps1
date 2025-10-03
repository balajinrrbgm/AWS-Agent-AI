# Healthcare AI Agent - Create AWS Deployment Package
# This script creates a deployment package for AWS Lambda

Write-Host "🚀 Creating AWS Lambda deployment package for eu-central-1" -ForegroundColor Green
Write-Host ""

# Set variables
$BackendDir = "backend"
$DeploymentDir = "aws-deployment"
$PackageName = "healthcare-ai-lambda.zip"

# Clean up previous deployment
if (Test-Path $DeploymentDir) {
    Write-Host "🧹 Cleaning up previous deployment..." -ForegroundColor Yellow
    Remove-Item $DeploymentDir -Recurse -Force
}

if (Test-Path $PackageName) {
    Remove-Item $PackageName -Force
}

# Create deployment directory
Write-Host "📦 Creating deployment package..." -ForegroundColor Blue
New-Item -ItemType Directory -Path $DeploymentDir -Force | Out-Null

# Copy application files
Write-Host "📄 Copying application files..." -ForegroundColor Blue
Copy-Item "$BackendDir\*.py" $DeploymentDir -Force

# Install dependencies
Write-Host "📚 Installing dependencies..." -ForegroundColor Blue
Set-Location $DeploymentDir

# Create a minimal requirements.txt for Lambda
@"
fastapi==0.104.1
pydantic==2.5.0
mangum==0.17.0
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8

# Install packages
pip install -r requirements.txt -t . --quiet --no-deps

# Clean up unnecessary files
Write-Host "🧹 Cleaning up package..." -ForegroundColor Yellow
Get-ChildItem -Recurse -Include "*.pyc", "__pycache__", "*.dist-info", "tests" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Create deployment zip
Write-Host "📦 Creating deployment zip..." -ForegroundColor Blue
Compress-Archive -Path * -DestinationPath "../$PackageName" -Force

Set-Location ..

Write-Host ""
Write-Host "✅ Deployment package created: $PackageName" -ForegroundColor Green
Write-Host "📊 Package size: $([math]::Round((Get-Item $PackageName).Length / 1MB, 2)) MB" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 Next steps for AWS deployment:" -ForegroundColor Cyan
Write-Host "1. Go to AWS Lambda Console (eu-central-1 region)" -ForegroundColor White
Write-Host "2. Create new function:" -ForegroundColor White
Write-Host "   - Name: healthcare-ai-agent" -ForegroundColor White
Write-Host "   - Runtime: Python 3.11" -ForegroundColor White
Write-Host "   - Handler: lambda_handler.lambda_handler" -ForegroundColor White
Write-Host "3. Upload $PackageName" -ForegroundColor White
Write-Host "4. Create API Gateway REST API" -ForegroundColor White
Write-Host "5. Connect API Gateway to Lambda function" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Manual AWS Console URLs:" -ForegroundColor Cyan
Write-Host "Lambda: https://eu-central-1.console.aws.amazon.com/lambda/" -ForegroundColor White
Write-Host "API Gateway: https://eu-central-1.console.aws.amazon.com/apigateway/" -ForegroundColor White
Write-Host ""