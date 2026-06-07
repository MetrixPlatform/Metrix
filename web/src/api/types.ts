export interface RoleBrief {
  id: number;
  code: string;
  name: string;
}

export interface UserProfile {
  id: number;
  username: string;
  full_name: string;
  phone: string;
  email: string;
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

export interface InstallStatus {
  installed: boolean;
  database_type: string | null;
}

export interface ServerMessage {
  code: string;
  message?: string;
  params?: Record<string, string | number | boolean | null>;
}

export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export type AnnouncementTargetType = "all" | "authenticated" | "permission" | "company" | "company_department" | "user";

export interface AnnouncementItem {
  id: number;
  title: string;
  content: string;
  target_type: AnnouncementTargetType;
  target_value: string;
  show_popup: boolean;
  show_ticker: boolean;
  show_sidebar: boolean;
  is_active: boolean;
  created_by: number | null;
  created_by_username: string;
  created_at: string;
  updated_at: string;
}

export interface AnnouncementFeedItem extends AnnouncementItem {
  is_read: boolean;
  read_at: string | null;
}

export interface PublicAnnouncementItem {
  id: number;
  title: string;
  content: string;
  created_at: string;
}

export interface AuditLogItem {
  id: number;
  actor_user_id: number | null;
  actor_username: string;
  action: string;
  target_type: string;
  target_id: string;
  detail: string;
  created_at: string;
}

export interface RegistrationRequiredFields {
  phone: boolean;
  email: boolean;
  company: boolean;
  department: boolean;
}

export interface PublicSettings {
  app_name: string;
  registration_enabled: boolean;
  registration_required_fields: RegistrationRequiredFields;
  default_locale: "zh-CN" | "en-US";
  api_enabled: boolean;
  api_token_reveal_enabled: boolean;
}

export interface SystemSettings extends PublicSettings {
  log_retention_days: 7 | 30 | 90 | 180 | 365;
}

export interface ApiTokenItem {
  id: number;
  name: string;
  token_prefix: string;
  secret_available: boolean;
  is_active: boolean;
  expires_at: string | null;
  last_used_at: string | null;
  created_at: string;
}

export interface ApiTokenCreateResponse extends ApiTokenItem {
  token: string;
}
