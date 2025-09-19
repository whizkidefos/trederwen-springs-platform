from django.contrib import admin
from .models import (SubscriptionPlan, Subscription, SubscriptionItem, 
                    SubscriptionDelivery, SubscriptionDiscount)

class SubscriptionItemInline(admin.TabularInline):
    model = SubscriptionItem
    extra = 0

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'billing_interval', 'interval_count', 'base_price', 'discounted_price', 'is_active']
    list_filter = ['billing_interval', 'is_active']
    search_fields = ['name', 'description']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'next_billing_date', 'created_at']
    list_filter = ['status', 'plan', 'created_at']
    search_fields = ['user__email', 'plan__name']
    inlines = [SubscriptionItemInline]
    readonly_fields = ['stripe_subscription_id', 'created_at', 'updated_at']
    
    actions = ['pause_subscriptions', 'resume_subscriptions', 'cancel_subscriptions']
    
    def pause_subscriptions(self, request, queryset):
        updated = 0
        for subscription in queryset:
            if subscription.status == 'active':
                subscription.pause()
                updated += 1
        self.message_user(request, f'{updated} subscriptions were paused.')
    
    def resume_subscriptions(self, request, queryset):
        updated = 0
        for subscription in queryset:
            if subscription.status == 'paused':
                subscription.resume()
                updated += 1
        self.message_user(request, f'{updated} subscriptions were resumed.')
    
    def cancel_subscriptions(self, request, queryset):
        updated = 0
        for subscription in queryset:
            if subscription.status in ['active', 'paused']:
                subscription.cancel()
                updated += 1
        self.message_user(request, f'{updated} subscriptions were cancelled.')

@admin.register(SubscriptionDelivery)
class SubscriptionDeliveryAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'scheduled_date', 'status', 'total']
    list_filter = ['status', 'scheduled_date']
    search_fields = ['subscription__user__email']