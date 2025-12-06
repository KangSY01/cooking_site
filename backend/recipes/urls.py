from django.urls import path
from .views import (
    RecipeListAPIView,
    RecipeDetailAPIView,
    RecipeCommentListAPIView,
)

app_name = 'recipes'

urlpatterns = [
    path('api/recipes/', RecipeListAPIView.as_view(), name='recipe-list'),
    path('api/recipes/<int:recipe_id>/', RecipeDetailAPIView.as_view(), name='recipe-detail'),
    path('api/recipes/<int:recipe_id>/comments/', RecipeCommentListAPIView.as_view(), name='recipe-comments'),
]
