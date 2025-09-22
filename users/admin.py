from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address, UserPreference, UserActivity

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'user_type', 'is_staff', 'created_at']
    list_filter = ['user_type', 'is_staff', 'is_superuser', 'is_active', 'created_at', 'marketing_emails']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = list(BaseUserAdmin.fieldsets) + [
        ('User Type', {
            'fields': ('user_type',)
        }),
        ('Admin Information', {
            'fields': ('admin_title', 'admin_department', 'admin_bio'),
            'classes': ('collapse',),
            'description': 'These fields are only relevant for users with Admin user type.'
        }),
        ('Personal Info', {
            'fields': ('phone', 'date_of_birth', 'avatar')
        }),
        ('Preferences', {
            'fields': ('is_newsletter_subscribed', 'dietary_preferences', 'flavor_preferences', 
                      'marketing_emails', 'sms_notifications')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_active', 'last_login_ip'),
            'classes': ('collapse',)
        }),
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'last_active', 'last_login_ip']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.user_type == 'admin':
            # Make admin fields visible for admin users
            if 'admin_title' in form.base_fields:
                form.base_fields['admin_title'].widget.attrs['class'] = 'vTextField'
            if 'admin_department' in form.base_fields:
                form.base_fields['admin_department'].widget.attrs['class'] = 'vTextField'
            if 'admin_bio' in form.base_fields:
                form.base_fields['admin_bio'].widget.attrs['class'] = 'vLargeTextField'
        return form

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'address_type', 'first_name', 'last_name', 'city', 'postcode', 'is_default']
    list_filter = ['address_type', 'is_default', 'country']
    search_fields = ['user__email', 'first_name', 'last_name', 'city', 'postcode']

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'object_id', 'timestamp']
    list_filter = ['activity_type', 'timestamp']
    search_fields = ['user__email', 'session_key']
    readonly_fields = ['timestamp']