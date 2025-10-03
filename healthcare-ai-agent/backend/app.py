"""
Healthcare AI Agent - Clean FastAPI Application
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import uvicorn
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare AI Agent",
    description="AI-powered healthcare assistant",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    message: str

class PatientQuery(BaseModel):
    question: str
    patient_id: Optional[str] = None

class AIResponse(BaseModel):
    response: str
    confidence: float
    timestamp: datetime

# Health check endpoint
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with health check"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        message="Healthcare AI Agent is running"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        message="All systems operational"
    )

# AI Query endpoint
@app.post("/api/v1/query", response_model=AIResponse)
async def query_ai(query: PatientQuery):
    """Process AI query from healthcare provider"""
    try:
        # Mock AI response for now
        response_text = f"Based on your question: '{query.question}', here's a professional healthcare AI response. This is a mock response for development."
        
        return AIResponse(
            response=response_text,
            confidence=0.85,
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

# Patient endpoints
@app.get("/api/v1/patients")
async def list_patients():
    """List all patients (mock data)"""
    return {
        "patients": [
            {"id": "1", "name": "John Doe", "age": 45},
            {"id": "2", "name": "Jane Smith", "age": 32}
        ]
    }

@app.get("/api/v1/patients/{patient_id}")
async def get_patient(patient_id: str):
    """Get specific patient information"""
    # Mock patient data
    return {
        "id": patient_id,
        "name": "Patient Name",
        "age": 35,
        "last_visit": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )