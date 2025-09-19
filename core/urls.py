# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('search/', views.search, name='search'),
    
    # Legal pages
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('shipping-info/', views.shipping_info, name='shipping_info'),
    path('returns-policy/', views.returns_policy, name='returns_policy'),
    
    # Cart functionality
    path('cart/', views.cart_detail, name='cart_detail'),
    
    # AJAX endpoints
    path('ajax/newsletter-signup/', views.newsletter_signup, name='newsletter_signup'),
    path('ajax/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('ajax/remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('ajax/update-cart/', views.update_cart, name='update_cart'),
]