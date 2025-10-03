from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from enum import Enum

class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Demographics(BaseModel):
    age: int = Field(..., ge=0, le=150, description="Patient age")
    gender: GenderEnum = Field(..., description="Patient gender")
    height_cm: Optional[float] = Field(None, ge=50, le=300, description="Height in centimeters")
    weight_kg: Optional[float] = Field(None, ge=10, le=500, description="Weight in kilograms")
    blood_type: Optional[str] = Field(None, description="Blood type (A+, B-, etc.)")
    
    @property
    def bmi(self) -> Optional[float]:
        if self.height_cm and self.weight_kg:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 1)
        return None

class EmergencyContact(BaseModel):
    name: str = Field(..., description="Emergency contact name")
    relationship: str = Field(..., description="Relationship to patient")
    phone: str = Field(..., description="Emergency contact phone number")
    email: Optional[str] = Field(None, description="Emergency contact email")

class MedicalHistory(BaseModel):
    condition: str = Field(..., description="Medical condition")
    diagnosed_date: Optional[date] = Field(None, description="Date of diagnosis")
    status: str = Field(default="active", description="Current status: active, resolved, managed")
    notes: Optional[str] = Field(None, description="Additional notes")

class Medication(BaseModel):
    name: str = Field(..., description="Medication name")
    dosage: str = Field(..., description="Dosage information")
    frequency: str = Field(..., description="How often taken")
    start_date: Optional[date] = Field(None, description="When medication was started")
    prescribing_doctor: Optional[str] = Field(None, description="Prescribing physician")
    notes: Optional[str] = Field(None, description="Additional notes")

class Allergy(BaseModel):
    allergen: str = Field(..., description="Allergen name")
    reaction: str = Field(..., description="Type of allergic reaction")
    severity: str = Field(..., description="Severity: mild, moderate, severe")
    notes: Optional[str] = Field(None, description="Additional notes")

class LifestyleFactors(BaseModel):
    smoking_status: str = Field(default="never", description="never, former, current")
    alcohol_consumption: str = Field(default="none", description="none, occasional, moderate, heavy")
    exercise_frequency: int = Field(default=0, ge=0, le=14, description="Exercise sessions per week")
    diet_type: Optional[str] = Field(None, description="Diet preferences or restrictions")
    sleep_hours: Optional[float] = Field(None, ge=0, le=24, description="Average sleep hours per night")
    stress_level: Optional[int] = Field(None, ge=1, le=10, description="Self-reported stress level 1-10")

class InsuranceInfo(BaseModel):
    provider: str = Field(..., description="Insurance provider name")
    policy_number: str = Field(..., description="Policy number")
    group_number: Optional[str] = Field(None, description="Group number")
    effective_date: Optional[date] = Field(None, description="Policy effective date")

class PatientProfile(BaseModel):
    user_id: Optional[str] = Field(None, description="System user ID")
    demographics: Demographics = Field(..., description="Patient demographic information")
    emergency_contact: Optional[EmergencyContact] = Field(None, description="Emergency contact")
    medical_history: List[MedicalHistory] = Field(default_factory=list, description="Medical history")
    medications: List[Medication] = Field(default_factory=list, description="Current medications")
    allergies: List[Allergy] = Field(default_factory=list, description="Known allergies")
    lifestyle: Optional[LifestyleFactors] = Field(None, description="Lifestyle factors")
    insurance: Optional[InsuranceInfo] = Field(None, description="Insurance information")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class ChatMessage(BaseModel):
    session_id: str = Field(..., description="Chat session ID")
    content: str = Field(..., min_length=1, max_length=2000, description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    message_type: str = Field(default="user", description="user or assistant")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Symptom(BaseModel):
    name: str = Field(..., description="Symptom name")
    severity: int = Field(..., ge=1, le=10, description="Severity rating 1-10")
    duration: str = Field(..., description="How long symptom has been present")
    description: Optional[str] = Field(None, description="Additional symptom description")
    associated_factors: List[str] = Field(default_factory=list, description="Factors that worsen/improve symptom")

class SymptomAnalysis(BaseModel):
    symptoms: List[Symptom] = Field(..., description="List of symptoms")
    duration: str = Field(..., description="Overall duration of symptoms")
    severity: int = Field(..., ge=1, le=10, description="Overall severity rating")
    additional_info: Optional[str] = Field(None, description="Additional information")
    
    @validator('symptoms')
    def symptoms_not_empty(cls, v):
        if not v:
            raise ValueError('At least one symptom must be provided')
        return v

class Provider(BaseModel):
    name: str = Field(..., description="Healthcare provider name")
    specialty: str = Field(..., description="Medical specialty")
    location: str = Field(..., description="Provider location")
    phone: str = Field(..., description="Provider phone number")
    availability: Optional[Dict[str, Any]] = Field(None, description="Available time slots")

class AppointmentRequest(BaseModel):
    patient_id: Optional[str] = Field(None, description="Patient ID")
    provider_id: Optional[str] = Field(None, description="Preferred provider ID")
    specialty: str = Field(..., description="Required medical specialty")
    preferred_date: Optional[date] = Field(None, description="Preferred appointment date")
    preferred_time: Optional[str] = Field(None, description="Preferred time slot")
    reason: str = Field(..., description="Reason for appointment")
    urgency: UrgencyLevel = Field(default=UrgencyLevel.MEDIUM, description="Appointment urgency")
    insurance_required: bool = Field(default=True, description="Whether insurance coverage is required")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }

class Appointment(BaseModel):
    appointment_id: str = Field(..., description="Unique appointment ID")
    patient_id: str = Field(..., description="Patient ID")
    provider: Provider = Field(..., description="Healthcare provider")
    scheduled_time: datetime = Field(..., description="Scheduled appointment time")
    duration_minutes: int = Field(default=30, description="Appointment duration")
    reason: str = Field(..., description="Reason for appointment")
    status: str = Field(default="scheduled", description="Appointment status")
    confirmation_number: str = Field(..., description="Confirmation number")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HealthMetric(BaseModel):
    metric_name: str = Field(..., description="Name of health metric")
    value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Unit of measurement")
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[str] = Field(None, description="Source of measurement")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MedicalInsight(BaseModel):
    insight_type: str = Field(..., description="Type of insight")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed description")
    recommendations: List[str] = Field(default_factory=list, description="Action recommendations")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Associated risk level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MedicationInteraction(BaseModel):
    medication1: str = Field(..., description="First medication")
    medication2: str = Field(..., description="Second medication")
    interaction_type: str = Field(..., description="Type of interaction")
    severity: str = Field(..., description="Interaction severity")
    description: str = Field(..., description="Interaction description")
    recommendation: str = Field(..., description="Clinical recommendation")

class MedicationAnalysis(BaseModel):
    interactions: List[MedicationInteraction] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    safe_to_take: bool = Field(default=True)

class VitalSigns(BaseModel):
    heart_rate: Optional[int] = Field(None, ge=30, le=200, description="Heart rate (bpm)")
    blood_pressure_systolic: Optional[int] = Field(None, ge=70, le=250, description="Systolic BP")
    blood_pressure_diastolic: Optional[int] = Field(None, ge=40, le=150, description="Diastolic BP")
    temperature_celsius: Optional[float] = Field(None, ge=30.0, le=45.0, description="Body temperature")
    respiratory_rate: Optional[int] = Field(None, ge=8, le=60, description="Respiratory rate")
    oxygen_saturation: Optional[int] = Field(None, ge=70, le=100, description="Oxygen saturation %")
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MedicalDocument(BaseModel):
    document_id: str = Field(..., description="Document ID")
    document_type: str = Field(..., description="Type of medical document")
    file_name: str = Field(..., description="Original file name")
    content_text: Optional[str] = Field(None, description="Extracted text content")
    medical_entities: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted medical entities")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = Field(None, description="When document was processed")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HealthTrend(BaseModel):
    metric_name: str = Field(..., description="Health metric name")
    trend_direction: str = Field(..., description="improving, declining, stable")
    change_percentage: float = Field(..., description="Percentage change")
    time_period: str = Field(..., description="Time period for trend")
    significance: str = Field(..., description="clinical significance")
    recommendations: List[str] = Field(default_factory=list)

class RiskFactor(BaseModel):
    factor_name: str = Field(..., description="Risk factor name")
    risk_level: RiskLevel = Field(..., description="Risk level")
    impact_score: float = Field(..., ge=0.0, le=1.0, description="Impact score")
    modifiable: bool = Field(..., description="Whether risk factor is modifiable")
    recommendations: List[str] = Field(default_factory=list)

class HealthAssessment(BaseModel):
    assessment_id: str = Field(..., description="Assessment ID")
    patient_id: str = Field(..., description="Patient ID")
    overall_health_score: float = Field(..., ge=0.0, le=100.0, description="Overall health score")
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    health_trends: List[HealthTrend] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    next_assessment_date: Optional[date] = Field(None, description="Next assessment date")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class EmergencyAlert(BaseModel):
    alert_id: str = Field(..., description="Alert ID")
    patient_id: str = Field(..., description="Patient ID")
    alert_type: str = Field(..., description="Type of emergency alert")
    severity: RiskLevel = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    triggered_by: str = Field(..., description="What triggered the alert")
    requires_immediate_action: bool = Field(..., description="Whether immediate action is required")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = Field(None, description="When alert was acknowledged")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Response models for API endpoints
class ConsultationResponse(BaseModel):
    response_text: str
    confidence: float
    recommendations: List[str]
    follow_up_questions: List[str]
    requires_human_review: bool
    risk_assessment: str
    session_id: str

class SymptomAnalysisResponse(BaseModel):
    risk_level: str
    possible_conditions: List[Dict[str, float]]
    urgency: str
    recommendations: List[str]
    next_steps: List[str]
    should_see_doctor: bool
    emergency_indicators: List[str]

class AppointmentResponse(BaseModel):
    appointment_id: str
    scheduled_time: datetime
    provider: Provider
    confirmation_number: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HealthInsightsResponse(BaseModel):
    health_score: float
    risk_factors: List[RiskFactor]
    recommendations: List[str]
    preventive_measures: List[str]
    lifestyle_suggestions: List[str]
    next_checkup_date: Optional[date]
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }

class DocumentProcessingResponse(BaseModel):
    document_id: str
    extracted_entities: List[Dict[str, Any]]
    medical_insights: List[str]
    processed_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }