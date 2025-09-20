from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Profile views
    path('profile/', views.profile_dashboard, name='profile_dashboard'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/addresses/', views.profile_addresses, name='profile_addresses'),
    path('profile/orders/', views.profile_orders, name='profile_orders'),
    path('profile/subscriptions/', views.profile_subscriptions, name='profile_subscriptions'),
    path('profile/preferences/', views.profile_preferences, name='profile_preferences'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # Address management
    path('profile/address/add/<str:address_type>/', views.address_add, name='address_add'),
    path('profile/address/edit/<uuid:pk>/', views.address_edit, name='address_edit'),
    path('profile/address/delete/<uuid:pk>/', views.address_delete, name='address_delete'),
    path('profile/address/set-default/<uuid:pk>/', views.address_set_default, name='address_set_default'),
]