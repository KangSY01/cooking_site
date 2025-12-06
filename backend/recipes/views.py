from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from .models import Recipe, RecipeComment
from .serializers import (
    RecipeListSerializer,
    RecipeDetailSerializer,
    RecipeCommentSerializer,
)


class RecipeListAPIView(generics.ListAPIView):
    """
    GET /api/recipes/
    레시피 목록 조회
    """
    queryset = Recipe.objects.select_related('author').order_by('-created_at')
    serializer_class = RecipeListSerializer


class RecipeDetailAPIView(generics.RetrieveAPIView):
    """
    GET /api/recipes/<pk>/
    특정 레시피 상세 조회
    """
    queryset = Recipe.objects.select_related('author')
    serializer_class = RecipeDetailSerializer
    lookup_field = 'recipe_id'  # 기본은 pk 이지만, 우리는 recipe_id가 PK이므로 이렇게 명시


class RecipeCommentListAPIView(generics.ListAPIView):
    """
    GET /api/recipes/<recipe_id>/comments/
    해당 레시피의 댓글 목록 조회
    """
    serializer_class = RecipeCommentSerializer

    def get_queryset(self):
        recipe_id = self.kwargs['recipe_id']
        return (
            RecipeComment.objects
            .select_related('author', 'recipe')
            .filter(recipe_id=recipe_id)
            .order_by('created_at')
        )
