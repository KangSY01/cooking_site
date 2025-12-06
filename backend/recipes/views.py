from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .jwt_utils import create_jwt
from django.shortcuts import render
from .authentication import JWTAuthentication
from .models import Recipe, RecipeComment, Member, RecipeLike, Rating, Follow
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import render, get_object_or_404

# Create your views here.
from rest_framework import generics, permissions
from .models import Recipe, RecipeComment
from .serializers import (
    RecipeListSerializer,
    RecipeDetailSerializer,
    RecipeCommentSerializer,
    MemberSignupSerializer,
    MemberLoginSerializer,
    RecipeCreateUpdateSerializer,
    RatingCreateUpdateSerializer,
    RecipeCommentCreateSerializer,
)
from .permissions import IsAuthorOrAdmin

class RecipeListAPIView(generics.ListCreateAPIView):
    """
    GET  /api/recipes/   : 누구나 조회 가능
    POST /api/recipes/   : 로그인한 회원이면 누구나 작성 가능
    """
    queryset = Recipe.objects.select_related('author').order_by('-created_at')

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]   # ✅ IsCook 제거
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer


class RecipeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/recipes/<recipe_id>/   상세 조회 (모두)
    PUT    /api/recipes/<recipe_id>/   수정 (작성자 또는 ADMIN)
    DELETE /api/recipes/<recipe_id>/   삭제 (작성자 또는 ADMIN)
    """
    queryset = Recipe.objects.select_related('author')
    lookup_field = 'recipe_id'       # DB PK 필드명
    lookup_url_kwarg = 'recipe_id'   # URL 변수명과 맞춰주기 (api/recipes/<int:recipe_id>/)

    def get_permissions(self):
        # 수정/삭제는 로그인 + 작성자 or ADMIN
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsAuthorOrAdmin()]
        # GET은 모두 허용
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        # 수정할 때는 생성/수정용
        if self.request.method in ['PUT', 'PATCH']:
            return RecipeCreateUpdateSerializer
        # 조회할 때는 상세 Serializer
        return RecipeDetailSerializer


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


class RecipeLikeToggleAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, recipe_id):
        member: Member = request.user
        recipe = get_object_or_404(Recipe, recipe_id=recipe_id)

        qs = RecipeLike.objects.filter(member=member, recipe=recipe)

        if qs.exists():
            # 이미 좋아요 되어 있으면 → 취소
            qs.delete()   # ✅ member+recipe 조건으로 삭제
            return Response({"liked": False}, status=status.HTTP_200_OK)
        else:
            # 아직 좋아요 안 했으면 → 추가
            RecipeLike.objects.create(member=member, recipe=recipe)
            return Response({"liked": True}, status=status.HTTP_201_CREATED)


class RecipeRatingAPIView(APIView):
    """
    GET    /api/recipes/<recipe_id>/rating/
    POST   /api/recipes/<recipe_id>/rating/
    DELETE /api/recipes/<recipe_id>/rating/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, recipe_id=recipe_id)

        my_score = None
        member = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        if member:
            rating = Rating.objects.filter(recipe=recipe, member=member).first()
            if rating:
                my_score = rating.score

        return Response(
            {
                "recipe_id": recipe.recipe_id,
                "avg_score": recipe.avg_score,
                "rating_count": recipe.rating_count,
                "my_score": my_score,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, recipe_id):
        # 로그인 필수
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"detail": "로그인이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        recipe = get_object_or_404(Recipe, recipe_id=recipe_id)
        member: Member = request.user

        serializer = RatingCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        score = serializer.validated_data["score"]

        rating, created = Rating.objects.update_or_create(
            recipe=recipe,
            member=member,
            defaults={"score": score},
        )

        # 트리거에 의해 recipe.avg_score, rating_count가 갱신되었을 수 있으니 새로 읽기
        recipe.refresh_from_db()

        return Response(
            {
                "created": created,
                "score": rating.score,
                "recipe_id": recipe.recipe_id,
                "avg_score": recipe.avg_score,
                "rating_count": recipe.rating_count,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, recipe_id):
        # 로그인 필수
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"detail": "로그인이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        recipe = get_object_or_404(Recipe, recipe_id=recipe_id)
        member: Member = request.user

        qs = Rating.objects.filter(recipe=recipe, member=member)
        if not qs.exists():
            return Response(
                {"detail": "이 레시피에 남긴 평점이 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        qs.delete()
        recipe.refresh_from_db()

        return Response(
            {
                "deleted": True,
                "recipe_id": recipe.recipe_id,
                "avg_score": recipe.avg_score,
                "rating_count": recipe.rating_count,
            },
            status=status.HTTP_200_OK,
        )


class RecipeCommentCreateAPIView(APIView):
    """
    POST /api/recipes/<recipe_id>/comments/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, recipe_id):
        serializer = RecipeCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipe = get_object_or_404(Recipe, recipe_id=recipe_id)
        member: Member = request.user
        content = serializer.validated_data["content"]

        comment = RecipeComment.objects.create(
            recipe=recipe,
            author=member,
            content=content
        )

        return Response(
            RecipeCommentSerializer(comment).data,
            status=status.HTTP_201_CREATED
        )
class RecipeCommentDeleteAPIView(APIView):
    """
    DELETE /api/comments/<comment_id>/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, comment_id):
        comment = get_object_or_404(RecipeComment, comment_id=comment_id)
        
        # 본인이거나 관리자여야 함
        if not (request.user.member_id == comment.author_id or request.user.role == "ADMIN"):
            return Response(
                {"detail": "삭제 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowToggleAPIView(APIView):
    """
    POST /api/members/<member_id>/follow/
    - 팔로우 안 했으면 생성
    - 이미 팔로우 했으면 삭제(언팔)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, member_id):
        me: Member = request.user

        # 자기 자신을 팔로우하는 것은 불가
        if me.member_id == member_id:
            return Response(
                {"detail": "자기 자신을 팔로우할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        followee = get_object_or_404(Member, member_id=member_id)

        qs = Follow.objects.filter(follower=me, followee=followee)

        if qs.exists():
            # 이미 팔로우 → 언팔로우
            qs.delete()
            return Response({"following": False}, status=status.HTTP_200_OK)
        else:
            # 새로 팔로우
            Follow.objects.create(follower=me, followee=followee)
            return Response({"following": True}, status=status.HTTP_201_CREATED)


class FollowingListAPIView(APIView):
    """
    GET /api/members/<member_id>/following/
    member_id 사용자가 팔로우하는 사람들 리스트
    """
    def get(self, request, member_id):
        member = get_object_or_404(Member, member_id=member_id)

        followings = Member.objects.filter(
            follower_set__follower=member
        )

        data = MemberSimpleSerializer(followings, many=True).data
        return Response(data, status=status.HTTP_200_OK)
