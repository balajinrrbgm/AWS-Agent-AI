# Healthcare AI Agent - AWS Deployment Script (Fixed)
# Deploys backend, frontend, and infrastructure to AWS (eu-central-1)

param(
    [string]$Region = "eu-central-1",
    [string]$StackName = "HealthcareAIAgentStack",
    [switch]$SkipPrerequisites = $false,
    [switch]$DeployOnly = $false
)

# Set error action preference
$ErrorActionPreference = "Continue"

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Test-Prerequisites {
    Write-Log "Checking prerequisites..." -Color "Blue"
    
    $allGood = $true
    
    # Check AWS CLI
    try {
        $null = aws --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "AWS CLI: Found" -Color "Green"
        } else {
            Write-Log "AWS CLI not found. Please install AWS CLI first." -Color "Red"
            $allGood = $false
        }
    }
    catch {
        Write-Log "AWS CLI not found. Please install AWS CLI first." -Color "Red"
        $allGood = $false
    }
    
    # Check AWS credentials
    try {
        $null = aws sts get-caller-identity 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "AWS credentials: Configured" -Color "Green"
        } else {
            Write-Log "AWS credentials not configured. Run 'aws configure' first." -Color "Red"
            $allGood = $false
        }
    }
    catch {
        Write-Log "AWS credentials not configured. Run 'aws configure' first." -Color "Red"
        $allGood = $false
    }
    
    # Check Node.js
    try {
        $null = node --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Node.js: Found" -Color "Green"
        } else {
            Write-Log "Node.js not found. Please install Node.js first." -Color "Red"
            $allGood = $false
        }
    }
    catch {
        Write-Log "Node.js not found. Please install Node.js first." -Color "Red"
        $allGood = $false
    }
    
    # Check Python
    try {
        $null = python --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Python: Found" -Color "Green"
        } else {
            Write-Log "Python not found. Please install Python first." -Color "Red"
            $allGood = $false
        }
    }
    catch {
        Write-Log "Python not found. Please install Python first." -Color "Red"
        $allGood = $false
    }
    
    return $allGood
}

function Set-AWSRegion {
    Write-Log "Setting AWS region to $Region" -Color "Blue"
    $env:AWS_DEFAULT_REGION = $Region
    aws configure set region $Region
}

function Install-CDK {
    Write-Log "Installing AWS CDK..." -Color "Blue"
    try {
        $null = cdk --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "CDK already installed" -Color "Green"
        } else {
            Write-Log "Installing AWS CDK CLI..." -Color "Yellow"
            npm install -g aws-cdk
        }
    }
    catch {
        Write-Log "Installing AWS CDK CLI..." -Color "Yellow"
        npm install -g aws-cdk
    }
}

function Build-Backend {
    Write-Log "Preparing backend..." -Color "Blue"
    
    if (Test-Path "backend") {
        Set-Location "backend"
        
        # Create deployment package
        $packageDir = "deployment-package"
        if (Test-Path $packageDir) {
            Remove-Item $packageDir -Recurse -Force
        }
        New-Item -ItemType Directory -Path $packageDir -Force | Out-Null
        
        # Copy source files
        Copy-Item "*.py" $packageDir -Force -ErrorAction SilentlyContinue
        
        # Create deployment zip
        if (Test-Path $packageDir) {
            Set-Location $packageDir
            Compress-Archive -Path "*" -DestinationPath "../backend-deployment.zip" -Force
            Set-Location ".."
        }
        
        Set-Location ".."
        Write-Log "Backend prepared" -Color "Green"
    } else {
        Write-Log "Backend directory not found" -Color "Yellow"
    }
}

function Build-Frontend {
    Write-Log "Building frontend..." -Color "Blue"
    
    if (Test-Path "frontend") {
        Set-Location "frontend"
        
        # Install dependencies
        npm install
        
        # Build production version
        npm run build
        
        Set-Location ".."
        Write-Log "Frontend built successfully" -Color "Green"
    } else {
        Write-Log "Frontend directory not found" -Color "Yellow"
    }
}

function Deploy-Infrastructure {
    Write-Log "Deploying infrastructure..." -Color "Blue"
    
    if (Test-Path "infrastructure") {
        Set-Location "infrastructure"
        
        # Install CDK dependencies
        npm install
        
        # Bootstrap CDK if needed
        Write-Log "Bootstrapping CDK..." -Color "Yellow"
        try {
            cdk bootstrap "aws://unknown-account/$Region"
        }
        catch {
            Write-Log "CDK bootstrap failed or already done" -Color "Yellow"
        }
        
        # Deploy stack
        Write-Log "Deploying CDK stack..." -Color "Yellow"
        cdk deploy --require-approval never --outputs-file outputs.json
        
        Set-Location ".."
        Write-Log "Infrastructure deployed" -Color "Green"
    } else {
        Write-Log "Infrastructure directory not found" -Color "Yellow"
    }
}

function Show-DeploymentInfo {
    Write-Log "Deployment Information:" -Color "Blue"
    Write-Host "=" * 60 -ForegroundColor "Blue"
    
    try {
        $outputs = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs" | ConvertFrom-Json
        
        if ($outputs) {
            foreach ($output in $outputs) {
                $key = $output.OutputKey
                $value = $output.OutputValue
                
                if ($key -like "*api*") {
                    Write-Log "API Endpoint: $value" -Color "Green"
                } elseif ($key -like "*distribution*") {
                    Write-Log "CloudFront URL: $value" -Color "Green"
                } elseif ($key -like "*bucket*") {
                    Write-Log "S3 Bucket: $value" -Color "Green"
                } else {
                    Write-Log "$key : $value" -Color "White"
                }
            }
        }
        
        Write-Host "=" * 60 -ForegroundColor "Blue"
    }
    catch {
        Write-Log "Could not retrieve deployment information" -Color "Yellow"
        Write-Log $_.Exception.Message -Color "Red"
    }
}

# Main deployment process
function Start-Deployment {
    Write-Log "Starting Healthcare AI Agent deployment to AWS" -Color "Blue"
    Write-Log "Target Region: $Region" -Color "Blue"
    Write-Log "Stack Name: $StackName" -Color "Blue"
    
    # Check prerequisites
    if (-not $SkipPrerequisites -and -not (Test-Prerequisites)) {
        Write-Log "Prerequisites not met. Exiting." -Color "Red"
        return $false
    }
    
    try {
        # Set AWS region
        Set-AWSRegion
        
        # Install CDK
        Install-CDK
        
        if (-not $DeployOnly) {
            # Build backend
            Build-Backend
            
            # Build frontend
            Build-Frontend
        }
        
        # Deploy infrastructure
        Deploy-Infrastructure
        
        # Show deployment information
        Show-DeploymentInfo
        
        Write-Log ""
        Write-Log "Deployment completed successfully!" -Color "Green"
        Write-Log ""
        Write-Log "Next Steps:" -Color "Blue"
        Write-Log "1. Test API endpoints" -Color "White"
        Write-Log "2. Configure custom domain (optional)" -Color "White"
        Write-Log "3. Set up monitoring and alerts" -Color "White"
        
        return $true
    }
    catch {
        Write-Log "Deployment failed: $($_.Exception.Message)" -Color "Red"
        return $false
    }
}

# Start deployment
Start-Deployment