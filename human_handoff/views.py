# human_handoff/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.db.models import Q

from admin_dashboard.models import Agent
from chatbot.models import ChatSession, UserProfile, ChatMessage
from .models import HumanHandoffSession, AgentActivity, SessionTransfer
from .serializers import (
    HumanHandoffSessionSerializer, AgentActivitySerializer,
    SessionTransferSerializer, EscalateSessionSerializer,
    AssignSessionSerializer, ResolveSessionSerializer
)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def escalate_session_view(request):
    """
    Escalate a chat session to human agent
    POST /api/human-handoff/escalate/
    
    Request:
    {
        "session_id": "session_uuid",
        "reason": "Customer needs detailed visa guidance",
        "priority": "high"
    }
    
    Response:
    {
        "message": "Session escalated successfully",
        "handoff_session": {...}
    }
    """
    serializer = EscalateSessionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    session_id = serializer.validated_data['session_id']
    reason = serializer.validated_data['reason']
    priority = serializer.validated_data.get('priority', 'medium')
    
    try:
        chat_session = ChatSession.objects.get(session_id=session_id)
        
        # Check if already escalated
        if hasattr(chat_session, 'handoff'):
            return Response({
                'error': 'Session is already escalated',
                'handoff_session': HumanHandoffSessionSerializer(chat_session.handoff).data
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create handoff session
        handoff_session = HumanHandoffSession.objects.create(
            chat_session=chat_session,
            escalation_reason=reason,
            priority=priority
        )
        
        # Update chat session status
        chat_session.status = 'escalated'
        chat_session.save()
        
        # Log activity
        if hasattr(request.user, 'agent_profile'):
            AgentActivity.objects.create(
                agent=request.user.agent_profile,
                activity_type='session_assign',
                description=f'Escalated session {session_id}',
                metadata={'session_id': session_id, 'reason': reason}
            )
        
        return Response({
            'message': 'Session escalated successfully',
            'handoff_session': HumanHandoffSessionSerializer(handoff_session).data
        })
        
    except ChatSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_session_view(request):
    """
    Assign escalated session to an agent
    POST /api/human-handoff/assign/
    
    Request:
    {
        "handoff_session_id": 1,
        "agent_id": 5
    }
    """
    serializer = AssignSessionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    handoff_session_id = serializer.validated_data['handoff_session_id']
    agent_id = serializer.validated_data['agent_id']
    
    try:
        handoff_session = HumanHandoffSession.objects.get(id=handoff_session_id)
        agent = Agent.objects.get(id=agent_id)
        
        # Store previous agent for transfer tracking
        previous_agent = handoff_session.agent
        
        # Assign agent
        handoff_session.agent = agent
        handoff_session.save()
        
        # Update chat session status
        handoff_session.chat_session.status = 'assigned'
        handoff_session.chat_session.save()
        
        # Log transfer if there was a previous agent
        if previous_agent and previous_agent != agent:
            SessionTransfer.objects.create(
                handoff_session=handoff_session,
                from_agent=previous_agent,
                to_agent=agent,
                reason='Reassigned by supervisor',
                transferred_by=request.user
            )
        
        # Log activity
        AgentActivity.objects.create(
            agent=agent,
            activity_type='session_assign',
            description=f'Assigned to session {handoff_session.chat_session.session_id}',
            metadata={'session_id': handoff_session.chat_session.session_id}
        )
        
        return Response({
            'message': 'Session assigned successfully',
            'handoff_session': HumanHandoffSessionSerializer(handoff_session).data
        })
        
    except HumanHandoffSession.DoesNotExist:
        return Response({'error': 'Handoff session not found'}, status=status.HTTP_404_NOT_FOUND)
    except Agent.DoesNotExist:
        return Response({'error': 'Agent not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_session_view(request):
    """
    Resolve/close a handoff session
    POST /api/human-handoff/resolve/
    
    Request:
    {
        "handoff_session_id": 1,
        "notes": "Issue resolved, provided visa guidance"
    }
    """
    serializer = ResolveSessionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    handoff_session_id = serializer.validated_data['handoff_session_id']
    notes = serializer.validated_data.get('notes', '')
    
    try:
        handoff_session = HumanHandoffSession.objects.get(id=handoff_session_id)
        
        # Mark as resolved
        handoff_session.resolved_at = timezone.now()
        handoff_session.notes = notes
        handoff_session.save()
        
        # Update chat session status
        handoff_session.chat_session.status = 'resolved'
        handoff_session.chat_session.save()
        
        # Log activity
        if handoff_session.agent:
            AgentActivity.objects.create(
                agent=handoff_session.agent,
                activity_type='session_resolve',
                description=f'Resolved session {handoff_session.chat_session.session_id}',
                metadata={'session_id': handoff_session.chat_session.session_id, 'notes': notes}
            )
        
        return Response({
            'message': 'Session resolved successfully',
            'handoff_session': HumanHandoffSessionSerializer(handoff_session).data
        })
        
    except HumanHandoffSession.DoesNotExist:
        return Response({'error': 'Handoff session not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_handoff_sessions_view(request):
    """
    List handoff sessions with filtering
    GET /api/human-handoff/sessions/
    GET /api/human-handoff/sessions/?agent_id=5
    GET /api/human-handoff/sessions/?status=escalated
    """
    queryset = HumanHandoffSession.objects.all().order_by('-escalated_at')
    
    # Filter by agent
    agent_id = request.GET.get('agent_id')
    if agent_id:
        queryset = queryset.filter(agent_id=agent_id)
    
    # Filter by status
    session_status = request.GET.get('status')
    if session_status:
        if session_status == 'escalated':
            queryset = queryset.filter(resolved_at__isnull=True, agent__isnull=True)
        elif session_status == 'assigned':
            queryset = queryset.filter(resolved_at__isnull=True, agent__isnull=False)
        elif session_status == 'resolved':
            queryset = queryset.filter(resolved_at__isnull=False)
    
    # Filter by priority
    priority = request.GET.get('priority')
    if priority:
        queryset = queryset.filter(priority=priority)
    
    serializer = HumanHandoffSessionSerializer(queryset, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_activities_view(request):
    """
    Get agent activities
    GET /api/human-handoff/activities/
    GET /api/human-handoff/activities/?agent_id=5
    """
    queryset = AgentActivity.objects.all().order_by('-timestamp')
    
    # Filter by agent
    agent_id = request.GET.get('agent_id')
    if agent_id:
        queryset = queryset.filter(agent_id=agent_id)
    
    # Filter by activity type
    activity_type = request.GET.get('activity_type')
    if activity_type:
        queryset = queryset.filter(activity_type=activity_type)
    
    # Limit results
    limit = int(request.GET.get('limit', 50))
    queryset = queryset[:limit]
    
    serializer = AgentActivitySerializer(queryset, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_dashboard_view(request):
    """
    Get agent dashboard data
    GET /api/human-handoff/dashboard/
    """
    # Ensure user is an agent
    if not hasattr(request.user, 'agent_profile'):
        return Response({'error': 'User is not an agent'}, status=status.HTTP_403_FORBIDDEN)
    
    agent = request.user.agent_profile
    
    # Get agent's assigned sessions
    assigned_sessions = HumanHandoffSession.objects.filter(
        agent=agent,
        resolved_at__isnull=True
    ).order_by('-escalated_at')
    
    # Get unassigned sessions for the agent's company
    unassigned_sessions = HumanHandoffSession.objects.filter(
        agent__isnull=True,
        resolved_at__isnull=True,
        chat_session__user_profile__isnull=False
    ).order_by('-escalated_at')
    
    # Recent activities
    recent_activities = AgentActivity.objects.filter(
        agent=agent
    ).order_by('-timestamp')[:10]
    
    dashboard_data = {
        'agent_info': {
            'id': agent.id,
            'name': agent.name,
            'status': agent.status,
            'company_id': agent.company_id
        },
        'assigned_sessions': HumanHandoffSessionSerializer(assigned_sessions, many=True).data,
        'unassigned_sessions': HumanHandoffSessionSerializer(unassigned_sessions, many=True).data,
        'recent_activities': AgentActivitySerializer(recent_activities, many=True).data,
        'stats': {
            'assigned_count': assigned_sessions.count(),
            'unassigned_count': unassigned_sessions.count(),
            'resolved_today': HumanHandoffSession.objects.filter(
                agent=agent,
                resolved_at__date=timezone.now().date()
            ).count()
        }
    }
    
    return Response(dashboard_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message_view(request):
    """
    Send message in a handoff session
    POST /api/human-handoff/send-message/
    
    Request:
    {
        "session_id": "session_uuid",
        "message": "Hello, how can I help you?"
    }
    """
    session_id = request.data.get('session_id')
    message = request.data.get('message')
    
    if not session_id or not message:
        return Response({'error': 'session_id and message are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        chat_session = ChatSession.objects.get(session_id=session_id)
        
        # Ensure session is escalated and user is the assigned agent
        if not hasattr(chat_session, 'handoff'):
            return Response({'error': 'Session is not escalated'}, status=status.HTTP_400_BAD_REQUEST)
        
        agent = getattr(request.user, 'agent_profile', None)
        if not agent:
            return Response({'error': 'User is not an agent'}, status=status.HTTP_403_FORBIDDEN)
        
        if chat_session.handoff.agent != agent:
            return Response({'error': 'Session is not assigned to this agent'}, status=status.HTTP_403_FORBIDDEN)
        
        # Create message
        chat_message = ChatMessage.objects.create(
            session=chat_session,
            message_type='agent',
            content=message,
            metadata={
                'agent_id': agent.id,
                'agent_name': agent.name
            }
        )
        
        # Log activity
        AgentActivity.objects.create(
            agent=agent,
            activity_type='message_sent',
            description=f'Sent message in session {session_id}',
            metadata={'session_id': session_id, 'message_preview': message[:50]}
        )
        
        return Response({
            'message': 'Message sent successfully',
            'chat_message': {
                'id': chat_message.id,
                'content': chat_message.content,
                'timestamp': chat_message.timestamp
            }
        })
        
    except ChatSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

# ==================== COMPANY-BASED AGENT APIS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_sessions_view(request):
    """
    Get escalated sessions for the authenticated agent's company
    GET /api/human-handoff/agent/sessions/?status=unassigned&page=1&per_page=10
    
    Query Parameters:
    - status: Filter by status (unassigned, assigned, resolved)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10)
    
    Response:
    {
        "count": 15,
        "current_page": 1,
        "total_pages": 2,
        "sessions": [
            {
                "id": 1,
                "chat_session": {
                    "session_id": "session-uuid",
                    "company_id": "COMP_123"
                },
                "agent": null,
                "escalated_at": "2025-08-26T10:30:00Z",
                "priority": "high",
                "escalation_reason": "Customer needs visa guidance"
            }
        ]
    }
    """
    # Get agent's company_id
    try:
        agent = Agent.objects.get(user=request.user)
        company_id = agent.company_id
    except Agent.DoesNotExist:
        return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if not company_id:
        return Response({'error': 'Agent company_id not configured'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get query parameters
    status_filter = request.GET.get('status', '').strip()
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 10)), 50)  # Max 50 per page
    
    # Filter sessions by company_id AND assigned to this agent
    sessions = HumanHandoffSession.objects.filter(
        chat_session__company_id=company_id,
        agent=agent  # Only sessions assigned to this specific agent
    ).select_related('chat_session', 'agent').order_by('-escalated_at')
    
    # Apply status filter
    if status_filter == 'unassigned':
        # For agents, show no unassigned sessions (they can only see their own)
        sessions = sessions.none()
    elif status_filter == 'assigned':
        sessions = sessions.filter(resolved_at__isnull=True)
    elif status_filter == 'resolved':
        sessions = sessions.filter(resolved_at__isnull=False)
    
    # Paginate results
    from django.core.paginator import Paginator
    paginator = Paginator(sessions, per_page)
    page_obj = paginator.page(page)
    
    # Serialize sessions
    sessions_data = []
    for session in page_obj:
        session_data = {
            'id': session.id,
            'chat_session': {
                'session_id': session.chat_session.session_id,
                'company_id': session.chat_session.company_id,
                'status': session.chat_session.status
            },
            'agent': {
                'id': session.agent.id,
                'name': session.agent.name
            } if session.agent else None,
            'escalated_at': session.escalated_at.isoformat(),
            'resolved_at': session.resolved_at.isoformat() if session.resolved_at else None,
            'priority': session.priority,
            'escalation_reason': session.escalation_reason,
            'notes': session.notes
        }
        sessions_data.append(session_data)
    
    return Response({
        'count': paginator.count,
        'current_page': page,
        'total_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'sessions': sessions_data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_session_messages_view(request, session_id):
    """
    Get messages for a specific session (company-isolated)
    GET /api/human-handoff/agent/sessions/{session_id}/messages/
    
    Response:
    {
        "session": {
            "session_id": "session-uuid",
            "company_id": "COMP_123",
            "user_profile": {...}
        },
        "messages": [
            {
                "id": 1,
                "message_type": "user",
                "content": "Hello, I need help",
                "timestamp": "2025-08-26T10:30:00Z"
            }
        ]
    }
    """
    # Get agent's company_id
    try:
        agent = Agent.objects.get(user=request.user)
        company_id = agent.company_id
    except Agent.DoesNotExist:
        return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        # Get session with company isolation
        chat_session = ChatSession.objects.get(
            session_id=session_id,
            company_id=company_id
        )
        
        # Check if session is escalated and assigned to this agent
        try:
            handoff_session = HumanHandoffSession.objects.get(
                chat_session=chat_session,
                agent=agent
            )
        except HumanHandoffSession.DoesNotExist:
            return Response({'error': 'Session not assigned to this agent'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get all messages for this session
        messages = ChatMessage.objects.filter(session=chat_session).order_by('timestamp')
        
        # Serialize messages
        messages_data = []
        for message in messages:
            message_data = {
                'id': message.id,
                'message_type': message.message_type,
                'content': message.content,
                'metadata': message.metadata,
                'timestamp': message.timestamp.isoformat()
            }
            messages_data.append(message_data)
        
        # Session data
        session_data = {
            'session_id': chat_session.session_id,
            'company_id': chat_session.company_id,
            'status': chat_session.status,
            'user_profile': None
        }
        
        # Add user profile if exists
        if chat_session.user_profile:
            from chatbot.serializers import UserProfileSerializer
            session_data['user_profile'] = UserProfileSerializer(chat_session.user_profile).data
        
        return Response({
            'session': session_data,
            'messages': messages_data
        })
        
    except ChatSession.DoesNotExist:
        return Response({'error': 'Session not found or access denied'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def agent_send_message_view(request):
    """
    Send message as agent to a session (company-isolated)
    POST /api/human-handoff/agent/send-message/
    
    Request:
    {
        "session_id": "session-uuid",
        "message": "Hello, I'm here to help you with your visa questions."
    }
    
    Response:
    {
        "message": "Message sent successfully",
        "chat_message": {
            "id": 123,
            "content": "Hello, I'm here to help...",
            "timestamp": "2025-08-26T10:30:00Z"
        }
    }
    """
    # Get agent's company_id
    try:
        agent = Agent.objects.get(user=request.user)
        company_id = agent.company_id
    except Agent.DoesNotExist:
        return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    session_id = request.data.get('session_id')
    message = request.data.get('message', '').strip()
    
    if not session_id or not message:
        return Response({
            'error': 'session_id and message are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get session with company isolation
        chat_session = ChatSession.objects.get(
            session_id=session_id,
            company_id=company_id
        )
        
        # Check if session is escalated and assigned to this agent
        try:
            handoff_session = HumanHandoffSession.objects.get(
                chat_session=chat_session,
                agent=agent
            )
        except HumanHandoffSession.DoesNotExist:
            return Response({'error': 'Session not assigned to this agent'}, status=status.HTTP_403_FORBIDDEN)
        
        # Create chat message
        chat_message = ChatMessage.objects.create(
            session=chat_session,
            message_type='agent',
            content=message,
            metadata={
                'agent_id': agent.id,
                'agent_name': agent.name
            }
        )
        
        # Log activity
        AgentActivity.objects.create(
            agent=agent,
            activity_type='message_sent',
            description=f'Sent message in session {session_id}',
            metadata={'session_id': session_id, 'message_preview': message[:50]}
        )
        
        return Response({
            'message': 'Message sent successfully',
            'chat_message': {
                'id': chat_message.id,
                'content': chat_message.content,
                'timestamp': chat_message.timestamp.isoformat()
            }
        })
        
    except ChatSession.DoesNotExist:
        return Response({'error': 'Session not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
