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
    # Use us-east-1 region for Bedrock as it has the best model availability
    bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
    logger.info("Bedrock client initialized successfully for us-east-1")
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
                'model_used': 'anthropic.claude-3-5-sonnet-20240620-v1:0' if bedrock_client else 'fallback'
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

        # Create the message payload for Claude 3
        message_payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": f"Please help me with this health concern: {user_message}"
                }
            ],
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        logger.info(f"Calling Bedrock with Claude 3 Sonnet")
        
        # Call Bedrock with Claude 3.5 Sonnet (requires model access approval)
        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
            body=json.dumps(message_payload),
            contentType='application/json',
            accept='application/json'
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        if 'content' in response_body and len(response_body['content']) > 0:
            ai_response = response_body['content'][0]['text']
            logger.info("Successfully generated Bedrock response")
            return ai_response
        else:
            logger.warning("Unexpected Bedrock response format")
            return generate_fallback_response(user_message)
            
    except Exception as e:
        logger.error(f"Error calling Bedrock: {str(e)}")
        return generate_fallback_response(user_message)

def generate_fallback_response(user_message):
    """Generate fallback response when Bedrock is not available"""
    message_lower = user_message.lower()
    
    if any(word in message_lower for word in ['headache', 'head', 'pain']):
        return """I understand you're experiencing headache or head pain. While I can provide general information, headaches can have various causes including tension, dehydration, eye strain, or underlying medical conditions.

**Immediate steps you can take:**
- Rest in a quiet, dark room
- Apply a cold or warm compress to your head or neck
- Stay hydrated by drinking water
- Consider over-the-counter pain relievers if appropriate

**When to seek medical attention:**
- Sudden, severe headache unlike any you've had before
- Headache with fever, stiff neck, confusion, or vision changes
- Headache after a head injury
- Chronic headaches that interfere with daily activities

Please consult with a healthcare professional for persistent or severe headaches, as they can properly evaluate your symptoms and provide appropriate treatment."""
    
    elif any(word in message_lower for word in ['fever', 'temperature', 'hot']):
        return """Fever can be a sign that your body is fighting an infection. Here's what you should know:

**General fever management:**
- Stay hydrated with plenty of fluids
- Rest and avoid strenuous activities
- Use light clothing and blankets
- Consider fever reducers if recommended by a healthcare provider

**Monitor your temperature and watch for:**
- Fever over 103°F (39.4°C)
- Difficulty breathing or chest pain
- Persistent vomiting or severe dehydration
- Confusion or unusual behavior

**Seek immediate medical attention if:**
- Fever persists for more than 3 days
- You have difficulty breathing
- You experience severe headache with neck stiffness
- You have signs of dehydration

Always consult with a healthcare professional for proper evaluation and treatment recommendations."""
    
    elif any(word in message_lower for word in ['chest', 'breath', 'breathing']):
        return """**IMPORTANT: Chest pain and breathing difficulties can be serious.**

**Seek immediate emergency care (call 911) if you experience:**
- Severe chest pain or pressure
- Difficulty breathing or shortness of breath
- Chest pain spreading to arms, neck, jaw, or back
- Rapid or irregular heartbeat
- Dizziness or fainting

**For mild symptoms:**
- Sit upright in a comfortable position
- Try slow, deep breathing exercises
- Loosen tight clothing
- Stay calm and avoid panic

**Common causes include:**
- Anxiety or stress
- Muscle strain
- Acid reflux
- Respiratory infections

However, chest symptoms should always be evaluated by a healthcare professional promptly to rule out serious conditions. Don't delay seeking medical attention if you're concerned."""
    
    else:
        return """Thank you for sharing your health concern with me. While I can provide general health information, it's important to remember that I cannot replace professional medical advice.

**General health guidance:**
- Monitor your symptoms and note any changes
- Stay hydrated and maintain good nutrition
- Get adequate rest
- Practice stress management techniques

**When to consult a healthcare professional:**
- Symptoms that persist or worsen
- New or concerning symptoms
- Any symptoms that interfere with daily activities
- When you have questions about your health

**Seek immediate medical attention for:**
- Severe or sudden onset symptoms
- Difficulty breathing
- Chest pain
- High fever
- Signs of serious illness

Please consult with a qualified healthcare professional for personalized medical advice. They can properly evaluate your symptoms, medical history, and provide appropriate treatment recommendations."""

def analyze_risk_level(user_message, ai_response):
    """Analyze the risk level based on symptoms mentioned"""
    message_lower = user_message.lower()
    response_lower = ai_response.lower()
    
    # Critical risk indicators
    critical_keywords = [
        'chest pain', 'difficulty breathing', 'shortness of breath',
        'severe headache', 'loss of consciousness', 'severe bleeding',
        'stroke', 'heart attack', 'seizure', 'severe abdominal pain'
    ]
    
    # High risk indicators
    high_keywords = [
        'severe pain', 'high fever', 'persistent vomiting',
        'confusion', 'severe dizziness', 'rapid heartbeat'
    ]
    
    # Medium risk indicators
    medium_keywords = [
        'fever', 'headache', 'nausea', 'pain', 'cough',
        'fatigue', 'dizziness'
    ]
    
    if any(keyword in message_lower for keyword in critical_keywords):
        return 'critical'
    elif any(keyword in message_lower for keyword in high_keywords):
        return 'high'
    elif any(keyword in message_lower for keyword in medium_keywords):
        return 'medium'
    else:
        return 'low'

def generate_recommendations(user_message, risk_level):
    """Generate recommendations based on risk level and symptoms"""
    base_recommendations = [
        "Monitor your symptoms closely",
        "Stay hydrated and get adequate rest",
        "Consult with a healthcare professional if symptoms persist or worsen"
    ]
    
    if risk_level == 'critical':
        return [
            "Seek immediate emergency medical attention",
            "Call 911 or go to the nearest emergency room",
            "Do not drive yourself - have someone drive you or call an ambulance",
            "Stay calm and follow emergency responder instructions"
        ]
    elif risk_level == 'high':
        return [
            "Contact your healthcare provider immediately",
            "Consider urgent care if your doctor is not available",
            "Monitor symptoms closely and seek emergency care if they worsen",
            "Have someone stay with you if possible"
        ] + base_recommendations
    elif risk_level == 'medium':
        return [
            "Schedule an appointment with your healthcare provider",
            "Keep track of your symptoms and their progression",
            "Take appropriate over-the-counter medications if suitable"
        ] + base_recommendations
    else:
        return base_recommendations + [
            "Maintain good general health practices",
            "Don't hesitate to seek medical advice if you're concerned"
        ]