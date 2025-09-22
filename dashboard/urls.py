from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard home
    path('', views.dashboard, name='index'),
    
    # Orders management
    path('orders/', views.orders, name='orders'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_number>/update-status/', views.update_order_status, name='update_order_status'),
    
    # Products management
    path('products/', views.products, name='products'),
    
    # Customers management
    path('customers/', views.customers, name='customers'),
    
    # Messages management
    path('messages/', views.messages_view, name='messages'),
    
    # Analytics and reporting
    path('analytics/', views.analytics, name='analytics'),
    
    # Settings
    path('settings/', views.settings_view, name='settings'),
    
    # Admin users management (superuser only)
    path('admin-users/', views.admin_users, name='admin_users'),
    path('admin-users/<str:user_id>/edit/', views.edit_admin_user, name='edit_admin_user'),
    
    # Audit logs (superuser only)
    path('audit-logs/', views.audit_logs, name='audit_logs'),
]
