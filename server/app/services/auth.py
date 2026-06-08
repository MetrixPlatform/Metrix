from sqlalchemy.orm import Session

from app.core.exceptions import bad_request
from app.core.permissions import USER_ROLE
from app.core.security import create_access_token, hash_password, verify_password
from app.core.time import utc_now
from app.models import Role, User
from app.repositories.roles import RoleRepository
from app.repositories.users import UserRepository
from app.schemas.auth import ChangePasswordRequest, LoginRequest, ProfileUpdateRequest, RegisterRequest
from app.schemas.settings import PublicSettings
from app.services.audit import audit_changes, audit_detail, record_audit
from app.services.permissions import get_user_permission_codes
from app.services.settings import SettingService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, payload: RegisterRequest) -> User:
        settings = self._guard_registration(payload)
        if self.users.get_by_username(payload.username):
            raise bad_request("error.usernameExists", "Username already exists")
        approval_required = settings.registration_approval_required
        approval_status = "pending" if approval_required else "approved"
        user = User(
            username=payload.username,
            full_name=payload.full_name,
            phone=payload.phone,
            email=payload.email,
            company=payload.company,
            department=payload.department,
            password_hash=hash_password(payload.password),
            approval_status=approval_status,
            approved_at=None if approval_required else utc_now(),
            is_active=True,
            is_builtin=False,
            roles=[] if approval_required else self._default_user_roles(),
        )
        self.users.create(user)
        record_audit(
            self.db,
            None,
            "user.register",
            "user",
            str(user.id),
            user.username,
            audit_detail(
                user.username,
                meta={
                    "username": user.username,
                    "full_name": user.full_name,
                    "phone": user.phone,
                    "email": user.email,
                    "company": user.company,
                    "department": user.department,
                    "approval_status": user.approval_status,
                    "registration_approval_required": approval_required,
                },
            ),
        )
        self.db.commit()
        return user

    def _guard_registration(self, payload: RegisterRequest) -> PublicSettings:
        settings = SettingService(self.db).public_settings()
        if not settings.registration_enabled:
            raise bad_request("error.registrationDisabled", "Registration is disabled")
        required = settings.registration_required_fields
        missing_fields = [
            field
            for field, required_flag in {
                "phone": required.phone,
                "email": required.email,
                "company": required.company,
                "department": required.department,
            }.items()
            if required_flag and not getattr(payload, field).strip()
        ]
        if missing_fields:
            raise bad_request("error.registrationFieldRequired", "Required registration field is missing", field=missing_fields[0])
        return settings

    def _default_user_roles(self) -> list[Role]:
        role = RoleRepository(self.db).get_by_code(USER_ROLE)
        return [role] if role else []

    def login(self, payload: LoginRequest) -> tuple[str, User, list[str]]:
        user = self.users.get_by_username(payload.username)
        if not user or not verify_password(payload.password, user.password_hash):
            record_audit(
                self.db,
                None,
                "auth.login_failed",
                "user",
                "",
                payload.username,
                audit_detail(payload.username, meta={"reason": "invalid_credentials"}),
            )
            self.db.commit()
            raise bad_request("error.invalidCredentials", "Invalid username or password")
        if user.approval_status != "approved":
            raise bad_request("error.accountPending", "Account approval is pending")
        if not user.is_active:
            raise bad_request("error.accountDisabled", "Account is disabled")
        user.last_login_at = utc_now()
        token = create_access_token(str(user.id))
        permissions = sorted(get_user_permission_codes(user))
        record_audit(self.db, user.id, "auth.login", "user", str(user.id), user.username, audit_detail(user.username))
        self.db.commit()
        return token, user, permissions

    def update_profile(self, user: User, payload: ProfileUpdateRequest) -> User:
        before = _user_profile_snapshot(user)
        user.full_name = payload.full_name
        user.phone = payload.phone
        user.email = payload.email
        user.company = payload.company
        user.department = payload.department
        record_audit(
            self.db,
            user.id,
            "auth.profile_update",
            "user",
            str(user.id),
            user.username,
            audit_detail(user.username, audit_changes(before, _user_profile_snapshot(user))),
        )
        self.db.commit()
        return user

    def change_password(self, user: User, payload: ChangePasswordRequest) -> None:
        if not verify_password(payload.old_password, user.password_hash):
            raise bad_request("error.oldPasswordIncorrect", "Old password is incorrect")
        user.password_hash = hash_password(payload.new_password)
        record_audit(
            self.db,
            user.id,
            "auth.change_password",
            "user",
            str(user.id),
            user.username,
            audit_detail(user.username, meta={"password_changed": True}),
        )
        self.db.commit()


def _user_profile_snapshot(user: User) -> dict[str, str]:
    return {
        "full_name": user.full_name,
        "phone": user.phone,
        "email": user.email,
        "company": user.company,
        "department": user.department,
    }
