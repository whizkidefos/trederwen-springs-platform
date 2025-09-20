from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone
from django.db.models import Sum, Count

from .models import User, Address, UserPreference
from .forms import UserProfileForm, AddressForm
from orders.models import Order
from subscriptions.models import Subscription

@login_required
def profile_dashboard(request):
    """User profile dashboard view"""
    # Get recent orders
    recent_orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Get active subscriptions
    active_subscriptions = Subscription.objects.filter(
        user=request.user,
        status='active'
    ).select_related('plan').order_by('-created_at')
    
    # Get order statistics
    order_stats = Order.objects.filter(user=request.user).aggregate(
        total_spent=Sum('total'),
        total_orders=Count('id')
    )
    
    # Get default addresses
    default_shipping = Address.objects.filter(
        user=request.user,
        address_type='shipping',
        is_default=True
    ).first()
    
    default_billing = Address.objects.filter(
        user=request.user,
        address_type='billing',
        is_default=True
    ).first()
    
    context = {
        'recent_orders': recent_orders,
        'active_subscriptions': active_subscriptions,
        'order_stats': order_stats,
        'default_shipping': default_shipping,
        'default_billing': default_billing,
    }
    
    return render(request, 'users/profile_dashboard.html', context)

@login_required
def profile_edit(request):
    """Edit user profile information"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('users:profile_dashboard')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form
    }
    
    return render(request, 'users/profile_edit.html', context)

@login_required
def profile_addresses(request):
    """Manage user addresses"""
    shipping_addresses = Address.objects.filter(
        user=request.user,
        address_type='shipping'
    ).order_by('-is_default')
    
    billing_addresses = Address.objects.filter(
        user=request.user,
        address_type='billing'
    ).order_by('-is_default')
    
    context = {
        'shipping_addresses': shipping_addresses,
        'billing_addresses': billing_addresses,
    }
    
    return render(request, 'users/profile_addresses.html', context)

@login_required
def address_add(request, address_type):
    """Add a new address"""
    if address_type not in ['shipping', 'billing']:
        messages.error(request, 'Invalid address type.')
        return redirect('users:profile_addresses')
    
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.address_type = address_type
            address.save()
            messages.success(request, f'Your {address_type} address has been added successfully.')
            return redirect('users:profile_addresses')
    else:
        # Pre-fill with user's name if available
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'phone': request.user.phone,
        }
        form = AddressForm(initial=initial_data)
    
    context = {
        'form': form,
        'address_type': address_type,
    }
    
    return render(request, 'users/address_form.html', context)

@login_required
def address_edit(request, pk):
    """Edit an existing address"""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully.')
            return redirect('users:profile_addresses')
    else:
        form = AddressForm(instance=address)
    
    context = {
        'form': form,
        'address': address,
        'address_type': address.address_type,
    }
    
    return render(request, 'users/address_form.html', context)

@login_required
def address_delete(request, pk):
    """Delete an address"""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    if request.method == 'POST':
        address_type = address.address_type
        address.delete()
        messages.success(request, f'Your {address_type} address has been deleted.')
    
    return redirect('users:profile_addresses')

@login_required
def address_set_default(request, pk):
    """Set an address as default"""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    if not address.is_default:
        # Update the address to be default
        address.is_default = True
        address.save()  # This will handle setting other addresses to non-default
        messages.success(request, f'Default {address.address_type} address updated.')
    
    return redirect('users:profile_addresses')

@login_required
def profile_orders(request):
    """View order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'users/profile_orders.html', context)

@login_required
def profile_subscriptions(request):
    """View and manage subscriptions"""
    active_subscriptions = Subscription.objects.filter(
        user=request.user,
        status='active'
    ).select_related('plan').order_by('-created_at')
    
    paused_subscriptions = Subscription.objects.filter(
        user=request.user,
        status='paused'
    ).select_related('plan').order_by('-created_at')
    
    cancelled_subscriptions = Subscription.objects.filter(
        user=request.user,
        status__in=['cancelled', 'expired']
    ).select_related('plan').order_by('-created_at')
    
    context = {
        'active_subscriptions': active_subscriptions,
        'paused_subscriptions': paused_subscriptions,
        'cancelled_subscriptions': cancelled_subscriptions,
    }
    
    return render(request, 'users/profile_subscriptions.html', context)

@login_required
def profile_preferences(request):
    """Manage user preferences"""
    # Get existing preferences
    flavor_prefs = UserPreference.objects.filter(
        user=request.user,
        preference_type='flavor'
    )
    
    dietary_prefs = UserPreference.objects.filter(
        user=request.user,
        preference_type='dietary'
    )
    
    communication_prefs = UserPreference.objects.filter(
        user=request.user,
        preference_type='communication'
    )
    
    if request.method == 'POST':
        # Handle form submission
        # Update marketing preferences
        request.user.marketing_emails = 'marketing_emails' in request.POST
        request.user.sms_notifications = 'sms_notifications' in request.POST
        request.user.is_newsletter_subscribed = 'newsletter' in request.POST
        request.user.save()
        
        messages.success(request, 'Your preferences have been updated.')
        return redirect('users:profile_preferences')
    
    context = {
        'flavor_preferences': flavor_prefs,
        'dietary_preferences': dietary_prefs,
        'communication_preferences': communication_prefs,
    }
    
    return render(request, 'users/profile_preferences.html', context)

@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('users:profile_dashboard')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'users/change_password.html', context)
