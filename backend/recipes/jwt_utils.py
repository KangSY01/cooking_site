import datetime
import jwt
from django.conf import settings

JWT_EXP_DELTA_DAYS = 1
JWT_ALGORITHM = "HS256"


def create_jwt(member_id: int, role: str) -> str:
    """
    member_id, role을 payload에 넣어 JWT access token 생성
    """
    exp = datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXP_DELTA_DAYS)
    payload = {
        "member_id": member_id,
        "role": role,          # COOK / GOURMET / ADMIN
        "type": "access",
        "exp": exp,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def decode_jwt(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
