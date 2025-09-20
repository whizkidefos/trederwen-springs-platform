from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import SubscriptionPlan, Subscription
from core.models import SiteSettings

def subscription_plans(request):
    """Display all available subscription plans"""
    plans = SubscriptionPlan.objects.filter(is_active=True)
    
    # Get site settings
    settings = SiteSettings.get_settings()
    
    context = {
        'plans': plans,
        'settings': settings,
    }
    
    return render(request, 'subscriptions/subscription_plans.html', context)

def subscription_plan_detail(request, pk):
    """Display details for a specific subscription plan"""
    plan = get_object_or_404(SubscriptionPlan, pk=pk, is_active=True)
    
    # Get related products for this plan
    related_products = []
    if hasattr(plan, 'products'):
        related_products = plan.products.filter(is_active=True)[:4]
    
    # Get site settings
    settings = SiteSettings.get_settings()
    
    context = {
        'plan': plan,
        'related_products': related_products,
        'settings': settings,
    }
    
    return render(request, 'subscriptions/subscription_plan_detail.html', context)

@login_required
def my_subscriptions(request):
    """Display user's active subscriptions"""
    subscriptions = Subscription.objects.filter(
        user=request.user
    ).select_related('plan').order_by('-created_at')
    
    # Group subscriptions by status
    active_subscriptions = [sub for sub in subscriptions if sub.status == 'active']
    paused_subscriptions = [sub for sub in subscriptions if sub.status == 'paused']
    cancelled_subscriptions = [sub for sub in subscriptions if sub.status in ['cancelled', 'expired']]
    
    context = {
        'active_subscriptions': active_subscriptions,
        'paused_subscriptions': paused_subscriptions,
        'cancelled_subscriptions': cancelled_subscriptions,
    }
    
    return render(request, 'subscriptions/my_subscriptions.html', context)

@login_required
def subscription_detail(request, pk):
    """Display details for a specific user subscription"""
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    
    # Get upcoming deliveries
    upcoming_deliveries = subscription.deliveries.filter(
        status__in=['scheduled', 'processing'],
        scheduled_date__gte=timezone.now().date()
    ).order_by('scheduled_date')
    
    # Get past deliveries
    past_deliveries = subscription.deliveries.filter(
        status__in=['shipped', 'delivered']
    ).order_by('-scheduled_date')
    
    context = {
        'subscription': subscription,
        'upcoming_deliveries': upcoming_deliveries,
        'past_deliveries': past_deliveries,
    }
    
    return render(request, 'subscriptions/subscription_detail.html', context)

@login_required
@require_POST
def pause_subscription(request, pk):
    """Pause a subscription"""
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    
    if subscription.status != 'active':
        messages.error(request, 'Only active subscriptions can be paused.')
        return redirect('subscriptions:subscription_detail', pk=pk)
    
    reason = request.POST.get('reason', '')
    auto_resume_date_str = request.POST.get('auto_resume_date')
    
    auto_resume_date = None
    if auto_resume_date_str:
        try:
            auto_resume_date = timezone.datetime.strptime(auto_resume_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid resume date format.')
            return redirect('subscriptions:subscription_detail', pk=pk)
    
    subscription.pause(reason=reason, auto_resume_date=auto_resume_date)
    messages.success(request, 'Your subscription has been paused successfully.')
    
    return redirect('subscriptions:subscription_detail', pk=pk)

@login_required
@require_POST
def resume_subscription(request, pk):
    """Resume a paused subscription"""
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    
    if subscription.status != 'paused':
        messages.error(request, 'Only paused subscriptions can be resumed.')
        return redirect('subscriptions:subscription_detail', pk=pk)
    
    subscription.resume()
    messages.success(request, 'Your subscription has been resumed successfully.')
    
    return redirect('subscriptions:subscription_detail', pk=pk)

@login_required
@require_POST
def cancel_subscription(request, pk):
    """Cancel a subscription"""
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    
    if subscription.status not in ['active', 'paused']:
        messages.error(request, 'This subscription cannot be cancelled.')
        return redirect('subscriptions:subscription_detail', pk=pk)
    
    reason = request.POST.get('reason', '')
    immediately = request.POST.get('immediately') == 'true'
    
    subscription.cancel(reason=reason, immediately=immediately)
    
    if immediately:
        messages.success(request, 'Your subscription has been cancelled immediately.')
    else:
        messages.success(request, 'Your subscription will be cancelled at the end of the current billing period.')
    
    return redirect('subscriptions:subscription_detail', pk=pk)

@login_required
@require_POST
def skip_delivery(request, subscription_pk, delivery_pk):
    """Skip a scheduled delivery"""
    subscription = get_object_or_404(Subscription, pk=subscription_pk, user=request.user)
    delivery = get_object_or_404(subscription.deliveries, pk=delivery_pk, status='scheduled')
    
    reason = request.POST.get('reason', '')
    delivery.skip(reason=reason)
    
    messages.success(request, f'Delivery scheduled for {delivery.scheduled_date} has been skipped.')
    return redirect('subscriptions:subscription_detail', pk=subscription_pk)
