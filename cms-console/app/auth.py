#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
from itsdangerous import URLSafeSerializer
from app.config import (
    APP_SECRET_KEY,
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
)

serializer = URLSafeSerializer(APP_SECRET_KEY)


def verify_login(username: str, password: str) -> bool:
    return (
        username == ADMIN_USERNAME
        and password == ADMIN_PASSWORD
    )


def create_session_token(username: str) -> str:
    return serializer.dumps(
        {"username": username}
    )


def verify_session_token(token: str | None) -> bool:
    if not token:
        return False

    try:
        data = serializer.loads(token)
        return (
            data.get("username")
            == ADMIN_USERNAME
        )
    except Exception:
        return False