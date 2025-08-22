import string
import secrets
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, Plan, UserPlanAssignment


class LoginSerializer(serializers.Serializer):
    """Serializer for user login with email/username and password."""
    
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            # Try to authenticate with username first, then email
            user = authenticate(username=username, password=password)
            if not user:
                # Try with email
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user and user.is_active:
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError('Invalid credentials or inactive account.')
        else:
            raise serializers.ValidationError('Must include username/email and password.')


class AdminCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new Admin users by SuperAdmin."""

    plan_id = serializers.IntegerField(write_only=True, help_text="Plan ID to assign")

    class Meta:
        model = User
        fields = ('email', 'address', 'contact_person', 'contact_number', 'phone_number', 'plan_id')
        extra_kwargs = {
            'email': {'required': True},
            'address': {'required': False},
            'contact_person': {'required': False},
            'contact_number': {'required': False},
            'phone_number': {'required': False},
        }

    def validate_plan_id(self, value):
        """Validate that the plan exists and is active."""
        try:
            plan = Plan.objects.get(id=value, is_active=True)
            return plan
        except Plan.DoesNotExist:
            raise serializers.ValidationError("Invalid plan ID or plan is not active.")

    def generate_password(self):
        """Generate a random 8-character alphanumeric password."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(8))

    def validate_email(self, value):
        """Check if email already exists."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """Create new Admin user with generated password and plan assignment."""
        # Generate random password
        password = self.generate_password()

        # Get plan from validated plan_id
        plan = validated_data.pop('plan_id')

        # Create username from email (before @ symbol)
        email = validated_data['email']
        username = email.split('@')[0]

        # Ensure username is unique
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Create user without plan reference
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=username.title(),  # Use username as first name
            last_name='Admin',
            role=User.Role.ADMIN,
            address=validated_data.get('address', ''),
            contact_person=validated_data.get('contact_person', ''),
            contact_number=validated_data.get('contact_number', ''),
            phone_number=validated_data.get('phone_number', ''),
            generated_password=password  # Store generated password
        )

        # Create plan assignment
        UserPlanAssignment.objects.create(
            user=user,
            plan=plan,
            notes="Initial plan assignment"
        )

        # Store password for response
        user._generated_password = password
        user._assigned_plan = plan
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details."""

    current_plan = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'address', 'contact_person', 'contact_number', 'phone_number', 'current_plan', 'generated_password', 'date_joined')
        read_only_fields = ('id', 'date_joined')

    def get_current_plan(self, obj):
        assignment = obj.current_plan_assignment
        if assignment:
            return {
                'id': assignment.plan.id,
                'name': assignment.plan.get_plan_name_display(),
                'max_agents': assignment.plan.max_agents,
                'price': str(assignment.plan.price)
            }
        return None


class AdminListSerializer(serializers.ModelSerializer):
    """Serializer for listing admin users with complete information."""

    current_plan = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'address', 'contact_person', 'contact_number', 'phone_number', 'current_plan', 'generated_password', 'date_joined', 'is_active')
        read_only_fields = ('id', 'username', 'generated_password', 'date_joined')

    def get_current_plan(self, obj):
        assignment = obj.current_plan_assignment
        if assignment:
            return {
                'assignment_id': assignment.id,
                'plan_id': assignment.plan.id,
                'plan_name': assignment.plan.get_plan_name_display(),
                'max_agents': assignment.plan.max_agents,
                'price': str(assignment.plan.price),
                'start_date': assignment.start_date,
                'expiry_date': assignment.expiry_date,
                'status': assignment.status,
                'days_remaining': assignment.days_remaining
            }
        return None


class AdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating admin user information."""

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'address', 'contact_person', 'contact_number', 'phone_number')
        extra_kwargs = {
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'address': {'required': False},
            'contact_person': {'required': False},
            'contact_number': {'required': False},
            'phone_number': {'required': False},
        }

    def validate_email(self, value):
        # Check if email is already taken by another user
        if value and User.objects.filter(email=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value


class AdminPlanChangeSerializer(serializers.Serializer):
    """Serializer for changing admin's plan."""

    new_plan_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=500, required=False, default="Plan changed by SuperAdmin")

    def validate_new_plan_id(self, value):
        try:
            plan = Plan.objects.get(id=value, is_active=True)
            return plan
        except Plan.DoesNotExist:
            raise serializers.ValidationError("Invalid plan ID or plan is not active.")


class PlanSerializer(serializers.ModelSerializer):
    """Serializer for Plan model."""

    plan_name_display = serializers.CharField(source='get_plan_name_display', read_only=True)

    class Meta:
        model = Plan
        fields = ('id', 'plan_name', 'plan_name_display', 'max_agents', 'price', 'is_active', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value


class PlanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new plans."""

    class Meta:
        model = Plan
        fields = ('plan_name', 'max_agents', 'price')
        extra_kwargs = {
            'plan_name': {'required': True},
            'max_agents': {'required': True},
            'price': {'required': True},
        }

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_max_agents(self, value):
        if value <= 0:
            raise serializers.ValidationError("Max agents must be greater than 0.")
        return value


class UserPlanAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for UserPlanAssignment model."""

    user_details = serializers.SerializerMethodField()
    plan_details = serializers.SerializerMethodField()
    days_remaining = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = UserPlanAssignment
        fields = ('id', 'user', 'user_details', 'plan', 'plan_details', 'start_date', 'expiry_date', 'status', 'status_display', 'days_remaining', 'is_expired', 'notes', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'role': obj.user.role
        }

    def get_plan_details(self, obj):
        return {
            'id': obj.plan.id,
            'plan_name': obj.plan.get_plan_name_display(),
            'max_agents': obj.plan.max_agents,
            'price': str(obj.plan.price)
        }





class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response with user role."""
    
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
    
    @classmethod
    def get_token_response(cls, user):
        """Generate token response for authenticated user."""
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }
