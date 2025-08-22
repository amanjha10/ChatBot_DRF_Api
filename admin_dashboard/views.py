import string
import secrets
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import transaction
from django.contrib.auth import authenticate
from django.utils import timezone
from authentication.models import User
from authentication.permissions import IsSuperAdmin
from .models import Agent, AgentSession
from .serializers import (
    AgentCreateSerializer, AgentListSerializer, AgentUpdateSerializer,
    AgentPasswordResetSerializer, AgentFirstLoginSerializer, AgentStatusUpdateSerializer,
    AgentSessionSerializer
)


# Custom permission for Admin and SuperAdmin
from rest_framework.permissions import BasePermission

class IsAdminOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.role in [User.Role.ADMIN, User.Role.SUPERADMIN])
        )


@api_view(['POST'])
@permission_classes([IsAdminOrSuperAdmin])
def create_agent_view(request):
    """
    Create Agent from Admin Dashboard.
    POST /api/admin-dashboard/create-agent/

    Expected form data:
    {
        "name": "John Doe",
        "phone": "1234567890",
        "email": "john@example.com",
        "specialization": "Customer Support"
    }

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
            "status": "OFFLINE"
        }
    }
    """
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
            "status": "AVAILABLE",
            "formatted_last_active": "21/08/2025 14:30",
            "is_active": true
        }
    ]
    """
    # Filter agents created by current admin (or all if SuperAdmin)
    if request.user.role == User.Role.SUPERADMIN:
        agents = Agent.objects.filter(is_active=True).order_by('-created_at')
    else:
        agents = Agent.objects.filter(created_by=request.user, is_active=True).order_by('-created_at')

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
        # Check if agent belongs to current admin (or allow if SuperAdmin)
        if request.user.role == User.Role.SUPERADMIN:
            agent = Agent.objects.get(id=agent_id)
        else:
            agent = Agent.objects.get(id=agent_id, created_by=request.user)
    except Agent.DoesNotExist:
        return Response({'error': 'Agent not found'}, status=status.HTTP_404_NOT_FOUND)

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
        sessions = sessions.filter(agent__created_by=request.user)

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
