from django import template
from django.urls import reverse

register = template.Library()

@register.simple_tag
def get_dashboard_url():
    """Return the URL to the dashboard"""
    return reverse('dashboard:index')

@register.simple_tag
def is_admin_user(user):
    """Check if user is an admin"""
    return user.user_type == 'admin' or user.is_superuser
