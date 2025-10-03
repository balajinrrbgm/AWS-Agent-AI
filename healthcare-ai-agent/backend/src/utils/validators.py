import re
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    pass

class DataValidator:
    """
    Comprehensive data validation utilities
    """
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address format
        """
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Validate phone number format
        """
        if not phone:
            return False
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check if it's a valid length (10-15 digits)
        return len(digits_only) >= 10 and len(digits_only) <= 15
    
    @staticmethod
    def validate_age(age: Any) -> bool:
        """
        Validate age value
        """
        try:
            age_int = int(age)
            return 0 <= age_int <= 150
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_date_of_birth(dob: str) -> bool:
        """
        Validate date of birth
        """
        if not dob:
            return False
        
        try:
            # Try parsing different date formats
            formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S']
            
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(dob, fmt).date()
                    # Check if date is reasonable (not in future, not too old)
                    today = date.today()
                    if parsed_date <= today and (today - parsed_date).days <= 150 * 365:
                        return True
                except ValueError:
                    continue
            
            return False
        except Exception:
            return False
    
    @staticmethod
    def validate_gender(gender: str) -> bool:
        """
        Validate gender value
        """
        if not gender:
            return False
        
        valid_genders = {'male', 'female', 'other', 'prefer not to say', 'non-binary'}
        return gender.lower().strip() in valid_genders
    
    @staticmethod
    def validate_blood_type(blood_type: str) -> bool:
        """
        Validate blood type
        """
        if not blood_type:
            return False
        
        valid_types = {'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'}
        return blood_type.strip().upper() in valid_types
    
    @staticmethod
    def validate_vital_signs(vitals: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate vital signs data
        """
        errors = {}
        
        # Blood pressure validation
        if 'systolic_bp' in vitals or 'diastolic_bp' in vitals:
            systolic = vitals.get('systolic_bp')
            diastolic = vitals.get('diastolic_bp')
            
            try:
                if systolic is not None:
                    systolic = float(systolic)
                    if not (60 <= systolic <= 250):
                        errors.setdefault('systolic_bp', []).append('Systolic BP must be between 60-250 mmHg')
                
                if diastolic is not None:
                    diastolic = float(diastolic)
                    if not (30 <= diastolic <= 150):
                        errors.setdefault('diastolic_bp', []).append('Diastolic BP must be between 30-150 mmHg')
                
                if systolic is not None and diastolic is not None and diastolic >= systolic:
                    errors.setdefault('blood_pressure', []).append('Systolic BP must be higher than diastolic BP')
                    
            except (ValueError, TypeError):
                errors.setdefault('blood_pressure', []).append('Blood pressure values must be numeric')
        
        # Heart rate validation
        if 'heart_rate' in vitals:
            try:
                hr = float(vitals['heart_rate'])
                if not (30 <= hr <= 220):
                    errors.setdefault('heart_rate', []).append('Heart rate must be between 30-220 bpm')
            except (ValueError, TypeError):
                errors.setdefault('heart_rate', []).append('Heart rate must be numeric')
        
        # Temperature validation
        if 'temperature' in vitals:
            try:
                temp = float(vitals['temperature'])
                # Assuming Celsius, but could add unit detection
                if not (35.0 <= temp <= 42.0):
                    errors.setdefault('temperature', []).append('Temperature must be between 35-42°C')
            except (ValueError, TypeError):
                errors.setdefault('temperature', []).append('Temperature must be numeric')
        
        # Respiratory rate validation
        if 'respiratory_rate' in vitals:
            try:
                rr = float(vitals['respiratory_rate'])
                if not (8 <= rr <= 60):
                    errors.setdefault('respiratory_rate', []).append('Respiratory rate must be between 8-60 breaths/min')
            except (ValueError, TypeError):
                errors.setdefault('respiratory_rate', []).append('Respiratory rate must be numeric')
        
        # Oxygen saturation validation
        if 'oxygen_saturation' in vitals:
            try:
                o2_sat = float(vitals['oxygen_saturation'])
                if not (70 <= o2_sat <= 100):
                    errors.setdefault('oxygen_saturation', []).append('Oxygen saturation must be between 70-100%')
            except (ValueError, TypeError):
                errors.setdefault('oxygen_saturation', []).append('Oxygen saturation must be numeric')
        
        return errors
    
    @staticmethod
    def validate_symptoms(symptoms: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Validate symptoms data
        """
        errors = {}
        
        if not isinstance(symptoms, list):
            errors['symptoms'] = ['Symptoms must be a list']
            return errors
        
        for i, symptom in enumerate(symptoms):
            if not isinstance(symptom, dict):
                errors.setdefault(f'symptom_{i}', []).append('Each symptom must be an object')
                continue
            
            # Validate symptom name
            if not symptom.get('name'):
                errors.setdefault(f'symptom_{i}', []).append('Symptom name is required')
            
            # Validate severity
            severity = symptom.get('severity')
            if severity and severity not in ['mild', 'moderate', 'severe']:
                errors.setdefault(f'symptom_{i}', []).append('Severity must be mild, moderate, or severe')
            
            # Validate duration
            if 'duration_days' in symptom:
                try:
                    duration = float(symptom['duration_days'])
                    if duration < 0 or duration > 365:
                        errors.setdefault(f'symptom_{i}', []).append('Duration must be between 0-365 days')
                except (ValueError, TypeError):
                    errors.setdefault(f'symptom_{i}', []).append('Duration must be numeric')
        
        return errors
    
    @staticmethod
    def validate_medication(medication: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate medication data
        """
        errors = {}
        
        # Required fields
        if not medication.get('name'):
            errors.setdefault('name', []).append('Medication name is required')
        
        # Dosage validation
        if 'dosage' in medication and medication['dosage']:
            dosage = str(medication['dosage']).strip()
            if not re.match(r'^\d+(\.\d+)?\s*(mg|g|ml|mcg|units?)(\s+.*)?$', dosage, re.IGNORECASE):
                errors.setdefault('dosage', []).append('Dosage format should include amount and unit (e.g., "10 mg twice daily")')
        
        # Frequency validation
        if 'frequency' in medication and medication['frequency']:
            frequency = medication['frequency'].lower().strip()
            valid_frequencies = [
                'once daily', 'twice daily', 'three times daily', 'four times daily',
                'every 4 hours', 'every 6 hours', 'every 8 hours', 'every 12 hours',
                'as needed', 'prn', 'once weekly', 'once monthly'
            ]
            
            if not any(freq in frequency for freq in valid_frequencies):
                errors.setdefault('frequency', []).append('Please specify a clear frequency (e.g., "twice daily", "every 8 hours")')
        
        return errors
    
    @staticmethod
    def validate_appointment_data(appointment: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate appointment data
        """
        errors = {}
        
        # Required fields
        required_fields = ['patient_id', 'appointment_date', 'appointment_time', 'type']
        for field in required_fields:
            if not appointment.get(field):
                errors.setdefault(field, []).append(f'{field.replace("_", " ").title()} is required')
        
        # Date validation
        if appointment.get('appointment_date'):
            try:
                appt_date = datetime.strptime(appointment['appointment_date'], '%Y-%m-%d').date()
                if appt_date < date.today():
                    errors.setdefault('appointment_date', []).append('Appointment date cannot be in the past')
            except ValueError:
                errors.setdefault('appointment_date', []).append('Invalid date format (use YYYY-MM-DD)')
        
        # Time validation
        if appointment.get('appointment_time'):
            try:
                datetime.strptime(appointment['appointment_time'], '%H:%M')
            except ValueError:
                errors.setdefault('appointment_time', []).append('Invalid time format (use HH:MM)')
        
        # Type validation
        if appointment.get('type'):
            valid_types = [
                'consultation', 'follow-up', 'check-up', 'emergency',
                'lab_test', 'imaging', 'vaccination', 'screening'
            ]
            if appointment['type'].lower() not in valid_types:
                errors.setdefault('type', []).append(f'Invalid appointment type. Valid types: {", ".join(valid_types)}')
        
        return errors
    
    @staticmethod
    def validate_emergency_level(level: str) -> bool:
        """
        Validate emergency level
        """
        if not level:
            return False
        
        valid_levels = {'low', 'medium', 'high', 'critical'}
        return level.lower().strip() in valid_levels
    
    @staticmethod
    def sanitize_medical_text(text: str) -> str:
        """
        Sanitize medical text input
        """
        if not text:
            return ""
        
        # Remove potentially harmful content while preserving medical terminology
        text = text.strip()
        
        # Remove HTML tags but preserve line breaks
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Limit length
        if len(text) > 5000:
            text = text[:5000] + "..."
        
        return text
    
    @staticmethod
    def validate_lab_results(results: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Validate laboratory results data
        """
        errors = {}
        
        if not isinstance(results, list):
            errors['lab_results'] = ['Lab results must be a list']
            return errors
        
        for i, result in enumerate(results):
            if not isinstance(result, dict):
                errors.setdefault(f'result_{i}', []).append('Each result must be an object')
                continue
            
            # Validate test name
            if not result.get('test_name'):
                errors.setdefault(f'result_{i}', []).append('Test name is required')
            
            # Validate value and unit
            if 'value' in result:
                try:
                    float(result['value'])  # Check if numeric
                except (ValueError, TypeError):
                    # Allow non-numeric values like "Positive", "Negative"
                    pass
            
            # Validate reference range if provided
            if result.get('reference_range'):
                ref_range = result['reference_range']
                if not re.match(r'^[\d\.\-\s<>]+$', str(ref_range)):
                    # Allow text ranges like "Normal", "Abnormal"
                    pass
        
        return errors

# Global validator instance
validator = DataValidator()

def validate_patient_data(patient_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Comprehensive patient data validation
    """
    errors = {}
    
    # Personal information validation
    if not validator.validate_email(patient_data.get('email', '')):
        errors.setdefault('email', []).append('Invalid email address format')
    
    if patient_data.get('phone') and not validator.validate_phone(patient_data['phone']):
        errors.setdefault('phone', []).append('Invalid phone number format')
    
    if patient_data.get('age') and not validator.validate_age(patient_data['age']):
        errors.setdefault('age', []).append('Age must be between 0-150 years')
    
    if patient_data.get('date_of_birth') and not validator.validate_date_of_birth(patient_data['date_of_birth']):
        errors.setdefault('date_of_birth', []).append('Invalid date of birth')
    
    if patient_data.get('gender') and not validator.validate_gender(patient_data['gender']):
        errors.setdefault('gender', []).append('Invalid gender value')
    
    if patient_data.get('blood_type') and not validator.validate_blood_type(patient_data['blood_type']):
        errors.setdefault('blood_type', []).append('Invalid blood type')
    
    # Vital signs validation
    if patient_data.get('vital_signs'):
        vital_errors = validator.validate_vital_signs(patient_data['vital_signs'])
        errors.update(vital_errors)
    
    # Symptoms validation
    if patient_data.get('symptoms'):
        symptom_errors = validator.validate_symptoms(patient_data['symptoms'])
        errors.update(symptom_errors)
    
    return errors

def validate_medical_input(input_text: str) -> bool:
    """
    Validate medical query input
    """
    if not input_text or not isinstance(input_text, str):
        return False
    
    # Basic length validation
    if len(input_text.strip()) < 3 or len(input_text) > 5000:
        return False
    
    # Check for potentially malicious content
    malicious_patterns = [
        '<script', 'javascript:', 'onload=', 'eval(', 
        'document.cookie', 'window.location', '<?php'
    ]
    
    input_lower = input_text.lower()
    for pattern in malicious_patterns:
        if pattern in input_lower:
            return False
    
    return True