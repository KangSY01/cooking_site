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
    RecipeCommentCreateAPIView,
    RecipeCommentDeleteAPIView,
    FollowToggleAPIView,
    FollowingListAPIView,
    PopularRecipeListAPIView,
    RecipeReportCreateAPIView,     # ✅ 추가
    CommentReportCreateAPIView,    # ✅ 추가
    AdminReportListAPIView,        # ✅ 추가
    AdminReportUpdateAPIView,      # ✅ 추가
)

app_name = 'recipes'

urlpatterns = [
    # 레시피 목록 & 생성
    path('api/recipes/', RecipeListAPIView.as_view(), name='recipe-list'),

    # 레시피 상세 / 수정 / 삭제
    path('api/recipes/<int:recipe_id>/', RecipeDetailAPIView.as_view(), name='recipe-detail'),

    # 댓글 조회 / 작성 / 삭제
    path('api/recipes/<int:recipe_id>/comments/', RecipeCommentListAPIView.as_view(), name='recipe-comments'),
    path('api/recipes/<int:recipe_id>/comments/create/', RecipeCommentCreateAPIView.as_view(), name='recipe-comment-create'),
    path('api/comments/<int:comment_id>/', RecipeCommentDeleteAPIView.as_view(), name='recipe-comment-delete'),

    # 회원가입 / 로그인 / 본인 정보
    path("api/auth/signup/", MemberSignupAPIView.as_view(), name="member-signup"),
    path("api/auth/login/", MemberLoginAPIView.as_view(), name="member-login"),
    path("api/auth/me/", MemberMeAPIView.as_view(), name="member-me"),

    # 좋아요
    path('api/recipes/<int:recipe_id>/like/', RecipeLikeToggleAPIView.as_view(), name='recipe-like-toggle'),

    # 평점
    path('api/recipes/<int:recipe_id>/rating/', RecipeRatingAPIView.as_view(), name='recipe-rating'),

    # 팔로우
    path('api/members/<int:member_id>/follow/', FollowToggleAPIView.as_view(), name='member-follow'),
    path('api/members/<int:member_id>/following/', FollowingListAPIView.as_view(), name='member-following'),

    # 인기 레시피
    path('api/recipes/popular/', PopularRecipeListAPIView.as_view(), name='recipe-popular'),

    # ✅ 신고 관련
    path('api/recipes/<int:recipe_id>/report/', RecipeReportCreateAPIView.as_view(), name='recipe-report'),
    path('api/comments/<int:comment_id>/report/', CommentReportCreateAPIView.as_view(), name='comment-report'),
    path('api/admin/reports/', AdminReportListAPIView.as_view(), name='admin-report-list'),
    path('api/admin/reports/<int:report_id>/', AdminReportUpdateAPIView.as_view(), name='admin-report-update'),
]
