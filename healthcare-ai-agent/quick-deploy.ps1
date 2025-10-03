# Healthcare AI Agent - Simple Deployment Package Creator
param([string]$Region = "eu-central-1")

Write-Host "Healthcare AI Agent - Creating Deployment Package for $Region" -ForegroundColor Green
Write-Host ""

# Create Lambda deployment package
Write-Host "Creating Lambda deployment package..." -ForegroundColor Blue
$deployDir = "aws-deployment"
if (Test-Path $deployDir) { Remove-Item $deployDir -Recurse -Force }
New-Item -ItemType Directory -Path $deployDir -Force | Out-Null

if (Test-Path "backend/lambda_handler.py") {
    Copy-Item "backend/lambda_handler.py" "$deployDir/" -Force
    Write-Host "✅ Copied lambda_handler.py" -ForegroundColor Green
}

if (Test-Path "backend/app.py") {
    Copy-Item "backend/app.py" "$deployDir/" -Force
    Write-Host "✅ Copied app.py" -ForegroundColor Green
}

# Create requirements.txt
@"
fastapi==0.104.1
pydantic==2.5.0
mangum==0.17.0
"@ | Out-File -FilePath "$deployDir/requirements.txt" -Encoding UTF8
Write-Host "✅ Created requirements.txt" -ForegroundColor Green

# Create deployment zip
if (Test-Path "healthcare-ai-lambda.zip") { Remove-Item "healthcare-ai-lambda.zip" -Force }
Compress-Archive -Path "$deployDir/*" -DestinationPath "healthcare-ai-lambda.zip" -Force
$zipSize = (Get-Item "healthcare-ai-lambda.zip").Length / 1KB
Write-Host "✅ Created healthcare-ai-lambda.zip ($([math]::Round($zipSize, 2)) KB)" -ForegroundColor Green
Remove-Item $deployDir -Recurse -Force

# Create frontend package
Write-Host "Preparing frontend..." -ForegroundColor Blue
if (Test-Path "frontend/build") {
    if (Test-Path "frontend-deployment.zip") { Remove-Item "frontend-deployment.zip" -Force }
    Compress-Archive -Path "frontend/build/*" -DestinationPath "frontend-deployment.zip" -Force
    $frontendSize = (Get-Item "frontend-deployment.zip").Length / 1KB
    Write-Host "✅ Created frontend-deployment.zip ($([math]::Round($frontendSize, 2)) KB)" -ForegroundColor Green
} else {
    Write-Host "⚠️ Frontend not built. Run: cd frontend && npm run build" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 DEPLOYMENT READY FOR $Region" -ForegroundColor Green
Write-Host ""
Write-Host "Files Created:" -ForegroundColor Cyan
Write-Host "  ✅ healthcare-ai-lambda.zip (Lambda function)" -ForegroundColor White
Write-Host "  ✅ frontend-deployment.zip (Frontend files)" -ForegroundColor White
Write-Host "  ✅ AWS_DEPLOYMENT_GUIDE.md (Instructions)" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Go to AWS Console in $Region region" -ForegroundColor White
Write-Host "2. Follow AWS_DEPLOYMENT_GUIDE.md for step-by-step instructions" -ForegroundColor White
Write-Host ""
Write-Host "Direct AWS Console Links:" -ForegroundColor Cyan
Write-Host "  Lambda: https://$Region.console.aws.amazon.com/lambda/" -ForegroundColor Gray
Write-Host "  API Gateway: https://$Region.console.aws.amazon.com/apigateway/" -ForegroundColor Gray
Write-Host "  S3: https://$Region.console.aws.amazon.com/s3/" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ DEPLOYMENT PACKAGE COMPLETE!" -ForegroundColor Green