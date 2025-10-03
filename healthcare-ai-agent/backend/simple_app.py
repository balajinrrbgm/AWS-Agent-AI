#!/usr/bin/env python3
"""
Simple FastAPI Healthcare AI Agent startup script
This version loads minimal dependencies to get the server running quickly
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Healthcare AI Agent API",
    description="Intelligent Healthcare Assistant powered by AWS AI services",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple models
class HealthQuery(BaseModel):
    query: str
    patient_id: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "Healthcare AI Agent API",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "api": "operational",
            "bedrock": "mock_mode" if os.getenv("USE_MOCK_SERVICES", "true").lower() == "true" else "operational",
            "sagemaker": "mock_mode" if os.getenv("USE_MOCK_SERVICES", "true").lower() == "true" else "operational",
            "dynamodb": "mock_mode" if os.getenv("USE_MOCK_SERVICES", "true").lower() == "true" else "operational"
        }
    }

# Authentication endpoint
@app.post("/auth/login")
async def login(credentials: LoginRequest):
    """Simple authentication for demo purposes"""
    try:
        if not credentials.email or "@" not in credentials.email:
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        if not credentials.password or len(credentials.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Mock authentication - in production, validate against real user database
        token = f"mock_jwt_token_for_{credentials.email}_{datetime.utcnow().timestamp()}"
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user_id": f"user_{hash(credentials.email) % 10000}",
            "message": "Login successful (demo mode)"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")

# Simple health consultation endpoint
@app.post("/consultation/chat")
async def medical_consultation(query: HealthQuery):
    """Simple medical consultation endpoint"""
    try:
        if not query.query or len(query.query.strip()) < 3:
            raise HTTPException(status_code=400, detail="Query too short")
        
        # Mock AI response
        mock_response = {
            "response": f"Thank you for your question: '{query.query}'. This is a mock response from the Healthcare AI Agent. "
                       f"In a full implementation, this would be processed by Amazon Bedrock Claude 3 Sonnet for "
                       f"intelligent medical consultation and SageMaker AI for symptom analysis.",
            "confidence": 0.85,
            "follow_up_questions": [
                "How long have you been experiencing these symptoms?",
                "Have you tried any treatments or medications?",
                "Do you have any relevant medical history?"
            ],
            "recommendations": [
                "Consider consulting with a healthcare provider for proper evaluation",
                "Monitor your symptoms and keep a daily log",
                "Stay hydrated and get adequate rest"
            ],
            "requires_human_review": False,
            "session_id": f"session_{datetime.utcnow().timestamp()}",
            "note": "This is a demo response. Real implementation would use AWS Bedrock and SageMaker AI."
        }
        
        logger.info(f"Processed consultation query: {query.query[:50]}")
        return mock_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Consultation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Consultation failed")

# Simple symptom analysis endpoint
@app.post("/consultation/symptom-analysis")
async def analyze_symptoms(query: HealthQuery):
    """Simple symptom analysis endpoint"""
    try:
        if not query.query:
            raise HTTPException(status_code=400, detail="Symptoms description required")
        
        # Mock symptom analysis
        mock_analysis = {
            "risk_level": "low" if "mild" in query.query.lower() else "moderate",
            "possible_conditions": [
                "Common cold",
                "Viral infection",
                "Stress-related symptoms"
            ],
            "urgency": "routine",
            "recommendations": [
                "Rest and monitor symptoms",
                "Stay hydrated",
                "Consider over-the-counter remedies if appropriate"
            ],
            "next_steps": [
                "Monitor symptoms for 24-48 hours",
                "Consult healthcare provider if symptoms worsen",
                "Seek immediate care if experiencing severe symptoms"
            ],
            "should_see_doctor": "routine_checkup",
            "emergency_indicators": [],
            "note": "This is a demo analysis. Real implementation would use SageMaker AI for advanced symptom analysis."
        }
        
        logger.info(f"Processed symptom analysis: {query.query[:50]}")
        return mock_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Symptom analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Symptom analysis failed")

# API information endpoint
@app.get("/api/info")
async def api_info():
    """Get API information and available endpoints"""
    return {
        "title": "Healthcare AI Agent API",
        "version": "1.0.0",
        "description": "Intelligent Healthcare Assistant powered by AWS AI services",
        "endpoints": {
            "GET /": "API root information",
            "GET /health": "Health check",
            "GET /api/info": "API information",
            "POST /auth/login": "User authentication",
            "POST /consultation/chat": "Medical consultation chat",
            "POST /consultation/symptom-analysis": "Symptom analysis"
        },
        "aws_services": [
            "Amazon Bedrock (Claude 3 Sonnet)",
            "Amazon SageMaker AI", 
            "Amazon DynamoDB",
            "Amazon S3",
            "Amazon Cognito",
            "Amazon API Gateway",
            "AWS Lambda",
            "Amazon EventBridge",
            "Amazon Step Functions",
            "Amazon CloudWatch",
            "Amazon Textract",
            "Amazon Comprehend Medical",
            "Amazon CloudFront",
            "AWS IAM",
            "AWS KMS",
            "Amazon VPC",
            "AWS Systems Manager"
        ],
        "features": [
            "AI-powered medical consultations",
            "Symptom analysis and risk assessment", 
            "Multi-agent orchestration",
            "Patient management",
            "Appointment scheduling",
            "Health insights and recommendations",
            "Medical document processing",
            "Secure authentication and data protection"
        ],
        "note": "This is the simplified demo version. Full AWS integration available in production mode."
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting Healthcare AI Agent API on {host}:{port}")
    logger.info("Mode: Demo/Development (using mock services)")
    
    uvicorn.run(
        "simple_app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )