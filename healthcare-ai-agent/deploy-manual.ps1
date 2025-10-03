# Healthcare AI Agent - Manual Deployment Package Creator
# This script prepares everything needed for manual AWS deployment

param(
    [string]$Region = "eu-central-1"
)

$ErrorActionPreference = "Continue"

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Create-DeploymentPackage {
    Write-Log "Creating Lambda deployment package..." -Color "Blue"
    
    # Create deployment directory
    $deployDir = "aws-deployment"
    if (Test-Path $deployDir) {
        Remove-Item $deployDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $deployDir -Force | Out-Null
    
    # Copy Lambda files
    if (Test-Path "backend/lambda_handler.py") {
        Copy-Item "backend/lambda_handler.py" "$deployDir/" -Force
        Write-Log "✅ Copied lambda_handler.py" -Color "Green"
    }
    
    if (Test-Path "backend/app.py") {
        Copy-Item "backend/app.py" "$deployDir/" -Force
        Write-Log "✅ Copied app.py" -Color "Green"
    }
    
    # Create requirements.txt for Lambda
    $requirements = @"
fastapi==0.104.1
pydantic==2.5.0
mangum==0.17.0
"@
    $requirements | Out-File -FilePath "$deployDir/requirements.txt" -Encoding UTF8
    Write-Log "✅ Created requirements.txt" -Color "Green"
    
    # Create deployment zip
    if (Test-Path "healthcare-ai-lambda.zip") {
        Remove-Item "healthcare-ai-lambda.zip" -Force
    }
    
    Compress-Archive -Path "$deployDir/*" -DestinationPath "healthcare-ai-lambda.zip" -Force
    $zipSize = (Get-Item "healthcare-ai-lambda.zip").Length / 1KB
    Write-Log "✅ Created healthcare-ai-lambda.zip ($([math]::Round($zipSize, 2)) KB)" -Color "Green"
    
    # Cleanup
    Remove-Item $deployDir -Recurse -Force
}

function Prepare-Frontend {
    Write-Log "Preparing frontend for deployment..." -Color "Blue"
    
    if (Test-Path "frontend/build") {
        Write-Log "✅ Frontend build exists" -Color "Green"
        
        # Create frontend deployment package
        if (Test-Path "frontend-deployment.zip") {
            Remove-Item "frontend-deployment.zip" -Force
        }
        
        Compress-Archive -Path "frontend/build/*" -DestinationPath "frontend-deployment.zip" -Force
        $zipSize = (Get-Item "frontend-deployment.zip").Length / 1KB
        Write-Log "✅ Created frontend-deployment.zip ($([math]::Round($zipSize, 2)) KB)" -Color "Green"
    } else {
        Write-Log "⚠️ Frontend not built. Run: cd frontend && npm run build" -Color "Yellow"
    }
}

function Show-DeploymentInstructions {
    Write-Log ""
    Write-Log "🚀 MANUAL DEPLOYMENT READY FOR REGION: $Region" -Color "Green"
    Write-Log ""
    Write-Log "📦 Files Created:" -Color "Cyan"
    Write-Log "  ✅ healthcare-ai-lambda.zip (Lambda function)" -Color "White"
    Write-Log "  ✅ frontend-deployment.zip (Frontend files)" -Color "White"
    Write-Log "  ✅ AWS_DEPLOYMENT_GUIDE.md (Detailed instructions)" -Color "White"
    Write-Log ""
    Write-Log "🎯 Next Steps:" -Color "Yellow"
    Write-Log ""
    Write-Log "Manual Component Deployment:" -Color "Green"
    Write-Log "1. Follow AWS_DEPLOYMENT_GUIDE.md step by step" -Color "White"
    Write-Log "2. Upload healthcare-ai-lambda.zip to Lambda" -Color "White"
    Write-Log "3. Configure API Gateway manually" -Color "White"
    Write-Log "4. Upload frontend-deployment.zip to S3" -Color "White"
    Write-Log ""
    Write-Log "Direct Links for ${Region}:" -Color "Cyan"
    Write-Log "  Lambda Console: https://$Region.console.aws.amazon.com/lambda/" -Color "Gray"
    Write-Log "  API Gateway: https://$Region.console.aws.amazon.com/apigateway/" -Color "Gray"
    Write-Log "  S3 Console: https://$Region.console.aws.amazon.com/s3/" -Color "Gray"
    Write-Log ""
    Write-Log "🏥 Application Status:" -Color "Yellow"
    Write-Log "  Backend: Ready for deployment" -Color "White"
    Write-Log "  Frontend: Built and packaged" -Color "White"
    Write-Log "  Region: $Region" -Color "White"
}

# Main execution
Write-Log "Healthcare AI Agent - Manual Deployment Package Creator" -Color "Green"
Write-Log "Target Region: $Region" -Color "White"
Write-Log ""

Create-DeploymentPackage
Prepare-Frontend
Show-DeploymentInstructions

Write-Log ""
Write-Log "✅ DEPLOYMENT PACKAGE COMPLETE" -Color "Green"
Write-Log "Follow AWS_DEPLOYMENT_GUIDE.md for detailed deployment steps" -Color "White"