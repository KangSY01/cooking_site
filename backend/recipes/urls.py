from django.urls import path
from .views import (
    RecipeListAPIView,
    RecipeDetailAPIView,
    RecipeCommentListAPIView,
    MemberSignupAPIView,
    MemberLoginAPIView,
    MemberMeAPIView,
    RecipeLikeToggleAPIView,
    RecipeRatingAPIView,
)

app_name = 'recipes'

urlpatterns = [
    path('api/recipes/', RecipeListAPIView.as_view(), name='recipe-list'),
    path('api/recipes/<int:recipe_id>/', RecipeDetailAPIView.as_view(), name='recipe-detail'),
    path('api/recipes/<int:recipe_id>/comments/', RecipeCommentListAPIView.as_view(), name='recipe-comments'),

    path("api/auth/signup/", MemberSignupAPIView.as_view(), name="member-signup"),
    path("api/auth/login/", MemberLoginAPIView.as_view(), name="member-login"),
    path("api/auth/me/", MemberMeAPIView.as_view(), name="member-me"),
    
    # ✅ 좋아요 토글 API
    path('api/recipes/<int:recipe_id>/like/', RecipeLikeToggleAPIView.as_view(), name='recipe-like-toggle'),

     # ✅ 평점 API
    path('api/recipes/<int:recipe_id>/rating/', RecipeRatingAPIView.as_view(), name='recipe-rating'),
]

