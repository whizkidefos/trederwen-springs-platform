from django.contrib import admin
from .models import SiteSettings, Newsletter, ContactMessage, FAQ, Cart, CartItem

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'is_active', 'updated_at']
    list_filter = ['is_active']
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not SiteSettings.objects.exists()

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_subscribed', 'subscription_date']
    list_filter = ['is_subscribed', 'subscription_date']
    search_fields = ['email']
    actions = ['subscribe', 'unsubscribe']
    
    def subscribe(self, request, queryset):
        updated = queryset.update(is_subscribed=True)
        self.message_user(request, f'{updated} subscribers were subscribed.')
    
    def unsubscribe(self, request, queryset):
        updated = queryset.update(is_subscribed=False)
        self.message_user(request, f'{updated} subscribers were unsubscribed.')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject']
    readonly_fields = ['created_at']
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} messages were marked as read.')
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} messages were marked as unread.')

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['question', 'answer']
    ordering = ['order']