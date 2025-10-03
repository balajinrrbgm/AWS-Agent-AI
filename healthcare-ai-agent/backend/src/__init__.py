"""
Healthcare AI Agent Backend API

A comprehensive healthcare AI agent system using Amazon Bedrock, SageMaker AI,
and Bedrock AgentCore for intelligent medical consultations and health analysis.

Features:
- AI-powered medical consultations using Claude 3 Sonnet
- Symptom analysis and health risk assessment
- Multi-agent orchestration with Bedrock AgentCore
- Patient management and appointment scheduling
- Secure authentication and data protection
- Comprehensive health insights and recommendations

Author: AWS AI Agent Healthcare Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "AWS AI Agent Healthcare Team"
__description__ = "Healthcare AI Agent Backend API using Amazon Bedrock and SageMaker AI"

# Import main application components
try:
    from .config import settings
except ImportError:
    # Config import will be handled when needed
    settings = None

# Service layer imports
try:
    from .services.patient_service import PatientService
    from .services.appointment_service import AppointmentService
    from .services.medical_service import MedicalAnalysisService
except ImportError:
    # Services will be imported when needed
    pass

# Agent imports
try:
    from .agents.bedrock_agent import BedrockHealthAgent
    from .agents.sagemaker_agent import SageMakerHealthAnalyzer
    from .agents.orchestrator_agent import HealthcareOrchestrator
except ImportError as e:
    # Agents will be imported when needed
    pass

# Utility imports
try:
    from .utils.security import SecurityUtils
    from .utils.validators import DataValidator
except ImportError:
    # Utilities will be imported when needed
    pass

__all__ = [
    "settings"
]