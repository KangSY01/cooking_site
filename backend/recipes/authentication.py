# backend/recipes/authentication.py
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .jwt_utils import decode_jwt
from .models import Member


class JWTAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            raise AuthenticationFailed("Authorization 헤더 형식이 올바르지 않습니다. 'Bearer <token>'")

        token = parts[1]
        payload = decode_jwt(token)
        if payload is None:
            raise AuthenticationFailed("토큰이 유효하지 않거나 만료되었습니다.")

        member_id = payload.get("member_id")
        if member_id is None:
            raise AuthenticationFailed("토큰에 member_id가 없습니다.")

        try:
            member = Member.objects.get(member_id=member_id)
        except Member.DoesNotExist:
            raise AuthenticationFailed("해당 사용자를 찾을 수 없습니다.")

        return (member, token)
