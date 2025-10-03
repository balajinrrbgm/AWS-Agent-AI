import { useState, useCallback } from 'react';

// Types
interface ChatMessage {
  session_id: string;
  content: string;
  timestamp: Date;
  message_type: 'user' | 'assistant';
}

interface ChatResponse {
  response: string;
  confidence: number;
  recommendations?: string[];
  risk_assessment?: 'low' | 'medium' | 'high' | 'critical';
  requires_human_review?: boolean;
  follow_up_questions?: string[];
  session_id: string;
  timestamp: string;
}

interface Patient {
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  medical_history?: string[];
  current_medications?: string[];
  allergies?: string[];
  emergency_contact?: string;
}

interface HealthAPIHook {
  sendChatMessage: (message: ChatMessage) => Promise<ChatResponse>;
  getPatients: () => Promise<Patient[]>;
  createPatient: (patient: Omit<Patient, 'patient_id'>) => Promise<Patient>;
  updatePatient: (patientId: string, updates: Partial<Patient>) => Promise<Patient>;
  deletePatient: (patientId: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://mc6u6jct2j.execute-api.eu-central-1.amazonaws.com/prod';

export const useHealthAPI = (): HealthAPIHook => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Helper function to make API calls
  const apiCall = useCallback(async <T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Send chat message
  const sendChatMessage = useCallback(async (message: ChatMessage): Promise<ChatResponse> => {
    try {
      const response = await apiCall<ChatResponse>('/api/v1/query', {
        method: 'POST',
        body: JSON.stringify({
          session_id: message.session_id,
          content: message.content,
          timestamp: message.timestamp.toISOString(),
          message_type: message.message_type,
        }),
      });

      return response;
    } catch (error) {
      // Fallback response for demo purposes
      console.warn('API call failed, using fallback response:', error);
      
      const fallbackResponse: ChatResponse = {
        response: "I'm here to help with your healthcare questions. However, I'm currently experiencing connectivity issues. Please note that for any urgent medical concerns, you should contact your healthcare provider or emergency services immediately.",
        confidence: 0.5,
        recommendations: [
          "For urgent medical concerns, contact your healthcare provider",
          "For emergencies, call 911 or go to the nearest emergency room",
          "Try refreshing the page or check your internet connection"
        ],
        risk_assessment: 'low',
        requires_human_review: true,
        session_id: message.session_id,
        timestamp: new Date().toISOString(),
      };

      return fallbackResponse;
    }
  }, [apiCall]);

  // Get all patients
  const getPatients = useCallback(async (): Promise<Patient[]> => {
    try {
      return await apiCall<Patient[]>('/api/v1/patients');
    } catch (error) {
      console.warn('Failed to fetch patients:', error);
      return [];
    }
  }, [apiCall]);

  // Create new patient
  const createPatient = useCallback(async (patient: Omit<Patient, 'patient_id'>): Promise<Patient> => {
    return await apiCall<Patient>('/api/v1/patients', {
      method: 'POST',
      body: JSON.stringify(patient),
    });
  }, [apiCall]);

  // Update patient
  const updatePatient = useCallback(async (patientId: string, updates: Partial<Patient>): Promise<Patient> => {
    return await apiCall<Patient>(`/api/v1/patients/${patientId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }, [apiCall]);

  // Delete patient
  const deletePatient = useCallback(async (patientId: string): Promise<void> => {
    await apiCall<void>(`/api/v1/patients/${patientId}`, {
      method: 'DELETE',
    });
  }, [apiCall]);

  return {
    sendChatMessage,
    getPatients,
    createPatient,
    updatePatient,
    deletePatient,
    isLoading,
    error,
  };
};

export default useHealthAPI;