# chatbot/serializers.py
from rest_framework import serializers
from .models import ChatSession, UserProfile, ChatMessage, UploadedFile, RAGDocument

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'session_id', 'company_id', 'persistent_user_id', 'name', 'phone', 'email', 'address', 'country_code', 'created_at', 'last_used']
        read_only_fields = ['id', 'persistent_user_id', 'created_at', 'last_used']

class ChatSessionSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = ChatSession
        fields = ['id', 'session_id', 'company_id', 'user_profile', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'session_id', 'created_at', 'updated_at']

class UploadedFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UploadedFile
        fields = ['id', 'session', 'user_profile', 'company_id', 'original_name', 'filename', 
                 'file_size', 'file_type', 'file_url', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at', 'file_url']
    
    def get_file_url(self, obj):
        return obj.get_file_url()

class ChatMessageSerializer(serializers.ModelSerializer):
    attachments = UploadedFileSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'message_type', 'content', 'attachments', 'metadata', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class RAGDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RAGDocument
        fields = ['id', 'chunk_id', 'question', 'answer', 'section', 'document', 'page', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

# Request/Response Serializers
class FileUploadRequestSerializer(serializers.Serializer):
    file = serializers.FileField()
    session_id = serializers.CharField(max_length=100)
    company_id = serializers.CharField(max_length=20, required=False, default='DEFAULT_COMPANY')
    message_context = serializers.CharField(max_length=500, required=False, allow_blank=True)

class FileUploadResponseSerializer(serializers.Serializer):
    file_id = serializers.IntegerField()
    file_url = serializers.CharField()
    original_name = serializers.CharField()
    file_size = serializers.IntegerField()
    file_type = serializers.CharField()
    message = serializers.CharField()

class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    session_id = serializers.CharField(max_length=100, required=False)
    context = serializers.CharField(max_length=500, required=False, default='Initial conversation')
    company_id = serializers.CharField(max_length=20, required=False, help_text="Company ID for multi-tenant isolation")
    attachment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of uploaded file IDs to attach to this message"
    )
    
    def validate(self, data):
        # Ensure either message or attachment_ids is provided
        message = data.get('message', '').strip()
        attachment_ids = data.get('attachment_ids', [])
        
        if not message and not attachment_ids:
            raise serializers.ValidationError("Either message content or attachments must be provided")
        
        return data

class ChatResponseSerializer(serializers.Serializer):
    response = serializers.CharField()
    suggestions = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    type = serializers.CharField(required=False, default='bot_response')
    escalated = serializers.BooleanField(required=False, default=False)
    session_id = serializers.CharField(required=False)
    persistent_user_id = serializers.CharField(required=False)
    attachments = UploadedFileSerializer(many=True, required=False, default=list)
    user_message = ChatMessageSerializer(required=False)

class ProfileCollectionRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    phone = serializers.CharField(max_length=20, required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    country_code = serializers.CharField(max_length=10, required=False, default='+977')
    session_id = serializers.CharField(max_length=100, required=False)

class PhoneValidationRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    country_code = serializers.CharField(max_length=10, default='+977')

class PhoneValidationResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    message = serializers.CharField()
    provider = serializers.CharField(required=False, allow_null=True)
