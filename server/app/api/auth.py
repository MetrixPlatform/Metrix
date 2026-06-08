from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_web_session
from app.db.session import get_db
from app.models import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse, ProfileUpdateRequest, RegisterRequest
from app.schemas.common import MessageResponse, message_response
from app.schemas.user import UserProfile
from app.services.auth import AuthService
from app.services.permissions import get_user_permission_codes

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> MessageResponse:
    AuthService(db).register(payload)
    return message_response("auth.registerSubmitted", "Registration request submitted")


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    token, user, permissions = AuthService(db).login(payload)
    return LoginResponse(token=token, user=UserProfile.model_validate(user), permissions=permissions)


@router.post("/logout", response_model=MessageResponse)
def logout(
    user: User = Depends(get_current_user),
    _: None = Depends(require_web_session),
) -> MessageResponse:
    return message_response("auth.loggedOut", "Logged out", username=user.username)


@router.get("/me", response_model=LoginResponse)
def me(
    user: User = Depends(get_current_user),
    _: None = Depends(require_web_session),
) -> LoginResponse:
    return LoginResponse(token="", user=UserProfile.model_validate(user), permissions=sorted(get_user_permission_codes(user)))


@router.put("/profile", response_model=UserProfile)
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(require_web_session),
) -> UserProfile:
    updated_user = AuthService(db).update_profile(user, payload)
    return UserProfile.model_validate(updated_user)


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(require_web_session),
) -> MessageResponse:
    AuthService(db).change_password(user, payload)
    return message_response("profile.passwordChanged", "Password changed")
