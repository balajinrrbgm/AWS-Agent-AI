#!/usr/bin/env python3
"""
Healthcare AI Agent - Complete AWS Deployment Script
Deploys backend, frontend, and infrastructure to AWS (eu-central-1)
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

class HealthcareAIDeployer:
    def __init__(self):
        self.region = "eu-central-1"
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.infrastructure_dir = self.project_root / "infrastructure"
        
        # AWS Configuration
        self.stack_name = "HealthcareAIAgentStack"
        self.app_name = "healthcare-ai-agent"
        
    def log(self, message):
        """Print timestamped log message"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def run_command(self, command, cwd=None, check=True):
        """Run shell command with error handling"""
        self.log(f"Running: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                check=check
            )
            if result.stdout:
                print(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {e}")
            if e.stderr:
                print(e.stderr)
            if check:
                sys.exit(1)
            return e
            
    def check_prerequisites(self):
        """Check if required tools are installed"""
        self.log("Checking prerequisites...")
        
        # Check AWS CLI
        try:
            result = self.run_command("aws --version", check=False)
            if result.returncode != 0:
                self.log("❌ AWS CLI not found. Please install AWS CLI first.")
                return False
        except Exception:
            self.log("❌ AWS CLI not found. Please install AWS CLI first.")
            return False
            
        # Check AWS credentials
        try:
            result = self.run_command("aws sts get-caller-identity", check=False)
            if result.returncode != 0:
                self.log("❌ AWS credentials not configured. Run 'aws configure' first.")
                return False
        except Exception:
            self.log("❌ AWS credentials not configured. Run 'aws configure' first.")
            return False
            
        # Check Node.js
        try:
            result = self.run_command("node --version", check=False)
            if result.returncode != 0:
                self.log("❌ Node.js not found. Please install Node.js first.")
                return False
        except Exception:
            self.log("❌ Node.js not found. Please install Node.js first.")
            return False
            
        # Check Python
        try:
            result = self.run_command("python --version", check=False)
            if result.returncode != 0:
                self.log("❌ Python not found. Please install Python first.")
                return False
        except Exception:
            self.log("❌ Python not found. Please install Python first.")
            return False
            
        self.log("✅ All prerequisites met!")
        return True
        
    def setup_aws_region(self):
        """Configure AWS region"""
        self.log(f"Setting AWS region to {self.region}")
        os.environ['AWS_DEFAULT_REGION'] = self.region
        self.run_command(f"aws configure set region {self.region}")
        
    def prepare_backend(self):
        """Prepare backend for deployment"""
        self.log("📦 Preparing backend...")
        
        # Create Lambda deployment package
        lambda_package_dir = self.backend_dir / "lambda-package"
        lambda_package_dir.mkdir(exist_ok=True)
        
        # Copy backend files
        self.run_command(f"xcopy /E /I /Y *.py lambda-package\\", cwd=self.backend_dir)
        
        # Install dependencies in package directory
        self.run_command(
            f"pip install -r requirements.txt -t lambda-package/",
            cwd=self.backend_dir
        )
        
        self.log("✅ Backend prepared for deployment")
        
    def prepare_frontend(self):
        """Prepare frontend for deployment"""
        self.log("🎨 Preparing frontend...")
        
        # Install dependencies
        self.run_command("npm install", cwd=self.frontend_dir)
        
        # Build production version
        self.run_command("npm run build", cwd=self.frontend_dir)
        
        self.log("✅ Frontend built successfully")
        
    def deploy_infrastructure(self):
        """Deploy infrastructure using CDK"""
        self.log("🏗️ Deploying infrastructure...")
        
        # Install CDK dependencies
        self.run_command("npm install", cwd=self.infrastructure_dir)
        
        # Install CDK CLI if not present
        try:
            self.run_command("cdk --version", check=False)
        except:
            self.log("Installing AWS CDK CLI...")
            self.run_command("npm install -g aws-cdk")
            
        # Bootstrap CDK (if not already done)
        self.log("Bootstrapping CDK...")
        self.run_command(f"cdk bootstrap aws://unknown-account/{self.region}", cwd=self.infrastructure_dir)
        
        # Deploy the stack
        self.log("Deploying CDK stack...")
        self.run_command(f"cdk deploy --require-approval never", cwd=self.infrastructure_dir)
        
        self.log("✅ Infrastructure deployed successfully")
        
    def deploy_frontend_to_s3(self):
        """Deploy frontend to S3 and CloudFront"""
        self.log("🌐 Deploying frontend to S3...")
        
        # Get S3 bucket name from stack outputs
        try:
            result = self.run_command(
                f"aws cloudformation describe-stacks --stack-name {self.stack_name} --query 'Stacks[0].Outputs'",
                check=False
            )
            if result.returncode == 0:
                outputs = json.loads(result.stdout)
                s3_bucket = None
                for output in outputs:
                    if 'bucket' in output.get('OutputKey', '').lower():
                        s3_bucket = output['OutputValue']
                        break
                        
                if s3_bucket:
                    # Sync frontend build to S3
                    self.run_command(
                        f"aws s3 sync build/ s3://{s3_bucket}/ --delete",
                        cwd=self.frontend_dir
                    )
                    self.log(f"✅ Frontend deployed to S3 bucket: {s3_bucket}")
                else:
                    self.log("⚠️ Could not find S3 bucket in stack outputs")
            else:
                self.log("⚠️ Could not retrieve stack outputs for S3 deployment")
        except Exception as e:
            self.log(f"⚠️ Frontend S3 deployment failed: {e}")
            
    def create_lambda_layer(self):
        """Create and deploy Lambda layer for dependencies"""
        self.log("📦 Creating Lambda layer...")
        
        layer_dir = self.project_root / "lambda-layer"
        layer_dir.mkdir(exist_ok=True)
        
        python_dir = layer_dir / "python"
        python_dir.mkdir(exist_ok=True)
        
        # Install dependencies in layer
        self.run_command(
            f"pip install -r backend/requirements.txt -t lambda-layer/python/",
            cwd=self.project_root
        )
        
        # Create layer zip
        self.run_command(
            "powershell Compress-Archive -Path lambda-layer/* -DestinationPath lambda-layer.zip -Force",
            cwd=self.project_root
        )
        
        self.log("✅ Lambda layer created")
        
    def get_deployment_info(self):
        """Get deployment information"""
        self.log("📋 Getting deployment information...")
        
        try:
            # Get stack outputs
            result = self.run_command(
                f"aws cloudformation describe-stacks --stack-name {self.stack_name} --query 'Stacks[0].Outputs'",
                check=False
            )
            
            if result.returncode == 0:
                outputs = json.loads(result.stdout)
                self.log("\\n🎉 Deployment Information:")
                self.log("=" * 50)
                
                for output in outputs:
                    key = output.get('OutputKey', '')
                    value = output.get('OutputValue', '')
                    description = output.get('Description', '')
                    
                    if 'api' in key.lower():
                        self.log(f"🔗 API Endpoint: {value}")
                    elif 'distribution' in key.lower():
                        self.log(f"🌐 CloudFront URL: {value}")
                    elif 'bucket' in key.lower():
                        self.log(f"🪣 S3 Bucket: {value}")
                    elif 'userpool' in key.lower():
                        self.log(f"👥 Cognito User Pool: {value}")
                        
                self.log("=" * 50)
            else:
                self.log("⚠️ Could not retrieve deployment information")
                
        except Exception as e:
            self.log(f"⚠️ Error getting deployment info: {e}")
            
    def create_env_file(self):
        """Create environment file for frontend"""
        self.log("📝 Creating environment configuration...")
        
        try:
            # Get API Gateway URL from stack outputs
            result = self.run_command(
                f"aws cloudformation describe-stacks --stack-name {self.stack_name} --query 'Stacks[0].Outputs'",
                check=False
            )
            
            if result.returncode == 0:
                outputs = json.loads(result.stdout)
                api_url = None
                user_pool_id = None
                user_pool_client_id = None
                
                for output in outputs:
                    key = output.get('OutputKey', '')
                    value = output.get('OutputValue', '')
                    
                    if 'apiendpoint' in key.lower():
                        api_url = value
                    elif 'userpoolid' in key.lower():
                        user_pool_id = value
                    elif 'userpoolclientid' in key.lower():
                        user_pool_client_id = value
                        
                # Create .env file for frontend
                env_content = f"""REACT_APP_API_URL={api_url or 'https://your-api-gateway-url'}
REACT_APP_AWS_REGION={self.region}
REACT_APP_USER_POOL_ID={user_pool_id or 'your-user-pool-id'}
REACT_APP_USER_POOL_CLIENT_ID={user_pool_client_id or 'your-user-pool-client-id'}
REACT_APP_ENVIRONMENT=production
"""
                
                env_file = self.frontend_dir / ".env.production"
                with open(env_file, 'w') as f:
                    f.write(env_content)
                    
                self.log(f"✅ Environment file created: {env_file}")
                
        except Exception as e:
            self.log(f"⚠️ Error creating environment file: {e}")
            
    def deploy(self):
        """Main deployment function"""
        self.log("🚀 Starting Healthcare AI Agent deployment to AWS")
        self.log(f"🌍 Target Region: {self.region}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
            
        try:
            # Setup AWS region
            self.setup_aws_region()
            
            # Create Lambda layer
            self.create_lambda_layer()
            
            # Prepare backend
            self.prepare_backend()
            
            # Deploy infrastructure
            self.deploy_infrastructure()
            
            # Create environment configuration
            self.create_env_file()
            
            # Prepare and deploy frontend
            self.prepare_frontend()
            self.deploy_frontend_to_s3()
            
            # Get deployment information
            self.get_deployment_info()
            
            self.log("\\n🎉 Deployment completed successfully!")
            self.log("\\n📖 Next Steps:")
            self.log("1. Configure DNS (if using custom domain)")
            self.log("2. Set up monitoring and alerts")
            self.log("3. Configure backup policies")
            self.log("4. Test all endpoints and functionality")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Deployment failed: {e}")
            return False

if __name__ == "__main__":
    deployer = HealthcareAIDeployer()
    success = deployer.deploy()
    sys.exit(0 if success else 1)