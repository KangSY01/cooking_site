from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .jwt_utils import create_jwt
from django.shortcuts import render
from .authentication import JWTAuthentication
from .models import Recipe, RecipeComment, Member
from rest_framework.permissions import IsAuthenticated

# Create your views here.
from rest_framework import generics
from .models import Recipe, RecipeComment
from .serializers import (
    RecipeListSerializer,
    RecipeDetailSerializer,
    RecipeCommentSerializer,
    MemberSignupSerializer,
    MemberLoginSerializer,
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

# ============================
# 회원가입 / 로그인 API
# ============================

class MemberSignupAPIView(APIView):
    def post(self, request):
        serializer = MemberSignupSerializer(data=request.data)
        if serializer.is_valid():
            member = serializer.save()
            return Response(
                {
                    "member_id": member.member_id,
                    "login_id": member.login_id,
                    "name": member.name,
                    "role": member.role,
                    "message": "회원가입이 완료되었습니다.",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MemberLoginAPIView(APIView):
    def post(self, request):
        serializer = MemberLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        member: Member = serializer.validated_data["member"]
        access_token = create_jwt(member_id=member.member_id, role=member.role)

        return Response(
            {
                "access_token": access_token,
                "token_type": "Bearer",
                "member_id": member.member_id,
                "login_id": member.login_id,
                "name": member.name,
                "role": member.role,
            },
            status=status.HTTP_200_OK,
        )

class MemberMeAPIView(APIView):
    """
    GET /api/auth/me/
    현재 토큰으로 인증된 사용자 정보 반환
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        member: Member = request.user  # JWTAuthentication에서 반환한 Member 객체

        return Response(
            {
                "member_id": member.member_id,
                "login_id": member.login_id,
                "name": member.name,
                "role": member.role,
            },
            status=status.HTTP_200_OK,
        )
