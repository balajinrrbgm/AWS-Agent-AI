import boto3
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import logging

from src.models.schemas import AppointmentRequest, Appointment, Provider

logger = logging.getLogger(__name__)

class AppointmentService:
    """
    Service for managing medical appointments
    """
    
    def __init__(self, dynamodb_resource):
        self.dynamodb = dynamodb_resource
        self.table_name = "healthcare-appointments"
        try:
            self.table = self.dynamodb.Table(self.table_name)
        except Exception as e:
            logger.warning(f"DynamoDB table not available: {e}. Using mock mode.")
            self.table = None
            self._mock_appointments = {}

    async def schedule_appointment(self, appointment_request: AppointmentRequest) -> Appointment:
        """
        Schedule a new appointment
        """
        try:
            # Generate appointment ID
            appointment_id = str(uuid.uuid4())
            
            # Find available provider (mock implementation)
            provider = await self._find_available_provider(
                appointment_request.specialty,
                appointment_request.preferred_date,
                appointment_request.preferred_time
            )
            
            # Schedule time (mock logic)
            if appointment_request.preferred_date:
                scheduled_time = datetime.combine(
                    appointment_request.preferred_date,
                    datetime.strptime(appointment_request.preferred_time or "09:00", "%H:%M").time()
                )
            else:
                # Schedule for next available slot (mock)
                scheduled_time = datetime.now() + timedelta(days=3)
            
            # Create appointment
            appointment = Appointment(
                appointment_id=appointment_id,
                patient_id=appointment_request.patient_id,
                provider=provider,
                scheduled_time=scheduled_time,
                reason=appointment_request.reason,
                status="scheduled",
                confirmation_number=f"CONF-{appointment_id[:8].upper()}"
            )
            
            if self.table:
                # Save to DynamoDB
                appointment_dict = appointment.dict()
                # Convert datetime to ISO string
                appointment_dict['scheduled_time'] = scheduled_time.isoformat()
                appointment_dict['created_at'] = datetime.utcnow().isoformat()
                
                self.table.put_item(Item=appointment_dict)
                logger.info(f"Appointment scheduled: {appointment_id}")
            else:
                # Mock mode
                self._mock_appointments[appointment_id] = appointment.dict()
                logger.info(f"Appointment scheduled (mock): {appointment_id}")
            
            return appointment
            
        except Exception as e:
            logger.error(f"Error scheduling appointment: {str(e)}")
            raise

    async def get_patient_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Get all appointments for a patient
        """
        try:
            if self.table:
                # Query using GSI
                response = self.table.query(
                    IndexName='patient-index',
                    KeyConditionExpression='patient_id = :pid',
                    ExpressionAttributeValues={':pid': patient_id}
                )
                
                appointments = response.get('Items', [])
                logger.info(f"Retrieved {len(appointments)} appointments for patient {patient_id}")
                return appointments
            else:
                # Mock mode
                patient_appointments = [
                    apt for apt in self._mock_appointments.values()
                    if apt.get('patient_id') == patient_id
                ]
                
                # Add some mock appointments if none exist
                if not patient_appointments:
                    mock_appointment = {
                        "appointment_id": "mock-apt-1",
                        "patient_id": patient_id,
                        "provider": {
                            "name": "Dr. Sarah Johnson",
                            "specialty": "Internal Medicine",
                            "location": "Downtown Medical Center",
                            "phone": "+1-555-0123"
                        },
                        "scheduled_time": (datetime.now() + timedelta(days=7)).isoformat(),
                        "reason": "Annual checkup",
                        "status": "scheduled",
                        "confirmation_number": "CONF-MOCK123"
                    }
                    patient_appointments = [mock_appointment]
                
                return patient_appointments
                
        except Exception as e:
            logger.error(f"Error retrieving appointments: {str(e)}")
            return []

    async def cancel_appointment(self, appointment_id: str, reason: str = "") -> bool:
        """
        Cancel an appointment
        """
        try:
            if self.table:
                response = self.table.update_item(
                    Key={'appointment_id': appointment_id},
                    UpdateExpression='SET #status = :status, cancellation_reason = :reason, updated_at = :updated',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'cancelled',
                        ':reason': reason,
                        ':updated': datetime.utcnow().isoformat()
                    },
                    ReturnValues='UPDATED_NEW'
                )
                
                logger.info(f"Appointment cancelled: {appointment_id}")
                return True
            else:
                # Mock mode
                if appointment_id in self._mock_appointments:
                    self._mock_appointments[appointment_id]['status'] = 'cancelled'
                    logger.info(f"Appointment cancelled (mock): {appointment_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling appointment: {str(e)}")
            return False

    async def reschedule_appointment(
        self, 
        appointment_id: str, 
        new_date: datetime,
        new_time: str = None
    ) -> bool:
        """
        Reschedule an appointment
        """
        try:
            if new_time:
                new_scheduled_time = datetime.combine(
                    new_date.date(),
                    datetime.strptime(new_time, "%H:%M").time()
                )
            else:
                new_scheduled_time = new_date
            
            if self.table:
                response = self.table.update_item(
                    Key={'appointment_id': appointment_id},
                    UpdateExpression='SET scheduled_time = :time, updated_at = :updated',
                    ExpressionAttributeValues={
                        ':time': new_scheduled_time.isoformat(),
                        ':updated': datetime.utcnow().isoformat()
                    },
                    ReturnValues='UPDATED_NEW'
                )
                
                logger.info(f"Appointment rescheduled: {appointment_id}")
                return True
            else:
                # Mock mode
                if appointment_id in self._mock_appointments:
                    self._mock_appointments[appointment_id]['scheduled_time'] = new_scheduled_time.isoformat()
                    logger.info(f"Appointment rescheduled (mock): {appointment_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error rescheduling appointment: {str(e)}")
            return False

    async def get_available_slots(
        self, 
        specialty: str, 
        date: datetime,
        provider_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get available appointment slots
        """
        try:
            # Mock implementation - in production, this would check actual provider schedules
            available_slots = []
            
            # Generate mock available slots
            for hour in range(9, 17):  # 9 AM to 5 PM
                if hour != 12:  # Skip lunch hour
                    slot_time = datetime.combine(date.date(), datetime.min.time().replace(hour=hour))
                    available_slots.append({
                        "time": slot_time.isoformat(),
                        "duration_minutes": 30,
                        "available": True,
                        "provider_id": provider_id or "mock-provider-1"
                    })
            
            logger.info(f"Generated {len(available_slots)} available slots for {specialty}")
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting available slots: {str(e)}")
            return []

    async def _find_available_provider(
        self, 
        specialty: str, 
        preferred_date: datetime = None,
        preferred_time: str = None
    ) -> Provider:
        """
        Find an available provider for the given specialty
        """
        # Mock provider database
        mock_providers = {
            "cardiology": [
                {
                    "name": "Dr. Michael Chen",
                    "specialty": "Cardiology",
                    "location": "Heart Center - Downtown",
                    "phone": "+1-555-0101"
                },
                {
                    "name": "Dr. Sarah Williams",
                    "specialty": "Cardiology", 
                    "location": "Cardiac Care Clinic",
                    "phone": "+1-555-0102"
                }
            ],
            "internal medicine": [
                {
                    "name": "Dr. James Rodriguez",
                    "specialty": "Internal Medicine",
                    "location": "Primary Care Associates",
                    "phone": "+1-555-0201"
                }
            ],
            "dermatology": [
                {
                    "name": "Dr. Lisa Thompson",
                    "specialty": "Dermatology",
                    "location": "Skin Health Center",
                    "phone": "+1-555-0301"
                }
            ]
        }
        
        # Default provider if specialty not found
        default_provider = {
            "name": "Dr. John Smith",
            "specialty": specialty.title(),
            "location": "General Medical Center",
            "phone": "+1-555-0999"
        }
        
        specialty_lower = specialty.lower()
        providers = mock_providers.get(specialty_lower, [default_provider])
        
        # Return first available provider (in production, check actual availability)
        selected_provider = providers[0]
        
        return Provider(**selected_provider)

    async def send_appointment_reminder(self, appointment_id: str) -> bool:
        """
        Send appointment reminder to patient
        """
        try:
            # In production, this would integrate with SES, SNS, or third-party services
            logger.info(f"Appointment reminder sent for: {appointment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending appointment reminder: {str(e)}")
            return False

    async def get_appointment_by_id(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get appointment details by ID
        """
        try:
            if self.table:
                response = self.table.get_item(Key={'appointment_id': appointment_id})
                
                if 'Item' in response:
                    return response['Item']
                else:
                    return None
            else:
                # Mock mode
                return self._mock_appointments.get(appointment_id)
                
        except Exception as e:
            logger.error(f"Error retrieving appointment: {str(e)}")
            return None