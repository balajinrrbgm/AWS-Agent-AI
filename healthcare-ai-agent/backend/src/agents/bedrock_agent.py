import boto3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MedicalResponse:
    response_text: str
    confidence: float
    medical_entities: List[Dict[str, Any]]
    recommendations: List[str]
    follow_up_questions: List[str]
    requires_human_review: bool
    risk_level: str

class BedrockHealthAgent:
    """
    Advanced medical AI agent powered by Amazon Bedrock
    Handles medical consultations, symptom analysis, and health recommendations
    """
    
    def __init__(self, bedrock_client):
        self.bedrock_client = bedrock_client
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"  # Use latest Claude model
        self.medical_model_id = "amazon.titan-text-premier-v1:0"  # Backup model
        
        # Medical prompt templates
        self.consultation_prompt = """
        You are an advanced AI medical assistant with deep knowledge of medical literature, 
        clinical guidelines, and patient care protocols. You provide evidence-based medical 
        guidance while being careful to recommend professional medical care when appropriate.

        Patient Context: {patient_context}
        Medical History: {medical_history}
        Current Medications: {medications}
        
        Patient Query: {query}

        Please provide:
        1. A comprehensive, empathetic response to the patient's concern
        2. Evidence-based medical information relevant to their query
        3. Clear recommendations for next steps
        4. Any red flags that require immediate medical attention
        5. Follow-up questions to gather more relevant information
        
        Important: Always emphasize that this is not a substitute for professional medical advice.
        For serious symptoms or emergencies, direct the patient to seek immediate medical care.

        Response format should be structured and easy to understand.
        """
        
        self.symptom_analysis_prompt = """
        You are a clinical decision support AI specializing in symptom analysis and medical triage.
        
        Patient Information:
        - Age: {age}
        - Gender: {gender}
        - Medical History: {medical_history}
        - Current Medications: {medications}
        - Allergies: {allergies}
        
        Symptoms Reported: {symptoms}
        Duration: {duration}
        Severity (1-10): {severity}
        
        Please analyze these symptoms and provide:
        1. Most likely differential diagnoses (top 3-5)
        2. Risk stratification (Low/Medium/High/Critical)
        3. Recommended urgency of care (Self-care/Primary care/Urgent care/Emergency)
        4. Warning signs to watch for
        5. Initial care recommendations
        6. When to seek immediate medical attention
        
        Base your analysis on current medical guidelines and evidence-based medicine.
        """

    async def process_medical_consultation(
        self, 
        query: str, 
        patient_context: Dict[str, Any],
        session_history: Optional[List[Dict]] = None
    ) -> MedicalResponse:
        """
        Process a medical consultation query using Bedrock
        """
        try:
            # Prepare the prompt with patient context
            formatted_prompt = self.consultation_prompt.format(
                patient_context=json.dumps(patient_context.get('demographics', {})),
                medical_history=patient_context.get('medical_history', 'No significant history'),
                medications=', '.join(patient_context.get('medications', [])) or 'None reported',
                query=query
            )
            
            # Include conversation history for context
            if session_history:
                formatted_prompt += f"\n\nPrevious conversation context:\n{json.dumps(session_history[-3:])}"
            
            # Call Bedrock
            response = await self._call_bedrock_model(formatted_prompt)
            
            # Parse and structure the response
            medical_response = await self._parse_medical_response(response, query)
            
            # Log for monitoring and improvement
            logger.info(f"Medical consultation processed: confidence={medical_response.confidence}")
            
            return medical_response
            
        except Exception as e:
            logger.error(f"Medical consultation error: {str(e)}")
            return MedicalResponse(
                response_text="I apologize, but I'm experiencing technical difficulties. Please consult with a healthcare professional for your medical concerns.",
                confidence=0.0,
                medical_entities=[],
                recommendations=["Consult with a healthcare provider"],
                follow_up_questions=[],
                requires_human_review=True,
                risk_level="unknown"
            )

    async def analyze_symptoms_with_bedrock(
        self,
        symptoms: List[str],
        patient_context: Dict[str, Any],
        duration: str,
        severity: int
    ) -> MedicalResponse:
        """
        Analyze symptoms using Bedrock for medical insights
        """
        try:
            formatted_prompt = self.symptom_analysis_prompt.format(
                age=patient_context.get('demographics', {}).get('age', 'Not specified'),
                gender=patient_context.get('demographics', {}).get('gender', 'Not specified'),
                medical_history=patient_context.get('medical_history', 'No significant history'),
                medications=', '.join(patient_context.get('medications', [])) or 'None',
                allergies=', '.join(patient_context.get('allergies', [])) or 'None known',
                symptoms=', '.join(symptoms),
                duration=duration,
                severity=severity
            )
            
            response = await self._call_bedrock_model(formatted_prompt)
            return await self._parse_symptom_analysis(response, symptoms, severity)
            
        except Exception as e:
            logger.error(f"Symptom analysis error: {str(e)}")
            return MedicalResponse(
                response_text="Unable to analyze symptoms at this time. Please consult a healthcare provider.",
                confidence=0.0,
                medical_entities=[],
                recommendations=["Seek professional medical evaluation"],
                follow_up_questions=[],
                requires_human_review=True,
                risk_level="unknown"
            )

    async def get_medical_recommendations(
        self,
        symptoms: List[str],
        analysis: Any,
        patient_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate personalized medical recommendations
        """
        try:
            recommendations_prompt = f"""
            Based on the following medical analysis, provide personalized recommendations:
            
            Patient Context: {json.dumps(patient_context)}
            Symptoms: {', '.join(symptoms)}
            Analysis: {analysis if hasattr(analysis, '__dict__') else str(analysis)}
            
            Please provide:
            1. Immediate care recommendations
            2. Lifestyle modifications
            3. When to follow up
            4. Warning signs to watch for
            5. Preventive measures
            
            Make recommendations specific to this patient's profile and current situation.
            """
            
            response = await self._call_bedrock_model(recommendations_prompt)
            
            return {
                "recommendations": self._extract_recommendations(response),
                "next_steps": self._extract_next_steps(response),
                "preventive_measures": self._extract_preventive_measures(response)
            }
            
        except Exception as e:
            logger.error(f"Recommendations generation error: {str(e)}")
            return {
                "recommendations": ["Consult with a healthcare provider for personalized advice"],
                "next_steps": ["Schedule an appointment with your doctor"],
                "preventive_measures": ["Maintain regular healthcare checkups"]
            }

    async def _call_bedrock_model(self, prompt: str) -> str:
        """
        Make async call to Bedrock model
        """
        try:
            # Prepare the request body for Claude
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "temperature": 0.1,  # Low temperature for medical accuracy
                "top_p": 0.9,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Make the async call
            response = await asyncio.to_thread(
                self.bedrock_client.invoke_model,
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            logger.error(f"Bedrock model call error: {str(e)}")
            # Fallback to Titan model
            try:
                return await self._call_titan_model(prompt)
            except:
                raise e

    async def _call_titan_model(self, prompt: str) -> str:
        """
        Fallback to Titan model
        """
        body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 4000,
                "temperature": 0.1,
                "topP": 0.9
            }
        }
        
        response = await asyncio.to_thread(
            self.bedrock_client.invoke_model,
            modelId=self.medical_model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['results'][0]['outputText']

    async def _parse_medical_response(self, response_text: str, original_query: str) -> MedicalResponse:
        """
        Parse and structure the medical response from Bedrock
        """
        try:
            # Extract confidence based on language used
            confidence = self._calculate_confidence(response_text)
            
            # Extract medical entities (simplified - in production, use Comprehend Medical)
            medical_entities = self._extract_medical_entities(response_text)
            
            # Determine if human review is needed
            requires_human_review = self._needs_human_review(response_text, confidence)
            
            # Extract recommendations and follow-up questions
            recommendations = self._extract_recommendations(response_text)
            follow_up_questions = self._extract_follow_up_questions(response_text)
            
            # Determine risk level
            risk_level = self._determine_risk_level(response_text)
            
            return MedicalResponse(
                response_text=response_text,
                confidence=confidence,
                medical_entities=medical_entities,
                recommendations=recommendations,
                follow_up_questions=follow_up_questions,
                requires_human_review=requires_human_review,
                risk_level=risk_level
            )
            
        except Exception as e:
            logger.error(f"Response parsing error: {str(e)}")
            return MedicalResponse(
                response_text=response_text,
                confidence=0.5,
                medical_entities=[],
                recommendations=[],
                follow_up_questions=[],
                requires_human_review=True,
                risk_level="unknown"
            )

    async def _parse_symptom_analysis(self, response_text: str, symptoms: List[str], severity: int) -> MedicalResponse:
        """
        Parse symptom analysis response
        """
        confidence = self._calculate_confidence(response_text)
        
        # Higher severity symptoms require human review
        requires_human_review = severity >= 7 or self._contains_emergency_keywords(response_text)
        
        risk_level = self._determine_risk_level(response_text)
        if severity >= 8:
            risk_level = "high"
        elif severity >= 6:
            risk_level = "medium"
        
        return MedicalResponse(
            response_text=response_text,
            confidence=confidence,
            medical_entities=self._extract_medical_entities(response_text),
            recommendations=self._extract_recommendations(response_text),
            follow_up_questions=self._extract_follow_up_questions(response_text),
            requires_human_review=requires_human_review,
            risk_level=risk_level
        )

    def _calculate_confidence(self, response_text: str) -> float:
        """
        Calculate confidence score based on response characteristics
        """
        confidence_indicators = [
            ("likely", 0.7), ("probably", 0.6), ("possibly", 0.5),
            ("definitely", 0.9), ("certainly", 0.9), ("clearly", 0.8),
            ("may be", 0.4), ("might be", 0.4), ("could be", 0.4),
            ("consistent with", 0.8), ("suggests", 0.7)
        ]
        
        base_confidence = 0.6
        for indicator, weight in confidence_indicators:
            if indicator.lower() in response_text.lower():
                base_confidence = weight
                break
        
        # Adjust for uncertainty phrases
        uncertainty_phrases = ["not sure", "uncertain", "unclear", "difficult to determine"]
        for phrase in uncertainty_phrases:
            if phrase in response_text.lower():
                base_confidence *= 0.7
        
        return min(max(base_confidence, 0.1), 0.95)

    def _extract_medical_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract medical entities (simplified version - use Comprehend Medical in production)
        """
        # This is a simplified version. In production, use Amazon Comprehend Medical
        common_entities = {
            'symptoms': ['pain', 'fever', 'headache', 'nausea', 'fatigue', 'cough', 'shortness of breath'],
            'body_parts': ['chest', 'head', 'stomach', 'back', 'leg', 'arm', 'heart', 'lung'],
            'conditions': ['infection', 'inflammation', 'diabetes', 'hypertension', 'pneumonia']
        }
        
        entities = []
        text_lower = text.lower()
        
        for category, terms in common_entities.items():
            for term in terms:
                if term in text_lower:
                    entities.append({
                        'text': term,
                        'category': category,
                        'confidence': 0.8
                    })
        
        return entities

    def _needs_human_review(self, response_text: str, confidence: float) -> bool:
        """
        Determine if human review is needed
        """
        emergency_keywords = [
            'emergency', 'urgent', 'immediate', 'serious', 'severe',
            'call 911', 'emergency room', 'life-threatening'
        ]
        
        # Low confidence requires review
        if confidence < 0.6:
            return True
        
        # Emergency indicators require review
        text_lower = response_text.lower()
        for keyword in emergency_keywords:
            if keyword in text_lower:
                return True
        
        return False

    def _contains_emergency_keywords(self, text: str) -> bool:
        """
        Check for emergency keywords
        """
        emergency_keywords = [
            'emergency', 'urgent', 'immediate', 'critical', 'severe',
            'life-threatening', '911', 'hospital', 'emergency room'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in emergency_keywords)

    def _determine_risk_level(self, response_text: str) -> str:
        """
        Determine risk level from response
        """
        text_lower = response_text.lower()
        
        high_risk_indicators = ['severe', 'serious', 'urgent', 'emergency', 'critical', 'life-threatening']
        medium_risk_indicators = ['moderate', 'concerning', 'monitor', 'follow up']
        low_risk_indicators = ['mild', 'minor', 'low risk', 'self-care', 'home treatment']
        
        for indicator in high_risk_indicators:
            if indicator in text_lower:
                return 'high'
        
        for indicator in medium_risk_indicators:
            if indicator in text_lower:
                return 'medium'
        
        for indicator in low_risk_indicators:
            if indicator in text_lower:
                return 'low'
        
        return 'medium'  # Default to medium risk

    def _extract_recommendations(self, text: str) -> List[str]:
        """
        Extract recommendations from response
        """
        recommendations = []
        lines = text.split('\n')
        
        in_recommendations = False
        for line in lines:
            line = line.strip()
            if 'recommendation' in line.lower() or 'suggest' in line.lower():
                in_recommendations = True
                continue
            
            if in_recommendations and line and (line.startswith('-') or line.startswith('•') or line.startswith('1.')):
                recommendations.append(line.lstrip('-•1234567890. '))
            elif in_recommendations and not line:
                break
        
        # If no structured recommendations found, extract general advice
        if not recommendations:
            advice_keywords = ['should', 'recommend', 'suggest', 'advise', 'consider']
            for line in lines:
                for keyword in advice_keywords:
                    if keyword in line.lower() and len(line.strip()) > 20:
                        recommendations.append(line.strip())
                        break
        
        return recommendations[:5]  # Limit to top 5 recommendations

    def _extract_follow_up_questions(self, text: str) -> List[str]:
        """
        Extract follow-up questions from response
        """
        questions = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if '?' in line and len(line) > 10:
                questions.append(line)
        
        # Generate contextual follow-up questions if none found
        if not questions:
            questions = [
                "How long have you been experiencing these symptoms?",
                "Are there any other symptoms you've noticed?",
                "Have you tried any treatments or medications?",
                "Is there anything that makes the symptoms better or worse?"
            ]
        
        return questions[:3]  # Limit to 3 questions

    def _extract_next_steps(self, text: str) -> List[str]:
        """
        Extract next steps from response
        """
        next_steps = []
        lines = text.split('\n')
        
        step_indicators = ['next step', 'follow up', 'should do', 'next', 'then']
        
        for line in lines:
            line_lower = line.lower()
            for indicator in step_indicators:
                if indicator in line_lower and len(line.strip()) > 15:
                    next_steps.append(line.strip())
                    break
        
        return next_steps[:3]

    def _extract_preventive_measures(self, text: str) -> List[str]:
        """
        Extract preventive measures from response
        """
        measures = []
        lines = text.split('\n')
        
        preventive_keywords = ['prevent', 'avoid', 'lifestyle', 'diet', 'exercise', 'healthy']
        
        for line in lines:
            line_lower = line.lower()
            for keyword in preventive_keywords:
                if keyword in line_lower and len(line.strip()) > 15:
                    measures.append(line.strip())
                    break
        
        return measures[:4]