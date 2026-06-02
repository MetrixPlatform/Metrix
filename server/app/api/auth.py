from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse, ProfileUpdateRequest, RegisterRequest
from app.schemas.common import MessageResponse
from app.schemas.user import UserProfile
from app.services.auth import AuthService
from app.services.permissions import get_user_permission_codes

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> MessageResponse:
    AuthService(db).register(payload)
    return MessageResponse(message="注册申请已提交，请等待管理员审核")


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    token, user, permissions = AuthService(db).login(payload)
    return LoginResponse(token=token, user=user, permissions=permissions)


@router.post("/logout", response_model=MessageResponse)
def logout(user: User = Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message=f"{user.username} 已退出")


@router.get("/me", response_model=LoginResponse)
def me(user: User = Depends(get_current_user)) -> LoginResponse:
    return LoginResponse(token="", user=user, permissions=sorted(get_user_permission_codes(user)))


@router.put("/profile", response_model=UserProfile)
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    return AuthService(db).update_profile(user, payload)


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MessageResponse:
    AuthService(db).change_password(user, payload)
    return MessageResponse(message="密码已修改")
