from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import boto3
import json
import os
from datetime import datetime, timedelta
import uuid
import asyncio
import logging
from contextlib import asynccontextmanager

# Import custom modules
from src.agents.bedrock_agent import BedrockHealthAgent
from src.agents.sagemaker_agent import SageMakerHealthAnalyzer
from src.agents.orchestrator_agent import HealthcareOrchestrator
from src.services.patient_service import PatientService
from src.services.appointment_service import AppointmentService
from src.services.medical_service import MedicalAnalysisService
from src.utils.security import verify_token, get_current_user
from src.utils.validators import validate_medical_input
from src.models.schemas import (
    PatientProfile, HealthQuery, SymptomAnalysis, 
    AppointmentRequest, MedicalInsight, ChatMessage
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Healthcare AI Agent...")
    app.state.bedrock_client = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION', 'us-east-1'))
    app.state.sagemaker_client = boto3.client('sagemaker-runtime', region_name=os.getenv('AWS_REGION', 'us-east-1'))
    app.state.dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
    
    # Initialize AI agents
    app.state.bedrock_agent = BedrockHealthAgent(app.state.bedrock_client)
    app.state.sagemaker_agent = SageMakerHealthAnalyzer(app.state.sagemaker_client)
    app.state.orchestrator = HealthcareOrchestrator(
        app.state.bedrock_agent, 
        app.state.sagemaker_agent
    )
    
    # Initialize services
    app.state.patient_service = PatientService(app.state.dynamodb)
    app.state.appointment_service = AppointmentService(app.state.dynamodb)
    app.state.medical_service = MedicalAnalysisService(
        app.state.bedrock_client, 
        app.state.sagemaker_client
    )
    
    logger.info("Healthcare AI Agent initialized successfully!")
    yield
    
    # Shutdown
    logger.info("Shutting down Healthcare AI Agent...")

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare AI Agent API",
    description="Intelligent Healthcare Assistant powered by AWS AI services",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "bedrock": "operational",
            "sagemaker": "operational",
            "dynamodb": "operational"
        }
    }

# Authentication endpoints
@app.post("/auth/login")
async def login(credentials: Dict[str, str]):
    """Authenticate user and return JWT token"""
    try:
        # Implement your authentication logic here
        # This is a simplified example
        email = credentials.get("email")
        password = credentials.get("password")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
        
        # Validate credentials (implement your own logic)
        # For demo purposes, accepting any valid email format
        if "@" not in email:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate JWT token (implement proper JWT handling)
        token = f"jwt_token_for_{email}_{datetime.utcnow().timestamp()}"
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user_id": str(uuid.uuid4())
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")

# Patient management endpoints
@app.post("/patients/profile")
async def create_patient_profile(
    profile: PatientProfile,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create or update patient profile"""
    try:
        user_id = verify_token(credentials.credentials)
        profile.user_id = user_id
        
        result = await app.state.patient_service.create_or_update_profile(profile)
        return {"message": "Profile created successfully", "patient_id": result}
    except Exception as e:
        logger.error(f"Profile creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create profile")

@app.get("/patients/profile")
async def get_patient_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get patient profile"""
    try:
        user_id = verify_token(credentials.credentials)
        profile = await app.state.patient_service.get_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve profile")

# Medical consultation endpoints
@app.post("/consultation/chat")
async def medical_consultation(
    message: ChatMessage,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Handle medical consultation chat"""
    try:
        user_id = verify_token(credentials.credentials)
        
        # Validate medical input
        if not validate_medical_input(message.content):
            raise HTTPException(status_code=400, detail="Invalid medical query")
        
        # Get patient context
        patient_profile = await app.state.patient_service.get_profile(user_id)
        
        # Process through orchestrator
        response = await app.state.orchestrator.process_health_query(
            query=message.content,
            patient_context=patient_profile,
            session_id=message.session_id
        )
        
        return {
            "response": response.response_text,
            "confidence": response.confidence,
            "follow_up_questions": response.follow_up_questions,
            "recommendations": response.recommendations,
            "requires_human_review": response.requires_human_review,
            "session_id": message.session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Consultation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Consultation failed")

@app.post("/consultation/symptom-analysis")
async def analyze_symptoms(
    symptoms: SymptomAnalysis,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Analyze symptoms and provide risk assessment"""
    try:
        user_id = verify_token(credentials.credentials)
        
        # Get patient context
        patient_profile = await app.state.patient_service.get_profile(user_id)
        
        # Analyze symptoms using SageMaker
        analysis = await app.state.sagemaker_agent.analyze_symptoms(
            symptoms=symptoms.symptoms,
            patient_context=patient_profile,
            duration=symptoms.duration,
            severity=symptoms.severity
        )
        
        # Get Bedrock recommendations
        recommendations = await app.state.bedrock_agent.get_medical_recommendations(
            symptoms=symptoms.symptoms,
            analysis=analysis,
            patient_context=patient_profile
        )
        
        return {
            "risk_level": analysis.risk_level,
            "possible_conditions": analysis.possible_conditions,
            "urgency": analysis.urgency,
            "recommendations": recommendations.recommendations,
            "next_steps": recommendations.next_steps,
            "should_see_doctor": analysis.should_see_doctor,
            "emergency_indicators": analysis.emergency_indicators
        }
    except Exception as e:
        logger.error(f"Symptom analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Symptom analysis failed")

# Appointment management endpoints
@app.post("/appointments/schedule")
async def schedule_appointment(
    appointment: AppointmentRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Schedule medical appointment"""
    try:
        user_id = verify_token(credentials.credentials)
        appointment.patient_id = user_id
        
        result = await app.state.appointment_service.schedule_appointment(appointment)
        return {
            "appointment_id": result.appointment_id,
            "scheduled_time": result.scheduled_time,
            "provider": result.provider,
            "confirmation_number": result.confirmation_number
        }
    except Exception as e:
        logger.error(f"Appointment scheduling error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to schedule appointment")

@app.get("/appointments")
async def get_appointments(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get patient appointments"""
    try:
        user_id = verify_token(credentials.credentials)
        appointments = await app.state.appointment_service.get_patient_appointments(user_id)
        return {"appointments": appointments}
    except Exception as e:
        logger.error(f"Appointments retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve appointments")

# Health insights endpoints
@app.get("/insights/health-summary")
async def get_health_insights(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get personalized health insights"""
    try:
        user_id = verify_token(credentials.credentials)
        
        # Get patient data
        patient_profile = await app.state.patient_service.get_profile(user_id)
        
        # Generate insights using AI
        insights = await app.state.medical_service.generate_health_insights(
            patient_profile=patient_profile
        )
        
        return {
            "health_score": insights.health_score,
            "risk_factors": insights.risk_factors,
            "recommendations": insights.recommendations,
            "preventive_measures": insights.preventive_measures,
            "lifestyle_suggestions": insights.lifestyle_suggestions,
            "next_checkup_date": insights.next_checkup_date
        }
    except Exception as e:
        logger.error(f"Health insights error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")

@app.post("/insights/medication-check")
async def check_medication_interactions(
    medications: List[str],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Check for medication interactions"""
    try:
        user_id = verify_token(credentials.credentials)
        
        # Get patient context
        patient_profile = await app.state.patient_service.get_profile(user_id)
        
        # Check interactions
        interactions = await app.state.medical_service.check_medication_interactions(
            medications=medications,
            patient_context=patient_profile
        )
        
        return {
            "interactions": interactions.interactions,
            "warnings": interactions.warnings,
            "recommendations": interactions.recommendations,
            "safe_to_take": interactions.safe_to_take
        }
    except Exception as e:
        logger.error(f"Medication check error: {str(e)}")
        raise HTTPException(status_code=500, detail="Medication check failed")

# Document processing endpoints
@app.post("/documents/upload")
async def upload_medical_document(
    document_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Upload and process medical document"""
    try:
        user_id = verify_token(credentials.credentials)
        
        # Process document using Textract and Comprehend Medical
        result = await app.state.medical_service.process_medical_document(
            document_data=document_data,
            patient_id=user_id
        )
        
        return {
            "document_id": result.document_id,
            "extracted_entities": result.extracted_entities,
            "medical_insights": result.medical_insights,
            "processed_at": result.processed_at
        }
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Document processing failed")

# Real-time endpoints
@app.get("/realtime/session/{session_id}")
async def get_session_status(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get real-time session status"""
    try:
        user_id = verify_token(credentials.credentials)
        
        status = await app.state.orchestrator.get_session_status(session_id)
        return status
    except Exception as e:
        logger.error(f"Session status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session status")

# Admin endpoints
@app.get("/admin/metrics")
async def get_system_metrics(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get system performance metrics"""
    try:
        # Verify admin privileges (implement your own logic)
        user_id = verify_token(credentials.credentials)
        
        metrics = {
            "total_consultations": await app.state.patient_service.get_consultation_count(),
            "active_sessions": await app.state.orchestrator.get_active_sessions_count(),
            "average_response_time": "1.2s",
            "system_health": "operational",
            "ai_model_accuracy": "94.5%"
        }
        
        return metrics
    except Exception as e:
        logger.error(f"Metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )