# Healthcare AI Agent - AWS Deployment Package Creator

Write-Host "Creating AWS Lambda deployment package..." -ForegroundColor Green

# Set variables
$BackendDir = "backend"
$DeploymentDir = "aws-deployment"
$PackageName = "healthcare-ai-lambda.zip"

# Clean up previous deployment
if (Test-Path $DeploymentDir) {
    Remove-Item $DeploymentDir -Recurse -Force
}
if (Test-Path $PackageName) {
    Remove-Item $PackageName -Force
}

# Create deployment directory and copy files
New-Item -ItemType Directory -Path $DeploymentDir -Force | Out-Null
Copy-Item "$BackendDir\*.py" $DeploymentDir -Force

Write-Host "Created deployment package setup"
Write-Host "Next: Manually create Lambda function in AWS Console (eu-central-1)"
Write-Host "Use lambda_handler.lambda_handler as the handler"