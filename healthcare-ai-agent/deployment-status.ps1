# Healthcare AI Agent - Deployment Status Check

param(
    [string]$Region = "eu-central-1"
)

Write-Host "Healthcare AI Agent - AWS Deployment Setup" -ForegroundColor Green
Write-Host "Region: $Region (Frankfurt)" -ForegroundColor Cyan
Write-Host ""

# Check if AWS credentials are configured
Write-Host "Step 1: Checking AWS Configuration..." -ForegroundColor Yellow

$awsConfigured = $false
try {
    $awsResult = aws sts get-caller-identity 2>$null
    if ($LASTEXITCODE -eq 0 -and $awsResult) {
        $awsIdentity = $awsResult | ConvertFrom-Json
        Write-Host "AWS Credentials: Configured" -ForegroundColor Green
        Write-Host "   Account: $($awsIdentity.Account)" -ForegroundColor White
        Write-Host "   User: $($awsIdentity.Arn)" -ForegroundColor White
        
        # Set region
        aws configure set region $Region
        Write-Host "Region set to $Region" -ForegroundColor Green
        $awsConfigured = $true
    }
} catch {
    # Credentials not configured
}

if (-not $awsConfigured) {
    Write-Host "AWS Credentials: Not configured" -ForegroundColor Red
    Write-Host ""
    Write-Host "MANUAL SETUP REQUIRED" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Option 1: Configure AWS CLI" -ForegroundColor Cyan
    Write-Host "aws configure" -ForegroundColor White
    Write-Host "Enter your AWS Access Key ID, Secret Key, and set region to $Region" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Option 2: Manual AWS Console Deployment" -ForegroundColor Cyan
    Write-Host "1. AWS Lambda Console: https://$Region.console.aws.amazon.com/lambda/" -ForegroundColor White
    Write-Host "2. Create function with Python 3.11" -ForegroundColor White
    Write-Host "3. Upload the lambda_handler.py code from backend/" -ForegroundColor White
    Write-Host "4. API Gateway Console: https://$Region.console.aws.amazon.com/apigateway/" -ForegroundColor White
    Write-Host "5. Create REST API and connect to Lambda" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "READY FOR AUTOMATED DEPLOYMENT" -ForegroundColor Green
    Write-Host ""
    Write-Host "Run the following commands:" -ForegroundColor Cyan
    Write-Host "1. cd infrastructure" -ForegroundColor White
    Write-Host "2. npm install" -ForegroundColor White
    Write-Host "3. cdk bootstrap aws://$($awsIdentity.Account)/$Region" -ForegroundColor White
    Write-Host "4. cdk deploy --require-approval never" -ForegroundColor White
}

Write-Host ""
Write-Host "LOCAL DEVELOPMENT (Available Now)" -ForegroundColor Blue
Write-Host "Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "Health Check: http://localhost:8000/health" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White

Write-Host ""
Write-Host "Deployment Files Ready:" -ForegroundColor Blue
Write-Host "Lambda Handler: backend/lambda_handler.py" -ForegroundColor Green
Write-Host "CDK Infrastructure: infrastructure/" -ForegroundColor Green
Write-Host "Frontend Build: frontend/build/ (after npm run build)" -ForegroundColor Green

Write-Host ""
Write-Host "Quick Test Commands:" -ForegroundColor Blue
Write-Host "curl http://localhost:8000/health" -ForegroundColor White
Write-Host 'curl -X POST http://localhost:8000/api/v1/query -H "Content-Type: application/json" -d "{""question"":""Hello""}"' -ForegroundColor White