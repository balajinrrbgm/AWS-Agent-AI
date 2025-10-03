from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime
import uuid
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class HealthQueryResponse:
    response_text: str
    confidence: float
    follow_up_questions: List[str]
    recommendations: List[str]
    requires_human_review: bool
    risk_assessment: str
    next_actions: List[str]

class HealthcareOrchestrator:
    """
    Orchestrator agent that coordinates between Bedrock and SageMaker agents
    Implements Bedrock AgentCore patterns for multi-agent healthcare workflows
    """
    
    def __init__(self, bedrock_agent, sagemaker_agent):
        self.bedrock_agent = bedrock_agent
        self.sagemaker_agent = sagemaker_agent
        
        # Session management
        self.active_sessions = {}
        
        # Workflow definitions
        self.workflows = {
            'symptom_analysis': self._symptom_analysis_workflow,
            'health_consultation': self._health_consultation_workflow,
            'risk_assessment': self._risk_assessment_workflow,
            'medication_review': self._medication_review_workflow,
            'preventive_care': self._preventive_care_workflow
        }
        
        # Decision trees for routing queries
        self.query_classifiers = {
            'symptoms': ['pain', 'ache', 'fever', 'cough', 'nausea', 'tired', 'dizzy'],
            'medications': ['drug', 'medicine', 'pill', 'prescription', 'medication', 'side effect'],
            'prevention': ['prevent', 'avoid', 'healthy', 'diet', 'exercise', 'lifestyle'],
            'emergency': ['chest pain', 'breathing', 'unconscious', 'bleeding', 'severe'],
            'mental_health': ['anxiety', 'depression', 'stress', 'mood', 'sleep', 'mental']
        }

    async def process_health_query(
        self,
        query: str,
        patient_context: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> HealthQueryResponse:
        """
        Main orchestration method for processing health queries
        """
        try:
            # Create or retrieve session
            if not session_id:
                session_id = str(uuid.uuid4())
            
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    'created_at': datetime.utcnow(),
                    'history': [],
                    'context': patient_context
                }
            
            session = self.active_sessions[session_id]
            
            # Classify the query to determine workflow
            workflow_type = await self._classify_query(query)
            
            # Execute appropriate workflow
            if workflow_type in self.workflows:
                response = await self.workflows[workflow_type](
                    query, patient_context, session
                )
            else:
                response = await self._default_consultation_workflow(
                    query, patient_context, session
                )
            
            # Update session history
            session['history'].append({
                'timestamp': datetime.utcnow(),
                'query': query,
                'response': response.response_text,
                'workflow': workflow_type
            })
            
            # Clean up old sessions (keep last 10)
            if len(session['history']) > 10:
                session['history'] = session['history'][-10:]
            
            logger.info(f"Query processed: workflow={workflow_type}, confidence={response.confidence}")
            return response
            
        except Exception as e:
            logger.error(f"Query processing error: {str(e)}")
            return HealthQueryResponse(
                response_text="I apologize, but I'm experiencing technical difficulties. Please consult with a healthcare professional for your medical concerns.",
                confidence=0.0,
                follow_up_questions=[],
                recommendations=["Consult with a healthcare provider"],
                requires_human_review=True,
                risk_assessment="unknown",
                next_actions=["Seek professional medical advice"]
            )

    async def _classify_query(self, query: str) -> str:
        """
        Classify the query to determine the appropriate workflow
        """
        query_lower = query.lower()
        
        # Check for emergency indicators first
        for keyword in self.query_classifiers['emergency']:
            if keyword in query_lower:
                return 'emergency_triage'
        
        # Check other categories
        for category, keywords in self.query_classifiers.items():
            if category == 'emergency':  # Already checked
                continue
                
            for keyword in keywords:
                if keyword in query_lower:
                    if category == 'symptoms':
                        return 'symptom_analysis'
                    elif category == 'medications':
                        return 'medication_review'
                    elif category == 'prevention':
                        return 'preventive_care'
                    elif category == 'mental_health':
                        return 'mental_health_consultation'
        
        # Default to general health consultation
        return 'health_consultation'

    async def _symptom_analysis_workflow(
        self,
        query: str,
        patient_context: Dict[str, Any],
        session: Dict[str, Any]
    ) -> HealthQueryResponse:
        """
        Workflow for symptom analysis combining ML and LLM insights
        """
        try:
            # Extract symptoms from query using Bedrock
            symptom_extraction_prompt = f"""
            Extract specific symptoms mentioned in this patient query: "{query}"
            
            Return symptoms as a structured list, including:
            - Primary symptoms
            - Duration if mentioned
            - Severity indicators
            - Associated factors
            
            Patient context: {patient_context.get('demographics', {})}
            """
            
            # Get Bedrock to extract structured symptom data
            bedrock_extraction = await self.bedrock_agent.process_medical_consultation(
                symptom_extraction_prompt, patient_context, session.get('history', [])
            )
            
            # Parse symptoms for SageMaker analysis
            symptoms = self._extract_symptoms_from_response(bedrock_extraction.response_text)
            
            # Run parallel analysis
            bedrock_task = self.bedrock_agent.analyze_symptoms_with_bedrock(
                symptoms, patient_context, "recent", 5  # Default values
            )
            
            sagemaker_task = self.sagemaker_agent.analyze_symptoms(
                symptoms, patient_context, "recent", 5
            )
            
            # Wait for both analyses
            bedrock_analysis, sagemaker_analysis = await asyncio.gather(
                bedrock_task, sagemaker_task, return_exceptions=True
            )
            
            # Combine insights
            combined_response = await self._combine_symptom_analyses(
                bedrock_analysis, sagemaker_analysis, query, patient_context
            )
            
            return combined_response
            
        except Exception as e:
            logger.error(f"Symptom analysis workflow error: {str(e)}")
            return await self._fallback_response(query, patient_context)

    async def _health_consultation_workflow(
        self,
        query: str,
        patient_context: Dict[str, Any],
        session: Dict[str, Any]
    ) -> HealthQueryResponse:
        """
        General health consultation workflow
        """
        try:
            # Get comprehensive medical consultation from Bedrock
            consultation_response = await self.bedrock_agent.process_medical_consultation(
                query, patient_context, session.get('history', [])
            )
            
            # Enhance with risk assessment if needed
            risk_assessment = "low"
            if consultation_response.requires_human_review:
                risk_assessment = consultation_response.risk_level
            
            # Generate contextual follow-up questions
            follow_up_questions = await self._generate_contextual_follow_ups(
                query, consultation_response.response_text, patient_context
            )
            
            return HealthQueryResponse(
                response_text=consultation_response.response_text,
                confidence=consultation_response.confidence,
                follow_up_questions=follow_up_questions,
                recommendations=consultation_response.recommendations,
                requires_human_review=consultation_response.requires_human_review,
                risk_assessment=risk_assessment,
                next_actions=self._generate_next_actions(consultation_response)
            )
            
        except Exception as e:
            logger.error(f"Health consultation workflow error: {str(e)}")
            return await self._fallback_response(query, patient_context)

    async def _risk_assessment_workflow(
        self,
        query: str,
        patient_context: Dict[str, Any],
        session: Dict[str, Any]
    ) -> HealthQueryResponse:
        """
        Comprehensive risk assessment workflow
        """
        try:
            # Run risk prediction using SageMaker
            risk_prediction = await self.sagemaker_agent.predict_health_risks(
                patient_context, session.get('history', [])
            )
            
            # Get Bedrock interpretation of risk factors
            risk_interpretation_prompt = f"""
            Interpret these health risk predictions for the patient:
            
            Risk Predictions: {risk_prediction.predictions}
            Risk Factors: {risk_prediction.risk_factors}
            Health Score: {risk_prediction.health_score}
            
            Patient Context: {patient_context}
            Patient Query: {query}
            
            Provide:
            1. Clear explanation of risk levels
            2. Actionable recommendations
            3. Timeline for interventions
            4. Monitoring suggestions
            """
            
            bedrock_interpretation = await self.bedrock_agent.process_medical_consultation(
                risk_interpretation_prompt, patient_context
            )
            
            # Combine insights
            combined_recommendations = list(set(
                risk_prediction.recommendations + bedrock_interpretation.recommendations
            ))
            
            return HealthQueryResponse(
                response_text=bedrock_interpretation.response_text,
                confidence=min(bedrock_interpretation.confidence, 0.9),
                follow_up_questions=bedrock_interpretation.follow_up_questions,
                recommendations=combined_recommendations,
                requires_human_review=risk_prediction.health_score < 60,
                risk_assessment=self._categorize_health_score(risk_prediction.health_score),
                next_actions=self._generate_risk_based_actions(risk_prediction)
            )
            
        except Exception as e:
            logger.error(f"Risk assessment workflow error: {str(e)}")
            return await self._fallback_response(query, patient_context)

    async def _medication_review_workflow(
        self,
        query: str,
        patient_context: Dict[str, Any],
        session: Dict[str, Any]
    ) -> HealthQueryResponse:
        """
        Medication review and interaction checking workflow
        """
        try:
            # Extract medications from query and patient context
            current_medications = patient_context.get('medications', [])
            
            # Use Bedrock to analyze medication-related query
            medication_analysis = await self.bedrock_agent.process_medical_consultation(
                f"Medication query: {query}\nCurrent medications: {current_medications}",
                patient_context, session.get('history', [])
            )
            
            # Add medication-specific recommendations
            medication_recommendations = [
                "Review medications with your pharmacist regularly",
                "Keep an updated medication list",
                "Report any side effects to your healthcare provider"
            ]
            
            all_recommendations = list(set(
                medication_analysis.recommendations + medication_recommendations
            ))
            
            return HealthQueryResponse(
                response_text=medication_analysis.response_text,
                confidence=medication_analysis.confidence,
                follow_up_questions=medication_analysis.follow_up_questions,
                recommendations=all_recommendations,
                requires_human_review=len(current_medications) > 5,  # Many medications need review
                risk_assessment=medication_analysis.risk_level,
                next_actions=["Consult with pharmacist", "Review with healthcare provider"]
            )
            
        except Exception as e:
            logger.error(f"Medication review workflow error: {str(e)}")
            return await self._fallback_response(query, patient_context)

    async def _preventive_care_workflow(
        self,
        query: str,
        patient_context: Dict[str, Any],
        session: Dict[str, Any]
    ) -> HealthQueryResponse:
        """
        Preventive care and wellness workflow
        """
        try:
            # Generate personalized preventive care recommendations
            preventive_prompt = f"""
            Provide personalized preventive care recommendations based on:
            
            Patient Context: {patient_context}
            Specific Query: {query}
            
            Consider:
            - Age-appropriate screenings
            - Lifestyle modifications
            - Vaccination schedules
            - Risk factor management
            - Wellness goals
            
            Provide actionable, evidence-based recommendations.
            """
            
            preventive_response = await self.bedrock_agent.process_medical_consultation(
                preventive_prompt, patient_context
            )
            
            # Add standard preventive care reminders
            standard_preventive = [
                "Schedule regular checkups",
                "Stay up to date with vaccinations",
                "Maintain healthy diet and exercise",
                "Monitor key health metrics"
            ]
            
            return HealthQueryResponse(
                response_text=preventive_response.response_text,
                confidence=preventive_response.confidence,
                follow_up_questions=preventive_response.follow_up_questions,
                recommendations=list(set(preventive_response.recommendations + standard_preventive)),
                requires_human_review=False,  # Preventive care usually low risk
                risk_assessment="low",
                next_actions=["Create preventive care schedule", "Discuss with healthcare provider"]
            )
            
        except Exception as e:
            logger.error(f"Preventive care workflow error: {str(e)}")
            return await self._fallback_response(query, patient_context)

    async def _default_consultation_workflow(
        self,
        query: str,
        patient_context: Dict[str, Any],
        session: Dict[str, Any]
    ) -> HealthQueryResponse:
        """
        Default workflow for general queries
        """
        return await self._health_consultation_workflow(query, patient_context, session)

    async def _combine_symptom_analyses(
        self,
        bedrock_analysis: Any,
        sagemaker_analysis: Any,
        original_query: str,
        patient_context: Dict[str, Any]
    ) -> HealthQueryResponse:
        """
        Combine insights from both Bedrock and SageMaker analyses
        """
        try:
            # Handle exceptions from parallel execution
            if isinstance(bedrock_analysis, Exception):
                bedrock_analysis = None
            if isinstance(sagemaker_analysis, Exception):
                sagemaker_analysis = None
            
            # Combine response text
            if bedrock_analysis and sagemaker_analysis:
                combined_text = f"{bedrock_analysis.response_text}\n\n**Additional ML Analysis:**\n"
                combined_text += f"Risk Level: {sagemaker_analysis.risk_level}\n"
                combined_text += f"Recommended Timeline: {sagemaker_analysis.recommended_timeline}"
                
                # Use higher confidence
                confidence = max(bedrock_analysis.confidence, sagemaker_analysis.confidence)
                
                # Combine recommendations
                recommendations = list(set(
                    bedrock_analysis.recommendations + 
                    [sagemaker_analysis.recommended_timeline]
                ))
                
                # More conservative approach for human review
                requires_human_review = (
                    bedrock_analysis.requires_human_review or 
                    sagemaker_analysis.should_see_doctor
                )
                
                risk_assessment = max(
                    [bedrock_analysis.risk_level, sagemaker_analysis.risk_level],
                    key=lambda x: ['low', 'medium', 'high', 'critical'].index(x) if x in ['low', 'medium', 'high', 'critical'] else 0
                )
                
            elif bedrock_analysis:
                return HealthQueryResponse(
                    response_text=bedrock_analysis.response_text,
                    confidence=bedrock_analysis.confidence,
                    follow_up_questions=bedrock_analysis.follow_up_questions,
                    recommendations=bedrock_analysis.recommendations,
                    requires_human_review=bedrock_analysis.requires_human_review,
                    risk_assessment=bedrock_analysis.risk_level,
                    next_actions=["Follow up with healthcare provider if symptoms persist"]
                )
            elif sagemaker_analysis:
                return HealthQueryResponse(
                    response_text=f"Based on symptom analysis: {sagemaker_analysis.recommended_timeline}",
                    confidence=sagemaker_analysis.confidence,
                    follow_up_questions=["How long have you had these symptoms?"],
                    recommendations=[sagemaker_analysis.recommended_timeline],
                    requires_human_review=sagemaker_analysis.should_see_doctor,
                    risk_assessment=sagemaker_analysis.risk_level,
                    next_actions=["Monitor symptoms", "Seek medical care if worsening"]
                )
            else:
                return await self._fallback_response(original_query, patient_context)
            
            return HealthQueryResponse(
                response_text=combined_text,
                confidence=confidence,
                follow_up_questions=bedrock_analysis.follow_up_questions if bedrock_analysis else [],
                recommendations=recommendations,
                requires_human_review=requires_human_review,
                risk_assessment=risk_assessment,
                next_actions=self._generate_symptom_based_actions(sagemaker_analysis)
            )
            
        except Exception as e:
            logger.error(f"Analysis combination error: {str(e)}")
            return await self._fallback_response(original_query, patient_context)

    def _extract_symptoms_from_response(self, response_text: str) -> List[str]:
        """
        Extract symptom list from Bedrock response
        """
        # Simple extraction - in production, use more sophisticated NLP
        common_symptoms = [
            'fever', 'cough', 'headache', 'fatigue', 'nausea', 'vomiting',
            'chest pain', 'shortness of breath', 'dizziness', 'abdominal pain',
            'sore throat', 'runny nose', 'muscle aches'
        ]
        
        found_symptoms = []
        response_lower = response_text.lower()
        
        for symptom in common_symptoms:
            if symptom in response_lower:
                found_symptoms.append(symptom)
        
        return found_symptoms if found_symptoms else ['general discomfort']

    async def _generate_contextual_follow_ups(
        self,
        original_query: str,
        response_text: str,
        patient_context: Dict[str, Any]
    ) -> List[str]:
        """
        Generate contextual follow-up questions
        """
        age = patient_context.get('demographics', {}).get('age', 0)
        
        base_questions = [
            "Are there any other symptoms you've noticed?",
            "How long have you been experiencing this?",
            "Have you tried any treatments?"
        ]
        
        # Age-specific questions
        if age > 65:
            base_questions.append("Have you discussed this with your regular doctor?")
        elif age < 18:
            base_questions.append("Have your parents been informed about these symptoms?")
        
        return base_questions[:3]

    def _generate_next_actions(self, consultation_response: Any) -> List[str]:
        """
        Generate next actions based on consultation response
        """
        actions = ["Monitor symptoms"]
        
        if hasattr(consultation_response, 'requires_human_review') and consultation_response.requires_human_review:
            actions.append("Schedule appointment with healthcare provider")
        
        if hasattr(consultation_response, 'risk_level'):
            if consultation_response.risk_level in ['high', 'critical']:
                actions.append("Seek immediate medical attention")
            elif consultation_response.risk_level == 'medium':
                actions.append("Consider urgent care if symptoms worsen")
        
        return actions

    def _generate_risk_based_actions(self, risk_prediction: Any) -> List[str]:
        """
        Generate actions based on risk prediction
        """
        actions = []
        
        if risk_prediction.health_score < 60:
            actions.append("Schedule comprehensive health evaluation")
        elif risk_prediction.health_score < 80:
            actions.append("Discuss risk factors with healthcare provider")
        
        actions.extend([
            "Implement recommended lifestyle changes",
            "Schedule regular monitoring appointments"
        ])
        
        return actions

    def _generate_symptom_based_actions(self, symptom_analysis: Any) -> List[str]:
        """
        Generate actions based on symptom analysis
        """
        if not symptom_analysis:
            return ["Monitor symptoms", "Consult healthcare provider if concerned"]
        
        actions = []
        
        if hasattr(symptom_analysis, 'urgency'):
            if symptom_analysis.urgency == 'emergency':
                actions.append("Seek immediate emergency care")
            elif symptom_analysis.urgency == 'urgent':
                actions.append("See a doctor within 24 hours")
            else:
                actions.append("Monitor symptoms and follow up as needed")
        
        if hasattr(symptom_analysis, 'emergency_indicators') and symptom_analysis.emergency_indicators:
            actions.append("Watch for worsening of emergency symptoms")
        
        return actions

    def _categorize_health_score(self, health_score: float) -> str:
        """
        Categorize health score into risk levels
        """
        if health_score >= 85:
            return "low"
        elif health_score >= 70:
            return "medium"
        elif health_score >= 50:
            return "high"
        else:
            return "critical"

    async def _fallback_response(
        self,
        query: str,
        patient_context: Dict[str, Any]
    ) -> HealthQueryResponse:
        """
        Fallback response when other workflows fail
        """
        return HealthQueryResponse(
            response_text="I understand you have a health concern. While I'm experiencing some technical difficulties with my analysis systems, I recommend consulting with a healthcare professional who can properly evaluate your situation.",
            confidence=0.5,
            follow_up_questions=["Would you like me to help you find healthcare resources in your area?"],
            recommendations=["Consult with a healthcare provider", "Keep track of your symptoms"],
            requires_human_review=True,
            risk_assessment="unknown",
            next_actions=["Contact healthcare provider", "Seek medical advice"]
        )

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific session
        """
        if session_id not in self.active_sessions:
            return {"status": "not_found"}
        
        session = self.active_sessions[session_id]
        return {
            "status": "active",
            "created_at": session['created_at'].isoformat(),
            "message_count": len(session['history']),
            "last_activity": session['history'][-1]['timestamp'].isoformat() if session['history'] else None
        }

    async def get_active_sessions_count(self) -> int:
        """
        Get count of active sessions
        """
        return len(self.active_sessions)