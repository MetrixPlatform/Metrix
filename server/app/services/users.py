from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, forbidden, not_found
from app.core.permissions import ADMIN_ROLE, USER_ROLE
from app.core.security import hash_password
from app.core.time import utc_now
from app.models import Role, User
from app.repositories.roles import RoleRepository
from app.repositories.users import UserRepository
from app.schemas.user import AssignRolesRequest, RejectUserRequest, ResetPasswordRequest, UserCreateRequest, UserUpdateRequest
from app.services.audit import record_audit


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)

    def list_users(self, keyword: str = "", approval_status: str = "", is_active: bool | None = None) -> list[User]:
        return self.users.list(keyword, approval_status, is_active)

    def get_user(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if not user:
            raise not_found("用户不存在")
        return user

    def create_user(self, actor: User, payload: UserCreateRequest) -> User:
        if self.users.get_by_username(payload.username):
            raise bad_request("账号已存在")
        user = User(
            username=payload.username,
            full_name=payload.full_name,
            company=payload.company,
            department=payload.department,
            password_hash=hash_password(payload.password),
            approval_status="approved",
            is_active=True,
            roles=self._roles_or_default(payload.role_ids),
        )
        self.users.create(user)
        record_audit(self.db, actor.id, "user.create", "user", str(user.id), user.username)
        self.db.commit()
        return user

    def update_user(self, actor: User, user_id: int, payload: UserUpdateRequest) -> User:
        user = self.get_user(user_id)
        user.full_name = payload.full_name
        user.company = payload.company
        user.department = payload.department
        record_audit(self.db, actor.id, "user.update", "user", str(user.id), user.username)
        self.db.commit()
        return user

    def delete_user(self, actor: User, user_id: int) -> None:
        user = self.get_user(user_id)
        self._guard_last_admin(user)
        if user.is_builtin:
            raise forbidden("内置用户不能删除")
        record_audit(self.db, actor.id, "user.delete", "user", str(user.id), user.username)
        self.users.delete(user)
        self.db.commit()

    def approve_user(self, actor: User, user_id: int, role_ids: list[int] | None = None) -> User:
        user = self.get_user(user_id)
        if user.approval_status != "pending":
            raise bad_request("只能审核待审核用户")
        user.roles = self._roles_or_default(role_ids)
        user.approval_status = "approved"
        user.approved_by = actor.id
        user.approved_at = utc_now()
        record_audit(self.db, actor.id, "user.approve", "user", str(user.id), user.username)
        self.db.commit()
        return user

    def reject_user(self, actor: User, user_id: int, payload: RejectUserRequest) -> User:
        user = self.get_user(user_id)
        if user.approval_status != "pending":
            raise bad_request("只能驳回待审核用户")
        user.approval_status = "rejected"
        user.rejected_reason = payload.reason
        record_audit(self.db, actor.id, "user.reject", "user", str(user.id), user.username)
        self.db.commit()
        return user

    def enable_user(self, actor: User, user_id: int) -> User:
        user = self.get_user(user_id)
        user.is_active = True
        record_audit(self.db, actor.id, "user.enable", "user", str(user.id), user.username)
        self.db.commit()
        return user

    def disable_user(self, actor: User, user_id: int) -> User:
        user = self.get_user(user_id)
        self._guard_last_admin(user)
        user.is_active = False
        record_audit(self.db, actor.id, "user.disable", "user", str(user.id), user.username)
        self.db.commit()
        return user

    def reset_password(self, actor: User, user_id: int, payload: ResetPasswordRequest) -> None:
        user = self.get_user(user_id)
        user.password_hash = hash_password(payload.password)
        record_audit(self.db, actor.id, "user.reset_password", "user", str(user.id), user.username)
        self.db.commit()

    def assign_roles(self, actor: User, user_id: int, payload: AssignRolesRequest) -> User:
        user = self.get_user(user_id)
        self._guard_last_admin_role_change(user, payload.role_ids)
        self._guard_self_admin_role(actor, user, payload.role_ids)
        roles = self.roles.by_ids(payload.role_ids)
        user.roles = roles
        record_audit(self.db, actor.id, "user.assign_roles", "user", str(user.id), user.username)
        self.db.commit()
        return user

    def _guard_last_admin(self, user: User) -> None:
        if any(role.code == ADMIN_ROLE for role in user.roles) and self.users.count_admins() <= 1:
            raise forbidden("不能操作最后一个管理员")

    def _roles_or_default(self, role_ids: list[int] | None) -> list[Role]:
        roles = self.roles.by_ids(role_ids or [])
        if roles:
            return roles
        default_role = self.roles.get_by_code(USER_ROLE)
        return [default_role] if default_role else []

    def _guard_last_admin_role_change(self, target: User, role_ids: list[int]) -> None:
        if not any(role.code == ADMIN_ROLE for role in target.roles) or self.users.count_admins() > 1:
            return
        roles = self.roles.by_ids(role_ids)
        if not any(role.code == ADMIN_ROLE for role in roles):
            raise forbidden("不能移除最后一个管理员的管理员角色")

    def _guard_self_admin_role(self, actor: User, target: User, role_ids: list[int]) -> None:
        if actor.id != target.id:
            return
        roles = self.roles.by_ids(role_ids)
        if not any(role.code == ADMIN_ROLE for role in roles):
            raise forbidden("不能移除自己的管理员角色")
