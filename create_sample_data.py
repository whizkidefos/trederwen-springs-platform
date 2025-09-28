#!/usr/bin/env python
"""
Script to create sample data for the Trederwen Springs platform
Run this with: python manage.py shell < create_sample_data.py
"""

# Create Blog Categories
from blog.models import BlogCategory

# Create blog categories if they don't exist
categories_data = [
    {
        'name': 'Sustainability',
        'slug': 'sustainability',
        'description': 'Our commitment to environmental sustainability and eco-friendly practices.',
        'color': '#059669',
        'order': 1
    },
    {
        'name': 'Welsh Heritage',
        'slug': 'welsh-heritage',
        'description': 'Stories about Welsh culture, traditions, and our mountain heritage.',
        'color': '#1e40af',
        'order': 2
    },
    {
        'name': 'Health & Wellness',
        'slug': 'health-wellness',
        'description': 'Benefits of natural spring water and healthy living tips.',
        'color': '#dc2626',
        'order': 3
    },
    {
        'name': 'Spring Sources',
        'slug': 'spring-sources',
        'description': 'Information about our natural spring water sources in Wales.',
        'color': '#7c3aed',
        'order': 4
    },
    {
        'name': 'Company News',
        'slug': 'company-news',
        'description': 'Latest updates and news from Trederwen Springs.',
        'color': '#ea580c',
        'order': 5
    }
]

for cat_data in categories_data:
    category, created = BlogCategory.objects.get_or_create(
        slug=cat_data['slug'],
        defaults=cat_data
    )
    if created:
        print(f"Created blog category: {category.name}")
    else:
        print(f"Blog category already exists: {category.name}")

# Create Product Categories
from products.models import ProductCategory

product_categories_data = [
    {
        'name': 'Premium Spring Water',
        'slug': 'premium',
        'description': 'Our finest quality spring water from the Welsh mountains.',
        'is_active': True,
        'order': 1
    },
    {
        'name': 'Natural Spring Water',
        'slug': 'natural',
        'description': 'Pure, natural spring water for everyday hydration.',
        'is_active': True,
        'order': 2
    },
    {
        'name': 'Sparkling Water',
        'slug': 'sparkling',
        'description': 'Naturally carbonated spring water with a refreshing fizz.',
        'is_active': True,
        'order': 3
    },
    {
        'name': 'Gift Sets',
        'slug': 'gift-sets',
        'description': 'Beautifully packaged gift sets perfect for any occasion.',
        'is_active': True,
        'order': 4
    }
]

for cat_data in product_categories_data:
    category, created = ProductCategory.objects.get_or_create(
        slug=cat_data['slug'],
        defaults=cat_data
    )
    if created:
        print(f"Created product category: {category.name}")
    else:
        print(f"Product category already exists: {category.name}")

# Create Sample Products
from products.models import Product
from decimal import Decimal

products_data = [
    {
        'name': 'Trederwen Premium Spring Water 500ml',
        'slug': 'premium-500ml',
        'description': 'Premium spring water sourced from the pristine Welsh mountains.',
        'price': Decimal('2.99'),
        'category_slug': 'premium',
        'is_active': True,
        'stock_quantity': 100,
        'sku': 'TSP-500-001'
    },
    {
        'name': 'Trederwen Premium Spring Water 1L',
        'slug': 'premium-1l',
        'description': 'Premium spring water in convenient 1-liter bottles.',
        'price': Decimal('4.99'),
        'category_slug': 'premium',
        'is_active': True,
        'stock_quantity': 75,
        'sku': 'TSP-1L-001'
    },
    {
        'name': 'Welsh Heritage Gift Set',
        'slug': 'heritage-gift-set',
        'description': 'A beautiful collection of our finest spring waters with Welsh-themed packaging.',
        'price': Decimal('29.99'),
        'category_slug': 'gift-sets',
        'is_active': True,
        'stock_quantity': 25,
        'sku': 'TSG-HER-001'
    }
]

for prod_data in products_data:
    category = ProductCategory.objects.get(slug=prod_data.pop('category_slug'))
    product, created = Product.objects.get_or_create(
        slug=prod_data['slug'],
        defaults={**prod_data, 'category': category}
    )
    if created:
        print(f"Created product: {product.name}")
    else:
        print(f"Product already exists: {product.name}")

print("Sample data creation completed!")
