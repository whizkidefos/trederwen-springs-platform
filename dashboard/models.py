from django.db import models
from django.utils import timezone
import uuid

class DashboardWidget(models.Model):
    """Model to store dashboard widget configurations for admin users"""
    WIDGET_TYPES = [
        ('sales_chart', 'Sales Chart'),
        ('orders_summary', 'Orders Summary'),
        ('recent_orders', 'Recent Orders'),
        ('stock_levels', 'Stock Levels'),
        ('customer_activity', 'Customer Activity'),
        ('messages', 'Messages'),
        ('subscriptions', 'Subscriptions'),
        ('revenue', 'Revenue'),
        ('top_products', 'Top Products'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', related_name='dashboard_widgets', on_delete=models.CASCADE)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    title = models.CharField(max_length=100)
    position = models.PositiveSmallIntegerField(default=0)  # For ordering widgets
    size = models.CharField(max_length=20, default='medium')  # small, medium, large
    is_enabled = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)  # Widget-specific settings
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position']
        unique_together = ('user', 'widget_type')
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"


class AdminNote(models.Model):
    """Model for admin notes and reminders"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', related_name='admin_notes', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_pinned = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-is_pinned', 'is_completed', '-priority', 'due_date', '-created_at']
    
    def __str__(self):
        return self.title
    
    def mark_completed(self):
        """Mark note as completed"""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save(update_fields=['is_completed', 'completed_at'])
    
    def mark_incomplete(self):
        """Mark note as incomplete"""
        self.is_completed = False
        self.completed_at = None
        self.save(update_fields=['is_completed', 'completed_at'])


class AuditLog(models.Model):
    """Model to track admin actions for auditing purposes"""
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('export', 'Export'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', related_name='audit_logs', on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    action_model = models.CharField(max_length=50)  # The model being acted upon
    action_object_id = models.CharField(max_length=100)  # ID of the object being acted upon
    action_details = models.JSONField(default=dict, blank=True)  # Details of the action
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.email if self.user else 'Unknown'} - {self.get_action_type_display()} - {self.action_model}"
