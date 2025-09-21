from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.utils import timezone
from django.db.models import Sum, Count
from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.conf import settings

from .models import User, Address, UserPreference, UserActivity
from .forms import UserProfileForm, AddressForm, UserRegisterForm, LoginForm
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

def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('core:home')
        
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the registration activity
            UserActivity.objects.create(
                user=user,
                activity_type='register',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Log the user in
            login(request, user)
            messages.success(request, f'Welcome to Trederwen Springs, {user.first_name}! Your account has been created.')
            
            # Redirect to profile or previous page if available
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('users:profile_dashboard')
    else:
        form = UserRegisterForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'users/register.html', context)


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('core:home')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                
                # Update last login IP and track activity
                user.last_login_ip = request.META.get('REMOTE_ADDR')
                user.update_last_active()
                
                # Log the login activity
                activity_type = 'admin_login' if user.is_admin_user else 'login'
                UserActivity.objects.create(
                    user=user,
                    activity_type=activity_type,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Redirect to next page if available
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                    
                # Redirect admin users to admin dashboard
                if user.is_admin_user:
                    return redirect('dashboard:index')
                    
                return redirect('users:profile_dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'users/login.html', context)


def logout_view(request):
    """User logout view"""
    if request.user.is_authenticated:
        # Log the logout activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='logout',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('core:home')


def password_reset_request(request):
    """Password reset request view"""
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            users = User.objects.filter(email=email)
            
            if users.exists():
                user = users.first()
                subject = 'Password Reset Request for Trederwen Springs'
                email_template_name = 'users/password_reset_email.html'
                
                context = {
                    'user': user,
                    'domain': request.get_host(),
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                    'protocol': 'https' if request.is_secure() else 'http',
                    'site_name': 'Trederwen Springs',
                }
                
                email_content = render_to_string(email_template_name, context)
                
                try:
                    send_mail(
                        subject=subject,
                        message='',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        html_message=email_content,
                        fail_silently=False
                    )
                    
                    return redirect('users:password_reset_done')
                except BadHeaderError:
                    return HttpResponse('Invalid header found.')
            
            # Always redirect to done page even if email not found for security
            return redirect('users:password_reset_done')
    else:
        form = PasswordResetForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'users/password_reset.html', context)


def password_reset_done(request):
    """Password reset done view"""
    return render(request, 'users/password_reset_done.html')


def password_reset_confirm(request, uidb64, token):
    """Password reset confirmation view"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been reset successfully. You can now log in with your new password.')
                return redirect('users:login')
        else:
            form = SetPasswordForm(user)
        
        context = {
            'form': form,
        }
        
        return render(request, 'users/password_reset_confirm.html', context)
    else:
        return render(request, 'users/password_reset_invalid.html')


def password_reset_complete(request):
    """Password reset complete view"""
    return render(request, 'users/password_reset_complete.html')


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
