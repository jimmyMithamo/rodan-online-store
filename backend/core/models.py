from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditLog(models.Model):
    """Track user actions for audit purposes"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    ip_address = models.GenericIPAddressField()
    action = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        user_info = self.user.email if self.user else 'Anonymous'
        return f"{user_info} - {self.action} at {self.timestamp}"
