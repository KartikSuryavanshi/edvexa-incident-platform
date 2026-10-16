import secrets
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    subject: str
    role: str


def configured_users() -> list[tuple[str, str, str]]:
    users = []
    for item in settings.auth_tokens.split(","):
        parts = item.strip().split(":", 1)
        if len(parts) == 2 and parts[0] and parts[1]:
            users.append((parts[1], parts[0], f"demo-{parts[0]}"))
    return users


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    access_token: str | None = Query(default=None, description="Local SSE compatibility token"),
) -> CurrentUser:
    token_value = credentials.credentials if credentials is not None else access_token
    if token_value is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required", headers={"WWW-Authenticate": "Bearer"})
    for token, role, subject in configured_users():
        if secrets.compare_digest(token_value, token):
            return CurrentUser(subject=subject, role=role)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token", headers={"WWW-Authenticate": "Bearer"})


def require_role(*allowed_roles: str):
    def dependency(user: CurrentUser = Depends(current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for this operation")
        return user
    return dependency
