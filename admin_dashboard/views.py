import string
import secrets
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import transaction
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from authentication.models import User
from authentication.permissions import IsSuperAdmin
from .models import Agent, AgentSession
from .serializers import (
    AgentCreateSerializer, AgentListSerializer, AgentUpdateSerializer,
    AgentPasswordResetSerializer, AgentFirstLoginSerializer, AgentStatusUpdateSerializer,
    AgentSessionSerializer
)

# Import chatbot models for user management
from chatbot.models import UserProfile, ChatSession
from chatbot.serializers import UserProfileSerializer


# Custom permission for Admin and SuperAdmin
from rest_framework.permissions import BasePermission

class IsAdminOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.role in [User.Role.ADMIN, User.Role.SUPERADMIN])
        )


# ==================== USER MANAGEMENT APIs ====================

@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def user_profiles_list_view(request):
    """
    Get paginated list of user profiles from chatbot profile collection
    GET /api/admin-dashboard/user-profiles/?page=1&per_page=10&search=john

    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10, max: 100)
    - search: Search by name, phone, or email
    - country_code: Filter by country code
    - created_from: Filter by creation date (YYYY-MM-DD)
    - created_to: Filter by creation date (YYYY-MM-DD)

    Response:
    {
        "count": 50,
        "total_pages": 5,
        "current_page": 1,
        "per_page": 10,
        "has_next": true,
        "has_previous": false,
        "profiles": [
            {
                "id": 1,
                "name": "John Smith",
                "phone": "+977-9841234567",
                "email": "john@example.com",
                "address": "Kathmandu, Nepal",
                "country_code": "+977",
                "created_at": "2025-08-26T08:01:19Z",
                "session_info": {
                    "session_id": "session-uuid",
                    "status": "active",
                    "is_escalated": false
                }
            }
        ]
    }
    """
    # Get query parameters
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 10)), 100)  # Max 100 per page
    search = request.GET.get('search', '').strip()
    country_code = request.GET.get('country_code', '').strip()
    created_from = request.GET.get('created_from', '').strip()
    created_to = request.GET.get('created_to', '').strip()

    # Start with all profiles filtered by company_id
    user = request.user
    if user.role == User.Role.SUPERADMIN:
        # Super admin can see all profiles
        profiles = UserProfile.objects.all().order_by('-created_at')
    elif user.role == User.Role.ADMIN:
        # Admin can only see profiles from their company
        profiles = UserProfile.objects.filter(company_id=user.company_id).order_by('-created_at')
    else:
        # Agents shouldn't access this view, but if they do, show only their company
        try:
            agent = Agent.objects.get(user=user)
            profiles = UserProfile.objects.filter(company_id=agent.company_id).order_by('-created_at')
        except Agent.DoesNotExist:
            profiles = UserProfile.objects.none()

    # Apply search filter
    if search:
        profiles = profiles.filter(
            Q(name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )

    # Apply country code filter
    if country_code:
        profiles = profiles.filter(country_code=country_code)

    # Apply date filters
    if created_from:
        try:
            from datetime import datetime
            from_date = datetime.strptime(created_from, '%Y-%m-%d').date()
            profiles = profiles.filter(created_at__date__gte=from_date)
        except ValueError:
            pass

    if created_to:
        try:
            from datetime import datetime
            to_date = datetime.strptime(created_to, '%Y-%m-%d').date()
            profiles = profiles.filter(created_at__date__lte=to_date)
        except ValueError:
            pass

    # Paginate results
    paginator = Paginator(profiles, per_page)
    
    # Check if requested page is valid
    profiles_data = []
    if page <= paginator.num_pages:
        page_obj = paginator.page(page)
        
        # Serialize profiles with session info
        for profile in page_obj:
            profile_data = UserProfileSerializer(profile).data
            
            # Add session information
            try:
                chat_session = ChatSession.objects.get(session_id=profile.session_id)
                profile_data['session_info'] = {
                    'session_id': chat_session.session_id,
                    'status': chat_session.status,
                    'is_escalated': hasattr(chat_session, 'handoff'),
                    'profile_completed': chat_session.profile_completed,
                    'created_at': chat_session.created_at.isoformat()
                }
            except ChatSession.DoesNotExist:
                profile_data['session_info'] = None
            
            profiles_data.append(profile_data)
        
        has_next = page_obj.has_next()
        has_previous = page_obj.has_previous()
    else:
        # Page is beyond available pages - return empty results
        has_next = False
        has_previous = paginator.num_pages > 0

    return Response({
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': has_next,
        'has_previous': has_previous,
        'profiles': profiles_data
    })


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def user_profile_detail_view(request, profile_id):
    """
    Get detailed information about a specific user profile
    GET /api/admin-dashboard/user-profiles/{profile_id}/

    Response:
    {
        "profile": {...},
        "session_info": {...},
        "chat_history": [
            {
                "message_type": "user",
                "content": "Hello",
                "timestamp": "2025-08-26T08:01:19Z"
            }
        ]
    }
    """
    try:
        profile = UserProfile.objects.get(id=profile_id)
        profile_data = UserProfileSerializer(profile).data

        # Get session information
        session_info = None
        chat_history = []
        
        try:
            chat_session = ChatSession.objects.get(session_id=profile.session_id)
            session_info = {
                'session_id': chat_session.session_id,
                'status': chat_session.status,
                'profile_completed': chat_session.profile_completed,
                'profile_collection_state': chat_session.profile_collection_state,
                'is_escalated': hasattr(chat_session, 'handoff'),
                'created_at': chat_session.created_at.isoformat(),
                'updated_at': chat_session.updated_at.isoformat()
            }

            # Get chat history (last 50 messages)
            from chatbot.models import ChatMessage
            messages = ChatMessage.objects.filter(
                session=chat_session
            ).order_by('-timestamp')[:50]

            chat_history = [
                {
                    'message_type': msg.message_type,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'metadata': msg.metadata
                }
                for msg in reversed(messages)  # Reverse to show chronological order
            ]

        except ChatSession.DoesNotExist:
            pass

        return Response({
            'profile': profile_data,
            'session_info': session_info,
            'chat_history': chat_history
        })

    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def user_profiles_stats_view(request):
    """
    Get statistics about user profiles
    GET /api/admin-dashboard/user-profiles/stats/

    Response:
    {
        "total_profiles": 150,
        "profiles_today": 5,
        "profiles_this_week": 25,
        "profiles_this_month": 80,
        "by_country": {
            "+977": 120,
            "+91": 20,
            "+1": 10
        },
        "with_email": 100,
        "without_email": 50,
        "escalated_sessions": 10
    }
    """
    from datetime import datetime, timedelta
    from django.db.models import Count
    
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Basic counts
    total_profiles = UserProfile.objects.count()
    profiles_today = UserProfile.objects.filter(created_at__date=today).count()
    profiles_this_week = UserProfile.objects.filter(created_at__date__gte=week_ago).count()
    profiles_this_month = UserProfile.objects.filter(created_at__date__gte=month_ago).count()

    # Country distribution
    country_stats = UserProfile.objects.values('country_code').annotate(
        count=Count('id')
    ).order_by('-count')
    
    by_country = {stat['country_code']: stat['count'] for stat in country_stats}

    # Email statistics
    with_email = UserProfile.objects.exclude(email__isnull=True).exclude(email='').count()
    without_email = total_profiles - with_email

    # Escalated sessions
    escalated_sessions = ChatSession.objects.filter(status='escalated').count()

    return Response({
        'total_profiles': total_profiles,
        'profiles_today': profiles_today,
        'profiles_this_week': profiles_this_week,
        'profiles_this_month': profiles_this_month,
        'by_country': by_country,
        'with_email': with_email,
        'without_email': without_email,
        'escalated_sessions': escalated_sessions
    })


@api_view(['DELETE'])
@permission_classes([IsAdminOrSuperAdmin])
def delete_user_profile_view(request, profile_id):
    """
    Delete a user profile and associated session
    DELETE /api/admin-dashboard/user-profiles/{profile_id}/

    Response:
    {
        "message": "User profile deleted successfully"
    }
    """
    try:
        profile = UserProfile.objects.get(id=profile_id)
        
        # Also delete associated chat session if exists
        try:
            chat_session = ChatSession.objects.get(session_id=profile.session_id)
            chat_session.delete()
        except ChatSession.DoesNotExist:
            pass
        
        profile.delete()
        
        return Response({
            'message': 'User profile deleted successfully'
        })

    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


# ==================== EXISTING AGENT APIs ====================

@api_view(['POST'])
@permission_classes([IsAdminOrSuperAdmin])
def create_agent_view(request):
    """
    Create Agent from Admin Dashboard.
    POST /api/admin-dashboard/create-agent/

    Expected form data (frontend sends only these fields):
    {
        "name": "John Doe",
        "phone": "1234567890",
        "email": "john@example.com",
        "specialization": "Customer Support"
    }

    Note: 
    - company_id is automatically extracted from admin's JWT token
    - Admins can only create agents for their own company
    - SuperAdmins can create agents but need a valid company_id

    Returns:
    {
        "email": "john@example.com",
        "password": "Abc123Xy",
        "agent": {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "specialization": "Customer Support",
            "company_id": "COM001",
            "status": "OFFLINE"
        }
    }
    """
    # Validate that admin has company_id
    if not request.user.company_id:
        return Response({
            'error': 'Admin user must have a company_id to create agents. Please contact SuperAdmin.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = AgentCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        with transaction.atomic():
            agent = serializer.save()

            return Response({
                'email': agent.email,
                'password': agent._generated_password,
                'agent': AgentListSerializer(agent).data
            }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def list_agents_view(request):
    """
    Get list of all agents for admin dashboard.
    GET /api/admin-dashboard/list-agents/

    Returns:
    [
        {
            "id": 1,
            "sn": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "specialization": "Customer Support",
            "company_id": "COM001",
            "status": "AVAILABLE",
            "formatted_last_active": "21/08/2025 14:30",
            "is_active": true
        }
    ]
    """
    # Filter agents based on user role and company_id
    if request.user.role == User.Role.SUPERADMIN:
        # SuperAdmin can see all agents
        agents = Agent.objects.filter(is_active=True).order_by('-created_at')
    else:
        # Admin can only see agents from their company
        agents = Agent.objects.filter(
            company_id=request.user.company_id, 
            is_active=True
        ).order_by('-created_at')

    serializer = AgentListSerializer(agents, many=True, context={'queryset': agents})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminOrSuperAdmin])
def update_agent_view(request, agent_id):
    """
    Update agent information.
    PUT/PATCH /api/admin-dashboard/update-agent/<agent_id>/

    Expected form data:
    {
        "name": "Updated Name",
        "phone": "9999999999",
        "email": "updated@example.com",
        "specialization": "Updated Specialization",
        "is_active": true
    }

    Note: All fields are optional. Only provided fields will be updated.
    """
    try:
        # Check if agent belongs to current admin's company (or allow if SuperAdmin)
        if request.user.role == User.Role.SUPERADMIN:
            agent = Agent.objects.get(id=agent_id)
        else:
            agent = Agent.objects.get(id=agent_id, company_id=request.user.company_id)
    except Agent.DoesNotExist:
        return Response({'error': 'Agent not found or does not belong to your company'}, status=status.HTTP_404_NOT_FOUND)

    serializer = AgentUpdateSerializer(agent, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()

        # Return updated agent info
        updated_agent = AgentListSerializer(agent).data
        return Response({
            'message': 'Agent updated successfully',
            'agent': updated_agent
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAdminOrSuperAdmin])
def reset_agent_password_view(request):
    """
    Reset agent password.
    POST /api/admin-dashboard/reset-agent-password/

    Expected form data:
    {
        "agent_id": 1
    }

    Returns:
    {
        "message": "Password reset successfully",
        "email": "agent@example.com",
        "new_password": "NewPass123"
    }
    """
    serializer = AgentPasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        agent = serializer.context['agent']

        # Check if agent belongs to current admin (or allow if SuperAdmin)
        if request.user.role != User.Role.SUPERADMIN and agent.created_by != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        # Generate new password
        new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))

        with transaction.atomic():
            # Update user password
            agent.user.set_password(new_password)
            agent.user.generated_password = new_password
            agent.user.save()

            # Reset first login flag
            agent.is_first_login = True
            agent.save()

        return Response({
            'message': 'Password reset successfully',
            'email': agent.email,
            'new_password': new_password
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([])
def agent_first_login_view(request):
    """
    Agent first login password setup.
    POST /api/admin-dashboard/agent-first-login/

    Expected form data:
    {
        "email": "agent@example.com",
        "current_password": "GeneratedPass",
        "new_password": "MyNewPassword123",
        "confirm_password": "MyNewPassword123"
    }

    Returns:
    {
        "message": "Password updated successfully. Please login with your new password.",
        "email": "agent@example.com"
    }
    """
    serializer = AgentFirstLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        agent = serializer.validated_data['agent']
        new_password = serializer.validated_data['new_password']

        with transaction.atomic():
            # Update password
            user.set_password(new_password)
            user.save()

            # Mark as no longer first login
            agent.is_first_login = False
            agent.save()

        return Response({
            'message': 'Password updated successfully. Please login with your new password.',
            'email': user.email
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([])
def agent_login_view(request):
    """
    Agent login with status tracking.
    POST /api/admin-dashboard/agent-login/

    Expected form data:
    {
        "email": "agent@example.com",
        "password": "password123"
    }

    Returns:
    {
        "access": "jwt_token",
        "agent": {
            "id": 1,
            "name": "John Doe",
            "email": "agent@example.com",
            "status": "AVAILABLE",
            "is_first_login": false
        }
    }
    """
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email, role=User.Role.AGENT, is_active=True)
        agent = user.agent_profile

        # Authenticate user
        authenticated_user = authenticate(username=user.username, password=password)
        if not authenticated_user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if first login
        if agent.is_first_login:
            return Response({
                'error': 'First login required',
                'message': 'Please set your password using the first-login endpoint',
                'is_first_login': True
            }, status=status.HTTP_200_OK)

        # Generate JWT token
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)

        # Update agent status to AVAILABLE and create session
        with transaction.atomic():
            agent.set_online()

            # Create session record
            ip_address = request.META.get('REMOTE_ADDR')
            AgentSession.objects.create(agent=agent, ip_address=ip_address)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'agent': {
                'id': agent.id,
                'name': agent.name,
                'email': agent.email,
                'status': agent.status,
                'is_first_login': agent.is_first_login
            }
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({'error': 'Agent not found'}, status=status.HTTP_404_NOT_FOUND)
    except Agent.DoesNotExist:
        return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([])  # We'll handle permissions manually
def agent_logout_view(request):
    """
    Agent logout with status tracking.
    POST /api/admin-dashboard/agent-logout/

    Headers: Authorization: Bearer <agent_jwt_token>

    Returns:
    {
        "message": "Logged out successfully"
    }
    """
    if not request.user.is_authenticated or request.user.role != User.Role.AGENT:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        agent = request.user.agent_profile

        with transaction.atomic():
            # Set agent status to OFFLINE
            agent.set_offline()

            # End current session
            current_session = AgentSession.objects.filter(
                agent=agent,
                logout_time__isnull=True
            ).order_by('-login_time').first()

            if current_session:
                current_session.end_session()

        return Response({
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)

    except Agent.DoesNotExist:
        return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([])  # We'll handle permissions manually
def update_agent_status_view(request):
    """
    Update agent status (AVAILABLE/BUSY).
    POST /api/admin-dashboard/update-agent-status/

    Headers: Authorization: Bearer <agent_jwt_token>

    Expected form data:
    {
        "status": "BUSY"  // AVAILABLE, BUSY
    }

    Returns:
    {
        "message": "Status updated successfully",
        "status": "BUSY"
    }
    """
    if not request.user.is_authenticated or request.user.role != User.Role.AGENT:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = AgentStatusUpdateSerializer(data=request.data)
    if serializer.is_valid():
        new_status = serializer.validated_data['status']

        # Don't allow setting to OFFLINE through this endpoint
        if new_status == 'OFFLINE':
            return Response({'error': 'Use logout endpoint to go offline'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            agent = request.user.agent_profile
            agent.update_status(new_status)

            return Response({
                'message': 'Status updated successfully',
                'status': agent.status
            }, status=status.HTTP_200_OK)

        except Agent.DoesNotExist:
            return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def agent_sessions_view(request):
    """
    Get agent session history.
    GET /api/admin-dashboard/agent-sessions/
    GET /api/admin-dashboard/agent-sessions/?agent_id=1

    Returns:
    [
        {
            "id": 1,
            "agent_name": "John Doe",
            "login_time": "2025-08-21T14:30:00Z",
            "logout_time": "2025-08-21T18:30:00Z",
            "duration_minutes": 240,
            "ip_address": "192.168.1.1"
        }
    ]
    """
    sessions = AgentSession.objects.all().order_by('-login_time')

    # Filter by agent_id if provided
    agent_id = request.GET.get('agent_id')
    if agent_id:
        try:
            agent_id = int(agent_id)
            sessions = sessions.filter(agent_id=agent_id)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid agent_id parameter'}, status=status.HTTP_400_BAD_REQUEST)

    # Filter by admin's agents if not SuperAdmin
    if request.user.role != User.Role.SUPERADMIN:
        sessions = sessions.filter(agent__company_id=request.user.company_id)

    serializer = AgentSessionSerializer(sessions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def debug_agent_view(request, agent_id):
    """
    Debug agent credentials (temporary endpoint).
    GET /api/admin-dashboard/debug-agent/<agent_id>/
    """
    try:
        agent = Agent.objects.get(id=agent_id)
        user = agent.user

        return Response({
            'agent_id': agent.id,
            'agent_email': agent.email,
            'user_id': user.id,
            'user_username': user.username,
            'user_email': user.email,
            'generated_password': user.generated_password,
            'is_first_login': agent.is_first_login,
            'user_is_active': user.is_active,
            'agent_is_active': agent.is_active
        }, status=status.HTTP_200_OK)

    except Agent.DoesNotExist:
        return Response({'error': 'Agent not found'}, status=status.HTTP_404_NOT_FOUND)
