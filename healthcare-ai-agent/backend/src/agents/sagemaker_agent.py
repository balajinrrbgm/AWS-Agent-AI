import boto3
import json
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
from dataclasses import dataclass
from sklearn.preprocessing import StandardScaler
import joblib
import os

logger = logging.getLogger(__name__)

@dataclass
class SymptomAnalysis:
    risk_level: str
    possible_conditions: List[Dict[str, float]]
    urgency: str
    confidence: float
    should_see_doctor: bool
    emergency_indicators: List[str]
    predicted_severity: float
    recommended_timeline: str

@dataclass
class HealthPrediction:
    health_score: float
    risk_factors: List[Dict[str, Any]]
    predictions: Dict[str, float]
    recommendations: List[str]
    confidence_intervals: Dict[str, Tuple[float, float]]

class SageMakerHealthAnalyzer:
    """
    Advanced health analyzer using Amazon SageMaker AI
    Performs symptom analysis, risk assessment, and health predictions
    """
    
    def __init__(self, sagemaker_client):
        self.sagemaker_client = sagemaker_client
        
        # SageMaker endpoint names (would be deployed separately)
        self.symptom_analyzer_endpoint = "healthcare-symptom-analyzer"
        self.risk_predictor_endpoint = "healthcare-risk-predictor" 
        self.health_scorer_endpoint = "healthcare-health-scorer"
        
        # Medical knowledge base
        self.condition_mappings = {
            'respiratory': ['pneumonia', 'bronchitis', 'asthma', 'covid-19', 'flu'],
            'cardiovascular': ['heart_attack', 'arrhythmia', 'hypertension', 'heart_failure'],
            'gastrointestinal': ['gastritis', 'appendicitis', 'ibs', 'food_poisoning'],
            'neurological': ['migraine', 'tension_headache', 'stroke', 'seizure'],
            'musculoskeletal': ['muscle_strain', 'arthritis', 'fracture', 'sprain'],
            'infectious': ['viral_infection', 'bacterial_infection', 'sepsis']
        }
        
        self.symptom_urgency_mapping = {
            'chest_pain': 'high',
            'difficulty_breathing': 'high',
            'severe_headache': 'high',
            'high_fever': 'medium',
            'persistent_cough': 'medium',
            'fatigue': 'low',
            'mild_headache': 'low'
        }
        
        # Emergency indicators
        self.emergency_symptoms = [
            'chest_pain', 'difficulty_breathing', 'severe_headache', 'loss_of_consciousness',
            'severe_bleeding', 'signs_of_stroke', 'severe_allergic_reaction',
            'severe_abdominal_pain', 'high_fever_with_confusion'
        ]

    async def analyze_symptoms(
        self,
        symptoms: List[str],
        patient_context: Dict[str, Any],
        duration: str,
        severity: int
    ) -> SymptomAnalysis:
        """
        Analyze symptoms using SageMaker ML models
        """
        try:
            # Prepare input features
            features = await self._prepare_symptom_features(
                symptoms, patient_context, duration, severity
            )
            
            # Call SageMaker endpoint for symptom analysis
            analysis_result = await self._invoke_symptom_analyzer(features)
            
            # Post-process results
            processed_analysis = await self._process_symptom_analysis(
                analysis_result, symptoms, severity, patient_context
            )
            
            logger.info(f"Symptom analysis completed: risk_level={processed_analysis.risk_level}")
            return processed_analysis
            
        except Exception as e:
            logger.error(f"Symptom analysis error: {str(e)}")
            return await self._fallback_symptom_analysis(symptoms, severity)

    async def predict_health_risks(
        self,
        patient_profile: Dict[str, Any],
        historical_data: Optional[List[Dict]] = None
    ) -> HealthPrediction:
        """
        Predict health risks using ML models
        """
        try:
            # Prepare features for risk prediction
            risk_features = await self._prepare_risk_features(
                patient_profile, historical_data
            )
            
            # Call SageMaker risk prediction endpoint
            risk_prediction = await self._invoke_risk_predictor(risk_features)
            
            # Generate health score
            health_score = await self._calculate_health_score(
                patient_profile, risk_prediction
            )
            
            return HealthPrediction(
                health_score=health_score,
                risk_factors=risk_prediction.get('risk_factors', []),
                predictions=risk_prediction.get('predictions', {}),
                recommendations=risk_prediction.get('recommendations', []),
                confidence_intervals=risk_prediction.get('confidence_intervals', {})
            )
            
        except Exception as e:
            logger.error(f"Health risk prediction error: {str(e)}")
            return await self._fallback_health_prediction(patient_profile)

    async def analyze_vital_trends(
        self,
        vital_data: List[Dict[str, Any]],
        patient_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze trends in vital signs and health metrics
        """
        try:
            # Prepare time series data
            time_series_features = await self._prepare_time_series_features(vital_data)
            
            # Analyze trends using SageMaker
            trend_analysis = await self._analyze_vital_trends_ml(
                time_series_features, patient_context
            )
            
            return {
                'trends': trend_analysis.get('trends', {}),
                'anomalies': trend_analysis.get('anomalies', []),
                'predictions': trend_analysis.get('future_predictions', {}),
                'recommendations': trend_analysis.get('recommendations', []),
                'alert_conditions': trend_analysis.get('alerts', [])
            }
            
        except Exception as e:
            logger.error(f"Vital trends analysis error: {str(e)}")
            return await self._fallback_vital_analysis(vital_data)

    async def _prepare_symptom_features(
        self,
        symptoms: List[str],
        patient_context: Dict[str, Any],
        duration: str,
        severity: int
    ) -> Dict[str, Any]:
        """
        Prepare features for symptom analysis ML model
        """
        # Convert symptoms to feature vector
        symptom_vector = self._encode_symptoms(symptoms)
        
        # Patient demographic features
        demographics = patient_context.get('demographics', {})
        age = demographics.get('age', 0)
        gender = demographics.get('gender', 'unknown')
        
        # Medical history features
        medical_history = patient_context.get('medical_history', [])
        chronic_conditions = patient_context.get('chronic_conditions', [])
        medications = patient_context.get('medications', [])
        
        # Duration encoding
        duration_days = self._encode_duration(duration)
        
        features = {
            'symptom_vector': symptom_vector,
            'age': age,
            'gender_encoded': 1 if gender.lower() == 'male' else 0,
            'severity': severity,
            'duration_days': duration_days,
            'chronic_condition_count': len(chronic_conditions),
            'medication_count': len(medications),
            'has_cardiovascular_history': any('heart' in condition.lower() or 'cardiac' in condition.lower() 
                                           for condition in medical_history),
            'has_respiratory_history': any('lung' in condition.lower() or 'asthma' in condition.lower()
                                        for condition in medical_history),
            'has_diabetes': any('diabetes' in condition.lower() for condition in medical_history)
        }
        
        return features

    def _encode_symptoms(self, symptoms: List[str]) -> List[float]:
        """
        Encode symptoms into numerical vector
        """
        # Common symptoms vocabulary (in practice, this would be larger)
        symptom_vocab = [
            'fever', 'cough', 'headache', 'fatigue', 'nausea', 'vomiting',
            'chest_pain', 'shortness_of_breath', 'dizziness', 'abdominal_pain',
            'muscle_aches', 'sore_throat', 'runny_nose', 'diarrhea', 'constipation',
            'rash', 'joint_pain', 'back_pain', 'anxiety', 'depression'
        ]
        
        # Create binary vector
        vector = [0.0] * len(symptom_vocab)
        for i, vocab_symptom in enumerate(symptom_vocab):
            for symptom in symptoms:
                if vocab_symptom.lower() in symptom.lower() or symptom.lower() in vocab_symptom.lower():
                    vector[i] = 1.0
                    break
        
        return vector

    def _encode_duration(self, duration: str) -> float:
        """
        Convert duration string to days
        """
        duration_lower = duration.lower()
        
        if 'hour' in duration_lower:
            if 'few' in duration_lower:
                return 0.2
            elif any(num in duration_lower for num in ['1', 'one']):
                return 0.04
            else:
                return 0.5
        elif 'day' in duration_lower:
            if 'few' in duration_lower:
                return 3.0
            elif any(num in duration_lower for num in ['1', 'one']):
                return 1.0
            else:
                return 5.0
        elif 'week' in duration_lower:
            if 'few' in duration_lower:
                return 14.0
            elif any(num in duration_lower for num in ['1', 'one']):
                return 7.0
            else:
                return 21.0
        elif 'month' in duration_lower:
            return 30.0
        else:
            return 1.0  # Default to 1 day

    async def _invoke_symptom_analyzer(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call SageMaker symptom analyzer endpoint
        """
        try:
            # Prepare payload
            payload = {
                'instances': [features]
            }
            
            # Invoke endpoint
            response = await asyncio.to_thread(
                self.sagemaker_client.invoke_endpoint,
                EndpointName=self.symptom_analyzer_endpoint,
                ContentType='application/json',
                Body=json.dumps(payload)
            )
            
            # Parse response
            result = json.loads(response['Body'].read().decode())
            return result
            
        except Exception as e:
            logger.error(f"SageMaker symptom analyzer invocation error: {str(e)}")
            # Return mock result for demo purposes
            return await self._mock_symptom_analysis(features)

    async def _mock_symptom_analysis(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock symptom analysis for demo purposes
        """
        # Simulate ML model predictions
        severity = features.get('severity', 5)
        age = features.get('age', 35)
        
        # Risk calculation based on severity and age
        base_risk = severity / 10.0
        age_factor = min(age / 100.0, 0.3)
        risk_score = min(base_risk + age_factor, 1.0)
        
        # Determine risk level
        if risk_score > 0.7:
            risk_level = 'high'
            urgency = 'urgent'
        elif risk_score > 0.4:
            risk_level = 'medium'
            urgency = 'moderate'
        else:
            risk_level = 'low'
            urgency = 'routine'
        
        # Mock condition predictions
        possible_conditions = [
            {'condition': 'viral_infection', 'probability': 0.6},
            {'condition': 'bacterial_infection', 'probability': 0.3},
            {'condition': 'allergic_reaction', 'probability': 0.1}
        ]
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'urgency': urgency,
            'possible_conditions': possible_conditions,
            'confidence': 0.8
        }

    async def _process_symptom_analysis(
        self,
        analysis_result: Dict[str, Any],
        symptoms: List[str],
        severity: int,
        patient_context: Dict[str, Any]
    ) -> SymptomAnalysis:
        """
        Process and enhance the ML analysis results
        """
        risk_level = analysis_result.get('risk_level', 'medium')
        possible_conditions = analysis_result.get('possible_conditions', [])
        urgency = analysis_result.get('urgency', 'moderate')
        confidence = analysis_result.get('confidence', 0.7)
        
        # Check for emergency indicators
        emergency_indicators = []
        for symptom in symptoms:
            if any(emergency in symptom.lower() for emergency in self.emergency_symptoms):
                emergency_indicators.append(symptom)
                risk_level = 'high'
                urgency = 'emergency'
        
        # Determine if doctor visit is needed
        should_see_doctor = (
            severity >= 7 or
            risk_level in ['high', 'critical'] or
            len(emergency_indicators) > 0 or
            urgency in ['urgent', 'emergency']
        )
        
        # Calculate predicted severity
        predicted_severity = min(severity * (1 + analysis_result.get('risk_score', 0.5)), 10)
        
        # Recommend timeline
        if urgency == 'emergency':
            recommended_timeline = 'Seek immediate emergency care'
        elif urgency == 'urgent':
            recommended_timeline = 'See a doctor within 24 hours'
        elif urgency == 'moderate':
            recommended_timeline = 'Schedule appointment within 3-5 days'
        else:
            recommended_timeline = 'Monitor symptoms, see doctor if worsening'
        
        return SymptomAnalysis(
            risk_level=risk_level,
            possible_conditions=possible_conditions,
            urgency=urgency,
            confidence=confidence,
            should_see_doctor=should_see_doctor,
            emergency_indicators=emergency_indicators,
            predicted_severity=predicted_severity,
            recommended_timeline=recommended_timeline
        )

    async def _fallback_symptom_analysis(
        self,
        symptoms: List[str],
        severity: int
    ) -> SymptomAnalysis:
        """
        Fallback analysis when ML models are unavailable
        """
        # Rule-based fallback
        emergency_count = sum(1 for symptom in symptoms 
                            if any(emergency in symptom.lower() 
                                 for emergency in self.emergency_symptoms))
        
        if emergency_count > 0 or severity >= 8:
            risk_level = 'high'
            urgency = 'emergency'
        elif severity >= 6:
            risk_level = 'medium'
            urgency = 'moderate'
        else:
            risk_level = 'low'
            urgency = 'routine'
        
        return SymptomAnalysis(
            risk_level=risk_level,
            possible_conditions=[],
            urgency=urgency,
            confidence=0.6,
            should_see_doctor=severity >= 6,
            emergency_indicators=symptoms if emergency_count > 0 else [],
            predicted_severity=float(severity),
            recommended_timeline=f'Assessment based on severity level {severity}'
        )

    async def _prepare_risk_features(
        self,
        patient_profile: Dict[str, Any],
        historical_data: Optional[List[Dict]]
    ) -> Dict[str, Any]:
        """
        Prepare features for health risk prediction
        """
        demographics = patient_profile.get('demographics', {})
        medical_history = patient_profile.get('medical_history', [])
        lifestyle = patient_profile.get('lifestyle', {})
        
        features = {
            'age': demographics.get('age', 0),
            'gender': demographics.get('gender', 'unknown'),
            'bmi': lifestyle.get('bmi', 25.0),
            'smoking_status': lifestyle.get('smoking', False),
            'alcohol_consumption': lifestyle.get('alcohol_weekly_units', 0),
            'exercise_frequency': lifestyle.get('exercise_per_week', 2),
            'family_history_heart_disease': 'heart' in str(medical_history).lower(),
            'family_history_diabetes': 'diabetes' in str(medical_history).lower(),
            'chronic_conditions_count': len(patient_profile.get('chronic_conditions', [])),
            'medications_count': len(patient_profile.get('medications', []))
        }
        
        # Add historical trends if available
        if historical_data:
            features['historical_trend'] = self._calculate_historical_trends(historical_data)
        
        return features

    async def _invoke_risk_predictor(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call SageMaker risk prediction endpoint
        """
        try:
            payload = {'instances': [features]}
            
            response = await asyncio.to_thread(
                self.sagemaker_client.invoke_endpoint,
                EndpointName=self.risk_predictor_endpoint,
                ContentType='application/json',
                Body=json.dumps(payload)
            )
            
            result = json.loads(response['Body'].read().decode())
            return result
            
        except Exception as e:
            logger.error(f"Risk predictor invocation error: {str(e)}")
            return await self._mock_risk_prediction(features)

    async def _mock_risk_prediction(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock risk prediction for demo
        """
        age = features.get('age', 35)
        bmi = features.get('bmi', 25.0)
        smoking = features.get('smoking_status', False)
        
        # Calculate cardiovascular risk
        cv_risk = 0.1
        if age > 60:
            cv_risk += 0.3
        elif age > 40:
            cv_risk += 0.1
        
        if bmi > 30:
            cv_risk += 0.2
        elif bmi > 25:
            cv_risk += 0.1
        
        if smoking:
            cv_risk += 0.3
        
        # Calculate diabetes risk
        diabetes_risk = 0.05
        if bmi > 30:
            diabetes_risk += 0.25
        if age > 45:
            diabetes_risk += 0.15
        
        return {
            'predictions': {
                'cardiovascular_disease_5yr': min(cv_risk, 0.8),
                'diabetes_5yr': min(diabetes_risk, 0.6),
                'hypertension_3yr': min(cv_risk * 0.8, 0.7)
            },
            'risk_factors': [
                {'factor': 'Age', 'impact': 'moderate' if age > 50 else 'low'},
                {'factor': 'BMI', 'impact': 'high' if bmi > 30 else 'moderate' if bmi > 25 else 'low'},
                {'factor': 'Smoking', 'impact': 'high' if smoking else 'none'}
            ],
            'recommendations': [
                'Maintain regular exercise routine',
                'Follow heart-healthy diet',
                'Monitor blood pressure regularly'
            ],
            'confidence_intervals': {
                'cardiovascular_disease_5yr': (max(cv_risk - 0.1, 0), min(cv_risk + 0.1, 1)),
                'diabetes_5yr': (max(diabetes_risk - 0.05, 0), min(diabetes_risk + 0.05, 1))
            }
        }

    async def _calculate_health_score(
        self,
        patient_profile: Dict[str, Any],
        risk_prediction: Dict[str, Any]
    ) -> float:
        """
        Calculate overall health score (0-100)
        """
        base_score = 85.0  # Start with good baseline
        
        # Deduct for age
        age = patient_profile.get('demographics', {}).get('age', 35)
        if age > 65:
            base_score -= 10
        elif age > 50:
            base_score -= 5
        
        # Deduct for predicted risks
        predictions = risk_prediction.get('predictions', {})
        for condition, risk in predictions.items():
            base_score -= risk * 20  # Each 10% risk reduces score by 2 points
        
        # Deduct for chronic conditions
        chronic_conditions = len(patient_profile.get('chronic_conditions', []))
        base_score -= chronic_conditions * 5
        
        # Lifestyle factors
        lifestyle = patient_profile.get('lifestyle', {})
        if lifestyle.get('smoking', False):
            base_score -= 15
        
        exercise_freq = lifestyle.get('exercise_per_week', 2)
        if exercise_freq >= 5:
            base_score += 5
        elif exercise_freq < 2:
            base_score -= 5
        
        return max(min(base_score, 100.0), 10.0)

    async def _fallback_health_prediction(
        self,
        patient_profile: Dict[str, Any]
    ) -> HealthPrediction:
        """
        Fallback health prediction when ML is unavailable
        """
        return HealthPrediction(
            health_score=75.0,
            risk_factors=[
                {'factor': 'General', 'impact': 'moderate'}
            ],
            predictions={
                'general_health_decline': 0.1
            },
            recommendations=[
                'Maintain regular checkups',
                'Follow healthy lifestyle',
                'Monitor key health metrics'
            ],
            confidence_intervals={
                'general_health_decline': (0.05, 0.15)
            }
        )

    def _calculate_historical_trends(self, historical_data: List[Dict]) -> Dict[str, float]:
        """
        Calculate trends from historical health data
        """
        if not historical_data:
            return {}
        
        # Simple trend calculation (would be more sophisticated in production)
        trends = {}
        
        # Group data by metric
        metrics = {}
        for record in historical_data:
            for key, value in record.items():
                if isinstance(value, (int, float)):
                    if key not in metrics:
                        metrics[key] = []
                    metrics[key].append(value)
        
        # Calculate trend for each metric
        for metric, values in metrics.items():
            if len(values) >= 2:
                # Simple linear trend
                x = list(range(len(values)))
                trend = np.polyfit(x, values, 1)[0]  # Slope
                trends[f'{metric}_trend'] = float(trend)
        
        return trends

    async def _prepare_time_series_features(
        self,
        vital_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Prepare time series features for vital signs analysis
        """
        if not vital_data:
            return {}
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(vital_data)
        
        features = {}
        
        # Process each vital sign
        vital_signs = ['heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                      'temperature', 'respiratory_rate', 'oxygen_saturation']
        
        for vital in vital_signs:
            if vital in df.columns:
                values = df[vital].dropna()
                if len(values) > 0:
                    features[f'{vital}_mean'] = float(values.mean())
                    features[f'{vital}_std'] = float(values.std())
                    features[f'{vital}_trend'] = float(np.polyfit(range(len(values)), values, 1)[0])
                    features[f'{vital}_latest'] = float(values.iloc[-1])
        
        return features

    async def _analyze_vital_trends_ml(
        self,
        features: Dict[str, Any],
        patient_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze vital trends using ML (mock implementation)
        """
        # Mock analysis - in production would call SageMaker endpoint
        trends = {}
        anomalies = []
        alerts = []
        
        # Check for concerning trends
        for key, value in features.items():
            if 'heart_rate' in key and 'mean' in key and value > 100:
                trends['heart_rate'] = 'elevated'
                alerts.append('Elevated average heart rate detected')
            elif 'blood_pressure_systolic' in key and 'mean' in key and value > 140:
                trends['blood_pressure'] = 'hypertensive'
                alerts.append('Hypertensive blood pressure pattern detected')
        
        return {
            'trends': trends,
            'anomalies': anomalies,
            'future_predictions': {},
            'recommendations': ['Monitor vital signs closely', 'Consult healthcare provider'],
            'alerts': alerts
        }

    async def _fallback_vital_analysis(
        self,
        vital_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fallback vital analysis
        """
        return {
            'trends': {},
            'anomalies': [],
            'predictions': {},
            'recommendations': ['Continue monitoring vital signs'],
            'alert_conditions': []
        }