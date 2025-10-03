import json
import boto3
from datetime import datetime
import logging
import re

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Bedrock client
bedrock_client = None
try:
    bedrock_client = boto3.client('bedrock-runtime', region_name='eu-central-1')
    logger.info("Bedrock client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Bedrock client: {str(e)}")

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Get the HTTP method and path
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    
    # Health check endpoint
    if path == '/health':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': json.dumps({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'service': 'healthcare-ai-agent',
                'version': '2.0.0',
                'bedrock_available': bedrock_client is not None
            })
        }
    
    # Chat/Query endpoint
    if path == '/api/v1/query' and http_method == 'POST':
        try:
            body = json.loads(event.get('body', '{}'))
            user_message = body.get('content', '')
            session_id = body.get('session_id', 'default-session')
            
            logger.info(f"Processing chat request for session: {session_id}")
            
            # Generate AI response using Bedrock
            ai_response = generate_bedrock_response(user_message)
            
            # Analyze risk level
            risk_level = analyze_risk_level(user_message, ai_response)
            
            # Generate recommendations
            recommendations = generate_recommendations(user_message, risk_level)
            
            response_data = {
                'response': ai_response,
                'confidence': 0.95,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'risk_assessment': risk_level,
                'recommendations': recommendations,
                'requires_human_review': risk_level in ['high', 'critical'],
                'model_used': 'anthropic.claude-3-sonnet-20240229-v1:0' if bedrock_client else 'fallback'
            }
            
            logger.info(f"Generated response with risk level: {risk_level}")
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                },
                'body': json.dumps(response_data)
            }
        except Exception as e:
            logger.error(f"Error processing chat request: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Internal server error',
                    'message': str(e),
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })
            }
    
    # Patients endpoint
    if path == '/api/v1/patients' and http_method == 'GET':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'patients': [
                    {
                        'patient_id': 'demo-patient-1',
                        'name': 'Demo Patient',
                        'age': 35,
                        'gender': 'Other',
                        'last_visit': '2025-09-15',
                        'risk_level': 'low'
                    }
                ],
                'total': 1
            })
        }
    
    # Default response
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'Healthcare AI Agent API v2.0',
            'version': '2.0.0',
            'endpoints': {
                'health': 'GET /health',
                'chat': 'POST /api/v1/query',
                'patients': 'GET /api/v1/patients'
            },
            'features': [
                'Amazon Bedrock Claude 3 Sonnet Integration',
                'Advanced Risk Assessment',
                'Intelligent Recommendations',
                'Medical Context Understanding'
            ]
        })
    }

def generate_bedrock_response(user_message):
    """Generate response using Amazon Bedrock Claude 3 Sonnet"""
    if not bedrock_client:
        logger.warning("Bedrock client not available, using fallback response")
        return generate_fallback_response(user_message)
    
    try:
        # Prepare the prompt for Claude 3
        system_prompt = """You are a highly knowledgeable healthcare AI assistant. Your role is to:

1. Provide accurate, evidence-based health information
2. Offer compassionate and helpful guidance
3. Assess symptom severity and recommend appropriate action
4. Always emphasize the importance of professional medical care
5. Be clear about limitations and when to seek immediate help

Guidelines:
- Never provide definitive diagnoses
- Always recommend consulting healthcare professionals for serious concerns
- Provide clear, actionable advice
- Be empathetic and understanding
- Focus on symptom management and general wellness guidance
- Flag urgent situations that require immediate medical attention

Remember: You are providing general health information, not medical diagnosis or treatment."""

        user_prompt = f"""Human: {user_message}

Please provide a helpful, accurate response about this health concern. Include:
1. Understanding of the symptoms/concern
2. General information about potential causes
3. Recommended actions or self-care measures
4. When to seek professional medical help
5. Any warning signs to watch for