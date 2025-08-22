from django.db import models
from django.utils import timezone
from authentication.models import User


class Agent(models.Model):
    """Agent model for managing agents in admin dashboard."""

    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('BUSY', 'Busy'),
        ('OFFLINE', 'Offline'),
    ]

    # Basic Information
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='agent_profile',
        limit_choices_to={'role': User.Role.AGENT}
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    specialization = models.CharField(max_length=200)
    company_id = models.CharField(max_length=20, null=True, blank=True, help_text="Company ID of the admin who created this agent")

    # Status and Activity Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OFFLINE')
    last_active = models.DateTimeField(null=True, blank=True)
    is_first_login = models.BooleanField(default=True)

    # Admin who created this agent
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_agents',
        limit_choices_to={'role__in': [User.Role.ADMIN, User.Role.SUPERADMIN]}
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.status}"

    def update_status(self, new_status):
        """Update agent status and last_active timestamp."""
        self.status = new_status
        if new_status == 'OFFLINE':
            self.last_active = timezone.now()
        self.save()

    def set_online(self):
        """Set agent status to AVAILABLE when they login."""
        self.update_status('AVAILABLE')

    def set_busy(self):
        """Set agent status to BUSY when they start chatting."""
        self.update_status('BUSY')

    def set_offline(self):
        """Set agent status to OFFLINE when they logout."""
        self.update_status('OFFLINE')

    @property
    def formatted_last_active(self):
        """Return formatted last active time."""
        if self.last_active:
            return self.last_active.strftime("%d/%m/%Y %H:%M")
        return "Never"


class AgentSession(models.Model):
    """Track agent login/logout sessions for analytics."""

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='sessions')
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    session_duration = models.DurationField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.agent.name} - {self.login_time.strftime('%d/%m/%Y %H:%M')}"

    def end_session(self):
        """End the session and calculate duration."""
        if not self.logout_time:
            self.logout_time = timezone.now()
            self.session_duration = self.logout_time - self.login_time
            self.save()

            # Update agent's last active time
            self.agent.set_offline()
