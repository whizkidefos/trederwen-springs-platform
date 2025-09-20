from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.subscription_plans, name='subscription_plans'),
    path('plan/<int:pk>/', views.subscription_plan_detail, name='subscription_plan_detail'),
    path('my-subscriptions/', views.my_subscriptions, name='my_subscriptions'),
    path('subscription/<int:pk>/', views.subscription_detail, name='subscription_detail'),
    path('subscription/<int:pk>/pause/', views.pause_subscription, name='pause_subscription'),
    path('subscription/<int:pk>/resume/', views.resume_subscription, name='resume_subscription'),
    path('subscription/<int:pk>/cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('subscription/<int:subscription_pk>/delivery/<int:delivery_pk>/skip/', views.skip_delivery, name='skip_delivery'),
]