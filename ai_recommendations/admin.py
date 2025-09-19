from django.contrib import admin
from .models import (RecommendationModel, UserBehavior, ProductSimilarity, 
                    UserProductInteraction, Recommendation, RecommendationItem)

@admin.register(RecommendationModel)
class RecommendationsModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_type', 'is_active', 'is_trained', 'accuracy_score']
    list_filter = ['model_type', 'is_active', 'is_trained']
    search_fields = ['name', 'description']
    readonly_fields = ['last_trained_at', 'training_duration']

@admin.register(UserBehavior)
class UserBehaviorAdmin(admin.ModelAdmin):
    list_display = ['user', 'behavior_type', 'object_id', 'created_at']
    list_filter = ['behavior_type', 'created_at']
    search_fields = ['user__email', 'session_key']
    readonly_fields = ['created_at']

@admin.register(Recommendation)
class RecommendationsAdmin(admin.ModelAdmin):
    list_display = ['user', 'recommendation_type', 'model_used', 'confidence_score', 'created_at']
    list_filter = ['recommendation_type', 'model_used', 'is_active']
    search_fields = ['user__email', 'session_key']
    readonly_fields = ['impressions', 'clicks', 'conversions', 'click_through_rate', 'conversion_rate']