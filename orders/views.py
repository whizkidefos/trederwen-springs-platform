from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from decimal import Decimal

from .models import Order, OrderItem, ShippingMethod, Coupon, CouponUsage
from core.models import Cart, CartItem, SiteSettings
from users.models import Address

import stripe
import uuid

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

def checkout(request):
    """Checkout page view"""
    # Get cart
    cart = Cart.get_cart(request)
    if not cart or cart.items.count() == 0:
        messages.warning(request, 'Your cart is empty. Please add some products before proceeding to checkout.')
        return redirect('core:cart')
    
    # Get shipping methods
    shipping_methods = ShippingMethod.objects.filter(is_active=True)
    
    # Get user addresses if authenticated
    shipping_addresses = []
    billing_addresses = []
    if request.user.is_authenticated:
        shipping_addresses = Address.objects.filter(
            user=request.user,
            address_type='shipping'
        ).order_by('-is_default')
        
        billing_addresses = Address.objects.filter(
            user=request.user,
            address_type='billing'
        ).order_by('-is_default')
    
    # Calculate cart totals
    cart_items = cart.items.all().select_related('product')
    subtotal = sum(item.total_price for item in cart_items)
    
    # Get site settings
    site_settings = SiteSettings.get_settings()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_methods': shipping_methods,
        'shipping_addresses': shipping_addresses,
        'billing_addresses': billing_addresses,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
        'site_settings': site_settings,
    }
    
    return render(request, 'orders/checkout.html', context)

@require_POST
def apply_coupon(request):
    """Apply a coupon code to the checkout"""
    code = request.POST.get('coupon_code')
    if not code:
        return JsonResponse({'success': False, 'message': 'Please enter a coupon code.'})
    
    try:
        coupon = Coupon.objects.get(code=code, is_active=True)
        
        # Check if coupon is valid
        if not coupon.is_valid:
            return JsonResponse({'success': False, 'message': 'This coupon has expired.'})
        
        # Check if user can use this coupon
        if not coupon.can_be_used_by_user(request.user):
            return JsonResponse({'success': False, 'message': 'You have already used this coupon.'})
        
        # Get cart total
        cart = Cart.get_cart(request)
        cart_total = sum(item.total_price for item in cart.items.all())
        
        # Check minimum order amount
        if coupon.minimum_order_amount and cart_total < coupon.minimum_order_amount:
            return JsonResponse({
                'success': False, 
                'message': f'This coupon requires a minimum order of £{coupon.minimum_order_amount}.'
            })
        
        # Calculate discount
        discount = coupon.calculate_discount(cart_total)
        
        # Store coupon in session
        request.session['coupon_code'] = coupon.code
        request.session['discount_amount'] = str(discount)
        
        return JsonResponse({
            'success': True, 
            'message': 'Coupon applied successfully!',
            'discount': float(discount),
            'new_total': float(cart_total - discount)
        })
        
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid coupon code.'})

@require_POST
def remove_coupon(request):
    """Remove applied coupon"""
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
    if 'discount_amount' in request.session:
        del request.session['discount_amount']
    
    return JsonResponse({'success': True, 'message': 'Coupon removed successfully!'})

@require_POST
def create_payment_intent(request):
    """Create a Stripe payment intent"""
    try:
        # Get cart
        cart = Cart.get_cart(request)
        cart_items = cart.items.all().select_related('product')
        subtotal = sum(item.total_price for item in cart_items)
        
        # Get shipping method
        shipping_method_id = request.POST.get('shipping_method')
        shipping_method = get_object_or_404(ShippingMethod, id=shipping_method_id)
        shipping_cost = shipping_method.get_price_for_order(subtotal)
        
        # Apply discount if coupon is present
        discount_amount = Decimal('0.00')
        if 'discount_amount' in request.session:
            discount_amount = Decimal(request.session['discount_amount'])
        
        # Calculate total
        total = subtotal + shipping_cost - discount_amount
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(total * 100),  # Convert to cents
            currency='gbp',
            metadata={
                'cart_id': str(cart.id),
                'shipping_method_id': shipping_method_id,
                'coupon_code': request.session.get('coupon_code', ''),
            }
        )
        
        return JsonResponse({
            'clientSecret': intent.client_secret,
            'total': float(total)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_POST
def complete_order(request):
    """Complete the order after successful payment"""
    payment_intent_id = request.POST.get('payment_intent_id')
    if not payment_intent_id:
        return JsonResponse({'success': False, 'message': 'Payment information missing.'}, status=400)
    
    try:
        # Retrieve payment intent
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if payment_intent.status != 'succeeded':
            return JsonResponse({'success': False, 'message': 'Payment was not successful.'}, status=400)
        
        # Get cart
        cart = Cart.get_cart(request)
        cart_items = cart.items.all().select_related('product')
        subtotal = sum(item.total_price for item in cart_items)
        
        # Get shipping details
        shipping_method_id = request.POST.get('shipping_method')
        shipping_method = get_object_or_404(ShippingMethod, id=shipping_method_id)
        shipping_cost = shipping_method.get_price_for_order(subtotal)
        
        # Get addresses
        shipping_address_data = {}
        billing_address_data = {}
        
        if request.user.is_authenticated:
            # Get addresses from user's saved addresses
            shipping_address_id = request.POST.get('shipping_address')
            billing_address_id = request.POST.get('billing_address')
            
            if shipping_address_id:
                shipping_address = get_object_or_404(Address, id=shipping_address_id, user=request.user)
                shipping_address_data = {
                    'first_name': shipping_address.first_name,
                    'last_name': shipping_address.last_name,
                    'company': shipping_address.company,
                    'address_line_1': shipping_address.address_line_1,
                    'address_line_2': shipping_address.address_line_2,
                    'city': shipping_address.city,
                    'county': shipping_address.county,
                    'postcode': shipping_address.postcode,
                    'country': shipping_address.country,
                    'phone': shipping_address.phone,
                }
            
            if billing_address_id:
                billing_address = get_object_or_404(Address, id=billing_address_id, user=request.user)
                billing_address_data = {
                    'first_name': billing_address.first_name,
                    'last_name': billing_address.last_name,
                    'company': billing_address.company,
                    'address_line_1': billing_address.address_line_1,
                    'address_line_2': billing_address.address_line_2,
                    'city': billing_address.city,
                    'county': billing_address.county,
                    'postcode': billing_address.postcode,
                    'country': billing_address.country,
                    'phone': billing_address.phone,
                }
        else:
            # Get addresses from form data
            shipping_address_data = {
                'first_name': request.POST.get('shipping_first_name', ''),
                'last_name': request.POST.get('shipping_last_name', ''),
                'company': request.POST.get('shipping_company', ''),
                'address_line_1': request.POST.get('shipping_address_line_1', ''),
                'address_line_2': request.POST.get('shipping_address_line_2', ''),
                'city': request.POST.get('shipping_city', ''),
                'county': request.POST.get('shipping_county', ''),
                'postcode': request.POST.get('shipping_postcode', ''),
                'country': request.POST.get('shipping_country', ''),
                'phone': request.POST.get('shipping_phone', ''),
            }
            
            if request.POST.get('same_as_shipping'):
                billing_address_data = shipping_address_data.copy()
            else:
                billing_address_data = {
                    'first_name': request.POST.get('billing_first_name', ''),
                    'last_name': request.POST.get('billing_last_name', ''),
                    'company': request.POST.get('billing_company', ''),
                    'address_line_1': request.POST.get('billing_address_line_1', ''),
                    'address_line_2': request.POST.get('billing_address_line_2', ''),
                    'city': request.POST.get('billing_city', ''),
                    'county': request.POST.get('billing_county', ''),
                    'postcode': request.POST.get('billing_postcode', ''),
                    'country': request.POST.get('billing_country', ''),
                    'phone': request.POST.get('billing_phone', ''),
                }
        
        # Apply discount if coupon is present
        discount_amount = Decimal('0.00')
        coupon_code = ''
        if 'discount_amount' in request.session and 'coupon_code' in request.session:
            discount_amount = Decimal(request.session['discount_amount'])
            coupon_code = request.session['coupon_code']
        
        # Calculate total
        total = subtotal + shipping_cost - discount_amount
        
        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            email=request.POST.get('email'),
            subtotal=subtotal,
            shipping_amount=shipping_cost,
            discount_amount=discount_amount,
            total=total,
            shipping_address=shipping_address_data,
            billing_address=billing_address_data,
            shipping_method=shipping_method.name,
            payment_method='Stripe',
            payment_intent_id=payment_intent_id,
            status='processing',
            payment_status='paid',
            coupon_code=coupon_code,
            notes=request.POST.get('order_notes', '')
        )
        
        # Create order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price,
                total_price=cart_item.total_price,
                product_data={
                    'name': cart_item.product.name,
                    'sku': cart_item.product.sku,
                    'description': cart_item.product.short_description,
                    'image_url': cart_item.product.get_first_image_url() if hasattr(cart_item.product, 'get_first_image_url') else None,
                }
            )
        
        # Record coupon usage if applicable
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                CouponUsage.objects.create(
                    coupon=coupon,
                    order=order,
                    user=request.user if request.user.is_authenticated else None,
                    discount_amount=discount_amount
                )
                
                # Update coupon usage count
                coupon.usage_count += 1
                coupon.save()
                
                # Clear coupon from session
                if 'coupon_code' in request.session:
                    del request.session['coupon_code']
                if 'discount_amount' in request.session:
                    del request.session['discount_amount']
            except Coupon.DoesNotExist:
                pass
        
        # Clear cart
        cart.items.all().delete()
        
        # Return success response with order details
        return JsonResponse({
            'success': True,
            'message': 'Order placed successfully!',
            'order_number': order.order_number,
            'redirect_url': reverse('orders:order_confirmation', kwargs={'order_number': order.order_number})
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

def order_confirmation(request, order_number):
    """Order confirmation page"""
    try:
        order = Order.objects.get(order_number=order_number)
        
        # Security check - only allow the user who placed the order or staff to view it
        if not request.user.is_staff and (not request.user.is_authenticated or (order.user and order.user != request.user)):
            messages.error(request, 'You do not have permission to view this order.')
            return redirect('core:home')
        
        context = {
            'order': order,
            'order_items': order.items.all()
        }
        
        return render(request, 'orders/order_confirmation.html', context)
        
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('core:home')

@login_required
def order_detail(request, order_number):
    """Order detail page for authenticated users"""
    try:
        order = Order.objects.get(order_number=order_number)
        
        # Security check - only allow the user who placed the order or staff to view it
        if not request.user.is_staff and (order.user != request.user):
            messages.error(request, 'You do not have permission to view this order.')
            return redirect('users:profile_orders')
        
        context = {
            'order': order,
            'order_items': order.items.all()
        }
        
        return render(request, 'orders/order_detail.html', context)
        
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('users:profile_orders')

@login_required
def cancel_order(request, order_number):
    """Cancel an order"""
    try:
        order = Order.objects.get(order_number=order_number, user=request.user)
        
        if not order.can_be_cancelled:
            messages.error(request, 'This order cannot be cancelled.')
            return redirect('orders:order_detail', order_number=order_number)
        
        order.status = 'cancelled'
        order.save()
        
        messages.success(request, 'Your order has been cancelled successfully.')
        return redirect('orders:order_detail', order_number=order_number)
        
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('users:profile_orders')
