from rest_framework import permissions


class IsAuthorOrAdmin(permissions.BasePermission):
    """
    레시피 수정/삭제 시:
      - 레시피 작성자 본인
      - ADMIN
    만 허용.
    """
    def has_object_permission(self, request, view, obj):
        # 읽기(GET, HEAD, OPTIONS)는 모두 허용
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False

        is_author = (obj.author_id == user.member_id)
        is_admin = (user.role == "ADMIN")
        return is_author or is_admin
