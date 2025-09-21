from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
import json

from users.models import User, UserActivity, Message, Notification
from orders.models import Order, OrderItem, ShippingMethod
from products.models import Product, Category
from subscriptions.models import Subscription
from .models import DashboardWidget, AdminNote, AuditLog

# Custom decorator for admin access
def admin_required(view_func):
    """Decorator to check if the user is an admin"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not request.user.is_admin_user:
            messages.error(request, 'You do not have permission to access the admin dashboard.')
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return wrapper

# Helper function to log admin actions
def log_admin_action(user, action_type, action_model, action_object_id, action_details=None, request=None):
    """Log admin actions for audit purposes"""
    if action_details is None:
        action_details = {}
        
    log = AuditLog(
        user=user,
        action_type=action_type,
        action_model=action_model,
        action_object_id=action_object_id,
        action_details=action_details
    )
    
    if request:
        log.ip_address = request.META.get('REMOTE_ADDR')
        log.user_agent = request.META.get('HTTP_USER_AGENT', '')
        
    log.save()
    return log

@admin_required
def dashboard(request):
    """Admin dashboard home view"""
    # Update last active timestamp
    request.user.update_last_active()
    
    # Get dashboard widgets for the user
    widgets = DashboardWidget.objects.filter(user=request.user, is_enabled=True)
    
    # If no widgets exist, create default ones
    if not widgets.exists():
        default_widgets = [
            {'widget_type': 'sales_chart', 'title': 'Sales Overview', 'position': 0, 'size': 'large'},
            {'widget_type': 'orders_summary', 'title': 'Orders Summary', 'position': 1, 'size': 'medium'},
            {'widget_type': 'recent_orders', 'title': 'Recent Orders', 'position': 2, 'size': 'medium'},
            {'widget_type': 'stock_levels', 'title': 'Low Stock Products', 'position': 3, 'size': 'medium'},
            {'widget_type': 'messages', 'title': 'Recent Messages', 'position': 4, 'size': 'medium'},
        ]
        
        for widget_data in default_widgets:
            DashboardWidget.objects.create(user=request.user, **widget_data)
            
        widgets = DashboardWidget.objects.filter(user=request.user, is_enabled=True)
    
    # Get recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    
    # Get order statistics
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    orders_today = Order.objects.filter(created_at__date=today).count()
    orders_month = Order.objects.filter(created_at__date__gte=start_of_month).count()
    
    revenue_today = Order.objects.filter(created_at__date=today, payment_status='paid').aggregate(total=Sum('total'))['total'] or 0
    revenue_month = Order.objects.filter(created_at__date__gte=start_of_month, payment_status='paid').aggregate(total=Sum('total'))['total'] or 0
    
    # Get low stock products
    low_stock_products = Product.objects.filter(
        manage_stock=True,
        stock_quantity__lte=F('low_stock_threshold')
    )[:10]
    
    # Get unread messages
    unread_messages = Message.objects.filter(recipient=request.user, status='unread').count()
    
    # Get admin notes
    notes = AdminNote.objects.filter(user=request.user, is_completed=False).order_by('-is_pinned', '-priority', 'due_date')[:5]
    
    # Get recent user activity
    user_activity = UserActivity.objects.all().order_by('-timestamp')[:20]
    
    context = {
        'widgets': widgets,
        'recent_orders': recent_orders,
        'orders_today': orders_today,
        'orders_month': orders_month,
        'revenue_today': revenue_today,
        'revenue_month': revenue_month,
        'low_stock_products': low_stock_products,
        'unread_messages': unread_messages,
        'notes': notes,
        'user_activity': user_activity,
    }
    
    # Log the dashboard view
    log_admin_action(
        user=request.user,
        action_type='view',
        action_model='dashboard',
        action_object_id='dashboard',
        request=request
    )
    
    return render(request, 'dashboard/index.html', context)

@admin_required
def orders(request):
    """Admin orders management view"""
    # Update last active timestamp
    request.user.update_last_active()
    
    # Get filter parameters
    status = request.GET.get('status', '')
    payment_status = request.GET.get('payment_status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    # Base queryset
    orders_qs = Order.objects.all()
    
    # Apply filters
    if status:
        orders_qs = orders_qs.filter(status=status)
    if payment_status:
        orders_qs = orders_qs.filter(payment_status=payment_status)
    if date_from:
        orders_qs = orders_qs.filter(created_at__date__gte=date_from)
    if date_to:
        orders_qs = orders_qs.filter(created_at__date__lte=date_to)
    if search:
        orders_qs = orders_qs.filter(
            Q(order_number__icontains=search) | 
            Q(user__email__icontains=search) | 
            Q(user__first_name__icontains=search) | 
            Q(user__last_name__icontains=search) | 
            Q(shipping_address__first_name__icontains=search) | 
            Q(shipping_address__last_name__icontains=search)
        )
    
    # Order by
    orders_qs = orders_qs.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders_qs, 20)  # Show 20 orders per page
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    
    # Get order statistics
    order_stats = {
        'total': Order.objects.count(),
        'pending': Order.objects.filter(status='pending').count(),
        'processing': Order.objects.filter(status='processing').count(),
        'shipped': Order.objects.filter(status='shipped').count(),
        'delivered': Order.objects.filter(status='delivered').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }
    
    context = {
        'orders': orders_page,
        'order_stats': order_stats,
        'status': status,
        'payment_status': payment_status,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
    }
    
    # Log the orders view
    log_admin_action(
        user=request.user,
        action_type='view',
        action_model='orders',
        action_object_id='orders_list',
        request=request
    )
    
    return render(request, 'dashboard/orders.html', context)

@admin_required
def order_detail(request, order_number):
    """Admin order detail view"""
    # Update last active timestamp
    request.user.update_last_active()
    
    # Get order
    order = get_object_or_404(Order, order_number=order_number)
    order_items = order.items.all().select_related('product')
    
    # Get order history
    order_history = order.status_history.all().order_by('-timestamp')
    
    context = {
        'order': order,
        'order_items': order_items,
        'order_history': order_history,
    }
    
    # Log the order detail view
    log_admin_action(
        user=request.user,
        action_type='view',
        action_model='order',
        action_object_id=order.order_number,
        request=request
    )
    
    return render(request, 'dashboard/order_detail.html', context)

@admin_required
@require_POST
def update_order_status(request, order_number):
    """Update order status"""
    order = get_object_or_404(Order, order_number=order_number)
    status = request.POST.get('status')
    notes = request.POST.get('notes', '')
    
    if status not in [choice[0] for choice in Order.STATUS_CHOICES]:
        messages.error(request, 'Invalid status.')
        return redirect('dashboard:order_detail', order_number=order_number)
    
    # Update order status
    old_status = order.status
    order.status = status
    order.save(update_fields=['status'])
    
    # Create status history entry
    order.status_history.create(
        status=status,
        notes=notes,
        created_by=request.user
    )
    
    # Log the order status update
    log_admin_action(
        user=request.user,
        action_type='update',
        action_model='order',
        action_object_id=order.order_number,
        action_details={
            'field': 'status',
            'old_value': old_status,
            'new_value': status,
            'notes': notes
        },
        request=request
    )
    
    messages.success(request, f'Order status updated to {order.get_status_display()}.')
    return redirect('dashboard:order_detail', order_number=order_number)

@admin_required
def products(request):
    """Admin products management view"""
    # Update last active timestamp
    request.user.update_last_active()
    
    # Get filter parameters
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    stock = request.GET.get('stock', '')
    search = request.GET.get('search', '')
    
    # Base queryset
    products_qs = Product.objects.all()
    
    # Apply filters
    if category:
        products_qs = products_qs.filter(category__id=category)
    if status:
        products_qs = products_qs.filter(is_active=(status == 'active'))
    if stock == 'low':
        products_qs = products_qs.filter(
            manage_stock=True,
            stock_quantity__lte=F('low_stock_threshold')
        )
    elif stock == 'out':
        products_qs = products_qs.filter(
            manage_stock=True,
            stock_quantity=0
        )
    if search:
        products_qs = products_qs.filter(
            Q(name__icontains=search) | 
            Q(sku__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Order by
    products_qs = products_qs.order_by('name')
    
    # Pagination
    paginator = Paginator(products_qs, 20)  # Show 20 products per page
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)
    
    # Get categories for filter
    categories = Category.objects.all()
    
    # Get product statistics
    product_stats = {
        'total': Product.objects.count(),
        'active': Product.objects.filter(is_active=True).count(),
        'inactive': Product.objects.filter(is_active=False).count(),
        'low_stock': Product.objects.filter(
            manage_stock=True,
            stock_quantity__lte=F('low_stock_threshold')
        ).count(),
        'out_of_stock': Product.objects.filter(
            manage_stock=True,
            stock_quantity=0
        ).count(),
    }
    
    context = {
        'products': products_page,
        'categories': categories,
        'product_stats': product_stats,
        'category': category,
        'status': status,
        'stock': stock,
        'search': search,
    }
    
    # Log the products view
    log_admin_action(
        user=request.user,
        action_type='view',
        action_model='products',
        action_object_id='products_list',
        request=request
    )
    
    return render(request, 'dashboard/products.html', context)

@admin_required
def customers(request):
    """Admin customers management view"""
    # Update last active timestamp
    request.user.update_last_active()
    
    # Get filter parameters
    status = request.GET.get('status', '')
    date_joined = request.GET.get('date_joined', '')
    search = request.GET.get('search', '')
    
    # Base queryset - only get customer users, not admin users
    customers_qs = User.objects.filter(user_type='customer')
    
    # Apply filters
    if status:
        customers_qs = customers_qs.filter(is_active=(status == 'active'))
    if date_joined == 'today':
        customers_qs = customers_qs.filter(date_joined__date=timezone.now().date())
    elif date_joined == 'week':
        customers_qs = customers_qs.filter(date_joined__date__gte=timezone.now().date() - timedelta(days=7))
    elif date_joined == 'month':
        customers_qs = customers_qs.filter(date_joined__date__gte=timezone.now().date() - timedelta(days=30))
    if search:
        customers_qs = customers_qs.filter(
            Q(email__icontains=search) | 
            Q(first_name__icontains=search) | 
            Q(last_name__icontains=search) | 
            Q(phone__icontains=search)
        )
    
    # Order by
    customers_qs = customers_qs.order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(customers_qs, 20)  # Show 20 customers per page
    page_number = request.GET.get('page')
    customers_page = paginator.get_page(page_number)
    
    # Get customer statistics
    customer_stats = {
        'total': User.objects.filter(user_type='customer').count(),
        'active': User.objects.filter(user_type='customer', is_active=True).count(),
        'inactive': User.objects.filter(user_type='customer', is_active=False).count(),
        'new_today': User.objects.filter(user_type='customer', date_joined__date=timezone.now().date()).count(),
        'new_week': User.objects.filter(user_type='customer', date_joined__date__gte=timezone.now().date() - timedelta(days=7)).count(),
    }
    
    context = {
        'customers': customers_page,
        'customer_stats': customer_stats,
        'status': status,
        'date_joined': date_joined,
        'search': search,
    }
    
    # Log the customers view
    log_admin_action(
        user=request.user,
        action_type='view',
        action_model='customers',
        action_object_id='customers_list',
        request=request
    )
    
    return render(request, 'dashboard/customers.html', context)

@admin_required
def messages_view(request):
    """Admin messages management view"""
    # Update last active timestamp
    request.user.update_last_active()
    
    # Get filter parameters
    message_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    # Base queryset
    if request.user.is_superuser:
        # Superusers can see all messages
        messages_qs = Message.objects.all()
    else:
        # Admin users can only see messages sent to them or messages they sent
        messages_qs = Message.objects.filter(
            Q(recipient=request.user) | 
            Q(sender=request.user)
        )
    
    # Apply filters
    if message_type:
        messages_qs = messages_qs.filter(message_type=message_type)
    if status:
        messages_qs = messages_qs.filter(status=status)
    if search:
        messages_qs = messages_qs.filter(
            Q(subject__icontains=search) | 
            Q(content__icontains=search) | 
            Q(sender__email__icontains=search) | 
            Q(recipient__email__icontains=search)
        )
    
    # Order by
    messages_qs = messages_qs.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(messages_qs, 20)  # Show 20 messages per page
    page_number = request.GET.get('page')
    messages_page = paginator.get_page(page_number)
    
    # Get message statistics
    message_stats = {
        'total': messages_qs.count(),
        'unread': messages_qs.filter(status='unread').count(),
        'read': messages_qs.filter(status='read').count(),
        'archived': messages_qs.filter(status='archived').count(),
    }
    
    context = {
        'messages_list': messages_page,
        'message_stats': message_stats,
        'message_type': message_type,
        'status': status,
        'search': search,
    }
    
    # Log the messages view
    log_admin_action(
        user=request.user,
        action_type='view',
        action_model='messages',
        action_object_id='messages_list',
        request=request
    )
    
    return render(request, 'dashboard/messages.html', context)

@admin_required
def analytics(request):
    """Admin analytics and reporting view"""
    # Update last active timestamp
    request.user.update_last_active()
    
    # Get date range parameters
    period = request.GET.get('period', 'month')
    
    # Define date ranges
    today = timezone.now().date()
    if period == 'week':
        start_date = today - timedelta(days=7)
        date_format = '%a'  # Day of week abbreviation
    elif period == 'month':
        start_date = today - timedelta(days=30)
        date_format = '%d %b'  # Day and month abbreviation
    elif period == 'year':
        start_date = today - timedelta(days=365)
        date_format = '%b'  # Month abbreviation
    else:  # Default to month
        start_date = today - timedelta(days=30)
        date_format = '%d %b'
    
    # Get sales data
    sales_data = Order.objects.filter(
        created_at__date__gte=start_date,
        payment_status='paid'
    ).values('created_at__date').annotate(
        revenue=Sum('total'),
        orders=Count('id')
    ).order_by('created_at__date')
    
    # Format sales data for charts
    dates = []
    revenue = []
    orders_count = []
    
    for data in sales_data:
        date_str = data['created_at__date'].strftime(date_format)
        dates.append(date_str)
        revenue.append(float(data['revenue']) if data['revenue'] else 0)
        orders_count.append(data['orders'])
    
    # Get top products
    top_products = OrderItem.objects.filter(
        order__created_at__date__gte=start_date,
        order__payment_status='paid'
    ).values('product__name').annotate(
        quantity=Sum('quantity'),
        revenue=Sum('total_price')
    ).order_by('-quantity')[:10]
    
    # Get customer acquisition data
    customer_data = User.objects.filter(
        user_type='customer',
        date_joined__date__gte=start_date
    ).values('date_joined__date').annotate(
        count=Count('id')
    ).order_by('date_joined__date')
    
    # Format customer data for charts
    customer_dates = []
    customer_counts = []
    
    for data in customer_data:
        date_str = data['date_joined__date'].strftime(date_format)
        customer_dates.append(date_str)
        customer_counts.append(data['count'])
    
    context = {
        'period': period,
        'dates': json.dumps(dates),
        'revenue': json.dumps(revenue),
        'orders_count': json.dumps(orders_count),
        'top_products': top_products,
        'customer_dates': json.dumps(customer_dates),
        'customer_counts': json.dumps(customer_counts),
    }
    
    # Log the analytics view
    log_admin_action(
        user=request.user,
        action_type='view',
        action_model='analytics',
        action_object_id='analytics',
        request=request
    )
    
    return render(request, 'dashboard/analytics.html', context)

@admin_required
def settings_view(request):
    """Admin settings view"""
    # Update last active timestamp
    request.user.update_last_active()
    
    # Get dashboard widgets
    widgets = DashboardWidget.objects.filter(user=request.user)
    
    context = {
        'widgets': widgets,
    }
    
    # Log the settings view
    log_admin_action(
        user=request.user,
        action_type='view',
        action_model='settings',
        action_object_id='settings',
        request=request
    )
    
    return render(request, 'dashboard/settings.html', context)

@admin_required
def admin_users(request):
    """Admin users management view"""
    # Update last active timestamp
    request.user.update_last_active()
    
    # Only superusers can access this view
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:index')
    
    # Get admin users
    admin_users = User.objects.filter(user_type='admin')
    
    # Get admin user statistics
    admin_stats = {
        'total': admin_users.count(),
        'active': admin_users.filter(is_active=True).count(),
        'inactive': admin_users.filter(is_active=False).count(),
        'superusers': admin_users.filter(is_superuser=True).count(),
    }
    
    context = {
        'admin_users': admin_users,
        'admin_stats': admin_stats,
    }
    
    # Log the admin users view
    log_admin_action(
        user=request.user,
        action_type='view',
        action_model='admin_users',
        action_object_id='admin_users_list',
        request=request
    )
    
    return render(request, 'dashboard/admin_users.html', context)

@admin_required
def audit_logs(request):
    """Admin audit logs view"""
    # Update last active timestamp
    request.user.update_last_active()
    
    # Only superusers can access this view
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:index')
    
    # Get filter parameters
    action_type = request.GET.get('action_type', '')
    user_id = request.GET.get('user_id', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    # Base queryset
    logs_qs = AuditLog.objects.all()
    
    # Apply filters
    if action_type:
        logs_qs = logs_qs.filter(action_type=action_type)
    if user_id:
        logs_qs = logs_qs.filter(user_id=user_id)
    if date_from:
        logs_qs = logs_qs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs_qs = logs_qs.filter(timestamp__date__lte=date_to)
    if search:
        logs_qs = logs_qs.filter(
            Q(action_model__icontains=search) | 
            Q(action_object_id__icontains=search) | 
            Q(user__email__icontains=search)
        )
    
    # Order by
    logs_qs = logs_qs.order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(logs_qs, 50)  # Show 50 logs per page
    page_number = request.GET.get('page')
    logs_page = paginator.get_page(page_number)
    
    # Get admin users for filter
    admin_users = User.objects.filter(user_type='admin')
    
    context = {
        'logs': logs_page,
        'admin_users': admin_users,
        'action_type': action_type,
        'user_id': user_id,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
    }
    
    # Log the audit logs view
    log_admin_action(
        user=request.user,
        action_type='view',
        action_model='audit_logs',
        action_object_id='audit_logs_list',
        request=request
    )
    
    return render(request, 'dashboard/audit_logs.html', context)
