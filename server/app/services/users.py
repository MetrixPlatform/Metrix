from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, forbidden, not_found
from app.core.permissions import ADMIN_ROLE, USER_ROLE
from app.core.security import hash_password
from app.core.time import utc_now
from app.models import Role, User
from app.repositories.roles import RoleRepository
from app.repositories.users import UserRepository
from app.schemas.user import AssignRolesRequest, RejectUserRequest, ResetPasswordRequest, UserCreateRequest, UserListResponse, UserUpdateRequest
from app.services.audit import audit_changes, audit_detail, record_audit


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)

    def list_users(
        self,
        keyword: str = "",
        approval_status: str = "",
        is_active: bool | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        sort_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> UserListResponse:
        created_at_order = "ascend" if sort_order == "ascend" else "descend"
        users, total = self.users.list(
            keyword,
            approval_status,
            is_active,
            start_time,
            end_time,
            created_at_order,
            page,
            page_size,
        )
        return UserListResponse(items=users, total=total, page=page, page_size=page_size)

    def list_role_options(self) -> list[Role]:
        return self.roles.list()

    def get_user(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if not user:
            raise not_found("error.userNotFound", "User not found")
        return user

    def create_user(self, actor: User, payload: UserCreateRequest) -> User:
        if self.users.get_by_username(payload.username):
            raise bad_request("error.usernameExists", "Username already exists")
        user = User(
            username=payload.username,
            full_name=payload.full_name,
            phone=payload.phone,
            email=payload.email,
            company=payload.company,
            department=payload.department,
            password_hash=hash_password(payload.password),
            approval_status="approved",
            is_active=True,
            roles=self._roles_or_default(payload.role_ids),
        )
        self.users.create(user)
        record_audit(
            self.db,
            actor.id,
            "user.create",
            "user",
            str(user.id),
            user.username,
            audit_detail(user.username, meta={**_user_snapshot(user), "roles": _role_codes(user.roles)}),
        )
        self.db.commit()
        return user

    def update_user(self, actor: User, user_id: int, payload: UserUpdateRequest) -> User:
        user = self.get_user(user_id)
        before = _user_profile_snapshot(user)
        user.full_name = payload.full_name
        user.phone = payload.phone
        user.email = payload.email
        user.company = payload.company
        user.department = payload.department
        record_audit(
            self.db,
            actor.id,
            "user.update",
            "user",
            str(user.id),
            user.username,
            audit_detail(user.username, audit_changes(before, _user_profile_snapshot(user))),
        )
        self.db.commit()
        return user

    def delete_user(self, actor: User, user_id: int) -> None:
        user = self.get_user(user_id)
        self._guard_last_admin(user)
        if user.is_builtin:
            raise forbidden("error.builtinUserCannotDelete", "Built-in users cannot be deleted")
        record_audit(
            self.db,
            actor.id,
            "user.delete",
            "user",
            str(user.id),
            user.username,
            audit_detail(user.username, meta={**_user_snapshot(user), "roles": _role_codes(user.roles)}),
        )
        self.users.delete(user)
        self.db.commit()

    def approve_user(self, actor: User, user_id: int, role_ids: list[int] | None = None) -> User:
        user = self.get_user(user_id)
        if user.approval_status != "pending":
            raise bad_request("error.onlyPendingUserCanApprove", "Only pending users can be approved")
        before = {"approval_status": user.approval_status, "roles": _role_codes(user.roles)}
        user.roles = self._roles_or_default(role_ids)
        user.approval_status = "approved"
        user.approved_by = actor.id
        user.approved_at = utc_now()
        record_audit(
            self.db,
            actor.id,
            "user.approve",
            "user",
            str(user.id),
            user.username,
            audit_detail(user.username, audit_changes(before, {"approval_status": user.approval_status, "roles": _role_codes(user.roles)})),
        )
        self.db.commit()
        return user

    def reject_user(self, actor: User, user_id: int, payload: RejectUserRequest) -> User:
        user = self.get_user(user_id)
        if user.approval_status != "pending":
            raise bad_request("error.onlyPendingUserCanReject", "Only pending users can be rejected")
        before = {"approval_status": user.approval_status, "rejected_reason": user.rejected_reason}
        user.approval_status = "rejected"
        user.rejected_reason = payload.reason
        record_audit(
            self.db,
            actor.id,
            "user.reject",
            "user",
            str(user.id),
            user.username,
            audit_detail(
                user.username,
                audit_changes(before, {"approval_status": user.approval_status, "rejected_reason": user.rejected_reason}),
            ),
        )
        self.db.commit()
        return user

    def enable_user(self, actor: User, user_id: int) -> User:
        user = self.get_user(user_id)
        before = {"is_active": user.is_active}
        user.is_active = True
        record_audit(
            self.db,
            actor.id,
            "user.enable",
            "user",
            str(user.id),
            user.username,
            audit_detail(user.username, audit_changes(before, {"is_active": user.is_active})),
        )
        self.db.commit()
        return user

    def disable_user(self, actor: User, user_id: int) -> User:
        user = self.get_user(user_id)
        self._guard_last_admin(user)
        before = {"is_active": user.is_active}
        user.is_active = False
        record_audit(
            self.db,
            actor.id,
            "user.disable",
            "user",
            str(user.id),
            user.username,
            audit_detail(user.username, audit_changes(before, {"is_active": user.is_active})),
        )
        self.db.commit()
        return user

    def reset_password(self, actor: User, user_id: int, payload: ResetPasswordRequest) -> None:
        user = self.get_user(user_id)
        user.password_hash = hash_password(payload.password)
        record_audit(
            self.db,
            actor.id,
            "user.reset_password",
            "user",
            str(user.id),
            user.username,
            audit_detail(user.username, meta={"password_changed": True}),
        )
        self.db.commit()

    def assign_roles(self, actor: User, user_id: int, payload: AssignRolesRequest) -> User:
        user = self.get_user(user_id)
        roles = self.roles.by_ids(payload.role_ids)
        self._guard_last_admin_role_change(user, roles)
        self._guard_self_admin_role(actor, user, roles)
        before = {"roles": _role_codes(user.roles)}
        user.roles = roles
        record_audit(
            self.db,
            actor.id,
            "user.assign_roles",
            "user",
            str(user.id),
            user.username,
            audit_detail(user.username, audit_changes(before, {"roles": _role_codes(user.roles)})),
        )
        self.db.commit()
        return user

    def _guard_last_admin(self, user: User) -> None:
        if any(role.code == ADMIN_ROLE for role in user.roles) and self.users.count_admins() <= 1:
            raise forbidden("error.lastAdminRequired", "The last administrator cannot be changed")

    def _roles_or_default(self, role_ids: list[int] | None) -> list[Role]:
        roles = self.roles.by_ids(role_ids or [])
        if roles:
            return roles
        default_role = self.roles.get_by_code(USER_ROLE)
        return [default_role] if default_role else []

    def _guard_last_admin_role_change(self, target: User, roles: list[Role]) -> None:
        if not any(role.code == ADMIN_ROLE for role in target.roles) or self.users.count_admins() > 1:
            return
        if not any(role.code == ADMIN_ROLE for role in roles):
            raise forbidden("error.lastAdminRoleRequired", "The last administrator role cannot be removed")

    def _guard_self_admin_role(self, actor: User, target: User, roles: list[Role]) -> None:
        if actor.id != target.id:
            return
        if not any(role.code == ADMIN_ROLE for role in roles):
            raise forbidden("error.selfAdminRoleRequired", "You cannot remove your own administrator role")


def _role_codes(roles: list[Role]) -> list[str]:
    return sorted(role.code for role in roles)


def _user_profile_snapshot(user: User) -> dict[str, str]:
    return {
        "full_name": user.full_name,
        "phone": user.phone,
        "email": user.email,
        "company": user.company,
        "department": user.department,
    }


def _user_snapshot(user: User) -> dict[str, object]:
    return {
        "username": user.username,
        **_user_profile_snapshot(user),
        "approval_status": user.approval_status,
        "is_active": user.is_active,
    }
