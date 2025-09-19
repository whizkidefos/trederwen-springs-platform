# ai_recommendations/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import BaseModel
import json

User = get_user_model()

class UserBehavior(BaseModel):
    """Track user behavior for recommendations"""
    BEHAVIOR_TYPES = [
        ('view', 'Product View'),
        ('cart_add', 'Added to Cart'),
        ('cart_remove', 'Removed from Cart'),
        ('purchase', 'Purchase'),
        ('wishlist_add', 'Added to Wishlist'),
        ('review', 'Product Review'),
        ('search', 'Search Query'),
        ('category_browse', 'Category Browse'),
    ]
    
    user = models.ForeignKey(User, related_name='behaviors', on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=50, blank=True)
    behavior_type = models.CharField(max_length=20, choices=BEHAVIOR_TYPES)
    
    # Generic relation to any model (Product, Category, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional context data
    context_data = models.JSONField(default=dict, blank=True)
    
    # Session and device info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    
    # Metadata
    weight = models.FloatField(default=1.0, help_text="Importance weight for this behavior")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'behavior_type']),
            models.Index(fields=['session_key', 'behavior_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        user_id = self.user.email if self.user else f"Session: {self.session_key}"
        return f"{user_id} - {self.get_behavior_type_display()}"

class RecommendationModel(BaseModel):
    """ML model configurations for recommendations"""
    MODEL_TYPES = [
        ('collaborative_filtering', 'Collaborative Filtering'),
        ('content_based', 'Content-Based'),
        ('hybrid', 'Hybrid'),
        ('popularity_based', 'Popularity-Based'),
        ('matrix_factorization', 'Matrix Factorization'),
    ]
    
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=30, choices=MODEL_TYPES)
    description = models.TextField(blank=True)
    
    # Model parameters
    parameters = models.JSONField(default=dict)
    
    # Model performance metrics
    accuracy_score = models.FloatField(null=True, blank=True)
    precision_score = models.FloatField(null=True, blank=True)
    recall_score = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    
    # Model status
    is_active = models.BooleanField(default=False)
    is_trained = models.BooleanField(default=False)
    training_data_count = models.PositiveIntegerField(default=0)
    
    # Model files
    model_file_path = models.CharField(max_length=500, blank=True)
    feature_columns = models.JSONField(default=list)
    
    # Training info
    last_trained_at = models.DateTimeField(null=True, blank=True)
    training_duration = models.DurationField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_model_type_display()})"
    
    @property
    def needs_retraining(self):
        """Check if model needs retraining based on new data"""
        if not self.is_trained:
            return True
        
        # Check if enough new behaviors have been recorded since last training
        if self.last_trained_at:
            new_behaviors = UserBehavior.objects.filter(created_at__gt=self.last_trained_at).count()
            return new_behaviors > (self.training_data_count * 0.1)  # 10% threshold
        
        return True

class ProductSimilarity(BaseModel):
    """Store product similarity scores for content-based recommendations"""
    product_1 = models.ForeignKey('products.Product', related_name='similarity_as_product_1', on_delete=models.CASCADE)
    product_2 = models.ForeignKey('products.Product', related_name='similarity_as_product_2', on_delete=models.CASCADE)
    similarity_score = models.FloatField()
    similarity_type = models.CharField(max_length=50, default='content_based')
    
    class Meta:
        unique_together = ('product_1', 'product_2', 'similarity_type')
        indexes = [
            models.Index(fields=['product_1', 'similarity_score']),
            models.Index(fields=['product_2', 'similarity_score']),
        ]
    
    def __str__(self):
        return f"{self.product_1.name} <-> {self.product_2.name}: {self.similarity_score:.3f}"

class UserProductInteraction(BaseModel):
    """Aggregated user-product interaction scores"""
    user = models.ForeignKey(User, related_name='product_interactions', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', related_name='user_interactions', on_delete=models.CASCADE)
    
    # Interaction scores
    view_score = models.FloatField(default=0.0)
    cart_score = models.FloatField(default=0.0)
    purchase_score = models.FloatField(default=0.0)
    wishlist_score = models.FloatField(default=0.0)
    review_score = models.FloatField(default=0.0)
    
    # Aggregated score
    total_score = models.FloatField(default=0.0)
    
    # Timestamps
    first_interaction = models.DateTimeField()
    last_interaction = models.DateTimeField()
    interaction_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'product')
        indexes = [
            models.Index(fields=['user', 'total_score']),
            models.Index(fields=['product', 'total_score']),
        ]
    
    def __str__(self):
        return f"{self.user.email} <-> {self.product.name}: {self.total_score:.2f}"
    
    def update_scores(self):
        """Recalculate interaction scores based on recent behaviors"""
        behaviors = UserBehavior.objects.filter(
            user=self.user,
            content_type__model='product',
            object_id=str(self.product.id)
        )
        
        # Score weights for different behaviors
        score_weights = {
            'view': 1.0,
            'cart_add': 3.0,
            'cart_remove': -1.0,
            'purchase': 10.0,
            'wishlist_add': 2.0,
            'review': 5.0,
        }
        
        # Reset scores
        self.view_score = 0.0
        self.cart_score = 0.0
        self.purchase_score = 0.0
        self.wishlist_score = 0.0
        self.review_score = 0.0
        
        # Calculate scores
        for behavior in behaviors:
            weight = score_weights.get(behavior.behavior_type, 1.0)
            if behavior.behavior_type == 'view':
                self.view_score += weight
            elif behavior.behavior_type in ['cart_add', 'cart_remove']:
                self.cart_score += weight
            elif behavior.behavior_type == 'purchase':
                self.purchase_score += weight
            elif behavior.behavior_type == 'wishlist_add':
                self.wishlist_score += weight
            elif behavior.behavior_type == 'review':
                self.review_score += weight
        
        # Calculate total score
        self.total_score = (
            self.view_score + self.cart_score + self.purchase_score + 
            self.wishlist_score + self.review_score
        )
        
        # Update metadata
        self.interaction_count = behaviors.count()
        if behaviors.exists():
            self.first_interaction = behaviors.earliest('created_at').created_at
            self.last_interaction = behaviors.latest('created_at').created_at
        
        self.save()

class Recommendation(BaseModel):
    """Generated recommendations for users"""
    RECOMMENDATION_TYPES = [
        ('personal', 'Personal Recommendations'),
        ('trending', 'Trending Products'),
        ('similar', 'Similar Products'),
        ('frequently_bought_together', 'Frequently Bought Together'),
        ('recently_viewed', 'Recently Viewed'),
        ('category_based', 'Category-Based'),
        ('seasonal', 'Seasonal'),
    ]
    
    user = models.ForeignKey(User, related_name='recommendations', on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=50, blank=True)
    
    recommendation_type = models.CharField(max_length=30, choices=RECOMMENDATION_TYPES)
    products = models.ManyToManyField('products.Product', through='RecommendationItem')
    
    # Context
    context_product = models.ForeignKey('products.Product', on_delete=models.CASCADE, null=True, blank=True,
                                       related_name='context_recommendations',
                                       help_text="Product that triggered this recommendation")
    context_category = models.ForeignKey('products.Category', on_delete=models.CASCADE, null=True, blank=True)
    
    # Generation info
    model_used = models.ForeignKey(RecommendationModel, on_delete=models.SET_NULL, null=True, blank=True)
    confidence_score = models.FloatField(default=0.0)
    
    # Usage tracking
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    conversions = models.PositiveIntegerField(default=0)
    
    # Validity
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'recommendation_type']),
            models.Index(fields=['session_key', 'recommendation_type']),
            models.Index(fields=['is_active', 'valid_until']),
        ]
    
    def __str__(self):
        user_id = self.user.email if self.user else f"Session: {self.session_key}"
        return f"{user_id} - {self.get_recommendation_type_display()}"
    
    @property
    def click_through_rate(self):
        """Calculate click-through rate"""
        if self.impressions > 0:
            return (self.clicks / self.impressions) * 100
        return 0
    
    @property
    def conversion_rate(self):
        """Calculate conversion rate"""
        if self.clicks > 0:
            return (self.conversions / self.clicks) * 100
        return 0
    
    def record_impression(self):
        """Record that this recommendation was shown"""
        self.impressions += 1
        self.save(update_fields=['impressions'])
    
    def record_click(self, product=None):
        """Record that a product in this recommendation was clicked"""
        self.clicks += 1
        self.save(update_fields=['clicks'])
        
        if product:
            try:
                rec_item = self.recommendationitem_set.get(product=product)
                rec_item.clicks += 1
                rec_item.save(update_fields=['clicks'])
            except:
                pass
    
    def record_conversion(self, product=None):
        """Record that a product in this recommendation was purchased"""
        self.conversions += 1
        self.save(update_fields=['conversions'])
        
        if product:
            try:
                rec_item = self.recommendationitem_set.get(product=product)
                rec_item.conversions += 1
                rec_item.save(update_fields=['conversions'])
            except:
                pass

class RecommendationItem(BaseModel):
    """Individual products in a recommendation with scores"""
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    score = models.FloatField(help_text="Recommendation score for this product")
    rank = models.PositiveIntegerField(help_text="Position in the recommendation list")
    
    # Individual tracking
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    conversions = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('recommendation', 'product')
        ordering = ['rank']
    
    def __str__(self):
        return f"#{self.rank}: {self.product.name} (score: {self.score:.3f})"

class RecommendationFeedback(BaseModel):
    """User feedback on recommendations"""
    FEEDBACK_TYPES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
        ('not_interested', 'Not Interested'),
        ('already_owned', 'Already Owned'),
        ('too_expensive', 'Too Expensive'),
    ]
    
    user = models.ForeignKey(User, related_name='recommendation_feedback', on_delete=models.CASCADE)
    recommendation = models.ForeignKey(Recommendation, related_name='feedback', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, null=True, blank=True)
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    comment = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('user', 'recommendation', 'product')
    
    def __str__(self):
        return f"{self.user.email} - {self.get_feedback_type_display()}"

class TrendingProduct(BaseModel):
    """Track trending products for recommendations"""
    product = models.OneToOneField('products.Product', on_delete=models.CASCADE, related_name='trending_data')
    
    # Trending scores (calculated periodically)
    daily_score = models.FloatField(default=0.0)
    weekly_score = models.FloatField(default=0.0)
    monthly_score = models.FloatField(default=0.0)
    
    # Metrics contributing to trending score
    view_velocity = models.FloatField(default=0.0)
    purchase_velocity = models.FloatField(default=0.0)
    cart_add_velocity = models.FloatField(default=0.0)
    
    # Rankings
    daily_rank = models.PositiveIntegerField(null=True, blank=True)
    weekly_rank = models.PositiveIntegerField(null=True, blank=True)
    monthly_rank = models.PositiveIntegerField(null=True, blank=True)
    
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-daily_score']
        indexes = [
            models.Index(fields=['daily_score']),
            models.Index(fields=['weekly_score']),
            models.Index(fields=['monthly_score']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - Trending (Daily: {self.daily_score:.2f})"