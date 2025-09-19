# ai_recommendations/services.py
from django.db.models import Q, Count, Avg, F
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
from products.models import Product, Category
from users.models import UserActivity
from .models import (UserBehavior, Recommendation, RecommendationItem, 
                    UserProductInteraction, ProductSimilarity, TrendingProduct)
import random
from typing import List, Optional, Dict, Any

class RecommendationService:
    """Main service for generating product recommendations"""
    
    def __init__(self):
        self.product_content_type = ContentType.objects.get_for_model(Product)
    
    def get_homepage_recommendations(self, request, limit: int = 8) -> Dict[str, Any]:
        """Get recommendations for homepage"""
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key
        
        if user:
            # Personalized recommendations for logged-in users
            recommendations = self._get_personalized_recommendations(user, limit)
        else:
            # General recommendations for anonymous users
            recommendations = self._get_popular_recommendations(session_key, limit)
        
        return {
            'products': recommendations,
            'type': 'homepage',
            'title': 'Recommended for You' if user else 'Popular Products'
        }
    
    def get_product_recommendations(self, request, product, limit: int = 4) -> Dict[str, Any]:
        """Get recommendations for product detail page"""
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key
        
        # Track product view
        self._track_behavior(user, session_key, 'view', str(product.id))
        
        # Get similar products
        similar_products = self._get_similar_products(product, limit)
        
        return {
            'products': similar_products,
            'type': 'similar',
            'title': 'Similar Products'
        }
    
    def get_cart_recommendations(self, request, limit: int = 4) -> Dict[str, Any]:
        """Get recommendations for cart page"""
        from core.cart import Cart
        
        cart = Cart(request)
        cart_items = list(cart)
        
        if not cart_items:
            return self.get_homepage_recommendations(request, limit)
        
        # Get frequently bought together items
        cart_product_ids = [item['product'].id for item in cart_items]
        recommendations = self._get_frequently_bought_together(cart_product_ids, limit)
        
        return {
            'products': recommendations,
            'type': 'frequently_bought_together',
            'title': 'Frequently Bought Together'
        }
    
    def get_category_recommendations(self, request, category, limit: int = 8) -> Dict[str, Any]:
        """Get recommendations for category page"""
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key
        
        # Track category browse
        self._track_behavior(user, session_key, 'category_browse', str(category.id))
        
        # Get trending products in category
        trending_products = self._get_trending_in_category(category, limit)
        
        return {
            'products': trending_products,
            'type': 'trending_category',
            'title': f'Trending in {category.name}'
        }
    
    def _get_personalized_recommendations(self, user, limit: int) -> List[Product]:
        """Generate personalized recommendations for a user"""
        # Get user's interaction history
        interactions = UserProductInteraction.objects.filter(
            user=user
        ).order_by('-total_score')[:20]
        
        if not interactions:
            return self._get_popular_recommendations(None, limit)
        
        # Get products the user has interacted with
        interacted_product_ids = [interaction.product.id for interaction in interactions]
        
        # Find similar products based on user's preferences
        recommended_products = []
        
        for interaction in interactions[:5]:  # Use top 5 interactions
            similar_products = ProductSimilarity.objects.filter(
                Q(product_1=interaction.product) | Q(product_2=interaction.product)
            ).order_by('-similarity_score')[:5]
            
            for similarity in similar_products:
                similar_product = (similarity.product_2 if similarity.product_1 == interaction.product 
                                 else similarity.product_1)
                
                if (similar_product.id not in interacted_product_ids and 
                    similar_product not in recommended_products and
                    similar_product.is_active and similar_product.is_in_stock):
                    recommended_products.append(similar_product)
                    
                    if len(recommended_products) >= limit:
                        break
            
            if len(recommended_products) >= limit:
                break
        
        # Fill remaining slots with popular products
        if len(recommended_products) < limit:
            popular_products = self._get_popular_products(
                limit - len(recommended_products),
                exclude_ids=[p.id for p in recommended_products] + interacted_product_ids
            )
            recommended_products.extend(popular_products)
        
        return recommended_products[:limit]
    
    def _get_popular_recommendations(self, session_key: Optional[str], limit: int) -> List[Product]:
        """Get popular products for anonymous users"""
        return self._get_popular_products(limit)
    
    def _get_similar_products(self, product: Product, limit: int) -> List[Product]:
        """Get products similar to the given product"""
        # Try to get from similarity matrix first
        similar_products = ProductSimilarity.objects.filter(
            Q(product_1=product) | Q(product_2=product)
        ).order_by('-similarity_score')[:limit * 2]  # Get more to filter
        
        recommendations = []
        for similarity in similar_products:
            similar_product = (similarity.product_2 if similarity.product_1 == product 
                             else similarity.product_1)
            
            if (similar_product.is_active and similar_product.is_in_stock and 
                similar_product != product):
                recommendations.append(similar_product)
                
                if len(recommendations) >= limit:
                    break
        
        # If not enough similar products, fill with category products
        if len(recommendations) < limit:
            category_products = Product.objects.filter(
                category=product.category,
                is_active=True,
                is_in_stock=True
            ).exclude(
                id__in=[p.id for p in recommendations] + [product.id]
            ).order_by('-view_count')[:limit - len(recommendations)]
            
            recommendations.extend(category_products)
        
        return recommendations[:limit]
    
    def _get_frequently_bought_together(self, product_ids: List[int], limit: int) -> List[Product]:
        """Get products frequently bought together with cart items"""
        # This is a simplified version - in production, you'd analyze order history
        
        # Get categories of cart items
        cart_categories = Product.objects.filter(
            id__in=product_ids
        ).values_list('category_id', flat=True).distinct()
        
        # Find popular products in those categories
        recommendations = Product.objects.filter(
            category_id__in=cart_categories,
            is_active=True,
            is_in_stock=True
        ).exclude(
            id__in=product_ids
        ).annotate(
            purchase_count=Count('orderitem')
        ).order_by('-purchase_count', '-view_count')[:limit]
        
        return list(recommendations)
    
    def _get_trending_in_category(self, category: Category, limit: int) -> List[Product]:
        """Get trending products in a specific category"""
        # Get products with trending data
        trending_products = Product.objects.filter(
            category=category,
            is_active=True,
            is_in_stock=True,
            trending_data__isnull=False
        ).select_related('trending_data').order_by(
            '-trending_data__daily_score'
        )[:limit]
        
        if trending_products.count() >= limit:
            return list(trending_products)
        
        # Fill remaining with popular products in category
        remaining = limit - trending_products.count()
        popular_products = Product.objects.filter(
            category=category,
            is_active=True,
            is_in_stock=True
        ).exclude(
            id__in=[p.id for p in trending_products]
        ).order_by('-view_count')[:remaining]
        
        return list(trending_products) + list(popular_products)
    
    def _get_popular_products(self, limit: int, exclude_ids: Optional[List[int]] = None) -> List[Product]:
        """Get popular products based on various metrics"""
        queryset = Product.objects.filter(
            is_active=True,
            is_in_stock=True
        )
        
        if exclude_ids:
            queryset = queryset.exclude(id__in=exclude_ids)
        
        # Order by a combination of metrics
        popular_products = queryset.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True)),
            order_count=Count('orderitem')
        ).order_by(
            '-is_featured',
            '-order_count',
            '-avg_rating',
            '-view_count'
        )[:limit]
        
        return list(popular_products)
    
    def _track_behavior(self, user, session_key: str, behavior_type: str, object_id: str):
        """Track user behavior for recommendations"""
        UserBehavior.objects.create(
            user=user,
            session_key=session_key or '',
            behavior_type=behavior_type,
            content_type=self.product_content_type,
            object_id=object_id,
            weight=self._get_behavior_weight(behavior_type)
        )
        
        # Update user-product interaction if user is authenticated
        if user:
            self._update_user_product_interaction(user, object_id, behavior_type)
    
    def _get_behavior_weight(self, behavior_type: str) -> float:
        """Get weight for different behavior types"""
        weights = {
            'view': 1.0,
            'cart_add': 3.0,
            'cart_remove': -1.0,
            'purchase': 10.0,
            'wishlist_add': 2.0,
            'review': 5.0,
            'search': 0.5,
            'category_browse': 0.3,
        }
        return weights.get(behavior_type, 1.0)
    
    def _update_user_product_interaction(self, user, product_id: str, behavior_type: str):
        """Update user-product interaction scores"""
        try:
            product = Product.objects.get(id=product_id)
            interaction, created = UserProductInteraction.objects.get_or_create(
                user=user,
                product=product,
                defaults={
                    'first_interaction': timezone.now(),
                    'last_interaction': timezone.now(),
                }
            )
            
            if not created:
                interaction.last_interaction = timezone.now()
            
            # Update scores based on behavior
            weight = self._get_behavior_weight(behavior_type)
            
            if behavior_type == 'view':
                interaction.view_score += weight
            elif behavior_type in ['cart_add', 'cart_remove']:
                interaction.cart_score += weight
            elif behavior_type == 'purchase':
                interaction.purchase_score += weight
            elif behavior_type == 'wishlist_add':
                interaction.wishlist_score += weight
            elif behavior_type == 'review':
                interaction.review_score += weight
            
            # Recalculate total score
            interaction.total_score = (
                interaction.view_score + interaction.cart_score + 
                interaction.purchase_score + interaction.wishlist_score + 
                interaction.review_score
            )
            
            interaction.interaction_count += 1
            interaction.save()
            
        except Product.DoesNotExist:
            pass
    
    def update_trending_products(self):
        """Update trending product scores (to be run periodically)"""
        # Calculate trending scores for products based on recent activity
        now = timezone.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Get all products
        products = Product.objects.filter(is_active=True)
        
        for product in products:
            # Calculate daily metrics
            daily_views = UserBehavior.objects.filter(
                content_type=self.product_content_type,
                object_id=str(product.id),
                behavior_type='view',
                created_at__gte=day_ago
            ).count()
            
            daily_purchases = UserBehavior.objects.filter(
                content_type=self.product_content_type,
                object_id=str(product.id),
                behavior_type='purchase',
                created_at__gte=day_ago
            ).count()
            
            daily_cart_adds = UserBehavior.objects.filter(
                content_type=self.product_content_type,
                object_id=str(product.id),
                behavior_type='cart_add',
                created_at__gte=day_ago
            ).count()
            
            # Calculate weekly and monthly metrics
            weekly_views = UserBehavior.objects.filter(
                content_type=self.product_content_type,
                object_id=str(product.id),
                behavior_type='view',
                created_at__gte=week_ago
            ).count()
            
            monthly_views = UserBehavior.objects.filter(
                content_type=self.product_content_type,
                object_id=str(product.id),
                behavior_type='view',
                created_at__gte=month_ago
            ).count()
            
            # Calculate trending scores
            daily_score = (daily_views * 1.0 + daily_purchases * 10.0 + daily_cart_adds * 3.0)
            weekly_score = (weekly_views * 0.5 + daily_score * 7)
            monthly_score = (monthly_views * 0.2 + weekly_score * 4)
            
            # Update or create trending data
            trending_data, created = TrendingProduct.objects.get_or_create(
                product=product,
                defaults={
                    'daily_score': daily_score,
                    'weekly_score': weekly_score,
                    'monthly_score': monthly_score,
                    'view_velocity': daily_views,
                    'purchase_velocity': daily_purchases,
                    'cart_add_velocity': daily_cart_adds,
                }
            )
            
            if not created:
                trending_data.daily_score = daily_score
                trending_data.weekly_score = weekly_score
                trending_data.monthly_score = monthly_score
                trending_data.view_velocity = daily_views
                trending_data.purchase_velocity = daily_purchases
                trending_data.cart_add_velocity = daily_cart_adds
                trending_data.save()
        
        # Update rankings
        self._update_trending_rankings()
    
    def _update_trending_rankings(self):
        """Update trending product rankings"""
        # Daily rankings
        daily_trending = TrendingProduct.objects.order_by('-daily_score')
        for rank, trending_data in enumerate(daily_trending, 1):
            trending_data.daily_rank = rank
            trending_data.save(update_fields=['daily_rank'])
        
        # Weekly rankings
        weekly_trending = TrendingProduct.objects.order_by('-weekly_score')
        for rank, trending_data in enumerate(weekly_trending, 1):
            trending_data.weekly_rank = rank
            trending_data.save(update_fields=['weekly_rank'])
        
        # Monthly rankings
        monthly_trending = TrendingProduct.objects.order_by('-monthly_score')
        for rank, trending_data in enumerate(monthly_trending, 1):
            trending_data.monthly_rank = rank
            trending_data.save(update_fields=['monthly_rank'])