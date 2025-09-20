from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Checkout process
    path('checkout/', views.checkout, name='checkout'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
    path('create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('complete-order/', views.complete_order, name='complete_order'),
    
    # Order views
    path('confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    path('order/<str:order_number>/cancel/', views.cancel_order, name='cancel_order'),
]