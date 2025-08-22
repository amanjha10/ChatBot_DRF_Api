from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from .models import User, Plan, UserPlanAssignment
from .serializers import (
    LoginSerializer, AdminCreateSerializer, TokenResponseSerializer,
    AdminListSerializer, AdminUpdateSerializer, AdminPlanChangeSerializer,
    PlanSerializer, PlanCreateSerializer, UserPlanAssignmentSerializer
)
from .permissions import IsSuperAdmin


class AdminPagination(PageNumberPagination):
    """Custom pagination class for admin list"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': len(data),  # Actual number of items on this page
            'requested_page_size': self.get_page_size(self.request),  # What was requested
            'results': data
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login endpoint that returns JWT token and user role.
    POST /api/auth/login/
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token_data = TokenResponseSerializer.get_token_response(user)
        return Response(token_data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def create_admin_view(request):
    """
    Create Admin user endpoint (restricted to SuperAdmin).
    POST /api/auth/create-admin/

    Expected form data:
    {
        "name": "John Smith Technology",
        "email": "admin@company.com",
        "address": "123 Main St",
        "contact_person": "Emergency Contact Name",
        "contact_number": "9876543210",
        "phone_number": "1234567890",
        "plan_id": 1  // Plan ID - creates plan assignment automatically
    }

    Note: Plan assignment is created automatically with 1-year expiry.
    Company ID is generated from the first 3 letters of the name field.

    Returns:
    {
        "name": "John Smith Technology",
        "email": "john@example.com",
        "password": "Abc123Xy",
        "company_id": "JOH001"
    }
    """
    serializer = AdminCreateSerializer(data=request.data)
    if serializer.is_valid():
        with transaction.atomic():
            user = serializer.save()

            return Response({
                'name': user.name,
                'email': user.email,
                'password': user._generated_password,
                'company_id': user.company_id,
                'plan': {
                    'id': user._assigned_plan.id,
                    'name': user._assigned_plan.get_plan_name_display(),
                    'max_agents': user._assigned_plan.max_agents,
                    'price': str(user._assigned_plan.price)
                }
            }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def profile_view(request):
    """
    Get current user profile.
    GET /api/auth/profile/
    """
    from .serializers import UserSerializer
    return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def list_admins_view(request):
    """
    Get list of all created admin users with complete information and pagination support.
    GET /api/auth/list-admins/
    GET /api/auth/list-admins/?admin_id=2  (for specific admin)
    GET /api/auth/list-admins/?page=2&page_size=5&search=tesla&ordering=name

    Query Parameters:
    - admin_id (optional): Filter to get specific admin by ID
    - page (optional): Page number (default: 1)
    - page_size (optional): Number of items per page (default: 10, max: 100)
    - search (optional): Search by name, email, or company_id
    - ordering (optional): Order by field (default: -date_joined)
      - Available fields: name, email, company_id, date_joined
      - Use '-' prefix for descending order (e.g., -date_joined)

    Returns:
    - With admin_id: Single admin object (not in array)
    - Without admin_id: Paginated list of all admin users

    Examples:
    GET /api/auth/list-admins/?admin_id=2
    Returns: {"id": 2, "name": "Admin 2", "email": "admin2@example.com", ...}

    GET /api/auth/list-admins/
    GET /api/auth/list-admins/?page=2&page_size=5
    GET /api/auth/list-admins/?search=tesla&ordering=name
    Returns: {
        "count": 25,
        "next": "http://127.0.0.1:8000/api/auth/list-admins/?page=3",
        "previous": "http://127.0.0.1:8000/api/auth/list-admins/?page=1",
        "total_pages": 3,
        "current_page": 2,
        "page_size": 10,
        "results": [...]
    }
    """
    admin_id = request.GET.get('admin_id')
    
    if admin_id:
        # Filter for specific admin
        try:
            admin_id = int(admin_id)
            admin = User.objects.get(id=admin_id, role=User.Role.ADMIN)
            serializer = AdminListSerializer(admin)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid admin_id parameter. Must be a number.'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Admin not found with the given ID.'}, status=status.HTTP_404_NOT_FOUND)
    else:
        # Return paginated list of all admins with search and ordering
        # Get query parameters
        search = request.GET.get('search', '')
        ordering = request.GET.get('ordering', '-date_joined')
        
        # Base queryset - all admin users
        queryset = User.objects.filter(role=User.Role.ADMIN)
        
        # Apply search filter if provided
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(company_id__icontains=search)
            )
        
        # Apply ordering
        valid_ordering_fields = ['name', 'email', 'company_id', 'date_joined', '-name', '-email', '-company_id', '-date_joined']
        if ordering in valid_ordering_fields:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-date_joined')  # Default ordering
        
        # Apply pagination
        paginator = AdminPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AdminListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        # Fallback if pagination fails
        serializer = AdminListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsSuperAdmin])
def update_admin_view(request, admin_id):
    """
    Update admin user information.
    PUT/PATCH /api/auth/update-admin/<admin_id>/

    Expected form data:
    {
        "email": "newemail@company.com",
        "first_name": "New First Name",
        "last_name": "New Last Name",
        "address": "New Address",
        "contact_person": "New Contact Person",
        "contact_number": "9876543210",
        "phone_number": "1234567890"
    }

    Note: All fields are optional. Only provided fields will be updated.
    """
    try:
        admin = User.objects.get(id=admin_id, role=User.Role.ADMIN)
    except User.DoesNotExist:
        return Response({'error': 'Admin not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = AdminUpdateSerializer(admin, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()

        # Return updated admin info
        updated_admin = AdminListSerializer(admin).data
        return Response({
            'message': 'Admin updated successfully',
            'admin': updated_admin
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def change_admin_plan_view(request, admin_id):
    """
    Change admin's plan (upgrade/downgrade).
    POST /api/auth/change-admin-plan/<admin_id>/

    Expected form data:
    {
        "new_plan_id": 2,
        "reason": "User requested upgrade to Pro plan"
    }

    Note: This preserves history by creating new assignment and marking old as 'upgraded'.
    """
    try:
        admin = User.objects.get(id=admin_id, role=User.Role.ADMIN)
    except User.DoesNotExist:
        return Response({'error': 'Admin not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get current active assignment
    current_assignment = admin.current_plan_assignment
    if not current_assignment:
        return Response({'error': 'Admin has no active plan assignment'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = AdminPlanChangeSerializer(data=request.data)
    if serializer.is_valid():
        new_plan = serializer.validated_data['new_plan_id']
        reason = serializer.validated_data['reason']

        # Check if it's the same plan
        if current_assignment.plan.id == new_plan.id:
            return Response({'error': 'Admin is already on this plan'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Create new assignment with new plan
            new_assignment = current_assignment.upgrade_plan(new_plan, reason)

            # Return updated admin info
            updated_admin = AdminListSerializer(admin).data
            return Response({
                'message': f'Plan changed successfully from {current_assignment.plan.get_plan_name_display()} to {new_plan.get_plan_name_display()}',
                'admin': updated_admin,
                'new_assignment': UserPlanAssignmentSerializer(new_assignment).data
            }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsSuperAdmin])
def delete_admin_view(request, admin_id):
    """
    Delete admin user and all associated data.
    DELETE /api/auth/delete-admin/<admin_id>/

    This endpoint will:
    1. Delete all plan assignments for the admin
    2. Delete the admin user
    3. Return confirmation message

    Returns:
    {
        "message": "Admin deleted successfully",
        "deleted_admin": {
            "id": 2,
            "name": "John Smith Technology",
            "email": "admin@company.com",
            "company_id": "JOH001"
        }
    }
    """
    try:
        admin = User.objects.get(id=admin_id, role=User.Role.ADMIN)
    except User.DoesNotExist:
        return Response({'error': 'Admin not found'}, status=status.HTTP_404_NOT_FOUND)

    # Store admin info for response before deletion
    admin_info = {
        'id': admin.id,
        'name': admin.name,
        'email': admin.email,
        'company_id': admin.company_id
    }

    with transaction.atomic():
        # Delete all plan assignments for this admin
        UserPlanAssignment.objects.filter(user=admin).delete()
        
        # Delete the admin user
        admin.delete()

    return Response({
        'message': 'Admin deleted successfully',
        'deleted_admin': admin_info
    }, status=status.HTTP_200_OK)


# Plan Management Views

@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def create_plan_view(request):
    """
    Create a new plan (restricted to SuperAdmin).
    POST /api/auth/create-plan/

    Expected form data:
    {
        "plan_name": "basic",        // Options: "basic", "pro", "premium"
        "max_agents": 5,             // Frontend specifies agent count
        "price": "99.99"
    }

    Returns:
    {
        "id": 1,
        "plan_name": "basic",
        "plan_name_display": "Basic",
        "max_agents": 5,
        "price": "99.99",
        "is_active": true,
        "created_at": "2025-08-21T10:00:00Z"
    }
    """
    serializer = PlanCreateSerializer(data=request.data)
    if serializer.is_valid():
        with transaction.atomic():
            plan = serializer.save()
            response_serializer = PlanSerializer(plan)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def list_plans_view(request):
    """
    Get list of all plans.
    GET /api/auth/list-plans/

    Returns:
    [
        {
            "id": 1,
            "plan_name": "basic",
            "plan_name_display": "Basic",
            "company_name": "Tech Corp",
            "price": "99.99",
            "is_active": true,
            "created_at": "2025-08-21T10:00:00Z"
        }
    ]
    """
    plans = Plan.objects.filter(is_active=True).order_by('plan_name', 'price')
    serializer = PlanSerializer(plans, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def list_user_plan_assignments_view(request):
    """
    Get combined table of user plan assignments.
    GET /api/auth/list-user-plan-assignments/
    GET /api/auth/list-user-plan-assignments/?user_id=4  (for specific user)

    Query Parameters:
    - user_id (optional): Filter assignments for specific user

    Returns:
    [
        {
            "id": 1,
            "user_details": {
                "id": 2,
                "username": "admin1",
                "email": "admin1@example.com",
                "role": "ADMIN"
            },
            "plan_details": {
                "id": 1,
                "plan_name": "Basic",
                "max_agents": 5,
                "price": "99.99"
            },
            "start_date": "2025-08-21T10:00:00Z",
            "expiry_date": "2026-08-21T10:00:00Z",
            "status": "active",
            "days_remaining": 365,
            "is_expired": false,
            "notes": "Initial plan assignment",
            "created_at": "2025-08-21T10:00:00Z"
        }
    ]
    """
    assignments = UserPlanAssignment.objects.all().order_by('-created_at')

    # Filter by user_id if provided
    user_id = request.GET.get('user_id')
    if user_id:
        try:
            user_id = int(user_id)
            assignments = assignments.filter(user_id=user_id)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid user_id parameter'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = UserPlanAssignmentSerializer(assignments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Subscription Management Views

@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def cancel_subscription_view(request):
    """
    Cancel a user's subscription.
    POST /api/auth/cancel-subscription/

    Expected data:
    {
        "assignment_id": 1,
        "reason": "User requested cancellation"
    }
    """
    assignment_id = request.data.get('assignment_id')
    reason = request.data.get('reason', '')

    try:
        assignment = UserPlanAssignment.objects.get(id=assignment_id, status='active')
        assignment.cancel_subscription(reason)

        return Response({
            'message': 'Subscription cancelled successfully',
            'assignment': UserPlanAssignmentSerializer(assignment).data
        }, status=status.HTTP_200_OK)
    except UserPlanAssignment.DoesNotExist:
        return Response({'error': 'Active assignment not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def renew_subscription_view(request):
    """
    Renew a user's subscription.
    POST /api/auth/renew-subscription/

    Expected data:
    {
        "assignment_id": 1,
        "expiry_date": "2026-08-21T10:00:00Z"  // Optional
    }
    """
    assignment_id = request.data.get('assignment_id')
    expiry_date = request.data.get('expiry_date')

    try:
        assignment = UserPlanAssignment.objects.get(id=assignment_id)
        new_assignment = assignment.renew_subscription(expiry_date)

        return Response({
            'message': 'Subscription renewed successfully',
            'new_assignment': UserPlanAssignmentSerializer(new_assignment).data
        }, status=status.HTTP_201_CREATED)
    except UserPlanAssignment.DoesNotExist:
        return Response({'error': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def upgrade_plan_view(request):
    """
    Upgrade a user's plan.
    POST /api/auth/upgrade-plan/

    Expected data:
    {
        "assignment_id": 1,
        "new_plan_id": 2,
        "reason": "User requested upgrade"
    }
    """
    assignment_id = request.data.get('assignment_id')
    new_plan_id = request.data.get('new_plan_id')
    reason = request.data.get('reason', '')

    try:
        assignment = UserPlanAssignment.objects.get(id=assignment_id, status='active')
        new_plan = Plan.objects.get(id=new_plan_id, is_active=True)

        new_assignment = assignment.upgrade_plan(new_plan, reason)

        return Response({
            'message': 'Plan upgraded successfully',
            'new_assignment': UserPlanAssignmentSerializer(new_assignment).data
        }, status=status.HTTP_201_CREATED)
    except UserPlanAssignment.DoesNotExist:
        return Response({'error': 'Active assignment not found'}, status=status.HTTP_404_NOT_FOUND)
    except Plan.DoesNotExist:
        return Response({'error': 'New plan not found'}, status=status.HTTP_404_NOT_FOUND)
