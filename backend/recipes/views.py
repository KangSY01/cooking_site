from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from django.db.models import Count
from django.core.files.storage import default_storage
from django.utils.crypto import get_random_string
from rest_framework.parsers import MultiPartParser, FormParser
import os
from rest_framework import permissions
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

from .jwt_utils import create_jwt
from django.shortcuts import render, get_object_or_404
from .authentication import JWTAuthentication
from .models import (
    Recipe,
    RecipeComment,
    Member,
    RecipeLike,
    Rating,
    Follow,
    RecipeSummary,
    Report,
    UserSanction,
)
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

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
    MemberSimpleSerializer,
    PopularRecipeSerializer,
    ReportCreateSerializer,
    ReportListSerializer,
    ReportUpdateSerializer,
    RecipeCreateSerializer,
    MyRecipeSerializer,
    MemberMeSerializer,
)
from .permissions import IsAuthorOrAdmin

class MemberMeAPIView(APIView):
    authentication_classes = [JWTAuthentication]  # ✅ 추가
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        qs = (
            Member.objects
            .filter(pk=request.user.pk)
            .annotate(
                recipe_count=Count("recipes", distinct=True),
                like_received_count=Count("recipes__likes", distinct=True),
            )
        )
        me = qs.first()
        serializer = MemberMeSerializer(me)
        return Response(serializer.data)

class LikedRecipeListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MyRecipeSerializer

    def get_queryset(self):
        user = self.request.user
        # 현재 로그인한 사용자가 좋아요한 레시피
        return (
            Recipe.objects.filter(likes__member=user)
            .order_by("-likes__liked_at", "-created_at")
            .distinct()
        )

class MyRecipeListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MyRecipeSerializer

    def get_queryset(self):
        # JWT 인증으로 들어온 현재 로그인 사용자 기준
        return Recipe.objects.filter(
            author=self.request.user
        ).order_by("-created_at")

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


class RecipeDetailAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, recipe_id):
        return get_object_or_404(Recipe, pk=recipe_id)

    def get(self, request, recipe_id):
        recipe = self.get_object(recipe_id)
        serializer = RecipeDetailSerializer(recipe)
        return Response(serializer.data)

    def delete(self, request, recipe_id):
        recipe = self.get_object(recipe_id)

        # 1) 로그인 확인
        if not request.user.is_authenticated:
            return Response({"detail": "로그인이 필요합니다."}, status=401)

        # 2) 작성자 또는 관리자만 삭제 가능
        # author 필드 이름은 실제 모델에 맞게 조정 (예: recipe.author_id, recipe.author)
        author_id = getattr(recipe, "author_id", None)
        user_role = getattr(request.user, "role", None)

        if (request.user.id != author_id) and (user_role != "ADMIN"):
            return Response({"detail": "삭제 권한이 없습니다."}, status=403)

        # 3) 삭제
        recipe.delete()
        return Response(status=204)


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


class PopularRecipeListAPIView(generics.ListAPIView):
    """
    GET /api/recipes/popular/
    v_recipe_summary 뷰를 기반으로 한 인기 레시피 목록
    """
    queryset = RecipeSummary.objects.all().order_by(
        '-like_count',
        '-avg_score',
        '-rating_count',
        '-comment_count',
        '-recipe_id',
    )
    serializer_class = PopularRecipeSerializer
    permission_classes = [permissions.AllowAny]


class RecipeReportCreateAPIView(APIView):
    """
    POST /api/recipes/<recipe_id>/report/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, recipe_id):
        reporter: Member = request.user
        recipe = get_object_or_404(Recipe, recipe_id=recipe_id)

        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data['reason']

        # 유저가 이미 PENDING 신고를 보낸 경우 막기
        existing = Report.objects.filter(
            reporter=reporter,
            target_type='RECIPE',
            recipe=recipe,
            status='PENDING'
        ).first()

        if existing:
            return Response(
                {"detail": "이미 처리 대기 중인 신고가 있습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        report = Report.objects.create(
            reporter=reporter,
            target_type='RECIPE',
            recipe=recipe,
            reason=reason,
            status='PENDING',
            created_at=timezone.now(),
        )

        return Response(
            {"report_id": report.report_id, "message": "신고가 접수되었습니다."},
            status=status.HTTP_201_CREATED
        )

class CommentReportCreateAPIView(APIView):
    """
    POST /api/comments/<comment_id>/report/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        reporter: Member = request.user
        comment = get_object_or_404(RecipeComment, comment_id=comment_id)

        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data['reason']

        existing = Report.objects.filter(
            reporter=reporter,
            target_type='COMMENT',
            comment=comment,
            status='PENDING'
        ).first()

        if existing:
            return Response(
                {"detail": "이미 처리 대기 중인 신고가 있습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        report = Report.objects.create(
            reporter=reporter,
            target_type='COMMENT',
            comment=comment,
            reason=reason,
            status='PENDING',
            created_at=timezone.now(),
        )

        return Response(
            {"report_id": report.report_id, "message": "신고가 접수되었습니다."},
            status=status.HTTP_201_CREATED
        )


class AdminReportListAPIView(APIView):
    """
    GET /api/admin/reports/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # admin: Member = request.user

        # if admin.role != "ADMIN":
        #     return Response(
        #         {"detail": "관리자만 접근할 수 있습니다."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )

        status_filter = request.query_params.get('status')

        qs = Report.objects.select_related('reporter', 'handled_by').order_by('-created_at')

        if status_filter:
            qs = qs.filter(status=status_filter)
        else:
            qs = qs.filter(status='PENDING')

        serializer = ReportListSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AdminReportUpdateAPIView(APIView):
    """
    PATCH /api/admin/reports/<report_id>/
    - 신고 상태 처리 (RESOLVED / REJECTED 등)
    - handle_note 작성
    - RESOLVED인 경우, 신고 대상 사용자에게 WARNING 제재 생성
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, report_id):
        # admin: Member = request.user

        # if admin.role != "ADMIN":
        #     return Response(
        #         {"detail": "관리자만 접근할 수 있습니다."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )

        report = get_object_or_404(Report, report_id=report_id)

        serializer = ReportUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        status_value = serializer.validated_data.get('status')
        handle_note = serializer.validated_data.get('handle_note')

        # 트랜잭션 시작
        with transaction.atomic():
            # 1) 신고 상태/메모 업데이트
            if status_value:
                report.status = status_value
            if handle_note is not None:
                report.handle_note = handle_note

            report.handled_by = admin
            report.handled_at = timezone.now()
            report.save()

            created_sanction_id = None

            # 2) RESOLVED인 경우, 제재(WARNING) 생성
            if status_value == 'RESOLVED':
                # 신고 대상 사용자: 레시피 작성자 or 댓글 작성자
                if report.target_type == 'RECIPE' and report.recipe_id:
                    target_member = report.recipe.author
                elif report.target_type == 'COMMENT' and report.comment_id:
                    target_member = report.comment.author
                else:
                    target_member = None

                if target_member:
                    sanction = UserSanction.objects.create(
                        member=target_member,
                        sanction='WARNING',
                        reason=handle_note or f"신고 처리 (report_id={report.report_id})에 따른 경고",
                        start_at=timezone.now(),
                        created_by=admin,
                        created_at=timezone.now(),
                    )
                    created_sanction_id = sanction.sanction_id

        return Response(
            {
                "report_id": report.report_id,
                "status": report.status,
                "handled_at": report.handled_at,
                "handled_by": admin.member_id,
                "handle_note": report.handle_note,
                "created_sanction_id": created_sanction_id,
            },
            status=status.HTTP_200_OK,
        )

from rest_framework.parsers import MultiPartParser, FormParser

class RecipeCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        # 0) 이미지 파일 받기
        image_file = request.FILES.get("image")

        image_path = None
        if image_file:
            ext = os.path.splitext(image_file.name)[1]
            filename = f"recipes/{get_random_string(12)}{ext}"

            saved_path = default_storage.save(filename, image_file)
            image_path = f"/media/{saved_path}"

        # 1) 재료 읽기
        ingredients = []
        idx = 0
        while True:
            name_key = f"ingredients[{idx}][name]"
            amount_key = f"ingredients[{idx}][amount]"
            if name_key not in request.data:
                break
            ingredients.append({
                "name": request.data[name_key],
                "amount": request.data.get(amount_key, "")
            })
            idx += 1

        # 2) 단계 읽기
        steps = []
        idx = 0
        while True:
            content_key = f"steps[{idx}][content]"
            order_key = f"steps[{idx}][step_order]"
            if content_key not in request.data:
                break
            steps.append({
                "content": request.data[content_key],
                "step_order": int(request.data[order_key]),
            })
            idx += 1

        data = {
            "title": request.data.get("title"),
            "description": request.data.get("description"),
            "cooking_time": request.data.get("cooking_time"),
            "image_path": image_path,
            "ingredients": ingredients,
            "steps": steps,
        }

        serializer = RecipeCreateSerializer(data=data)

        if serializer.is_valid():
            recipe = serializer.save(author=request.user)
            return Response({"recipe_id": recipe.recipe_id}, status=201)

        # 디버깅할 때는 이걸 잠깐 켜두면 어디서 막히는지 보임
        # print("serializer errors:", serializer.errors)
        return Response(serializer.errors, status=400)