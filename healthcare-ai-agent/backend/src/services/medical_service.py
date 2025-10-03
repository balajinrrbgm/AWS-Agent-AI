import boto3
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

class MedicalAnalysisService:
    """
    Service for medical document processing and analysis
    """
    
    def __init__(self, bedrock_client, sagemaker_client):
        self.bedrock_client = bedrock_client
        self.sagemaker_client = sagemaker_client
        
        # Initialize Comprehend Medical and Textract clients
        try:
            self.comprehend_medical = boto3.client('comprehendmedical')
            self.textract = boto3.client('textract')
        except Exception as e:
            logger.warning(f"AWS medical services not available: {e}. Using mock mode.")
            self.comprehend_medical = None
            self.textract = None

    async def generate_health_insights(self, patient_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized health insights for a patient
        """
        try:
            demographics = patient_profile.get('demographics', {})
            age = demographics.get('age', 0)
            lifestyle = patient_profile.get('lifestyle', {})
            medical_history = patient_profile.get('medical_history', [])
            
            # Calculate health score
            health_score = self._calculate_health_score(patient_profile)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(patient_profile)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(patient_profile, risk_factors)
            
            # Preventive measures
            preventive_measures = self._get_preventive_measures(age, medical_history)
            
            # Lifestyle suggestions
            lifestyle_suggestions = self._get_lifestyle_suggestions(lifestyle, risk_factors)
            
            # Next checkup date
            next_checkup_date = self._calculate_next_checkup(age, medical_history)
            
            insights = {
                "health_score": health_score,
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "preventive_measures": preventive_measures,
                "lifestyle_suggestions": lifestyle_suggestions,
                "next_checkup_date": next_checkup_date.isoformat() if next_checkup_date else None
            }
            
            logger.info(f"Health insights generated for patient")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating health insights: {str(e)}")
            return {
                "health_score": 75.0,
                "risk_factors": [],
                "recommendations": ["Schedule regular checkups"],
                "preventive_measures": ["Maintain healthy lifestyle"],
                "lifestyle_suggestions": ["Regular exercise", "Balanced diet"],
                "next_checkup_date": (datetime.now() + timedelta(days=365)).isoformat()
            }

    async def check_medication_interactions(
        self, 
        medications: List[str], 
        patient_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check for medication interactions
        """
        try:
            interactions = []
            warnings = []
            recommendations = []
            safe_to_take = True
            
            # Mock medication interaction database
            known_interactions = {
                ("lisinopril", "ibuprofen"): {
                    "severity": "moderate",
                    "description": "NSAIDs may reduce the antihypertensive effect of ACE inhibitors",
                    "recommendation": "Monitor blood pressure closely, consider alternative pain relief"
                },
                ("warfarin", "aspirin"): {
                    "severity": "major",
                    "description": "Increased risk of bleeding when used together",
                    "recommendation": "Use only under medical supervision, monitor INR levels"
                },
                ("metformin", "contrast dye"): {
                    "severity": "major",
                    "description": "Risk of lactic acidosis, especially with kidney problems",
                    "recommendation": "Discontinue metformin before contrast procedures"
                }
            }
            
            # Check all medication pairs
            for i, med1 in enumerate(medications):
                for med2 in medications[i+1:]:
                    interaction_key = tuple(sorted([med1.lower(), med2.lower()]))
                    
                    if interaction_key in known_interactions:
                        interaction_data = known_interactions[interaction_key]
                        interactions.append({
                            "medication1": med1,
                            "medication2": med2,
                            "severity": interaction_data["severity"],
                            "description": interaction_data["description"],
                            "recommendation": interaction_data["recommendation"]
                        })
                        
                        if interaction_data["severity"] in ["major", "severe"]:
                            safe_to_take = False
                            warnings.append(f"Major interaction between {med1} and {med2}")
                        else:
                            warnings.append(f"Moderate interaction between {med1} and {med2}")
            
            # General recommendations
            recommendations.extend([
                "Review all medications with your pharmacist regularly",
                "Inform all healthcare providers about your complete medication list",
                "Report any unusual symptoms or side effects immediately"
            ])
            
            if interactions:
                recommendations.append("Consult with your healthcare provider about these interactions")
            
            result = {
                "interactions": interactions,
                "warnings": warnings,
                "recommendations": recommendations,
                "safe_to_take": safe_to_take
            }
            
            logger.info(f"Checked interactions for {len(medications)} medications")
            return result
            
        except Exception as e:
            logger.error(f"Error checking medication interactions: {str(e)}")
            return {
                "interactions": [],
                "warnings": ["Unable to check interactions at this time"],
                "recommendations": ["Consult with pharmacist or healthcare provider"],
                "safe_to_take": True
            }

    async def process_medical_document(
        self, 
        document_data: Dict[str, Any], 
        patient_id: str
    ) -> Dict[str, Any]:
        """
        Process medical document using Textract and Comprehend Medical
        """
        try:
            document_id = str(uuid.uuid4())
            
            # Mock document processing for development
            if not self.textract or not self.comprehend_medical:
                # Return mock results
                mock_result = {
                    "document_id": document_id,
                    "extracted_entities": [
                        {
                            "text": "Blood Pressure",
                            "category": "TEST_NAME",
                            "confidence": 0.95
                        },
                        {
                            "text": "120/80 mmHg",
                            "category": "TEST_VALUE",
                            "confidence": 0.98
                        },
                        {
                            "text": "Cholesterol",
                            "category": "TEST_NAME",
                            "confidence": 0.93
                        },
                        {
                            "text": "Total: 180 mg/dL",
                            "category": "TEST_VALUE",
                            "confidence": 0.97
                        }
                    ],
                    "medical_insights": [
                        "Blood pressure is within normal range",
                        "Cholesterol levels are optimal",
                        "Continue current health maintenance routine"
                    ],
                    "processed_at": datetime.utcnow()
                }
                
                logger.info(f"Document processed (mock): {document_id}")
                return mock_result
            
            # Real implementation would use Textract and Comprehend Medical
            # This is a placeholder for the actual implementation
            
        except Exception as e:
            logger.error(f"Error processing medical document: {str(e)}")
            return {
                "document_id": str(uuid.uuid4()),
                "extracted_entities": [],
                "medical_insights": ["Unable to process document at this time"],
                "processed_at": datetime.utcnow()
            }

    def _calculate_health_score(self, patient_profile: Dict[str, Any]) -> float:
        """
        Calculate overall health score for a patient
        """
        base_score = 85.0
        
        demographics = patient_profile.get('demographics', {})
        age = demographics.get('age', 0)
        lifestyle = patient_profile.get('lifestyle', {})
        medical_history = patient_profile.get('medical_history', [])
        
        # Age factor
        if age > 65:
            base_score -= 10
        elif age > 50:
            base_score -= 5
        
        # Medical history factor
        chronic_conditions = len([h for h in medical_history if h.get('status') == 'active'])
        base_score -= chronic_conditions * 5
        
        # Lifestyle factors
        if lifestyle.get('smoking_status') == 'current':
            base_score -= 15
        elif lifestyle.get('smoking_status') == 'former':
            base_score -= 5
        
        exercise_freq = lifestyle.get('exercise_frequency', 0)
        if exercise_freq >= 5:
            base_score += 5
        elif exercise_freq < 2:
            base_score -= 5
        
        alcohol = lifestyle.get('alcohol_consumption', 'none')
        if alcohol == 'heavy':
            base_score -= 10
        elif alcohol == 'moderate':
            base_score -= 2
        
        return max(min(base_score, 100.0), 10.0)

    def _identify_risk_factors(self, patient_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify health risk factors for a patient
        """
        risk_factors = []
        
        demographics = patient_profile.get('demographics', {})
        age = demographics.get('age', 0)
        lifestyle = patient_profile.get('lifestyle', {})
        medical_history = patient_profile.get('medical_history', [])
        
        # Age-related risks
        if age > 65:
            risk_factors.append({
                "factor": "Advanced Age",
                "risk_level": "medium",
                "description": "Increased risk for various health conditions",
                "modifiable": False
            })
        
        # Lifestyle risks
        if lifestyle.get('smoking_status') == 'current':
            risk_factors.append({
                "factor": "Current Smoking",
                "risk_level": "high",
                "description": "Significantly increased risk for cardiovascular and pulmonary diseases",
                "modifiable": True
            })
        
        exercise_freq = lifestyle.get('exercise_frequency', 0)
        if exercise_freq < 2:
            risk_factors.append({
                "factor": "Sedentary Lifestyle",
                "risk_level": "medium",
                "description": "Increased risk for cardiovascular disease and metabolic disorders",
                "modifiable": True
            })
        
        # Medical history risks
        diabetes_history = any('diabetes' in str(h).lower() for h in medical_history)
        if diabetes_history:
            risk_factors.append({
                "factor": "Diabetes History",
                "risk_level": "high",
                "description": "Increased risk for cardiovascular complications",
                "modifiable": True
            })
        
        return risk_factors

    def _generate_recommendations(
        self, 
        patient_profile: Dict[str, Any], 
        risk_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate personalized health recommendations
        """
        recommendations = []
        
        # General recommendations
        recommendations.extend([
            "Schedule regular preventive care visits",
            "Maintain up-to-date vaccinations",
            "Monitor key health metrics regularly"
        ])
        
        # Risk-based recommendations
        for risk_factor in risk_factors:
            if risk_factor["factor"] == "Current Smoking":
                recommendations.append("Consider smoking cessation programs and resources")
            elif risk_factor["factor"] == "Sedentary Lifestyle":
                recommendations.append("Increase physical activity to at least 150 minutes per week")
            elif risk_factor["factor"] == "Diabetes History":
                recommendations.append("Monitor blood glucose levels and maintain diabetic care plan")
        
        return recommendations

    def _get_preventive_measures(self, age: int, medical_history: List) -> List[str]:
        """
        Get age-appropriate preventive care measures
        """
        measures = []
        
        # General measures
        measures.extend([
            "Annual physical examination",
            "Blood pressure monitoring",
            "Cholesterol screening"
        ])
        
        # Age-specific measures
        if age >= 50:
            measures.extend([
                "Colorectal cancer screening",
                "Annual eye examination"
            ])
        
        if age >= 65:
            measures.extend([
                "Bone density screening",
                "Fall prevention assessment",
                "Cognitive assessment"
            ])
        
        # Gender and risk-specific measures would be added here
        
        return measures

    def _get_lifestyle_suggestions(
        self, 
        lifestyle: Dict[str, Any], 
        risk_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Get personalized lifestyle suggestions
        """
        suggestions = []
        
        exercise_freq = lifestyle.get('exercise_frequency', 0)
        if exercise_freq < 3:
            suggestions.append("Increase physical activity - aim for 30 minutes daily")
        
        if lifestyle.get('smoking_status') == 'current':
            suggestions.append("Quit smoking - consider nicotine replacement therapy")
        
        suggestions.extend([
            "Maintain a balanced, nutrient-rich diet",
            "Ensure adequate sleep (7-9 hours nightly)",
            "Practice stress management techniques",
            "Stay hydrated - drink plenty of water",
            "Limit alcohol consumption"
        ])
        
        return suggestions

    def _calculate_next_checkup(self, age: int, medical_history: List) -> datetime:
        """
        Calculate recommended date for next checkup
        """
        # Base checkup frequency
        if age >= 65:
            months_until_checkup = 6  # Every 6 months
        elif age >= 40:
            months_until_checkup = 12  # Annually
        else:
            months_until_checkup = 24  # Every 2 years
        
        # Adjust for chronic conditions
        chronic_conditions = len([h for h in medical_history if h.get('status') == 'active'])
        if chronic_conditions > 0:
            months_until_checkup = min(months_until_checkup, 6)
        
        return datetime.now() + timedelta(days=months_until_checkup * 30)