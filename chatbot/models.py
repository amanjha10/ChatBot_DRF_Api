# chatbot/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid

class ChatSession(models.Model):
    SESSION_STATUS_CHOICES = [
        ('active', 'Active'),
        ('escalated', 'Escalated to Human'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PROFILE_COLLECTION_STATES = [
        ('name', 'Collecting Name'),
        ('country_code', 'Collecting Country Code'),
        ('phone', 'Collecting Phone'),
        ('email', 'Collecting Email'),
        ('address', 'Collecting Address'),
        ('complete', 'Profile Complete'),
    ]
    
    session_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    company_id = models.CharField(max_length=20, default='DEFAULT_COMPANY', help_text="Company ID for multi-tenant isolation")
    user_profile = models.ForeignKey('UserProfile', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=SESSION_STATUS_CHOICES, default='active')
    profile_completed = models.BooleanField(default=False)
    profile_collection_state = models.CharField(max_length=20, choices=PROFILE_COLLECTION_STATES, default='name')
    temp_profile_data = models.JSONField(default=dict, blank=True)  # Store temporary profile data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Session {self.session_id} - {self.status}"

class UserProfile(models.Model):
    session_id = models.CharField(max_length=100)
    company_id = models.CharField(max_length=20, default='DEFAULT_COMPANY', help_text="Company ID for multi-tenant isolation")
    persistent_user_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)  # Added address field
    country_code = models.CharField(max_length=10, default='+977')
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.phone}"

class ChatMessage(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
        ('agent', 'Agent'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES)
    content = models.TextField(blank=True, null=True)  # Allow empty content for file-only messages
    attachments = models.ManyToManyField('UploadedFile', blank=True, related_name='chat_messages')
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        attachment_count = self.attachments.count()
        content_preview = self.content[:50] if self.content else f"[{attachment_count} attachments]"
        return f"{self.message_type}: {content_preview}"

class UploadedFile(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    company_id = models.CharField(max_length=20, default='DEFAULT_COMPANY', help_text="Company ID for multi-tenant isolation")
    original_name = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)
    filepath = models.CharField(max_length=500)
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=10)
    message_context = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def get_file_url(self):
        """Get the URL to access the uploaded file"""
        from django.conf import settings
        return f"{settings.MEDIA_URL}{self.filepath}"
    
    def __str__(self):
        return f"{self.original_name} - {self.file_type}"

class RAGDocument(models.Model):
    """Model to store RAG documents and FAQ data"""
    chunk_id = models.CharField(max_length=100, unique=True)
    question = models.TextField()
    answer = models.TextField()
    section = models.CharField(max_length=100)
    document = models.CharField(max_length=200)
    page = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.section}: {self.question[:50]}"
