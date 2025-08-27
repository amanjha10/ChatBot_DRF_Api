# chatbot/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import uuid
import json
import re
import os

from .models import ChatSession, UserProfile, ChatMessage, UploadedFile, RAGDocument
from .serializers import (
    ChatRequestSerializer, ChatResponseSerializer, UserProfileSerializer,
    ProfileCollectionRequestSerializer, PhoneValidationRequestSerializer,
    PhoneValidationResponseSerializer, ChatSessionSerializer, ChatMessageSerializer,
    FileUploadRequestSerializer, FileUploadResponseSerializer, UploadedFileSerializer
)
from .utils.phone_validator import validate_phone_number, validate_name, validate_email, validate_nepali_phone
from .utils.rag_system import rag_system
from .utils.file_handler import FileUploadHandler
from authentication.models import User
from admin_dashboard.models import Agent

# Constants from Flask reference
COUNTRIES = [
    'United States', 'Canada', 'United Kingdom', 'Australia',
    'Germany', 'France', 'Netherlands', 'New Zealand',
    'Singapore', 'Ireland', 'Japan', 'South Korea', 'Other'
]

COUNTRY_CODES = [
    {'code': '+977', 'country': 'Nepal', 'flag': '🇳🇵'},
    {'code': '+91', 'country': 'India', 'flag': '🇮🇳'},
    {'code': '+1', 'country': 'United States/Canada', 'flag': '🇺🇸🇨🇦'},
    {'code': '+44', 'country': 'United Kingdom', 'flag': '🇬🇧'},
    {'code': '+61', 'country': 'Australia', 'flag': '🇦🇺'},
    {'code': '+49', 'country': 'Germany', 'flag': '🇩🇪'},
    {'code': '+33', 'country': 'France', 'flag': '🇫🇷'},
    {'code': '+31', 'country': 'Netherlands', 'flag': '🇳🇱'},
    {'code': '+64', 'country': 'New Zealand', 'flag': '🇳🇿'},
    {'code': '+65', 'country': 'Singapore', 'flag': '🇸🇬'},
    {'code': '+353', 'country': 'Ireland', 'flag': '🇮🇪'},
    {'code': '+81', 'country': 'Japan', 'flag': '🇯🇵'},
    {'code': '+86', 'country': 'China', 'flag': '🇨🇳'},
    {'code': '+880', 'country': 'Bangladesh', 'flag': '🇧🇩'},
    {'code': '+94', 'country': 'Sri Lanka', 'flag': '🇱🇰'}
]

GREETING_KEYWORDS = [
    'hello', 'hi', 'hey', 'how are you', 'good morning', 'good afternoon',
    'good evening', 'greetings', "what's up", "how's it going", 'namaste'
]

def get_company_id_from_request(request):
    """Extract company_id from request - either from JWT token or request data"""
    company_id = None
    
    # First try to get from request data (for visitor chats with company context)
    if hasattr(request, 'data') and 'company_id' in request.data:
        company_id = request.data.get('company_id')
    
    # If not found, try to extract from JWT token (for agent/admin requests)
    if not company_id:
        try:
            jwt_auth = JWTAuthentication()
            auth_header = jwt_auth.get_header(request)
            if auth_header:
                raw_token = jwt_auth.get_raw_token(auth_header)
                if raw_token:
                    validated_token = jwt_auth.get_validated_token(raw_token)
                    user_id = validated_token['user_id']
                    user = User.objects.get(id=user_id)
                    
                    if user.role == User.Role.AGENT:
                        # Get company_id from agent profile
                        agent = Agent.objects.get(user=user)
                        company_id = agent.company_id
                    elif user.role in [User.Role.ADMIN, User.Role.SUPERADMIN]:
                        # Get company_id from user
                        company_id = user.company_id
        except Exception:
            # Catch all exceptions to prevent 500 errors
            pass
    
    return company_id

def get_or_create_session(session_id=None, company_id=None):
    """Get existing session or create new one with company_id"""
    if session_id and company_id:
        try:
            return ChatSession.objects.get(session_id=session_id, company_id=company_id)
        except ChatSession.DoesNotExist:
            pass
    
    # Create new session - company_id is required for new sessions
    if not company_id:
        raise ValueError("company_id is required for creating new chat sessions")
    
    new_session_id = str(uuid.uuid4())
    return ChatSession.objects.create(session_id=new_session_id, company_id=company_id)

def is_greeting_query(user_message):
    """Check if a message is a greeting"""
    msg = user_message.lower().strip()
    if msg in GREETING_KEYWORDS:
        return True
    for greeting in GREETING_KEYWORDS:
        if msg.startswith(greeting + ' '):
            return True
    return False

def get_rag_response(user_input):
    """Query RAG system for document-based answers"""
    try:
        result = rag_system.get_best_answer(user_input, min_score=0.2)  # Lowered minimum score
        if result:
            return result, result['score']
        return None, 0.0
    except Exception as e:
        print(f"Error in RAG response: {e}")
        return None, 0.0

@api_view(['POST'])
@permission_classes([AllowAny])
def chat_message_view(request):
    """
    Handle chat messages from users
    POST /api/chatbot/chat/
    
    Request:
    {
        "message": "Hello, I want to study abroad",
        "session_id": "optional_session_id",
        "context": "Initial conversation",
        "company_id": "COMP_123" // Required for visitor chats, or extracted from JWT for agents
    }
    
    Response:
    {
        "response": "Hello! I'd be happy to help...",
        "suggestions": ["🌍 Choose Country", "🎓 Browse Programs"],
        "type": "bot_response",
        "session_id": "session_uuid",
        "escalated": false
    }
    """
    serializer = ChatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user_message = serializer.validated_data.get('message', '')
    session_id = serializer.validated_data.get('session_id')
    context = serializer.validated_data.get('context', 'Initial conversation')
    attachment_ids = serializer.validated_data.get('attachment_ids', [])
    
    # Extract company_id from request (either from data or JWT token)
    company_id = get_company_id_from_request(request)
    if not company_id:
        return Response({
            'error': 'company_id is required. Please provide company_id in request data or authenticate with valid JWT token.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get or create session with company isolation
    try:
        chat_session = get_or_create_session(session_id, company_id)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create user message with attachments
    user_message_obj = ChatMessage.objects.create(
        session=chat_session,
        message_type='user',
        content=user_message if user_message else None,
        metadata={'context': context, 'has_attachments': bool(attachment_ids)}
    )
    
    # Attach files if provided
    if attachment_ids:
        try:
            uploaded_files = UploadedFile.objects.filter(
                id__in=attachment_ids,
                session=chat_session,
                company_id=company_id
            )
            user_message_obj.attachments.set(uploaded_files)
        except Exception as e:
            return Response({
                'error': f'Failed to attach files: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if session needs profile collection
    profile = chat_session.user_profile
    if not profile:
        # Handle profile collection for new users
        if not hasattr(chat_session, 'profile_collection_started') or chat_session.profile_collection_state == 'name':
            # First message - start profile collection with welcome
            if is_greeting_query(user_message) or not ChatMessage.objects.filter(session=chat_session, message_type='bot').exists():
                # Send welcome message and start profile collection
                welcome_response = {
                    'response': "Hello! 👋 Welcome to EduConsult. I'm here to help you with your study abroad journey.<br><br>To get started, I'll need to collect some information. What's your full name?",
                    'suggestions': ['Example: John Doe'],
                    'type': 'profile_collection',
                    'collecting': 'name',
                    'session_id': chat_session.session_id
                }
                
                # Log bot response
                ChatMessage.objects.create(
                    session=chat_session,
                    message_type='bot',
                    content=welcome_response['response'],
                    metadata={'source': 'profile_collection', 'type': 'welcome'}
                )
                
                return Response(welcome_response)
        
        # Continue with profile collection
        profile_response = handle_profile_collection(user_message, chat_session)
        if profile_response:
            # Log bot response
            metadata = {
                'source': 'profile_collection', 
                'type': profile_response['type']
            }
            if 'collecting' in profile_response:
                metadata['collecting'] = profile_response['collecting']
            if 'temp_data' in profile_response:
                metadata['temp_data'] = profile_response['temp_data']
                
            ChatMessage.objects.create(
                session=chat_session,
                message_type='bot',
                content=profile_response['response'],
                metadata=metadata
            )
            profile_response['session_id'] = chat_session.session_id
            return Response(profile_response)
    
    # Check if session is escalated to human
    if hasattr(chat_session, 'handoff'):
        return Response({
            'response': '',
            'suggestions': [],
            'type': 'human_handling',
            'escalated': True,
            'session_id': chat_session.session_id
        })
    
    # Handle menu navigation
    if user_message.lower() in ['explore countries', 'choose country', '🌍 choose country']:
        response = {
            'response': "Here are the top study destinations. Which country interests you?",
            'suggestions': [
                '🇺🇸 United States', '🇨🇦 Canada', '🇬🇧 United Kingdom',
                '🇦🇺 Australia', '🇩🇪 Germany', 'More countries', '🎓 Browse by Field'
            ],
            'type': 'country_selection',
            'session_id': chat_session.session_id
        }
    elif user_message.lower() in ['browse programs', '🎓 browse programs']:
        response = {
            'response': "What type of program are you interested in?",
            'suggestions': [
                '🎓 Undergraduate Programs', '🎓 Graduate Programs', '🎓 PhD Programs',
                '💼 MBA Programs', '🔬 Research Programs', 'Back to main menu'
            ],
            'type': 'program_selection',
            'session_id': chat_session.session_id
        }
    elif user_message.lower() in ['talk to advisor', '🗣️ talk to advisor', 'human agent'] or \
         any(phrase in user_message.lower() for phrase in ['talk to advisor', 'human advisor', 'speak to human', 'talk to human', 'human agent', 'real person', 'live agent']):
        response = escalate_to_human(chat_session, user_message)
    else:
        # Try RAG system first
        rag_result, rag_score = get_rag_response(user_message)
        
        if rag_result and rag_score > 0.2:  # Lowered threshold for better matching
            response = {
                'response': rag_result['answer'],
                'suggestions': ['🌍 Choose Country', '🎓 Browse Programs', '🗣️ Talk to Advisor'],
                'type': 'rag_response',
                'session_id': chat_session.session_id
            }
        elif is_greeting_query(user_message):
            response = {
                'response': "Hello! 👋 Welcome to EduConsult. I'm here to help you with your study abroad journey. How can I assist you today?",
                'suggestions': [
                    '🌍 Choose Country', '🎓 Browse Programs', 
                    '📚 Requirements', '💰 Scholarships', '🗣️ Talk to Advisor'
                ],
                'type': 'greeting_response',
                'session_id': chat_session.session_id
            }
        else:
            response = {
                'response': "I'd be happy to help you with your study abroad plans. Could you please tell me which country you're interested in or what specific information you need?",
                'suggestions': [
                    '🌍 Choose Country', '🎓 Browse Programs',
                    '📚 Requirements', '🗣️ Talk to Advisor'
                ],
                'type': 'clarification_needed',
                'session_id': chat_session.session_id
            }
    
    # Log bot response
    ChatMessage.objects.create(
        session=chat_session,
        message_type='bot',
        content=response['response'],
        metadata={'source': 'bot', 'type': response['type']}
    )
    
    # Add user message and attachments to response
    response['user_message'] = ChatMessageSerializer(user_message_obj).data
    if attachment_ids:
        response['attachments'] = [
            UploadedFileSerializer(file).data 
            for file in user_message_obj.attachments.all()
        ]
    
    return Response(response)

def handle_profile_collection(user_message, chat_session):
    """Handle user profile collection flow using session state"""
    # Check if profile already exists
    if chat_session.user_profile:
        return None
    
    # Get current collection state from session
    collecting_state = chat_session.profile_collection_state
    temp_data = chat_session.temp_profile_data or {}
    
    if collecting_state == 'name':
        # Validate name
        is_valid, error_msg = validate_name(user_message)
        if not is_valid:
            return {
                'response': f"I'm sorry, but {error_msg}. Please enter your full name:",
                'suggestions': [],
                'type': 'profile_collection',
                'collecting': 'name'
            }
        
        # Store name and move to next state
        temp_data['name'] = user_message.strip()
        chat_session.temp_profile_data = temp_data
        chat_session.profile_collection_state = 'country_code'
        chat_session.save()
        
        # Ask for country code
        country_suggestions = [f"{cc['code']} {cc['flag']} {cc['country']}" for cc in COUNTRY_CODES[:8]]
        
        return {
            'response': f"Nice to meet you, {user_message.strip()}! 👋<br><br>Now I need your phone number. Please first select your country code:",
            'suggestions': country_suggestions + ['Show more countries'],
            'type': 'profile_collection',
            'collecting': 'country_code',
            'temp_data': temp_data
        }
    
    elif collecting_state == 'country_code':
        # Extract country code from selection
        country_code = '+977'  # Default
        for cc in COUNTRY_CODES:
            if cc['code'] in user_message or cc['country'].lower() in user_message.lower():
                country_code = cc['code']
                break
        
        temp_data['country_code'] = country_code
        chat_session.temp_profile_data = temp_data
        chat_session.profile_collection_state = 'phone'
        chat_session.save()
        
        return {
            'response': f"Great! Now please enter your phone number (without the country code {country_code}):",
            'suggestions': ['Example: 9841234567'],
            'type': 'profile_collection',
            'collecting': 'phone',
            'temp_data': temp_data
        }
    
    elif collecting_state == 'phone':
        # Validate phone number
        country_code = temp_data.get('country_code', '+977')
        is_valid, error_msg = validate_phone_number(user_message, country_code)
        
        if not is_valid:
            return {
                'response': f"I'm sorry, but {error_msg}. Please enter a valid phone number:",
                'suggestions': ['Example: 9841234567'],
                'type': 'profile_collection',
                'collecting': 'phone',
                'temp_data': temp_data
            }
        
        temp_data['phone'] = f"{country_code}-{user_message.strip()}"
        chat_session.temp_profile_data = temp_data
        chat_session.profile_collection_state = 'email'
        chat_session.save()
        
        return {
            'response': "Perfect! Now, would you like to provide your email address? (You can skip this by typing 'skip')",
            'suggestions': ['Example: your.email@example.com', 'Skip'],
            'type': 'profile_collection',
            'collecting': 'email',
            'temp_data': temp_data
        }
    
    elif collecting_state == 'email':
        # Handle optional email - user can skip
        email = user_message.strip().lower()
        
        if email in ['skip', 'no', 'no thanks', 'pass']:
            # Skip email, move to address
            temp_data['email'] = None
            chat_session.temp_profile_data = temp_data
            chat_session.profile_collection_state = 'address'
            chat_session.save()
            
            return {
                'response': "No problem! Finally, please provide your address:",
                'suggestions': ['Example: City, Country'],
                'type': 'profile_collection',
                'collecting': 'address',
                'temp_data': temp_data
            }
        else:
            # Validate email if provided
            if '@' not in email or '.' not in email:
                return {
                    'response': "Please enter a valid email address or type 'skip' to continue without email:",
                    'suggestions': ['Example: your.email@example.com', 'Skip'],
                    'type': 'profile_collection',
                    'collecting': 'email',
                    'temp_data': temp_data
                }
            
            temp_data['email'] = user_message.strip()
            chat_session.temp_profile_data = temp_data
            chat_session.profile_collection_state = 'address'
            chat_session.save()
            
            return {
                'response': "Great! Finally, please provide your address:",
                'suggestions': ['Example: City, Country'],
                'type': 'profile_collection',
                'collecting': 'address',
                'temp_data': temp_data
            }
    
    elif collecting_state == 'address':
        # Create user profile
        temp_data['address'] = user_message.strip()
        
        # Create UserProfile with all collected data including company_id
        user_profile = UserProfile.objects.create(
            session_id=chat_session.session_id,
            company_id=chat_session.company_id,  # Use company_id from session
            persistent_user_id=f"user_{uuid.uuid4().hex[:12]}",
            name=temp_data['name'],
            phone=temp_data['phone'],
            email=temp_data['email'],
            address=temp_data['address'],
            country_code=temp_data.get('country_code', '+977')
        )
        
        # Link to session and mark as complete
        chat_session.user_profile = user_profile
        chat_session.profile_completed = True
        chat_session.profile_collection_state = 'complete'
        chat_session.temp_profile_data = {}  # Clear temp data
        chat_session.save()
        
        return {
            'response': f"Thank you, {temp_data['name']}! Your profile is now complete. 🎉<br><br>How can I help you with your education abroad journey?",
            'suggestions': [
                '🌍 Explore Countries',
                '🎓 Browse Programs', 
                '💰 Financial Aid Info',
                '📋 Admission Requirements',
                '🗣️ Talk to Advisor'
            ],
            'type': 'profile_complete'
        }
    
    return None

def escalate_to_human(chat_session, reason):
    """Escalate session to human agent"""
    from human_handoff.models import HumanHandoffSession
    
    # Create handoff session
    HumanHandoffSession.objects.get_or_create(
        chat_session=chat_session,
        defaults={
            'escalation_reason': reason,
            'priority': 'medium'
        }
    )
    
    # Update chat session status
    chat_session.status = 'escalated'
    chat_session.save()
    
    return {
        'response': "I'm connecting you with one of our education consultants. Please wait a moment...",
        'suggestions': [],
        'type': 'escalated',
        'escalated': True,
        'session_id': chat_session.session_id
    }

@api_view(['POST'])
@permission_classes([AllowAny])
def validate_phone_view(request):
    """
    Validate phone number
    POST /api/chatbot/validate-phone/
    
    Request:
    {
        "phone": "9841234567",
        "country_code": "+977"
    }
    
    Response:
    {
        "valid": true,
        "message": "Valid Nepali mobile number.",
        "provider": "NTC"
    }
    """
    serializer = PhoneValidationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    phone = serializer.validated_data['phone']
    country_code = serializer.validated_data['country_code']
    
    is_valid, message = validate_phone_number(phone, country_code)
    
    # Extract provider info for Nepal
    provider = None
    if country_code == '+977' and is_valid:
        result = validate_nepali_phone(phone)
        provider = result.get('provider')
    
    response_data = {
        'valid': is_valid,
        'message': message,
        'provider': provider
    }
    
    return Response(response_data)

@api_view(['GET'])
@permission_classes([AllowAny])
def session_status_view(request):
    """
    Get session status
    GET /api/chatbot/session-status/?session_id=xxx
    
    Response:
    {
        "session_id": "session_uuid",
        "status": "active",
        "is_escalated": false,
        "user_profile": {...}
    }
    """
    session_id = request.GET.get('session_id')
    if not session_id:
        return Response({'error': 'session_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        chat_session = ChatSession.objects.get(session_id=session_id)
        is_escalated = hasattr(chat_session, 'handoff')
        
        response_data = {
            'session_id': chat_session.session_id,
            'status': chat_session.status,
            'is_escalated': is_escalated,
            'user_profile': UserProfileSerializer(chat_session.user_profile).data if chat_session.user_profile else None
        }
        
        return Response(response_data)
        
    except ChatSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def country_codes_view(request):
    """
    Get available country codes
    GET /api/chatbot/country-codes/
    
    Response:
    [
        {"code": "+977", "country": "Nepal", "flag": "🇳🇵"},
        ...
    ]
    """
    return Response(COUNTRY_CODES)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_profile_view(request):
    """
    Create user profile
    POST /api/chatbot/create-profile/
    
    Request:
    {
        "name": "John Doe",
        "phone": "+9779841234567",
        "email": "john@example.com",
        "session_id": "session_uuid"
    }
    """
    serializer = ProfileCollectionRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    session_id = serializer.validated_data.get('session_id')
    if not session_id:
        return Response({'error': 'session_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        chat_session = ChatSession.objects.get(session_id=session_id)
        
        # Create user profile
        persistent_user_id = f"user_{uuid.uuid4().hex[:12]}"
        profile = UserProfile.objects.create(
            session_id=session_id,
            persistent_user_id=persistent_user_id,
            name=serializer.validated_data['name'],
            phone=serializer.validated_data['phone'],
            email=serializer.validated_data.get('email'),
            country_code=serializer.validated_data.get('country_code', '+977')
        )
        
        # Link profile to session
        chat_session.user_profile = profile
        chat_session.save()
        
        return Response({
            'message': 'Profile created successfully',
            'profile': UserProfileSerializer(profile).data,
            'persistent_user_id': profile.persistent_user_id
        })
        
    except ChatSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def load_rag_documents_view(request):
    """
    Load RAG documents from JSON file (Admin only in production)
    GET /api/chatbot/load-rag-documents/
    """
    json_path = os.path.join(settings.BASE_DIR, 'refrence', 'data', 'documents', 'education_faq.json')
    
    success = rag_system.load_documents_from_json(json_path)
    
    if success:
        count = RAGDocument.objects.filter(is_active=True).count()
        return Response({
            'message': f'Successfully loaded {count} documents',
            'documents_count': count
        })
    else:
        return Response({
            'error': 'Failed to load documents'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def file_upload_view(request):
    """
    Handle file uploads for chat messages
    POST /api/chatbot/upload/
    
    Request:
    {
        "file": <file_object>,
        "session_id": "session_uuid",
        "company_id": "COMP_123",  // Optional, extracted from JWT if available
        "message_context": "Optional context about the file"
    }
    
    Response:
    {
        "file_id": 123,
        "file_url": "/media/uploads/COMP_123/2024/08/file_123_document.pdf",
        "original_name": "document.pdf",
        "file_size": 1024000,
        "file_type": "document",
        "message": "File uploaded successfully"
    }
    """
    serializer = FileUploadRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    uploaded_file = serializer.validated_data['file']
    session_id = serializer.validated_data['session_id']
    message_context = serializer.validated_data.get('message_context', '')
    
    # Extract company_id from request
    company_id = get_company_id_from_request(request)
    if not company_id:
        return Response({
            'error': 'company_id is required. Please provide company_id in request data or authenticate with valid JWT token.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get the chat session
        chat_session = ChatSession.objects.get(session_id=session_id, company_id=company_id)
        
        # Initialize file handler
        file_handler = FileUploadHandler()
        
        # Validate and save the file
        file_info = file_handler.save_file(uploaded_file, company_id, session_id)
        
        # Create UploadedFile record
        uploaded_file_obj = UploadedFile.objects.create(
            session=chat_session,
            user_profile=chat_session.user_profile,
            company_id=company_id,
            original_name=file_info['original_name'],
            filename=file_info['filename'],
            filepath=file_info['filepath'],
            file_size=file_info['file_size'],
            file_type=file_info['file_type'],
            message_context=message_context
        )
        
        response_data = {
            'file_id': uploaded_file_obj.id,
            'file_url': uploaded_file_obj.get_file_url(),
            'original_name': uploaded_file_obj.original_name,
            'file_size': uploaded_file_obj.file_size,
            'file_type': uploaded_file_obj.file_type,
            'message': 'File uploaded successfully'
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except ChatSession.DoesNotExist:
        return Response({
            'error': 'Chat session not found or access denied'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'File upload failed: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
