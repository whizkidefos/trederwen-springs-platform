# core/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class BaseModel(models.Model):
    """Base model with common fields for all models"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Cart(models.Model):
    """Shopping cart model for session-based carts"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart {self.id}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())
    
    def clear(self):
        self.items.all().delete()

class CartItem(models.Model):
    """Individual items in a cart"""
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('cart', 'product')
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    @property
    def total_price(self):
        return self.quantity * self.product.price

class SiteSettings(BaseModel):
    """Global site settings"""
    site_name = models.CharField(max_length=100, default="Trederwen Springs")
    site_description = models.TextField(default="Premium Welsh Spring Water")
    contact_email = models.EmailField(default="info@trederwensprings.co.uk")
    contact_phone = models.CharField(max_length=20, default="+44 1234 567890")
    address = models.TextField(default="Wales, UK")
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    delivery_info = models.TextField(default="Free delivery on orders over £25")
    returns_policy = models.TextField(default="30-day returns policy")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return self.site_name
    
    @classmethod
    def get_settings(cls):
        """Get the active site settings"""
        return cls.objects.filter(is_active=True).first() or cls.objects.create()

class Newsletter(BaseModel):
    """Newsletter subscription model"""
    email = models.EmailField(unique=True)
    is_subscribed = models.BooleanField(default=True)
    subscription_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.email

class ContactMessage(BaseModel):
    """Contact form messages"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    replied_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.name} - {self.subject}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()

class FAQ(BaseModel):
    """Frequently Asked Questions"""
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    
    def __str__(self):
        return self.question