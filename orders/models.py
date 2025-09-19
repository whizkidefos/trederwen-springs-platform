# orders/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel
import uuid

User = get_user_model()

class Order(BaseModel):
    """Order model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField()
    
    # Order status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Addresses
    billing_address = models.JSONField(default=dict)
    shipping_address = models.JSONField(default=dict)
    
    # Shipping
    shipping_method = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Payment
    payment_method = models.CharField(max_length=50, blank=True)
    payment_intent_id = models.CharField(max_length=200, blank=True)  # Stripe payment intent
    
    # Notes
    notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Coupons and discounts
    coupon_code = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            last_order = Order.objects.order_by('-created_at').first()
            if last_order and last_order.order_number:
                last_number = int(last_order.order_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1000
            self.order_number = f"TS-{new_number:06d}"
        super().save(*args, **kwargs)
    
    @property
    def can_be_cancelled(self):
        return self.status in ['pending', 'processing']
    
    @property
    def is_paid(self):
        return self.payment_status == 'paid'
    
    def calculate_total(self):
        """Recalculate order total"""
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.total = self.subtotal + self.tax_amount + self.shipping_amount - self.discount_amount
        return self.total
    
    def mark_as_shipped(self, tracking_number=None):
        """Mark order as shipped"""
        self.status = 'shipped'
        self.shipped_at = timezone.now()
        if tracking_number:
            self.tracking_number = tracking_number
        self.save()
    
    def mark_as_delivered(self):
        """Mark order as delivered"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()

class OrderItem(BaseModel):
    """Individual items in an order"""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Store product details at time of purchase
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=100)
    product_data = models.JSONField(default=dict)  # Snapshot of product data
    
    def __str__(self):
        return f"{self.quantity} x {self.product_name}"
    
    def save(self, *args, **kwargs):
        self.product_name = self.product.name
        self.product_sku = self.product.sku
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class ShippingMethod(BaseModel):
    """Available shipping methods"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_days_min = models.PositiveIntegerField()
    estimated_days_max = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} - £{self.price}"
    
    def get_price_for_order(self, order_total):
        """Get shipping price for a given order total"""
        if self.free_shipping_threshold and order_total >= self.free_shipping_threshold:
            return Decimal('0.00')
        return self.price

class Coupon(BaseModel):
    """Discount coupons"""
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
        ('free_shipping', 'Free Shipping'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    user_usage_limit = models.PositiveIntegerField(default=1)
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Restrictions
    applicable_products = models.ManyToManyField('products.Product', blank=True)
    applicable_categories = models.ManyToManyField('products.Category', blank=True)
    
    def __str__(self):
        return self.code
    
    @property
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and 
            self.valid_from <= now <= self.valid_until and
            (self.usage_limit is None or self.usage_count < self.usage_limit)
        )
    
    def can_be_used_by_user(self, user):
        """Check if coupon can be used by a specific user"""
        if not self.is_valid:
            return False
        
        if user.is_authenticated:
            user_usage = CouponUsage.objects.filter(coupon=self, user=user).count()
            return user_usage < self.user_usage_limit
        return True
    
    def calculate_discount(self, order_total):
        """Calculate discount amount for given order total"""
        if not self.is_valid:
            return Decimal('0.00')
        
        if self.minimum_order_amount and order_total < self.minimum_order_amount:
            return Decimal('0.00')
        
        if self.discount_type == 'percentage':
            return (order_total * self.discount_value) / 100
        elif self.discount_type == 'fixed_amount':
            return min(self.discount_value, order_total)
        return Decimal('0.00')

class CouponUsage(BaseModel):
    """Track coupon usage"""
    coupon = models.ForeignKey(Coupon, related_name='usages', on_delete=models.CASCADE)
    order = models.ForeignKey(Order, related_name='coupon_usages', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='coupon_usages', on_delete=models.CASCADE, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.coupon.code} used in {self.order.order_number}"

class OrderStatusHistory(BaseModel):
    """Track order status changes"""
    order = models.ForeignKey(Order, related_name='status_history', on_delete=models.CASCADE)
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Order Status Histories"
    
    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} → {self.new_status}"

class Refund(BaseModel):
    """Refund model"""
    REFUND_REASONS = [
        ('damaged', 'Damaged Product'),
        ('wrong_item', 'Wrong Item Sent'),
        ('not_as_described', 'Not as Described'),
        ('defective', 'Defective Product'),
        ('customer_change_mind', 'Customer Changed Mind'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    order = models.ForeignKey(Order, related_name='refunds', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=30, choices=REFUND_REASONS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    description = models.TextField()
    admin_notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_refunds')
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Refund #{self.id} for {self.order.order_number}"
    
    def approve(self, processed_by=None):
        """Approve the refund"""
        self.status = 'approved'
        self.processed_by = processed_by
        self.processed_at = timezone.now()
        self.save()
    
    def reject(self, processed_by=None, notes=''):
        """Reject the refund"""
        self.status = 'rejected'
        self.processed_by = processed_by
        self.processed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()