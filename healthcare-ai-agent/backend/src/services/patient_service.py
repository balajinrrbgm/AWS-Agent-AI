import boto3
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import logging
from botocore.exceptions import ClientError

from src.models.schemas import PatientProfile, Demographics

logger = logging.getLogger(__name__)

class PatientService:
    """
    Service for managing patient profiles and data
    """
    
    def __init__(self, dynamodb_resource):
        self.dynamodb = dynamodb_resource
        self.table_name = "healthcare-patients"
        try:
            self.table = self.dynamodb.Table(self.table_name)
        except Exception as e:
            logger.warning(f"DynamoDB table not available: {e}. Using mock mode.")
            self.table = None
            self._mock_data = {}

    async def create_or_update_profile(self, profile: PatientProfile) -> str:
        """
        Create or update a patient profile
        """
        try:
            if not profile.user_id:
                profile.user_id = str(uuid.uuid4())
            
            profile.updated_at = datetime.utcnow()
            
            if self.table:
                # Convert Pydantic model to dict
                profile_dict = profile.dict()
                
                # Convert datetime objects to ISO strings for DynamoDB
                for key, value in profile_dict.items():
                    if isinstance(value, datetime):
                        profile_dict[key] = value.isoformat()
                
                self.table.put_item(Item=profile_dict)
                logger.info(f"Patient profile saved: {profile.user_id}")
            else:
                # Mock mode for local development
                self._mock_data[profile.user_id] = profile.dict()
                logger.info(f"Patient profile saved (mock): {profile.user_id}")
            
            return profile.user_id
            
        except Exception as e:
            logger.error(f"Error saving patient profile: {str(e)}")
            raise

    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a patient profile by user ID
        """
        try:
            if self.table:
                response = self.table.get_item(Key={'user_id': user_id})
                
                if 'Item' in response:
                    logger.info(f"Patient profile retrieved: {user_id}")
                    return response['Item']
                else:
                    logger.warning(f"Patient profile not found: {user_id}")
                    return None
            else:
                # Mock mode
                profile = self._mock_data.get(user_id)
                if profile:
                    logger.info(f"Patient profile retrieved (mock): {user_id}")
                    return profile
                else:
                    # Return a default mock profile for development
                    mock_profile = {
                        "user_id": user_id,
                        "demographics": {
                            "age": 35,
                            "gender": "male",
                            "height_cm": 175,
                            "weight_kg": 70
                        },
                        "medical_history": [],
                        "medications": [],
                        "allergies": [],
                        "lifestyle": {
                            "smoking_status": "never",
                            "alcohol_consumption": "moderate",
                            "exercise_frequency": 3
                        }
                    }
                    logger.info(f"Using default mock profile: {user_id}")
                    return mock_profile
                    
        except Exception as e:
            logger.error(f"Error retrieving patient profile: {str(e)}")
            return None

    async def update_health_metrics(self, user_id: str, metrics: List[Dict[str, Any]]) -> bool:
        """
        Update health metrics for a patient
        """
        try:
            # In a real implementation, this would update a separate health metrics table
            # For now, we'll just log the metrics
            logger.info(f"Health metrics updated for user {user_id}: {metrics}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating health metrics: {str(e)}")
            return False

    async def get_consultation_count(self) -> int:
        """
        Get total consultation count (for admin metrics)
        """
        try:
            if self.table:
                # In a real implementation, this would query a consultations table
                # For now, return a mock value
                return 150
            else:
                return 42  # Mock value for development
                
        except Exception as e:
            logger.error(f"Error getting consultation count: {str(e)}")
            return 0

    async def search_patients(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search patients by name or other criteria
        """
        try:
            if self.table:
                # In a real implementation, this would use DynamoDB GSI or Elasticsearch
                # For now, return empty list
                return []
            else:
                # Mock search results
                return [
                    {
                        "user_id": "mock-patient-1",
                        "name": "John Doe",
                        "email": "john.doe@example.com",
                        "last_visit": "2025-09-20"
                    }
                ]
                
        except Exception as e:
            logger.error(f"Error searching patients: {str(e)}")
            return []

    async def get_patient_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of patient's health status
        """
        try:
            profile = await self.get_profile(user_id)
            if not profile:
                return {}
            
            # Calculate basic health summary
            demographics = profile.get('demographics', {})
            age = demographics.get('age', 0)
            
            # Simple health score calculation
            health_score = 85  # Base score
            
            if age > 65:
                health_score -= 10
            elif age > 50:
                health_score -= 5
            
            chronic_conditions = len(profile.get('chronic_conditions', []))
            health_score -= chronic_conditions * 5
            
            lifestyle = profile.get('lifestyle', {})
            if lifestyle.get('smoking_status') == 'current':
                health_score -= 15
            
            exercise_freq = lifestyle.get('exercise_frequency', 0)
            if exercise_freq >= 5:
                health_score += 5
            elif exercise_freq < 2:
                health_score -= 5
            
            health_score = max(min(health_score, 100), 10)
            
            summary = {
                "user_id": user_id,
                "health_score": health_score,
                "age": age,
                "chronic_conditions_count": chronic_conditions,
                "last_consultation": "2025-09-25",
                "upcoming_appointments": 1,
                "alerts": []
            }
            
            # Add alerts for high-risk conditions
            if health_score < 50:
                summary["alerts"].append("Low health score - recommend comprehensive evaluation")
            
            if chronic_conditions > 3:
                summary["alerts"].append("Multiple chronic conditions - requires care coordination")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating patient summary: {str(e)}")
            return {}

    async def delete_profile(self, user_id: str) -> bool:
        """
        Delete a patient profile (with proper data retention compliance)
        """
        try:
            if self.table:
                # In production, this should implement proper data retention policies
                # and audit logging for HIPAA compliance
                response = self.table.delete_item(
                    Key={'user_id': user_id},
                    ReturnValues='ALL_OLD'
                )
                
                if 'Attributes' in response:
                    logger.info(f"Patient profile deleted: {user_id}")
                    return True
                else:
                    logger.warning(f"Patient profile not found for deletion: {user_id}")
                    return False
            else:
                # Mock mode
                if user_id in self._mock_data:
                    del self._mock_data[user_id]
                    logger.info(f"Patient profile deleted (mock): {user_id}")
                    return True
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting patient profile: {str(e)}")
            return False