# users/models.py
from django.contrib.auth.models import AbstractUser, Permission, Group
from django.db import models
from django.urls import reverse
from django.utils import timezone
import uuid

class User(AbstractUser):
    """Custom user model with additional fields"""
    USER_TYPES = [
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_newsletter_subscribed = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # User type and admin-specific fields
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='customer')
    admin_title = models.CharField(max_length=100, blank=True)
    admin_department = models.CharField(max_length=100, blank=True)
    admin_bio = models.TextField(blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_active = models.DateTimeField(null=True, blank=True)
    
    # Preferences for AI recommendations
    dietary_preferences = models.JSONField(default=dict, blank=True)
    flavor_preferences = models.JSONField(default=dict, blank=True)
    
    # Marketing preferences
    marketing_emails = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def get_absolute_url(self):
        return reverse('users:profile')
    
    @property
    def total_orders(self):
        return self.orders.count()
    
    @property
    def total_spent(self):
        return sum(order.total for order in self.orders.filter(status='completed'))
        
    @property
    def is_admin_user(self):
        """Check if user is an admin"""
        return self.user_type == 'admin'
    
    def update_last_active(self):
        """Update the last active timestamp"""
        self.last_active = timezone.now()
        self.save(update_fields=['last_active'])
        
    def get_admin_permissions(self):
        """Get all permissions for admin user"""
        if not self.is_admin_user:
            return Permission.objects.none()
            
        return Permission.objects.filter(
            group__user=self
        ).select_related('content_type').order_by('content_type__app_label')

class Address(models.Model):
    """User address model for billing and shipping"""
    ADDRESS_TYPES = [
        ('billing', 'Billing'),
        ('shipping', 'Shipping'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, related_name='addresses', on_delete=models.CASCADE)
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES)
    company = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50)
    county = models.CharField(max_length=50, blank=True)
    postcode = models.CharField(max_length=10)
    country = models.CharField(max_length=50, default='United Kingdom')
    phone = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Addresses"
        unique_together = ('user', 'address_type', 'is_default')
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.get_address_type_display()}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_address(self):
        parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.county,
            self.postcode,
            self.country
        ]
        return ', '.join([part for part in parts if part])
    
    def save(self, *args, **kwargs):
        # Ensure only one default address per type per user
        if self.is_default:
            Address.objects.filter(
                user=self.user,
                address_type=self.address_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

class UserPreference(models.Model):
    """Store user preferences for personalization"""
    PREFERENCE_TYPES = [
        ('flavor', 'Flavor Preference'),
        ('dietary', 'Dietary Requirement'),
        ('delivery', 'Delivery Preference'),
        ('communication', 'Communication Preference'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, related_name='preferences', on_delete=models.CASCADE)
    preference_type = models.CharField(max_length=20, choices=PREFERENCE_TYPES)
    key = models.CharField(max_length=50)
    value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'preference_type', 'key')
    
    def __str__(self):
        return f"{self.user.email} - {self.preference_type}: {self.key}"

class UserActivity(models.Model):
    """Track user activity for analytics and recommendations"""
    ACTIVITY_TYPES = [
        ('view_product', 'Viewed Product'),
        ('add_to_cart', 'Added to Cart'),
        ('remove_from_cart', 'Removed from Cart'),
        ('start_checkout', 'Started Checkout'),
        ('complete_purchase', 'Completed Purchase'),
        ('view_category', 'Viewed Category'),
        ('search', 'Search'),
        ('newsletter_signup', 'Newsletter Signup'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('admin_login', 'Admin Login'),
        ('admin_action', 'Admin Action'),
        ('message_sent', 'Message Sent'),
        ('message_read', 'Message Read'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, related_name='activities', on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=50, blank=True)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    object_id = models.CharField(max_length=100, blank=True)  # ID of the object being interacted with
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        user_id = self.user.email if self.user else self.session_key
        return f"{user_id} - {self.get_activity_type_display()}"


class Message(models.Model):
    """Message model for communication between users and admins"""
    MESSAGE_TYPES = [
        ('system', 'System Message'),
        ('user_to_admin', 'User to Admin'),
        ('admin_to_user', 'Admin to User'),
        ('broadcast', 'Broadcast Message'),
    ]
    
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE, null=True, blank=True)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE, null=True, blank=True)
    message_type = models.CharField(max_length=15, choices=MESSAGE_TYPES)
    subject = models.CharField(max_length=255)
    content = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unread')
    is_important = models.BooleanField(default=False)
    parent = models.ForeignKey('self', related_name='replies', on_delete=models.CASCADE, null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)  # e.g., 'order', 'product', etc.
    related_object_id = models.CharField(max_length=100, blank=True)  # ID of the related object
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} - {self.get_message_type_display()}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if self.status == 'unread':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at'])
            
            # Log activity
            if self.recipient:
                UserActivity.objects.create(
                    user=self.recipient,
                    activity_type='message_read',
                    object_id=str(self.id),
                    metadata={
                        'message_type': self.message_type,
                        'subject': self.subject
                    }
                )
    
    def archive(self):
        """Archive message"""
        self.status = 'archived'
        self.save(update_fields=['status'])
    
    @property
    def thread(self):
        """Get all messages in the same thread"""
        if self.parent:
            return self.parent.replies.all()
        return self.replies.all()


class MessageAttachment(models.Model):
    """Attachments for messages"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='message_attachments/')
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # Size in bytes
    file_type = models.CharField(max_length=100)  # MIME type
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.file_name


class Notification(models.Model):
    """Notification model for system and user notifications"""
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('order_status', 'Order Status Update'),
        ('system', 'System Notification'),
        ('promotion', 'Promotional Notification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=15, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])