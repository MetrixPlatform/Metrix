export interface RoleBrief {
  id: number;
  code: string;
  name: string;
}

export interface UserProfile {
  id: number;
  username: string;
  full_name: string;
  company: string;
  department: string;
  approval_status: string;
  is_active: boolean;
  is_builtin: boolean;
  roles: RoleBrief[];
}

export interface UserListItem extends UserProfile {
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PermissionItem {
  id: number;
  code: string;
  name: string;
  type: string;
  resource: string;
  group_name: string;
  description: string;
  sort_order: number;
}

export interface RoleItem {
  id: number;
  code: string;
  name: string;
  description: string;
  is_builtin: boolean;
  permissions: PermissionItem[];
  created_at: string;
  updated_at: string;
}

export interface LoginResponse {
  token: string;
  user: UserProfile;
  permissions: string[];
}

export interface DashboardSummary {
  user_count: number;
  pending_user_count: number;
  role_count: number;
  permission_count: number;
}

export interface InstallStatus {
  installed: boolean;
  database_type: string | null;
}
