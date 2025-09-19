# subscriptions/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from core.models import BaseModel

User = get_user_model()

class SubscriptionPlan(BaseModel):
    """Subscription plan templates"""
    BILLING_INTERVALS = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    billing_interval = models.CharField(max_length=20, choices=BILLING_INTERVALS)
    interval_count = models.PositiveIntegerField(default=1)  # e.g., every 2 months
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Plan features
    free_shipping = models.BooleanField(default=True)
    priority_support = models.BooleanField(default=False)
    exclusive_products = models.BooleanField(default=False)
    flexible_delivery = models.BooleanField(default=True)
    
    # Plan constraints
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_items_per_delivery = models.PositiveIntegerField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_billing_interval_display()}"
    
    @property
    def discounted_price(self):
        """Get price after discount"""
        if self.discount_percentage > 0:
            discount_amount = (self.base_price * self.discount_percentage) / 100
            return self.base_price - discount_amount
        return self.base_price
    
    def get_next_billing_date(self, start_date=None):
        """Calculate next billing date"""
        if not start_date:
            start_date = timezone.now().date()
        
        if self.billing_interval == 'weekly':
            return start_date + relativedelta(weeks=self.interval_count)
        elif self.billing_interval == 'monthly':
            return start_date + relativedelta(months=self.interval_count)
        elif self.billing_interval == 'quarterly':
            return start_date + relativedelta(months=3 * self.interval_count)
        elif self.billing_interval == 'yearly':
            return start_date + relativedelta(years=self.interval_count)
        
        return start_date

class Subscription(BaseModel):
    """User subscriptions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('pending', 'Pending'),
    ]
    
    user = models.ForeignKey(User, related_name='subscriptions', on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, related_name='subscriptions', on_delete=models.CASCADE)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Billing
    current_period_start = models.DateField()
    current_period_end = models.DateField()
    next_billing_date = models.DateField()
    
    # Pricing (captured at subscription creation)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Delivery preferences
    delivery_address = models.JSONField(default=dict)
    delivery_instructions = models.TextField(blank=True)
    preferred_delivery_day = models.CharField(max_length=10, blank=True)  # monday, tuesday, etc.
    
    # Payment
    stripe_subscription_id = models.CharField(max_length=200, blank=True)
    payment_method_id = models.CharField(max_length=200, blank=True)
    
    # Pause/Resume
    paused_at = models.DateTimeField(null=True, blank=True)
    pause_reason = models.TextField(blank=True)
    auto_resume_date = models.DateField(null=True, blank=True)
    
    # Cancellation
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.plan.name}"
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def days_until_next_billing(self):
        if self.next_billing_date:
            delta = self.next_billing_date - timezone.now().date()
            return delta.days
        return 0
    
    def pause(self, reason='', auto_resume_date=None):
        """Pause the subscription"""
        self.status = 'paused'
        self.paused_at = timezone.now()
        self.pause_reason = reason
        self.auto_resume_date = auto_resume_date
        self.save()
    
    def resume(self):
        """Resume a paused subscription"""
        if self.status == 'paused':
            self.status = 'active'
            self.paused_at = None
            self.pause_reason = ''
            self.auto_resume_date = None
            # Recalculate next billing date
            self.next_billing_date = self.plan.get_next_billing_date(timezone.now().date())
            self.save()
    
    def cancel(self, reason='', immediately=False):
        """Cancel the subscription"""
        self.cancellation_reason = reason
        if immediately:
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
        else:
            self.cancel_at_period_end = True
        self.save()
    
    def renew_period(self):
        """Renew to next billing period"""
        self.current_period_start = self.current_period_end
        self.current_period_end = self.plan.get_next_billing_date(self.current_period_end)
        self.next_billing_date = self.current_period_end
        self.save()

class SubscriptionItem(BaseModel):
    """Items in a subscription"""
    subscription = models.ForeignKey(Subscription, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Delivery frequency override (if different from subscription)
    custom_interval = models.CharField(max_length=20, blank=True)
    custom_interval_count = models.PositiveIntegerField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('subscription', 'product', 'variant')
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price

class SubscriptionDelivery(BaseModel):
    """Individual deliveries from subscriptions"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('skipped', 'Skipped'),
        ('failed', 'Failed'),
    ]
    
    subscription = models.ForeignKey(Subscription, related_name='deliveries', on_delete=models.CASCADE)
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    
    # Delivery details
    scheduled_date = models.DateField()
    delivered_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Items for this delivery
    items = models.JSONField(default=list)  # Snapshot of subscription items at time of delivery
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Skip/failure details
    skip_reason = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    next_retry_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"Delivery for {self.subscription} - {self.scheduled_date}"
    
    def skip(self, reason=''):
        """Skip this delivery"""
        self.status = 'skipped'
        self.skip_reason = reason
        self.save()
    
    def create_order(self):
        """Create an order for this delivery"""
        if self.order:
            return self.order
        
        from orders.models import Order, OrderItem
        
        # Create order
        order = Order.objects.create(
            user=self.subscription.user,
            email=self.subscription.user.email,
            status='processing',
            subtotal=self.subtotal,
            total=self.total,
            shipping_address=self.subscription.delivery_address,
            billing_address=self.subscription.delivery_address,
            notes=f"Subscription delivery for {self.subscription.plan.name}"
        )
        
        # Create order items
        for item_data in self.items:
            OrderItem.objects.create(
                order=order,
                product_id=item_data['product_id'],
                variant_id=item_data.get('variant_id'),
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                product_name=item_data['product_name'],
                product_sku=item_data['product_sku']
            )
        
        self.order = order
        self.status = 'processing'
        self.save()
        
        return order

class SubscriptionPause(BaseModel):
    """Track subscription pause periods"""
    subscription = models.ForeignKey(Subscription, related_name='pause_periods', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    reason = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        end_str = f" to {self.end_date}" if self.end_date else " (ongoing)"
        return f"Pause from {self.start_date}{end_str}"
    
    def end_pause(self):
        """End the pause period"""
        self.end_date = timezone.now().date()
        self.is_active = False
        self.save()

class SubscriptionDiscount(BaseModel):
    """Discounts applied to subscriptions"""
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
        ('free_shipping', 'Free Shipping'),
    ]
    
    subscription = models.ForeignKey(Subscription, related_name='discounts', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Duration
    duration_in_cycles = models.PositiveIntegerField(null=True, blank=True, help_text="Number of billing cycles, null for permanent")
    cycles_used = models.PositiveIntegerField(default=0)
    
    # Validity
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.subscription}"
    
    @property
    def is_valid(self):
        """Check if discount is currently valid"""
        today = timezone.now().date()
        
        # Check active status
        if not self.is_active:
            return False
        
        # Check date range
        if today < self.valid_from:
            return False
        
        if self.valid_until and today > self.valid_until:
            return False
        
        # Check cycle limit
        if self.duration_in_cycles and self.cycles_used >= self.duration_in_cycles:
            return False
        
        return True
    
    def apply_discount(self, amount):
        """Calculate discount amount for given price"""
        if not self.is_valid:
            return Decimal('0.00')
        
        if self.discount_type == 'percentage':
            return (amount * self.discount_value) / 100
        elif self.discount_type == 'fixed_amount':
            return min(self.discount_value, amount)
        
        return Decimal('0.00')
    
    def use_cycle(self):
        """Mark one cycle as used"""
        self.cycles_used += 1
        self.save()
        
        # Deactivate if limit reached
        if self.duration_in_cycles and self.cycles_used >= self.duration_in_cycles:
            self.is_active = False
            self.save()

class SubscriptionChangeLog(BaseModel):
    """Log all changes to subscriptions"""
    subscription = models.ForeignKey(Subscription, related_name='change_logs', on_delete=models.CASCADE)
    change_type = models.CharField(max_length=50)  # 'status_change', 'item_added', 'item_removed', etc.
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    description = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subscription} - {self.change_type}"

class SubscriptionNotification(BaseModel):
    """Notifications related to subscriptions"""
    NOTIFICATION_TYPES = [
        ('upcoming_delivery', 'Upcoming Delivery'),
        ('payment_failed', 'Payment Failed'),
        ('subscription_paused', 'Subscription Paused'),
        ('subscription_resumed', 'Subscription Resumed'),
        ('subscription_cancelled', 'Subscription Cancelled'),
        ('delivery_skipped', 'Delivery Skipped'),
        ('price_change', 'Price Change'),
    ]
    
    subscription = models.ForeignKey(Subscription, related_name='notifications', on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    
    # Related objects
    delivery = models.ForeignKey(SubscriptionDelivery, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.subscription.user.get_full_name()}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save()

# Signal handlers and utility functions would go here
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

@receiver(post_save, sender=Subscription)
def create_initial_delivery(sender, instance, created, **kwargs):
    """Create first delivery when subscription is created"""
    if created and instance.status == 'active':
        # Create the first scheduled delivery
        SubscriptionDelivery.objects.create(
            subscription=instance,
            scheduled_date=instance.next_billing_date,
            items=[],  # Will be populated by a background task
            subtotal=instance.price,
            total=instance.price
        )

@receiver(pre_save, sender=Subscription)
def log_subscription_changes(sender, instance, **kwargs):
    """Log changes to subscription"""
    if instance.pk:  # Only for updates, not creation
        try:
            old_instance = Subscription.objects.get(pk=instance.pk)
            
            # Check for status changes
            if old_instance.status != instance.status:
                SubscriptionChangeLog.objects.create(
                    subscription=instance,
                    change_type='status_change',
                    old_value={'status': old_instance.status},
                    new_value={'status': instance.status},
                    description=f"Status changed from {old_instance.get_status_display()} to {instance.get_status_display()}"
                )
        except Subscription.DoesNotExist:
            pass