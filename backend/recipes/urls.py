from django.urls import path
from .views import (
    RecipeListAPIView,
    RecipeDetailAPIView,
    RecipeCommentListAPIView,
    MemberSignupAPIView,
    MemberLoginAPIView,
    MemberMeAPIView,
)

app_name = 'recipes'

urlpatterns = [
    path('api/recipes/', RecipeListAPIView.as_view(), name='recipe-list'),
    path('api/recipes/<int:recipe_id>/', RecipeDetailAPIView.as_view(), name='recipe-detail'),
    path('api/recipes/<int:recipe_id>/comments/', RecipeCommentListAPIView.as_view(), name='recipe-comments'),

    # 회원가입 / 로그인 API
    path("api/auth/signup/", MemberSignupAPIView.as_view(), name="member-signup"),
    path("api/auth/login/", MemberLoginAPIView.as_view(), name="member-login"),
    path("api/auth/me/", MemberMeAPIView.as_view(), name="member-me"),
]
