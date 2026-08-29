const TOKEN_KEY = "eaios_token";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, message: string, detail = message) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

function parseDetail(text: string): string {
  try {
    const data = JSON.parse(text) as { detail?: unknown };
    const detail = data.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => (typeof item === "object" && item && "msg" in item ? String((item as { msg: string }).msg) : String(item)))
        .join("; ");
    }
    if (detail && typeof detail === "object") return JSON.stringify(detail);
  } catch {
    /* texto plano */
  }
  return text;
}

function userMessage(status: number, detail: string): string {
  if (status === 401) return "Su sesión ha vencido. Inicie sesión nuevamente.";
  if (status === 403) return "No tiene permisos para realizar esta acción.";
  if (status === 404) return "El recurso solicitado no fue encontrado.";
  if (status === 409) return detail || "La operación no puede completarse por un conflicto de estado.";
  if (status === 422) return detail || "Los datos enviados no son válidos.";
  if (status >= 500) return "Ocurrió un error al procesar la solicitud.";
  return detail || "No se pudo completar la solicitud.";
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let res: Response;
  try {
    res = await fetch(path, { ...options, headers });
  } catch (err) {
    console.error("[api] network error", path, err);
    throw new ApiError(0, "No se pudo conectar con el servidor. Verifique que el backend esté en ejecución.");
  }

  if (!res.ok) {
    const detail = parseDetail(text);
    const message = userMessage(res.status, detail);
    console.error("[api]", res.status, path, detail);
    if (res.status === 401) {
      const isLoginAttempt = path === "/api/auth/login";
      if (!isLoginAttempt) {
        clearToken();
        sessionStorage.removeItem("eaios_user");
        if (!window.location.pathname.startsWith("/login")) {
          window.location.href = "/login?expired=1";
        }
      }
    }
    throw new ApiError(res.status, message, detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  if (res.status === 204) {
    return undefined as T;
  }
  const text = await res.text();
  if (!text) {
    return undefined as T;
  }
  return JSON.parse(text) as T;
}

export type UserMe = {
  id: string;
  username: string;
  role: string;
  organization_id: string;
  organization_name: string;
  email?: string | null;
  full_name?: string | null;
  status?: string;
  permissions: string[];
  auth_via_sso?: boolean;
  identity_provider_name?: string | null;
};

export type Organization = {
  id: string;
  name: string;
  slug?: string;
  status?: string;
  timezone?: string;
  created_at: string;
  updated_at?: string | null;
};

export type PlatformOrganization = {
  id: string;
  name: string;
  slug: string;
  status: string;
  timezone: string;
  created_at: string;
  updated_at?: string | null;
  users_count: number;
};

export type PlatformOrganizationCreateResponse = {
  organization: PlatformOrganization;
  admin_user_id: string;
  admin_username: string;
  temporary_password?: string | null;
};

export type AdminUser = {
  id: string;
  username: string;
  email: string | null;
  full_name: string | null;
  role: string;
  status: string;
  is_active: boolean;
  organization_id: string;
  last_login_at: string | null;
  created_at: string;
  updated_at: string | null;
};

export type AdminRole = {
  id: string;
  code: string;
  name: string;
  description: string | null;
  is_system: boolean;
  is_active: boolean;
  organization_id: string | null;
};

export type OrgConfig = {
  language: string;
  timezone: string;
  date_format: string;
  time_format: string;
};

export type SecuritySummary = {
  users_active: number;
  users_inactive: number;
  users_blocked: number;
  roles_total: number;
  recent_events: Array<{ action: string; detail: string | null; created_at: string }>;
  mfa_enabled_count?: number;
  scim_metrics?: {
    users_provisioned: number;
    users_active: number;
    users_deactivated: number;
    errors_count: number;
    conflicts_count: number;
    rate_limited_count: number;
    requests_total: number;
    last_sync_at: string | null;
    last_latency_ms: number | null;
  } | null;
  scim_rate_limit_note?: string | null;
};

export type AdminUserMfaOverview = {
  enabled: boolean;
  enrollment_pending: boolean;
  confirmed_at?: string | null;
  updated_at?: string | null;
  mfa_required_by_policy: boolean;
  policy_mfa_mode?: string | null;
  allowed_method: string;
};

export type AdminUserIdentityOrigin = {
  source: string;
  provider_code?: string | null;
  provider_name?: string | null;
  external_subject_ref?: string | null;
};

export type AdminUserProvisionOverview = {
  status: string;
  external_id?: string | null;
  scim_resource_id?: string | null;
  updated_at?: string | null;
};

export type AdminUserOverview = {
  id: string;
  username: string;
  email: string | null;
  full_name: string | null;
  role: string;
  role_name?: string | null;
  status: string;
  is_active: boolean;
  organization_id: string;
  organization_name?: string | null;
  last_login_at: string | null;
  created_at: string;
  updated_at: string | null;
  mfa: AdminUserMfaOverview;
  identity_origin: AdminUserIdentityOrigin;
  provisioning: AdminUserProvisionOverview;
};

export type AdminUserPermissionEffective = {
  code: string;
  source: string;
  role_code?: string | null;
  organization_id: string;
};

export type AdminUserAuditEntry = {
  stream: string;
  action: string;
  result?: string | null;
  actor_id?: string | null;
  organization_id?: string | null;
  detail?: string | null;
  correlation_id?: string | null;
  created_at: string;
};

export type AdminUserIdentityDetail = {
  user: AdminUser;
  organization_name?: string | null;
  role_name?: string | null;
  mfa: AdminUserMfaOverview;
  identity_origin: AdminUserIdentityOrigin;
  provisioning: AdminUserProvisionOverview;
  permissions_effective: AdminUserPermissionEffective[];
  sessions: Array<{
    id: string;
    ip_address?: string | null;
    user_agent?: string | null;
    created_at: string;
    last_activity_at: string;
    expires_at: string;
    mfa_verified: boolean;
    auth_method?: string | null;
  }>;
  audit_entries: AdminUserAuditEntry[];
  scim_user_events: Array<{
    action: string;
    result: string;
    detail?: string | null;
    correlation_id?: string | null;
    created_at: string;
  }>;
};

export type AuditLog = {
  id: string;
  action: string;
  detail: string | null;
  user_id: string | null;
  created_at: string;
};

export type PlanResult = {
  plan_id: string;
  correlation_id?: string;
  status: string;
  objective?: string;
  summary?: string;
  confidence?: number;
  approval_status?: string;
  error?: string;
  result?: {
    findings?: Array<{ severity: string; code: string; message: string }>;
    summary?: string;
    confidence?: number;
    evidence?: unknown;
  };
  tasks?: Array<{
    id: string;
    title: string;
    status: string;
    executor_type: string;
    confidence?: number;
    approval_status: string;
  }>;
  started_at?: string;
  completed_at?: string;
};

export type ExecutionItem = {
  id: string;
  request: string;
  objective: string;
  status: string;
  summary?: string;
  confidence?: number;
  approval_status: string;
  employee_id?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
};

export type ExecutionDetail = PlanResult;

export type EmployeeItem = {
  id: string;
  code: string;
  name: string;
  specialty: string;
  lifecycle_status: string;
  maturity: string;
  risk_level: string;
  status: string;
  version: number;
  capabilities: string[];
  model_provider?: string;
  model_name?: string;
  last_certification?: string;
  shadow_mode?: boolean;
  created_at?: string;
  updated_at?: string;
};

export type ApprovalItem = {
  id: string;
  work_plan_id: string;
  action: string;
  employee_name?: string;
  reason: string;
  impact?: string;
  status: string;
  created_at: string;
};

export type WorkEventItem = {
  id: string;
  event_type: string;
  work_plan_id?: string;
  task_id?: string;
  created_at: string;
};

export type DashboardSummary = {
  employees_total: number;
  employees_active: number;
  executions_total: number;
  executions_running: number;
  executions_failed: number;
  approvals_pending: number;
  recent_events: WorkEventItem[];
  recent_audit: AuditLog[];
};

export async function submitWorkRequest(
  message: string,
  context?: Record<string, unknown>,
): Promise<PlanResult> {
  return api<PlanResult>("/api/assistant/ask", {
    method: "POST",
    body: JSON.stringify({ message, context, auto_execute: true }),
  });
}

export async function fetchExecutions(): Promise<ExecutionItem[]> {
  return api<ExecutionItem[]>("/api/operations/executions");
}

export async function fetchExecution(planId: string): Promise<ExecutionDetail> {
  return api<ExecutionDetail>(`/api/operations/executions/${planId}`);
}

export async function fetchEmployees(): Promise<EmployeeItem[]> {
  return api<EmployeeItem[]>("/api/operations/employees");
}

export async function fetchApprovals(): Promise<ApprovalItem[]> {
  return api<ApprovalItem[]>("/api/operations/approvals/pending");
}

export async function decideApproval(
  approvalId: string,
  decision: "approve" | "reject",
  comment?: string,
): Promise<PlanResult> {
  return api<PlanResult>(`/api/operations/approvals/${approvalId}/decide`, {
    method: "POST",
    body: JSON.stringify({ decision, comment }),
  });
}

export async function fetchEvents(): Promise<WorkEventItem[]> {
  return api<WorkEventItem[]>("/api/operations/events");
}

export async function fetchAuditLogs(): Promise<AuditLog[]> {
  return api<AuditLog[]>("/api/audit/logs");
}

export async function fetchOrganization(): Promise<Organization> {
  return api<Organization>("/api/organization");
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const [employees, executions, approvals, events, audit] = await Promise.all([
    fetchEmployees(),
    fetchExecutions(),
    fetchApprovals(),
    fetchEvents(),
    fetchAuditLogs(),
  ]);
  return {
    employees_total: employees.length,
    employees_active: employees.filter((e) => e.lifecycle_status === "ACTIVE").length,
    executions_total: executions.length,
    executions_running: executions.filter((e) => e.status === "RUNNING" || e.status === "PLANNING").length,
    executions_failed: executions.filter((e) => e.status === "FAILED").length,
    approvals_pending: approvals.length,
    recent_events: events.slice(0, 8),
    recent_audit: audit.slice(0, 8),
  };
}

export type NotificationItem = {
  id: string; type: string; severity: string; title: string; message: string;
  source_type: string; source_id?: string; recipient_user_id?: string; recipient_role?: string;
  status: string; channel: string; created_at: string; metadata?: Record<string, unknown>;
};

export async function fetchNotifications(filters = ""): Promise<NotificationItem[]> {
  return api<NotificationItem[]>(`/api/notifications${filters ? `?${filters}` : ""}`);
}

export async function fetchUnreadCount(): Promise<number> {
  return (await api<{ count: number }>("/api/notifications/unread-count")).count;
}

export async function transitionNotification(id: string, action: "read" | "acknowledge" | "dismiss") {
  return api<NotificationItem>(`/api/notifications/${id}/${action}`, { method: "POST" });
}

export type TrabajoAccion = {
  codigo: string;
  etiqueta: string;
  permiso?: string | null;
  href?: string | null;
  payload?: Record<string, unknown> | null;
};

export type TrabajoItem = {
  id: string;
  source_id: string;
  tipo: string;
  asunto: string;
  modulo: string;
  organization_id: string;
  organization_name?: string | null;
  prioridad: string;
  prioridad_orden: number;
  estado_dominio: string;
  estado_presentacion: string;
  responsable_id?: string | null;
  responsable_nombre?: string | null;
  created_at?: string | null;
  fecha_limite?: string | null;
  antiguedad_horas?: number | null;
  vencida: boolean;
  correlation_id?: string | null;
  requires_action: boolean;
  informativa: boolean;
  semantic_kind?: string | null;
  detalle?: string | null;
  enlace: string;
  trazabilidad_enlace?: string | null;
  acciones: TrabajoAccion[];
  metadata?: Record<string, unknown>;
};

export type TrabajoResumen = {
  organization_id: string;
  pendientes: number;
  vencidas: number;
  requieren_aprobacion: number;
  total_visible: number;
};

export type TrabajoItemsResponse = {
  items: TrabajoItem[];
  total: number;
  filtros_aplicados: Record<string, unknown>;
};

export async function fetchTrabajoItems(params: Record<string, string | boolean | undefined> = {}): Promise<TrabajoItemsResponse> {
  const qs = new URLSearchParams();
  for (const [key, val] of Object.entries(params)) {
    if (val !== undefined && val !== "") {
      qs.set(key, String(val));
    }
  }
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return api<TrabajoItemsResponse>(`/api/trabajo/items${suffix}`);
}

export async function fetchTrabajoResumen(): Promise<TrabajoResumen> {
  return api<TrabajoResumen>("/api/trabajo/resumen");
}

export type EmployeeTemplate = { code: string; name: string; description?: string; specialty: string };
export type CapabilityItem = { id: string; code: string; name: string; risk_level: string };
export type ToolItem = { id: string; code: string; name: string; executor_type: string; risk_level: string };

export async function fetchTemplates(): Promise<EmployeeTemplate[]> {
  return api<EmployeeTemplate[]>("/api/agent-factory/templates");
}

export async function fetchCapabilities(): Promise<CapabilityItem[]> {
  return api<CapabilityItem[]>("/api/agent-factory/capabilities");
}

export async function fetchTools(): Promise<ToolItem[]> {
  return api<ToolItem[]>("/api/agent-factory/tools");
}

export async function fetchEmployeeDetail(id: string): Promise<Record<string, unknown>> {
  return api<Record<string, unknown>>(`/api/agent-factory/employees/${id}`);
}

export async function createEmployee(data: {
  name: string;
  specialty: string;
  role?: string;
  objective?: string;
  template_code?: string;
}): Promise<Record<string, unknown>> {
  return api("/api/agent-factory/employees", { method: "POST", body: JSON.stringify(data) });
}

export async function updateEmployee(id: string, data: Record<string, unknown>): Promise<Record<string, unknown>> {
  return api(`/api/agent-factory/employees/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function testEmployee(id: string): Promise<Record<string, unknown>> {
  return api(`/api/agent-factory/employees/${id}/test`, { method: "POST" });
}

export async function certifyEmployee(id: string): Promise<Record<string, unknown>> {
  return api(`/api/agent-factory/employees/${id}/certify`, { method: "POST" });
}

export async function publishEmployee(id: string): Promise<Record<string, unknown>> {
  return api(`/api/agent-factory/employees/${id}/publish`, { method: "POST" });
}

export async function activateEmployee(id: string): Promise<Record<string, unknown>> {
  return api(`/api/agent-factory/employees/${id}/activate`, { method: "POST" });
}


export type AutomationItem = {
  id: string;
  name: string;
  description?: string;
  status: string;
  trigger_type: string;
  schedule_type?: string | null;
  timezone: string;
  start_at?: string | null;
  end_at?: string | null;
  next_run_at?: string;
  last_run_at?: string;
  objective: string;
  employee_id?: string | null;
  priority: number;
  requires_approval: boolean;
  max_retries?: number;
  retry_delay_seconds?: number;
  timeout_seconds?: number | null;
  max_cost_per_run?: number | null;
  max_runs_per_day?: number | null;
  missed_run_policy?: string;
  recurrence?: {
    hour?: number;
    minute?: number;
    interval_minutes?: number;
    event_type?: string;
    weekdays?: number[];
    day_of_month?: number;
  } | null;
  workflow?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type AutomationRunItem = {
  id: string;
  automation_id: string;
  scheduled_for: string;
  started_at?: string;
  finished_at?: string;
  status: string;
  work_plan_id?: string;
  attempt: number;
  error?: string;
  cost_reference?: number;
  trigger_source: string;
  created_at: string;
};

export async function fetchAutomations(): Promise<AutomationItem[]> {
  return api<AutomationItem[]>("/api/automations");
}

export async function fetchAutomation(id: string): Promise<AutomationItem> {
  return api<AutomationItem>(`/api/automations/${id}`);
}

export async function createAutomation(data: Record<string, unknown>): Promise<AutomationItem> {
  return api<AutomationItem>("/api/automations", { method: "POST", body: JSON.stringify(data) });
}

export async function updateAutomation(id: string, data: Record<string, unknown>): Promise<AutomationItem> {
  return api<AutomationItem>(`/api/automations/${id}`, { method: "PUT", body: JSON.stringify(data) });
}

export async function activateAutomation(id: string): Promise<AutomationItem> {
  return api<AutomationItem>(`/api/automations/${id}/activate`, { method: "POST" });
}

export async function pauseAutomation(id: string): Promise<AutomationItem> {
  return api<AutomationItem>(`/api/automations/${id}/pause`, { method: "POST" });
}

export async function disableAutomation(id: string): Promise<AutomationItem> {
  return api<AutomationItem>(`/api/automations/${id}/disable`, { method: "POST" });
}

export async function duplicateAutomation(id: string): Promise<AutomationItem> {
  return api<AutomationItem>(`/api/automations/${id}/duplicate`, { method: "POST" });
}

export async function deleteAutomation(id: string): Promise<void> {
  return api<void>(`/api/automations/${id}`, { method: "DELETE" });
}

export async function runAutomationNow(id: string): Promise<AutomationRunItem> {
  return api<AutomationRunItem>(`/api/automations/${id}/run-now`, { method: "POST" });
}

export async function fetchAutomationRuns(automationId: string): Promise<AutomationRunItem[]> {
  return api<AutomationRunItem[]>(`/api/automations/${automationId}/runs`);
}

export async function fetchAdminUsers(q?: string, status?: string): Promise<AdminUser[]> {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (status) params.set("status", status);
  const qs = params.toString();
  return api<AdminUser[]>(`/api/admin/users${qs ? `?${qs}` : ""}`);
}

export async function fetchAdminUsersOverview(q?: string, status?: string): Promise<AdminUserOverview[]> {
  const params = new URLSearchParams({ vista: "operativa" });
  if (q) params.set("q", q);
  if (status) params.set("status", status);
  return api<AdminUserOverview[]>(`/api/admin/users?${params}`);
}

export async function fetchAdminUser(id: string): Promise<AdminUser> {
  return api<AdminUser>(`/api/admin/users/${id}`);
}

export async function fetchAdminUserIdentityDetail(id: string): Promise<AdminUserIdentityDetail> {
  return api<AdminUserIdentityDetail>(`/api/admin/users/${id}/identidad`);
}

export async function createAdminUser(data: Record<string, unknown>): Promise<AdminUser> {
  return api<AdminUser>("/api/admin/users", { method: "POST", body: JSON.stringify(data) });
}

export async function updateAdminUser(id: string, data: Record<string, unknown>): Promise<AdminUser> {
  return api<AdminUser>(`/api/admin/users/${id}`, { method: "PUT", body: JSON.stringify(data) });
}

export async function setAdminUserStatus(id: string, status: string): Promise<AdminUser> {
  return api<AdminUser>(`/api/admin/users/${id}/status`, { method: "POST", body: JSON.stringify({ status }) });
}

export async function resetAdminUserPassword(id: string): Promise<{ temporary_password: string }> {
  return api(`/api/admin/users/${id}/reset-password`, { method: "POST", body: JSON.stringify({}) });
}

export async function fetchAdminRoles(): Promise<AdminRole[]> {
  return api<AdminRole[]>("/api/admin/roles");
}

export async function fetchPermissionMatrix(): Promise<{
  permissions: Array<{ code: string; module: string; description: string | null }>;
  roles: AdminRole[];
  matrix: Record<string, Record<string, boolean>>;
}> {
  return api("/api/admin/roles/permission-matrix");
}

export async function createAdminRole(data: {
  code: string;
  name: string;
  description?: string | null;
}): Promise<AdminRole> {
  return api<AdminRole>("/api/admin/roles", { method: "POST", body: JSON.stringify(data) });
}

export async function updateRolePermissions(roleId: string, permissionCodes: string[]): Promise<AdminRole> {
  return api<AdminRole>(`/api/admin/roles/${roleId}/permissions`, {
    method: "PUT",
    body: JSON.stringify({ permission_codes: permissionCodes }),
  });
}

export async function fetchAdminOrganization(): Promise<Organization> {
  return api<Organization>("/api/admin/organization");
}

export async function updateAdminOrganization(data: Record<string, unknown>): Promise<Organization> {
  return api<Organization>("/api/admin/organization", { method: "PUT", body: JSON.stringify(data) });
}

export async function fetchOrgConfig(): Promise<OrgConfig> {
  return api<OrgConfig>("/api/admin/config");
}

export async function updateOrgConfig(data: Partial<OrgConfig>): Promise<OrgConfig> {
  return api<OrgConfig>("/api/admin/config", { method: "PUT", body: JSON.stringify(data) });
}

export async function fetchSecuritySummary(): Promise<SecuritySummary> {
  return api<SecuritySummary>("/api/admin/security");
}

export type MfaStatus = {
  enabled: boolean;
  confirmed_at?: string | null;
  recovery_codes_remaining: number;
  enrollment_pending: boolean;
  mfa_required_by_policy: boolean;
};

export type UserSession = {
  id: string;
  ip_address?: string | null;
  user_agent?: string | null;
  created_at: string;
  last_activity_at: string;
  expires_at: string;
  mfa_verified: boolean;
  current: boolean;
  user_id?: string | null;
  username?: string | null;
  auth_method?: string | null;
};

export type SecurityPolicy = {
  mfa_mode: string;
  mfa_required_roles: string[];
  session_duration_minutes: number;
  max_active_sessions: number;
  login_max_attempts: number;
  lockout_minutes: number;
  revoke_sessions_on_password_change: boolean;
  excess_session_policy: string;
};

export type SecurityEvent = {
  id: string;
  event_type: string;
  user_id?: string | null;
  detail?: string | null;
  ip_address?: string | null;
  created_at: string;
};

export async function fetchMfaStatus(): Promise<MfaStatus> {
  return api<MfaStatus>("/api/security/mfa/status");
}

export async function startMfaEnrollment(): Promise<{ secret: string; provisioning_uri: string; qr_data_url: string }> {
  return api("/api/security/mfa/enroll/start", { method: "POST" });
}

export async function confirmMfaEnrollment(code: string): Promise<{ recovery_codes: string[] }> {
  return api("/api/security/mfa/enroll/confirm", { method: "POST", body: JSON.stringify({ code }) });
}

export async function disableMfa(password: string): Promise<void> {
  await api("/api/security/mfa/disable", { method: "POST", body: JSON.stringify({ password }) });
}

export async function regenerateMfaRecovery(password: string): Promise<{ recovery_codes: string[] }> {
  return api("/api/security/mfa/recovery/regenerate", { method: "POST", body: JSON.stringify({ password }) });
}

export async function fetchMySessions(): Promise<UserSession[]> {
  return api<UserSession[]>("/api/security/sessions");
}

export async function revokeMySession(sessionId: string): Promise<void> {
  await api(`/api/security/sessions/${sessionId}`, { method: "DELETE" });
}

export async function revokeOtherSessions(): Promise<void> {
  await api("/api/security/sessions/revoke-others", { method: "POST" });
}

export async function changePassword(current: string, newPassword: string, revokeOthers = true): Promise<void> {
  await api("/api/auth/change-password", {
    method: "POST",
    body: JSON.stringify({
      current_password: current,
      new_password: newPassword,
      revoke_other_sessions: revokeOthers,
    }),
  });
}

export async function verifyMfaLogin(code: string, mfaToken: string): Promise<{ access_token: string }> {
  return api("/api/auth/mfa/verify", {
    method: "POST",
    body: JSON.stringify({ code, mfa_token: mfaToken }),
  });
}

export async function fetchSecurityPolicy(): Promise<SecurityPolicy> {
  return api<SecurityPolicy>("/api/security/policy");
}

export async function updateSecurityPolicy(data: Partial<SecurityPolicy>): Promise<SecurityPolicy> {
  return api<SecurityPolicy>("/api/security/policy", { method: "PUT", body: JSON.stringify(data) });
}

export async function fetchSecurityEvents(limit = 50): Promise<SecurityEvent[]> {
  return api<SecurityEvent[]>(`/api/security/events?limit=${limit}`);
}

export async function fetchAdminSessions(): Promise<UserSession[]> {
  return api<UserSession[]>("/api/security/admin/sessions");
}

export async function revokeAdminSession(sessionId: string): Promise<void> {
  await api(`/api/security/admin/sessions/${sessionId}`, { method: "DELETE" });
}

export type IdentityPolicy = {
  auth_mode: string;
  mfa_sso_mode: string;
  auto_provision_enabled: boolean;
  default_role_on_provision: string;
  allowed_domains: string[];
  org_discovery_code: string | null;
  attribute_mapping: Record<string, unknown>;
  break_glass_enabled: boolean;
  break_glass_configured: boolean;
  scim_prepared: boolean;
  scim_enabled?: boolean;
};

export type ScimStatus = {
  scim_enabled: boolean;
  scim_base_url: string;
  metrics: Record<string, number>;
  tokens: {
    id: string;
    name: string;
    token_prefix: string;
    masked: string;
    active: boolean;
    expires_at: string | null;
    last_used_at: string | null;
    created_at: string;
  }[];
  conflicts_pending: number;
  recent_events: { action: string; result: string; detail: string | null; created_at: string }[];
};

export type ScimRoleMapping = { id: string; external_group: string; role_code: string };

export type ScimConflict = {
  id: string;
  conflict_type: string;
  external_id: string | null;
  detail: string | null;
  created_at: string;
};

export type IdentityProvider = {
  id: string;
  code: string;
  name: string;
  provider_type: string;
  vendor_hint: string | null;
  status: string;
  is_default: boolean;
  secret_configured: boolean;
  config: Record<string, unknown>;
  health: Record<string, string | null>;
};

export type IdentityLoginEvent = {
  id: string;
  login_method: string;
  result: string;
  detail: string | null;
  created_at: string;
};

export async function fetchIdentityPolicy(): Promise<IdentityPolicy> {
  return api<IdentityPolicy>("/api/identidad/politica");
}

export async function updateIdentityPolicy(data: Partial<IdentityPolicy>): Promise<IdentityPolicy> {
  return api<IdentityPolicy>("/api/identidad/politica", { method: "PUT", body: JSON.stringify(data) });
}

export async function fetchIdentityProviders(): Promise<IdentityProvider[]> {
  return api<IdentityProvider[]>("/api/identidad/proveedores");
}

export async function createIdentityProvider(data: Record<string, unknown>): Promise<IdentityProvider> {
  return api<IdentityProvider>("/api/identidad/proveedores", { method: "POST", body: JSON.stringify(data) });
}

export async function testIdentityProvider(id: string): Promise<{ resultado: string; mensaje: string }> {
  return api(`/api/identidad/proveedores/${id}/probar`, { method: "POST", body: JSON.stringify({}) });
}

export async function activateIdentityProvider(id: string): Promise<IdentityProvider> {
  return api<IdentityProvider>(`/api/identidad/proveedores/${id}/activar`, { method: "POST", body: JSON.stringify({}) });
}

export async function upsertGroupRoleMapping(providerId: string, data: { external_group: string; role_code: string }) {
  return api(`/api/identidad/proveedores/${providerId}/mapeos-roles`, { method: "POST", body: JSON.stringify(data) });
}

export async function fetchIdentityEvents(limit = 50): Promise<IdentityLoginEvent[]> {
  return api<IdentityLoginEvent[]>(`/api/identidad/eventos?limit=${limit}`);
}

export async function discoverLogin(orgCode: string): Promise<{ auth_mode: string | null; providers: { id: string; name: string; provider_type: string }[] }> {
  return api("/api/identidad/descubrir", { method: "POST", body: JSON.stringify({ org_code: orgCode }) });
}

export async function beginPublicOidc(providerId: string, orgCode: string): Promise<{ authorization_url: string; state: string }> {
  return api(`/api/identidad/public/oidc/${providerId}/iniciar`, { method: "POST", body: JSON.stringify({ org_code: orgCode }) });
}

export async function completeOidcCallback(state: string, code: string): Promise<{ access_token: string }> {
  return api("/api/identidad/oidc/callback", { method: "POST", body: JSON.stringify({ state, code }) });
}

export async function fetchScimStatus(): Promise<ScimStatus> {
  return api<ScimStatus>("/api/identidad/scim/estado");
}

export async function configureScim(data: { scim_enabled: boolean }): Promise<{ scim_enabled: boolean; message: string }> {
  return api("/api/identidad/scim/configuracion", { method: "PUT", body: JSON.stringify(data) });
}

export async function createScimToken(data?: { name?: string; expires_days?: number }): Promise<{ id: string; token: string; message: string }> {
  return api("/api/identidad/scim/tokens", { method: "POST", body: JSON.stringify(data ?? {}) });
}

export async function rotateScimToken(tokenId: string): Promise<{ id: string; token: string; message: string }> {
  return api(`/api/identidad/scim/tokens/${tokenId}/rotar`, { method: "POST", body: JSON.stringify({}) });
}

export async function revokeScimToken(tokenId: string): Promise<{ message: string }> {
  return api(`/api/identidad/scim/tokens/${tokenId}/revocar`, { method: "POST", body: JSON.stringify({}) });
}

export async function fetchScimRoleMappings(): Promise<ScimRoleMapping[]> {
  return api<ScimRoleMapping[]>("/api/identidad/scim/mapeos-roles");
}

export async function upsertScimRoleMapping(data: { external_group: string; role_code: string }): Promise<ScimRoleMapping> {
  return api<ScimRoleMapping>("/api/identidad/scim/mapeos-roles", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchScimConflicts(): Promise<ScimConflict[]> {
  return api<ScimConflict[]>("/api/identidad/scim/conflictos");
}

export async function fetchPlatformOrganizations(): Promise<PlatformOrganization[]> {
  return api<PlatformOrganization[]>("/api/platform/organizations");
}

export async function createPlatformOrganization(data: {
  name: string;
  slug: string;
  timezone?: string;
  admin_username: string;
  admin_password?: string;
  admin_email?: string;
  admin_full_name?: string;
}): Promise<PlatformOrganizationCreateResponse> {
  return api<PlatformOrganizationCreateResponse>("/api/platform/organizations", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function setPlatformOrganizationStatus(orgId: string, status: "ACTIVE" | "INACTIVE"): Promise<PlatformOrganization> {
  return api<PlatformOrganization>(`/api/platform/organizations/${orgId}/status`, {
    method: "POST",
    body: JSON.stringify({ status }),
  });
}

export async function fetchMe(): Promise<UserMe> {
  return api<UserMe>("/api/auth/me");
}

export type CatalogItem = {
  id: string;
  code: string;
  name: string;
  description?: string;
  status: string;
  risk_level: string;
  category?: string;
  tool_type?: string;
  source_type?: string;
  requires_approval?: boolean;
};

export type AssignmentLists<T> = { assigned: T[]; available: T[] };

export async function fetchCapabilitiesCatalog(search?: string): Promise<CatalogItem[]> {
  const q = search ? `?search=${encodeURIComponent(search)}` : "";
  return api<CatalogItem[]>(`/api/capabilities${q}`);
}

export async function createCapability(data: Record<string, unknown>): Promise<CatalogItem> {
  return api("/api/capabilities", { method: "POST", body: JSON.stringify(data) });
}

export async function updateCapability(id: string, data: Record<string, unknown>): Promise<CatalogItem> {
  return api(`/api/capabilities/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function setCapabilityStatus(id: string, active: boolean): Promise<CatalogItem> {
  return api(`/api/capabilities/${id}/${active ? "activate" : "deactivate"}`, { method: "POST" });
}

export async function fetchToolsCatalog(search?: string): Promise<CatalogItem[]> {
  const q = search ? `?search=${encodeURIComponent(search)}` : "";
  return api<CatalogItem[]>(`/api/tools${q}`);
}

export async function createTool(data: Record<string, unknown>): Promise<CatalogItem> {
  return api("/api/tools", { method: "POST", body: JSON.stringify(data) });
}

export async function updateTool(id: string, data: Record<string, unknown>): Promise<CatalogItem> {
  return api(`/api/tools/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function setToolStatus(id: string, active: boolean): Promise<CatalogItem> {
  return api(`/api/tools/${id}/${active ? "activate" : "deactivate"}`, { method: "POST" });
}

export async function fetchKnowledgeCatalog(search?: string): Promise<CatalogItem[]> {
  const q = search ? `?search=${encodeURIComponent(search)}` : "";
  return api<CatalogItem[]>(`/api/knowledge/sources${q}`);
}

export async function createKnowledgeSource(data: Record<string, unknown>): Promise<CatalogItem> {
  return api("/api/knowledge/sources", { method: "POST", body: JSON.stringify(data) });
}

export async function updateKnowledgeSource(id: string, data: Record<string, unknown>): Promise<CatalogItem> {
  return api(`/api/knowledge/sources/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function setKnowledgeStatus(id: string, active: boolean): Promise<CatalogItem> {
  return api(`/api/knowledge/sources/${id}/${active ? "activate" : "deactivate"}`, { method: "POST" });
}

export async function ingestKnowledge(id: string, content: string, contentType?: string): Promise<Record<string, unknown>> {
  return api(`/api/knowledge/sources/${id}/ingest`, {
    method: "POST",
    body: JSON.stringify({ content, content_type: contentType }),
  });
}

export async function fetchEmployeeCapabilities(employeeId: string): Promise<AssignmentLists<CatalogItem>> {
  return api(`/api/capabilities/employees/${employeeId}/assignments`);
}

export async function assignEmployeeCapability(employeeId: string, capabilityId: string): Promise<AssignmentLists<CatalogItem>> {
  return api(`/api/capabilities/employees/${employeeId}/assign/${capabilityId}`, { method: "POST" });
}

export async function removeEmployeeCapability(employeeId: string, capabilityId: string): Promise<AssignmentLists<CatalogItem>> {
  return api(`/api/capabilities/employees/${employeeId}/assign/${capabilityId}`, { method: "DELETE" });
}

export async function fetchEmployeeTools(employeeId: string): Promise<AssignmentLists<CatalogItem & { permission?: string }>> {
  return api(`/api/tools/employees/${employeeId}/assignments`);
}

export async function assignEmployeeTool(employeeId: string, toolId: string, permission = "ALLOW"): Promise<AssignmentLists<CatalogItem>> {
  return api(`/api/tools/employees/${employeeId}/assign`, {
    method: "POST",
    body: JSON.stringify({ tool_id: toolId, permission }),
  });
}

export async function removeEmployeeTool(employeeId: string, toolId: string): Promise<AssignmentLists<CatalogItem>> {
  return api(`/api/tools/employees/${employeeId}/assign/${toolId}`, { method: "DELETE" });
}

export async function fetchEmployeeKnowledge(employeeId: string): Promise<AssignmentLists<CatalogItem>> {
  return api(`/api/knowledge/employees/${employeeId}/assignments`);
}

export async function assignEmployeeKnowledge(employeeId: string, sourceId: string): Promise<AssignmentLists<CatalogItem>> {
  return api(`/api/knowledge/employees/${employeeId}/assign/${sourceId}`, { method: "POST" });
}

export async function removeEmployeeKnowledge(employeeId: string, sourceId: string): Promise<AssignmentLists<CatalogItem>> {
  return api(`/api/knowledge/employees/${employeeId}/assign/${sourceId}`, { method: "DELETE" });
}

export type TestLabRun = {
  id: string;
  employee_id: string;
  employee_name?: string;
  task_description: string;
  status: string;
  capability_code?: string;
  tool_code?: string;
  knowledge_source_ids?: string[];
  work_plan_id?: string;
  execution_id?: string;
  result?: Record<string, unknown>;
  error_message?: string;
  duration_ms?: number;
  cost?: number;
  cost_label?: string;
  tokens_in?: number;
  tokens_out?: number;
  approval_id?: string;
  created_at?: string;
  completed_at?: string;
};

export async function fetchTestLabRuns(): Promise<TestLabRun[]> {
  return api<TestLabRun[]>("/api/test-lab/runs");
}

export async function runTestLab(data: Record<string, unknown>): Promise<TestLabRun> {
  return api<TestLabRun>("/api/test-lab/run", { method: "POST", body: JSON.stringify(data) });
}

export type FinOpsDashboard = {
  period_start?: string;
  period_end?: string;
  total_cost?: string | null;
  total_cost_label: string;
  total_value?: string | null;
  total_value_label: string;
  estimated_savings?: string | null;
  net_benefit?: string | null;
  roi_percent?: string | null;
  roi_label: string;
  execution_count: number;
  avg_cost_per_work?: string | null;
  currency?: string | null;
};

export type FinOpsConsumption = {
  id: string;
  category?: string;
  provider?: string;
  model_name?: string;
  employee_id?: string | null;
  work_plan_id?: string | null;
  opportunity_id?: string | null;
  tokens_in?: number | null;
  tokens_out?: number | null;
  cost_label: string;
  currency?: string;
  created_at: string;
};

export type FinOpsBudget = {
  id: string;
  name?: string | null;
  scope_type: string;
  amount_limit: string;
  currency: string;
  policy: string;
  alert_threshold_pct: number;
  spent: string;
  balance: string;
  state: string;
  blocks_execution: boolean;
  period_start: string;
  period_end: string;
  active: boolean;
};

export type FinOpsRate = {
  id: string;
  provider?: string | null;
  model_service?: string | null;
  category: string;
  price_input?: string | null;
  price_output?: string | null;
  currency: string;
  active: boolean;
};

export type FinOpsOpportunityEconomics = {
  opportunity_id: string;
  opportunity_codigo: string;
  total_cost_label: string;
  valor_potencial?: string | null;
  valor_materializado?: string | null;
  consumption_count: number;
  consumptions: FinOpsConsumption[];
  finops_reference?: string | null;
  atribucion_nivel?: string | null;
};

export async function fetchFinOpsDashboard(params?: {
  period_start?: string;
  period_end?: string;
}): Promise<FinOpsDashboard> {
  const qs = new URLSearchParams();
  if (params?.period_start) qs.set("period_start", params.period_start);
  if (params?.period_end) qs.set("period_end", params.period_end);
  const suffix = qs.toString() ? `?${qs}` : "";
  return api<FinOpsDashboard>(`/api/finops/dashboard${suffix}`);
}

export async function fetchFinOpsConsumptions(params?: {
  employee_id?: string;
  opportunity_id?: string;
  provider?: string;
  model_name?: string;
  category?: string;
  period_start?: string;
  period_end?: string;
}): Promise<FinOpsConsumption[]> {
  const qs = new URLSearchParams();
  if (params?.employee_id) qs.set("employee_id", params.employee_id);
  if (params?.opportunity_id) qs.set("opportunity_id", params.opportunity_id);
  if (params?.provider) qs.set("provider", params.provider);
  if (params?.model_name) qs.set("model_name", params.model_name);
  if (params?.category) qs.set("category", params.category);
  if (params?.period_start) qs.set("period_start", params.period_start);
  if (params?.period_end) qs.set("period_end", params.period_end);
  const suffix = qs.toString() ? `?${qs}` : "";
  return api<FinOpsConsumption[]>(`/api/finops/consumptions${suffix}`);
}

export async function fetchFinOpsBudgets(): Promise<FinOpsBudget[]> {
  return api<FinOpsBudget[]>("/api/finops/budgets");
}

export async function createFinOpsBudget(data: Record<string, unknown>): Promise<FinOpsBudget> {
  return api<FinOpsBudget>("/api/finops/budgets", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchFinOpsRates(): Promise<FinOpsRate[]> {
  return api<FinOpsRate[]>("/api/finops/rates");
}

export async function createFinOpsRate(data: Record<string, unknown>): Promise<FinOpsRate> {
  return api<FinOpsRate>("/api/finops/rates", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchOpportunityEconomics(opportunityId: string): Promise<FinOpsOpportunityEconomics> {
  return api<FinOpsOpportunityEconomics>(`/api/finops/opportunities/${opportunityId}/economics`);
}

export type ValuationSummary = {
  has_valuation: boolean;
  opportunity_id: string;
  valuation?: {
    id: string;
    value_type: string;
    scope: string;
    currency: string;
    status: string;
    version: number;
  };
  expected?: {
    gross_value?: string | null;
    probability?: string | null;
    adjusted_expected?: string | null;
    execution_cost_expected?: string | null;
    period_days?: number | null;
    value_nature?: string;
    assumptions?: string | null;
    source?: string | null;
    evidence?: string | null;
  };
  scenarios?: Array<{
    scenario_type: string;
    value_amount?: string | null;
    probability?: string | null;
    cost?: string | null;
    period_days?: number | null;
    adjusted_value?: string | null;
    assumptions?: string | null;
  }>;
  real?: {
    materialized_value?: string | null;
    attributable_value?: string | null;
    value_nature?: string;
    attribution_level?: string;
    attribution_pct?: string | null;
    source?: string | null;
    evidence?: string | null;
    justification?: string | null;
  };
  execution_costs?: Array<{ id: string; cost_type: string; amount: string; currency: string }>;
  finops_ia_cost_label?: string;
  total_execution_cost?: string | null;
  gross_expected?: string | null;
  adjusted_expected?: string | null;
  materialized_value?: string | null;
  attributable_value?: string | null;
  net_benefit?: string | null;
  return_label?: string;
  payback_label?: string;
  missing_for_calculation?: string[];
  history?: Array<{ version: number; action: string; change_summary?: string; changed_at: string }>;
};

export async function fetchValuationSummary(opportunityId: string): Promise<ValuationSummary> {
  return api<ValuationSummary>(`/api/valoracion/opportunities/${opportunityId}`);
}

export async function createValuation(
  opportunityId: string,
  data: { value_type: string; scope: string; currency?: string }
): Promise<unknown> {
  return api(`/api/valoracion/opportunities/${opportunityId}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateValuationExpected(
  opportunityId: string,
  data: Record<string, unknown>
): Promise<unknown> {
  return api(`/api/valoracion/opportunities/${opportunityId}/expected`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function updateValuationScenario(
  opportunityId: string,
  scenarioType: string,
  data: Record<string, unknown>
): Promise<unknown> {
  return api(`/api/valoracion/opportunities/${opportunityId}/scenarios/${scenarioType}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function registerValuationReal(
  opportunityId: string,
  data: Record<string, unknown>
): Promise<unknown> {
  return api(`/api/valoracion/opportunities/${opportunityId}/real`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function registerValuationCost(
  opportunityId: string,
  data: Record<string, unknown>
): Promise<unknown> {
  return api(`/api/valoracion/opportunities/${opportunityId}/costs`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function validateValuation(opportunityId: string): Promise<unknown> {
  return api(`/api/valoracion/opportunities/${opportunityId}/validate`, { method: "POST" });
}

export type OperationSummary = {
  running: number;
  pending: number;
  approval: number;
  error: number;
  overdue: number;
  due_soon: number;
};

export type OperationItem = {
  id: string;
  trabajo: string;
  proceso: string | null;
  responsable: string | null;
  empleado_ia: string | null;
  prioridad: string;
  prioridad_codigo: string;
  estado: string;
  estado_codigo: string;
  progreso: string;
  aprobaciones_pendientes: number;
  inicio: string | null;
  vencimiento: string | null;
  vencimiento_estado: string;
  vencimiento_codigo: string;
  ultima_actividad: string | null;
  resultado: string | null;
  approval_status: string;
  confidence: number | null;
  correlation_id: string;
  employee_id: string | null;
  acciones: string[];
};

export type OperationDetail = OperationItem & {
  objective: string;
  summary: string | null;
  error: string | null;
  costo_metadata: Record<string, unknown>;
};

export async function fetchOperationsSummary(): Promise<OperationSummary> {
  return api<OperationSummary>("/api/operations/summary");
}

export async function fetchOperationsCenter(filters = ""): Promise<OperationItem[]> {
  return api<OperationItem[]>(`/api/operations/center${filters ? `?${filters}` : ""}`);
}

export async function fetchOperationDetail(id: string): Promise<OperationDetail> {
  return api<OperationDetail>(`/api/operations/center/${id}`);
}

export async function fetchOperationTasks(id: string) {
  return api<Array<Record<string, unknown>>>(`/api/operations/center/${id}/tasks`);
}

export async function fetchOperationExecutions(id: string) {
  return api<Array<Record<string, unknown>>>(`/api/operations/center/${id}/executions`);
}

export async function fetchOperationApprovals(id: string) {
  return api<Array<Record<string, unknown>>>(`/api/operations/center/${id}/approvals`);
}

export async function fetchOperationResults(id: string) {
  return api<Record<string, unknown>>(`/api/operations/center/${id}/results`);
}

export async function fetchOperationActivity(id: string) {
  return api<Array<Record<string, unknown>>>(`/api/operations/center/${id}/activity`);
}

export async function cancelOperation(id: string): Promise<OperationDetail> {
  return api<OperationDetail>(`/api/operations/center/${id}/cancel`, { method: "POST" });
}

export async function updateOperation(
  id: string,
  body: { prioridad?: string; vencimiento?: string | null; sin_vencimiento?: boolean },
): Promise<OperationDetail> {
  return api<OperationDetail>(`/api/operations/center/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function runOperation(id: string): Promise<PlanResult> {
  return api<PlanResult>(`/api/operations/center/${id}/run`, { method: "POST" });
}

export type KnowledgeDocumentItem = {
  id: string;
  organization_id: string;
  name: string;
  source_type: string;
  file_type: string | null;
  mime_type: string | null;
  status: string;
  original_filename: string | null;
  size_bytes: number | null;
  version: number;
  is_active: boolean;
  error_message: string | null;
  association_count: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
  has_content: boolean;
};

export type KnowledgeDocumentDetail = KnowledgeDocumentItem & {
  processed_content: string | null;
  chunks_count: number;
};

export type KnowledgeActivityItem = {
  id: string;
  action: string;
  detail: string | null;
  user_id: string | null;
  created_at: string;
};

export async function fetchKnowledgeDocuments(): Promise<KnowledgeDocumentItem[]> {
  return api<KnowledgeDocumentItem[]>("/api/knowledge");
}

export async function fetchKnowledgeDocument(id: string): Promise<KnowledgeDocumentDetail> {
  return api<KnowledgeDocumentDetail>(`/api/knowledge/${id}`);
}

export async function fetchKnowledgeActivity(id: string): Promise<KnowledgeActivityItem[]> {
  return api<KnowledgeActivityItem[]>(`/api/knowledge/${id}/activity`);
}

export async function updateKnowledgeDocument(
  id: string,
  data: { name?: string; metadata?: Record<string, unknown>; is_active?: boolean },
): Promise<KnowledgeDocumentItem> {
  return api<KnowledgeDocumentItem>(`/api/knowledge/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function deleteKnowledgeDocument(id: string): Promise<void> {
  await api(`/api/knowledge/${id}`, { method: "DELETE" });
}

export async function reprocessKnowledgeDocument(id: string): Promise<KnowledgeDocumentDetail> {
  return api<KnowledgeDocumentDetail>(`/api/knowledge/${id}/reprocess`, { method: "POST" });
}

export async function deactivateKnowledgeDocument(id: string): Promise<KnowledgeDocumentItem> {
  return api<KnowledgeDocumentItem>(`/api/knowledge/${id}/deactivate`, { method: "POST" });
}

function parseContentDispositionFilename(header: string | null): string | null {
  if (!header) return null;
  const match = /filename\*?=(?:UTF-8''|")?([^";]+)/i.exec(header);
  if (!match?.[1]) return null;
  try {
    return decodeURIComponent(match[1].replace(/"/g, ""));
  } catch {
    return match[1].replace(/"/g, "");
  }
}

/** Descarga autenticada vía Bearer — no expone token en URL. */
export async function downloadKnowledgeDocument(id: string, fallbackFilename?: string): Promise<void> {
  const headers = new Headers();
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const res = await fetch(`/api/knowledge/${id}/download`, { headers });
  if (!res.ok) {
    const text = await res.text();
    const detail = parseDetail(text);
    throw new ApiError(res.status, userMessage(res.status, detail), detail);
  }
  const blob = await res.blob();
  const filename =
    parseContentDispositionFilename(res.headers.get("Content-Disposition")) ||
    fallbackFilename ||
    `documento-${id}`;
  const objectUrl = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = filename;
    anchor.rel = "noopener";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

export async function uploadKnowledgeFile(file: File, name?: string): Promise<KnowledgeDocumentItem> {
  const form = new FormData();
  form.append("file", file);
  const headers = new Headers();
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const url = name ? `/api/knowledge/upload?name=${encodeURIComponent(name)}` : "/api/knowledge/upload";
  const res = await fetch(url, { method: "POST", headers, body: form });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<KnowledgeDocumentItem>;
}

export async function createKnowledgeText(name: string, content: string): Promise<KnowledgeDocumentItem> {
  return api<KnowledgeDocumentItem>("/api/knowledge/text", {
    method: "POST",
    body: JSON.stringify({ name, content }),
  });
}

export async function searchKnowledge(q: string): Promise<Array<{ id: string; name: string; snippet: string | null }>> {
  return api(`/api/knowledge/search?q=${encodeURIComponent(q)}`);
}

export async function retrieveKnowledge(query: string, employeeId?: string): Promise<Array<Record<string, unknown>>> {
  return api("/api/knowledge/retrieve", {
    method: "POST",
    body: JSON.stringify({ query, employee_id: employeeId, limit: 10 }),
  });
}

// --- Oportunidades proactivas (1030) ---

export type OpportunityItem = {
  id: string;
  codigo: string;
  tipo: string;
  dominio: string;
  titulo: string;
  descripcion?: string | null;
  estado: string;
  urgencia: string;
  riesgo?: string | null;
  impacto_estimado: number | null;
  valor_potencial: number | null;
  valor_potencial_certidumbre: string;
  valor_materializado: number | null;
  confianza: number;
  pertinencia: string | null;
  pertinencia_razon?: string | null;
  momento: string | null;
  prioridad_score: number | null;
  siguiente_accion: Record<string, unknown> | null;
  equipo?: Record<string, unknown> | null;
  work_plan_id?: string | null;
  finops_reference?: string | null;
  atribucion_nivel?: string | null;
  correlation_id?: string | null;
  contexto?: Record<string, unknown> | null;
  evidencia?: Record<string, unknown> | unknown[] | null;
  resultado?: Record<string, unknown> | null;
  fecha_deteccion: string | null;
};

export type OpportunityTrackingItem = {
  id?: string;
  accion: string;
  resultado?: string | null;
  responsable_id?: string | null;
  bloqueo?: string | null;
  fecha?: string | null;
};

export type OpportunityTrace = {
  opportunity_id: string;
  correlation_id: string;
  estado: string;
  trazas: Array<{ etapa: string; detalle: unknown; fecha: string }>;
  transiciones: Array<{ de: string; a: string; motivo?: string | null; actor_id?: string | null; fecha?: string | null }>;
  seguimiento: OpportunityTrackingItem[];
};

export type OpportunitySummary = {
  oportunidades_detectadas: number;
  pertinentes: number;
  activadas: number;
  materializadas: number;
  valor_potencial_total: number;
  valor_materializado_total: number;
  pendientes_aprobacion: number;
};

export async function fetchOpportunities(params = ""): Promise<{ items: OpportunityItem[]; total: number }> {
  return api(`/api/oportunidades${params ? `?${params}` : ""}`);
}

export async function fetchOpportunity(id: string): Promise<OpportunityItem> {
  return api(`/api/oportunidades/${id}`);
}

export async function fetchOpportunitySummary(): Promise<OpportunitySummary> {
  return api("/api/oportunidades/resumen");
}

export async function evaluateOpportunity(id: string): Promise<Record<string, unknown>> {
  return api(`/api/oportunidades/${id}/evaluar`, { method: "POST", body: JSON.stringify({}) });
}

export async function approveOpportunity(id: string, aprobado = true, motivo?: string): Promise<OpportunityItem> {
  return api(`/api/oportunidades/${id}/aprobar`, {
    method: "POST",
    body: JSON.stringify({ aprobado, motivo }),
  });
}

export async function activateOpportunity(
  id: string,
  autoExecute = false,
): Promise<Record<string, unknown>> {
  return api(`/api/oportunidades/${id}/activar`, {
    method: "POST",
    body: JSON.stringify({ auto_execute: autoExecute }),
  });
}

export async function addOpportunityTracking(
  id: string,
  data: { accion: string; bloqueo?: string; kpi_inicial?: Record<string, unknown>; kpi_objetivo?: Record<string, unknown> },
): Promise<{ tracking_id: string }> {
  return api(`/api/oportunidades/${id}/seguimiento`, { method: "POST", body: JSON.stringify(data) });
}

export async function registerOpportunityResult(
  id: string,
  data: {
    valor_real?: number;
    valor_esperado?: number;
    evidencia?: Record<string, unknown>;
    estado_resultado?: string;
  },
): Promise<{ resultado: Record<string, unknown>; oportunidad: OpportunityItem }> {
  return api(`/api/oportunidades/${id}/resultado`, { method: "POST", body: JSON.stringify(data) });
}

export async function fetchOpportunityTrace(id: string): Promise<OpportunityTrace> {
  return api(`/api/oportunidades/${id}/trazabilidad`);
}

export async function prioritizeOpportunities(): Promise<Record<string, unknown>> {
  return api("/api/oportunidades/priorizar", { method: "POST", body: JSON.stringify({}) });
}

// --- Señales reales (1120) ---

export type SignalSourceItem = {
  id: string;
  code: string;
  name: string;
  tipo_fuente: string;
  descripcion: string | null;
  is_active: boolean;
  configuracion: Record<string, unknown> | null;
  created_at: string | null;
};

export type SignalItem = {
  id: string;
  tipo: string;
  dominio: string;
  origen: string;
  modo_ingesta: string;
  proceso: string | null;
  metrica: string | null;
  valor_metrica: string | null;
  unidad: string | null;
  referencia: string | null;
  evidencia_resumen: string | null;
  estado_procesamiento: string;
  procesada: boolean;
  opportunity_id?: string | null;
  signal_at: string | null;
  created_at: string | null;
};

export async function fetchSignalSources(): Promise<SignalSourceItem[]> {
  return api("/api/senales/fuentes");
}

export async function fetchRecentSignals(modo?: string): Promise<SignalItem[]> {
  const q = modo ? `?modo=${encodeURIComponent(modo)}` : "";
  return api(`/api/senales${q}`);
}

export async function fetchSignalTrace(signalId: string): Promise<Record<string, unknown>> {
  return api(`/api/senales/${signalId}/trazabilidad`);
}

// --- Diagnósticos transversales (1220) ---

export type DiagnosticSummary = {
  id: string;
  codigo: string;
  version: number;
  estado: string;
  periodo_inicio: string | null;
  periodo_fin: string | null;
  dominios: string[] | null;
  resumen: string | null;
  prioridad_score: number | null;
  created_at: string | null;
  validated_at: string | null;
};

export type DiagnosticFinding = {
  id: string;
  codigo: string;
  tipo_contenido: string;
  que_ocurre: string;
  dominio: string;
  severidad: string;
  confianza: number;
  signal_ids?: string[] | null;
};

export type DiagnosticCause = {
  id: string;
  tipo: string;
  descripcion: string;
  justificacion: string | null;
};

export type DiagnosticDetail = DiagnosticSummary & {
  procesos: string[] | null;
  explicacion: {
    que_esta_pasando?: string;
    donde?: string;
    desde_cuando?: string;
    que_deberia_hacerse?: string;
    nota_evidencia?: string;
  } | null;
  hallazgos: DiagnosticFinding[];
  causas: DiagnosticCause[];
  correlaciones: Array<{ id: string; titulo: string; nota_causalidad: string }>;
  items_estructurados: Array<{
    hallazgo: DiagnosticFinding | null;
    prioridad: number | null;
    accion_recomendada: { accion?: string } | null;
    opportunity_id: string | null;
  }>;
  oportunidades: Array<{ opportunity_id: string; finding_id: string | null; signal_id: string | null }>;
};

export async function fetchDiagnostics(): Promise<DiagnosticSummary[]> {
  return api("/api/diagnosticos");
}

export async function fetchDiagnostic(id: string): Promise<DiagnosticDetail> {
  return api(`/api/diagnosticos/${id}`);
}

export async function generateDiagnostic(body: {
  periodo_inicio?: string;
  periodo_fin?: string;
  dominios?: string[];
}): Promise<DiagnosticDetail> {
  return api("/api/diagnosticos/generar", { method: "POST", body: JSON.stringify(body) });
}

export async function validateDiagnostic(id: string): Promise<DiagnosticDetail> {
  return api(`/api/diagnosticos/${id}/validar`, { method: "POST", body: JSON.stringify({}) });
}

export async function fetchDiagnosticTrace(id: string): Promise<Record<string, unknown>> {
  return api(`/api/diagnosticos/${id}/trazabilidad`);
}

// --- Inteligencia externa (1240) ---

export type ExternalSourceItem = {
  id: string;
  code: string;
  name: string;
  source_type: string;
  ingestion_channel: string;
  url_reference?: string | null;
  sector?: string | null;
  pais_region?: string | null;
  confiabilidad: number;
  is_active: boolean;
  ultima_actualizacion?: string | null;
};

export type ExternalSignalItem = {
  signal: SignalItem;
  external: {
    classification: string;
    relevance: string;
    freshness_status: string;
    hecho_observado?: string;
    interpretacion?: string;
    hipotesis?: string;
    is_risk: boolean;
    confidence_level: number;
    validated_at?: string | null;
  };
  source?: ExternalSourceItem | null;
};

export async function fetchExternalSources(): Promise<ExternalSourceItem[]> {
  return api("/api/inteligencia-externa/fuentes");
}

export async function fetchExternalSignals(params?: {
  classification?: string;
  relevance?: string;
  source_type?: string;
}): Promise<{ items: ExternalSignalItem[]; message?: string }> {
  const qs = new URLSearchParams();
  if (params?.classification) qs.set("classification", params.classification);
  if (params?.relevance) qs.set("relevance", params.relevance);
  if (params?.source_type) qs.set("source_type", params.source_type);
  const suffix = qs.toString() ? `?${qs}` : "";
  return api(`/api/inteligencia-externa/senales${suffix}`);
}

export async function fetchExternalSignalDetail(signalId: string): Promise<Record<string, unknown>> {
  return api(`/api/inteligencia-externa/senales/${signalId}`);
}

export async function createExternalSource(data: Record<string, unknown>): Promise<ExternalSourceItem> {
  return api("/api/inteligencia-externa/fuentes", { method: "POST", body: JSON.stringify(data) });
}

export async function ingestExternalSignal(data: Record<string, unknown>): Promise<Record<string, unknown>> {
  return api("/api/inteligencia-externa/ingesta", { method: "POST", body: JSON.stringify(data) });
}

export type LlmProvider = {
  id: string;
  organization_id: string;
  name: string;
  provider_type: string;
  provider_label?: string | null;
  adapter_mode?: string | null;
  model_default: string | null;
  endpoint: string | null;
  timeout_seconds: number;
  priority: number;
  is_enabled: boolean;
  is_fallback: boolean;
  secret_ref: string | null;
  secret_configured: boolean;
  secret_masked: string | null;
  health_status?: string | null;
  health_detail?: string | null;
  config_json: Record<string, unknown> | null;
};

export type LlmProviderHealth = {
  provider_id: string;
  provider_type: string;
  nombre: string;
  etiqueta: string;
  modo?: string | null;
  estado: string;
  detalle: string;
  habilitado: boolean;
  configurado: boolean;
  es_fallback: boolean;
  prioridad: number;
};

export type LlmObservabilitySummary = {
  periodo?: string | null;
  total_inferencias: number;
  exitosas: number;
  errores: number;
  tasa_exito: number | null;
  latencia_promedio_ms: number | null;
  tokens_total: number | null;
  costo_total: number | null;
  fallbacks: number;
  por_proveedor: Record<string, number>;
  errores_por_categoria: Record<string, number>;
};

export type LlmRoutingPolicy = {
  id: string;
  name: string;
  preferred_provider: string | null;
  preferred_model: string | null;
  required_capability: string | null;
  fallback_allowed: boolean;
  max_cost_per_1k_tokens: number | null;
  credential_scope: string;
  priority: number;
  is_active: boolean;
};

export type LlmRoutingExplain = {
  seleccionado: Record<string, unknown> | null;
  razones: string[];
};

export type LlmTestResult = {
  success: boolean;
  status: string;
  message: string;
  provider?: string;
  model?: string;
  latency_ms?: number;
  error_category?: string;
};

export async function fetchLlmProviders(): Promise<LlmProvider[]> {
  return api("/api/llm/providers");
}

export async function createLlmProvider(data: Record<string, unknown>): Promise<LlmProvider> {
  return api("/api/llm/providers", { method: "POST", body: JSON.stringify(data) });
}

export async function updateLlmProvider(id: string, data: Record<string, unknown>): Promise<LlmProvider> {
  return api(`/api/llm/providers/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function testLlmProvider(id: string): Promise<LlmTestResult> {
  return api(`/api/llm/providers/${id}/test`, { method: "POST", body: JSON.stringify({}) });
}


// --- Línea base e impacto (1200) ---

export type LineaBaseItem = {
  id: string;
  indicador: string;
  descripcion?: string | null;
  unidad: string;
  valor_base: number;
  fecha_inicio_base: string;
  fecha_fin_base: string;
  fuente: string;
  metodo_calculo?: string | null;
  evidencia?: Record<string, unknown> | null;
  direccion_indicador: string;
  impacto_esperado?: number | null;
  estado: string;
  responsable_id?: string | null;
  proceso?: string | null;
  opportunity_id?: string | null;
  work_plan_id?: string | null;
  employee_id?: string | null;
  accion_referencia?: string | null;
  valor_economico_tipo?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type LineaBaseImpacto = {
  id: string;
  medicion_id: string;
  valor_base: number;
  valor_posterior: number;
  variacion_absoluta: number;
  variacion_porcentual?: number | null;
  evaluacion: string;
  tipo_impacto: string;
  atribucion_nivel: string;
  atribucion_porcentaje?: number | null;
  atribucion_justificacion?: string | null;
  impacto_esperado?: number | null;
  impacto_real?: number | null;
  congelado: boolean;
};

export type LineaBaseMedicion = {
  id: string;
  valor_posterior: number;
  periodo_inicio: string;
  periodo_fin: string;
  fuente: string;
  evidencia?: Record<string, unknown> | null;
  responsable_id?: string | null;
  estado: string;
  created_at?: string;
  validated_at?: string | null;
  impacto?: LineaBaseImpacto | null;
};

export type LineaBaseDetail = {
  linea_base: LineaBaseItem;
  mediciones: LineaBaseMedicion[];
  evolucion: { linea_base_id: string; puntos: Array<{ fecha: string; valor: number; evaluacion?: string; estado: string }> };
  historial: Array<{ id: string; accion: string; actor_id?: string; fecha?: string }>;
};

export async function fetchLineasBase(params = ""): Promise<{ items: LineaBaseItem[]; total: number }> {
  return api(`/api/lineas-base${params ? `?${params}` : ""}`);
}

export async function fetchLineaBase(id: string): Promise<LineaBaseDetail> {
  return api(`/api/lineas-base/${id}`);
}

export async function createLineaBase(data: Record<string, unknown>): Promise<LineaBaseItem> {
  return api("/api/lineas-base", { method: "POST", body: JSON.stringify(data) });
}

export async function updateLineaBase(id: string, data: Record<string, unknown>): Promise<LineaBaseItem> {
  return api(`/api/lineas-base/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function addLineaBaseMedicion(id: string, data: Record<string, unknown>): Promise<{ medicion: LineaBaseMedicion; comparacion: LineaBaseImpacto }> {
  return api(`/api/lineas-base/${id}/mediciones`, { method: "POST", body: JSON.stringify(data) });
}

export async function validateLineaBaseMedicion(lineaBaseId: string, medicionId: string): Promise<Record<string, unknown>> {
  return api(`/api/lineas-base/${lineaBaseId}/mediciones/${medicionId}/validar`, { method: "POST", body: JSON.stringify({}) });
}

export async function updateLineaBaseAtribucion(
  lineaBaseId: string,
  medicionId: string,
  data: Record<string, unknown>,
): Promise<LineaBaseImpacto> {
  return api(`/api/lineas-base/${lineaBaseId}/mediciones/${medicionId}/atribucion`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function fetchLineasBaseByOpportunity(opportunityId: string): Promise<{ items: LineaBaseItem[] }> {
  return api(`/api/lineas-base/oportunidad/${opportunityId}`);
}

// --- Centro de Control ejecutivo (1230) ---

export type CentroControlIndicador = {
  id: string;
  label: string;
  valor: unknown;
  disponible: boolean;
  estado?: string | null;
  enlace: string;
};

export type CentroControlAtencion = {
  prioridad: number;
  tipo: string;
  titulo: string;
  detalle?: string | null;
  fecha?: string | null;
  enlace: string;
  origen: string;
};

export type CentroControlResumen = {
  generated_at: string;
  organization_id: string;
  resumen_ejecutivo: { indicadores: CentroControlIndicador[]; operaciones?: Record<string, number> | null };
  atencion_requerida: CentroControlAtencion[];
  empleados_ia?: {
    total: number;
    activos: number;
    items: Array<{
      id: string;
      nombre: string;
      estado: string;
      ultima_actividad?: string | null;
      enlace: string;
    }>;
  } | null;
  oportunidades?: Record<string, unknown> | null;
  impacto?: Record<string, unknown> | null;
  finops?: {
    disponible: boolean;
    dashboard?: Record<string, unknown>;
    tokens_periodo?: number;
    presupuestos?: Array<Record<string, unknown>>;
  } | null;
  finops_extendido?: {
    disponible: boolean;
    estado?: string;
    consumos_periodo?: number;
    tokens_periodo?: number;
    costo_periodo?: number | null;
    presupuestos?: Array<Record<string, unknown>>;
    alertas_registradas?: number;
    presupuestos_con_bloqueo?: number;
    oportunidades_con_costo?: number;
    enlace?: string;
  } | null;
  valor_retorno?: Record<string, unknown> | null;
  diagnostico?: Record<string, unknown> | null;
  senales?: Record<string, unknown> | null;
  inteligencia_externa?: {
    disponible: boolean;
    estado?: string;
    fuentes_activas?: number;
    total_senales?: number;
    sin_validar?: number;
    riesgos_abiertos?: number;
    oportunidades_detectadas?: number;
    tendencias?: number;
    recientes?: Array<{
      id: string;
      titulo: string;
      clasificacion?: string;
      relevancia?: string;
      es_riesgo?: boolean;
      validada?: boolean;
      enlace: string;
    }>;
    enlace?: string;
  } | null;
  llm?: {
    disponible?: boolean;
    total?: number;
    degradados?: number;
    proveedores?: Array<{
      id: string;
      nombre: string;
      proveedor: string;
      modelo?: string | null;
      habilitado: boolean;
      errores_24h: number;
      latencia_media_ms?: number | null;
      tokens_24h?: number;
      estado?: string;
      enlace: string;
    }>;
    enlace?: string;
  } | null;
  auditoria_reciente?: Array<{
    id: string;
    accion: string;
    detalle?: string | null;
    actor?: string | null;
    modulo?: string | null;
    fecha?: string | null;
    enlace: string;
  }> | null;
  actividad_reciente?: Array<{
    id: string;
    tipo: string;
    plan_id?: string | null;
    fecha?: string | null;
    enlace?: string | null;
  }>;
  cadena_ejecutiva?: Array<Record<string, unknown>> | null;
  salud_plataforma?: Record<string, unknown> | null;
  explicacion?: {
    disponible: boolean;
    estado?: string;
    nota_causalidad?: string;
    enlace?: string;
    elementos?: Array<{
      id: string;
      tipo_entrada: string;
      situacion?: string | null;
      indicador_origen?: string | null;
      causa?: string | null;
      certeza?: string | null;
      certeza_codigo?: string | null;
      tipo_contenido: string;
      confianza?: number | null;
      evidencia?: {
        fuente?: string | null;
        identificador?: string | null;
        correlation_id?: string | null;
        periodo?: { inicio?: string | null; fin?: string | null } | null;
        valor?: unknown;
        comparacion?: unknown;
        resumen?: string | null;
      } | null;
      fuente_ambito?: string | null;
      correlation_id?: string | null;
      magnitud?: number | null;
      impacto?: Record<string, unknown> | null;
      enlace?: string | null;
      nota?: string | null;
    }>;
  } | null;
};

export async function fetchCentroControlResumen(periodo = "mtd"): Promise<CentroControlResumen> {
  return api(`/api/centro-control/resumen-ejecutivo?periodo=${encodeURIComponent(periodo)}`);
}

// --- Modelo comercial (1280) ---

export type CommercialPlanItem = {
  id: string;
  code: string;
  name: string;
  descripcion?: string | null;
  margen_minimo_pct: number;
  fraccion_valor_sugerida?: number | null;
  consumo_ia_incluido_tokens?: number | null;
  presupuesto_ia_incluido?: number | null;
  excedente_ia_por_millon?: number | null;
  alerta_consumo_pct?: number | null;
  bloqueo_excedente?: boolean;
  credential_mode: string;
  precio_base_mensual?: number | null;
  precio_minimo?: number | null;
  precio_maximo?: number | null;
  limits?: Record<string, unknown> | null;
  currency?: string;
};

export type CommercialProposalSummary = {
  id: string;
  codigo: string;
  titulo: string;
  estado: string;
  valor_atribuible_total?: number | null;
  precio_sugerido?: number | null;
  precio_final?: number | null;
};

export type CommercialProposalDetail = CommercialProposalSummary & {
  escenario_recomendado: string;
  credential_mode?: string;
  currency?: string;
  valor_total_esperado?: number | null;
  costo_total?: number | null;
  beneficio_neto_cliente?: number | null;
  roi_pct?: number | null;
  payback_meses?: number | null;
  margen_pct?: number | null;
  pct_valor_conservado_cliente?: number | null;
  pct_valor_capturado_empleados_ia?: number | null;
  desglose_naturaleza?: Record<string, number> | null;
  valor_potencial_atribuible?: number | null;
  contrato_centro_control?: Record<string, unknown> | null;
  plan?: CommercialPlanItem | null;
  vigencia_hasta?: string | null;
  valores: Array<{
    id: string;
    categoria: string;
    alcance?: string;
    naturaleza: string;
    valor_bruto: number;
    atribucion_pct: number;
    valor_atribuible: number;
    external_intelligence_ref?: string | null;
  }>;
  escenarios: Array<{
    scenario_type: string;
    valor_esperado?: number | null;
    valor_atribuible?: number | null;
    probabilidad?: number | null;
    es_recomendado: boolean;
  }>;
  costos: Array<{ id: string; categoria: string; clase_costo: string; monto: number; finops_record_id?: string | null; descripcion?: string | null }>;
  alertas_doble_conteo: Array<{ id: string; severidad: string; mensaje: string }>;
  trazabilidad: Record<string, unknown>;
};

export async function fetchCommercialPlans(): Promise<CommercialPlanItem[]> {
  return api("/api/comercial/planes");
}

export async function createCommercialPlan(data: Record<string, unknown>): Promise<CommercialPlanItem> {
  return api("/api/comercial/planes", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchCommercialProposals(): Promise<CommercialProposalSummary[]> {
  return api("/api/comercial/propuestas");
}

export async function createCommercialProposal(data: Record<string, unknown>): Promise<CommercialProposalDetail> {
  return api("/api/comercial/propuestas", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchCommercialProposal(id: string): Promise<CommercialProposalDetail> {
  return api(`/api/comercial/propuestas/${id}`);
}

export async function addCommercialValue(proposalId: string, data: Record<string, unknown>) {
  return api(`/api/comercial/propuestas/${proposalId}/valores`, { method: "POST", body: JSON.stringify(data) });
}

export async function addCommercialScenario(proposalId: string, data: Record<string, unknown>) {
  return api(`/api/comercial/propuestas/${proposalId}/escenarios`, { method: "POST", body: JSON.stringify(data) });
}

export async function addCommercialCost(proposalId: string, data: Record<string, unknown>) {
  return api(`/api/comercial/propuestas/${proposalId}/costos`, { method: "POST", body: JSON.stringify(data) });
}

export async function suggestCommercialPrice(proposalId: string, scenario_type = "BASE") {
  return api(`/api/comercial/propuestas/${proposalId}/precio-sugerido`, {
    method: "POST",
    body: JSON.stringify({ scenario_type }),
  });
}

export async function setCommercialFinalPrice(proposalId: string, data: Record<string, unknown>) {
  return api(`/api/comercial/propuestas/${proposalId}/precio-final`, { method: "POST", body: JSON.stringify(data) });
}

export async function approveCommercialProposal(proposalId: string) {
  return api(`/api/comercial/propuestas/${proposalId}/aprobar`, { method: "POST", body: JSON.stringify({}) });
}

export async function detectCommercialDoubleCount(proposalId: string) {
  return api(`/api/comercial/propuestas/${proposalId}/detectar-doble-conteo`, { method: "POST", body: JSON.stringify({}) });
}

export async function fetchCommercialTraceability(proposalId: string): Promise<Record<string, unknown>> {
  return api(`/api/comercial/propuestas/${proposalId}/trazabilidad`);
}

export async function fetchCommercialPlan(id: string): Promise<CommercialPlanItem> {
  return api(`/api/comercial/planes/${id}`);
}

export async function simulateCommercialValue(data: Record<string, unknown>) {
  return api("/api/comercial/simular", { method: "POST", body: JSON.stringify(data) });
}

export async function simulateCommercialProposal(proposalId: string, data: Record<string, unknown>) {
  return api(`/api/comercial/propuestas/${proposalId}/simular`, { method: "POST", body: JSON.stringify(data) });
}

// --- TCO y ecosistema de aliados (1320) ---

export type TcoProveedorItem = {
  id: string;
  codigo: string;
  nombre: string;
  tipo: string;
  riesgo_nivel: string;
  estado: string;
};

export type TcoTablero = {
  tco_total: number;
  desglose: Record<string, number>;
  margen_pct?: number | null;
  desviacion?: { estimado: number; real: number; desviacion_pct: number };
  proveedores_criticos?: Array<{ nombre: string; pct: number }>;
  concentracion?: { max_proveedor_pct: number; advertencia: boolean };
  alertas?: Array<{ tipo: string; mensaje: string; severidad: string }>;
};

export async function fetchTcoCategorias(): Promise<Array<Record<string, unknown>>> {
  return api("/api/tco/categorias");
}

export async function fetchTcoProveedores(): Promise<TcoProveedorItem[]> {
  return api("/api/tco/proveedores");
}

export async function createTcoProveedor(data: Record<string, unknown>): Promise<TcoProveedorItem> {
  return api("/api/tco/proveedores", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchTcoCostos(): Promise<Array<Record<string, unknown>>> {
  return api("/api/tco/costos");
}

export async function createTcoCosto(data: Record<string, unknown>) {
  return api("/api/tco/costos", { method: "POST", body: JSON.stringify(data) });
}

export async function calcularTco(data: Record<string, unknown>) {
  return api("/api/tco/calcular", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchTcoTablero(): Promise<TcoTablero> {
  return api("/api/tco/tablero");
}

export async function fetchTcoRentabilidad(data: Record<string, unknown>) {
  return api("/api/tco/rentabilidad", { method: "POST", body: JSON.stringify(data) });
}

export async function simularTco(data: { tipo: string; parametros?: Record<string, unknown> }) {
  return api("/api/tco/simular", { method: "POST", body: JSON.stringify(data) });
}

export async function simularMakeOrBuy(data: Record<string, unknown>) {
  return api("/api/tco/simular/make-or-buy", { method: "POST", body: JSON.stringify(data) });
}

export async function compararProveedoresTco(data: { proveedor_ids: string[]; unidades?: number }) {
  return api("/api/tco/comparar-proveedores", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchTcoAlianzas(): Promise<Array<Record<string, unknown>>> {
  return api("/api/tco/alianzas");
}

export async function createTcoAlianza(data: Record<string, unknown>) {
  return api("/api/tco/alianzas", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchTcoHistorial() {
  return api("/api/tco/historial");
}

// --- Implementación y éxito del cliente (1340) ---

export type ImplProyectoSummary = {
  id: string;
  codigo: string;
  titulo: string;
  estado: string;
  avance_pct: number;
  proposal_id?: string | null;
  valor_compromiso?: Record<string, unknown> | null;
};

export type ImplTablero = {
  proyecto?: ImplProyectoSummary;
  fase_actual?: string | null;
  avance_pct?: number;
  salud?: { resultado: string; puntuacion: number };
  tco?: { total: number; margen_pct?: number };
  bloqueadores?: Array<{ descripcion: string }>;
  trazabilidad?: Record<string, unknown>;
};

export type ImplProyectoDetalle = ImplProyectoSummary & {
  hitos?: Array<{ id: string; nombre: string; estado: string }>;
  tareas?: Array<Record<string, unknown>>;
  requisitos?: Array<Record<string, unknown>>;
  tablero?: ImplTablero;
};

export async function fetchImplProyectos(): Promise<ImplProyectoSummary[]> {
  return api("/api/implementacion/proyectos");
}

export async function createImplProyecto(data: Record<string, unknown>): Promise<ImplProyectoSummary> {
  return api("/api/implementacion/proyectos", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchImplProyectoDetalle(id: string): Promise<ImplProyectoDetalle> {
  return api(`/api/implementacion/proyectos/${id}`);
}

export async function fetchImplTablero(id: string): Promise<ImplTablero> {
  return api(`/api/implementacion/proyectos/${id}/tablero`);
}

export async function createImplHito(proyectoId: string, data: Record<string, unknown>) {
  return api(`/api/implementacion/proyectos/${proyectoId}/hitos`, { method: "POST", body: JSON.stringify(data) });
}

export async function completarImplHito(hitoId: string, data: Record<string, unknown>) {
  return api(`/api/implementacion/hitos/${hitoId}/completar`, { method: "POST", body: JSON.stringify(data) });
}

export async function createImplRequisito(proyectoId: string, data: Record<string, unknown>) {
  return api(`/api/implementacion/proyectos/${proyectoId}/requisitos`, { method: "POST", body: JSON.stringify(data) });
}

export async function evaluarImplReadiness(proyectoId: string, dimensiones: Record<string, number>) {
  return api(`/api/implementacion/proyectos/${proyectoId}/readiness`, { method: "POST", body: JSON.stringify({ dimensiones }) });
}

export async function createImplBloqueador(proyectoId: string, data: Record<string, unknown>) {
  return api(`/api/implementacion/proyectos/${proyectoId}/bloqueadores`, { method: "POST", body: JSON.stringify(data) });
}

export async function createImplPiloto(proyectoId: string, data: Record<string, unknown>) {
  return api(`/api/implementacion/proyectos/${proyectoId}/pilotos`, { method: "POST", body: JSON.stringify(data) });
}

export async function registrarImplPilotoResultado(pilotoId: string, data: Record<string, unknown>) {
  return api(`/api/implementacion/pilotos/${pilotoId}/resultado`, { method: "POST", body: JSON.stringify(data) });
}

export async function aprobarImplPiloto(pilotoId: string, data: Record<string, unknown>) {
  return api(`/api/implementacion/pilotos/${pilotoId}/aprobar-produccion`, { method: "POST", body: JSON.stringify(data) });
}

export async function aprobarImplGoLive(proyectoId: string, data: Record<string, unknown>) {
  return api(`/api/implementacion/proyectos/${proyectoId}/go-live`, { method: "POST", body: JSON.stringify(data) });
}

export async function registrarImplAdopcion(proyectoId: string, data: Record<string, unknown>) {
  return api(`/api/implementacion/proyectos/${proyectoId}/adopcion`, { method: "POST", body: JSON.stringify(data) });
}

export async function createImplExitoPlan(data: Record<string, unknown>) {
  return api("/api/implementacion/exito/planes", { method: "POST", body: JSON.stringify(data) });
}

export async function medirImplObjetivo(objetivoId: string, valor_medido: number) {
  return api(`/api/implementacion/exito/objetivos/${objetivoId}/medir`, { method: "POST", body: JSON.stringify({ valor_medido }) });
}

export async function calcularImplSalud(proyectoId: string) {
  return api(`/api/implementacion/proyectos/${proyectoId}/salud`, { method: "POST", body: JSON.stringify({}) });
}

// --- Segmentación y planes verticales (1310) ---

export type PackageItem = {
  id: string;
  code: string;
  name: string;
  empleados_ia_incluidos?: number | null;
  usuarios_incluidos?: number | null;
  precio_estimado?: number | null;
  is_custom?: boolean;
  capabilities?: Record<string, unknown>;
};

export type RecommendationResult = {
  plan_sugerido?: { id: string; code: string; name: string } | null;
  paquete_sugerido?: { id: string; code: string; name: string } | null;
  nivel_ajuste: string;
  razones: string[];
  advertencias: string[];
  alternativas?: unknown[];
  plan_personalizado_recomendado?: boolean;
};

export async function fetchSectors() {
  return api("/api/segmentacion/sectores");
}

export async function fetchSegments() {
  return api("/api/segmentacion/segmentos");
}

export async function fetchCommercialProfile() {
  return api("/api/segmentacion/perfil");
}

export async function upsertCommercialProfile(data: Record<string, unknown>) {
  return api("/api/segmentacion/perfil", { method: "PUT", body: JSON.stringify(data) });
}

export async function fetchPackages(): Promise<PackageItem[]> {
  return api("/api/segmentacion/paquetes");
}

export async function createPackage(data: Record<string, unknown>): Promise<PackageItem> {
  return api("/api/segmentacion/paquetes", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchRecommendation(): Promise<RecommendationResult> {
  return api("/api/segmentacion/recomendar");
}

export async function comparePackages(package_ids: string[]) {
  return api("/api/segmentacion/comparar", { method: "POST", body: JSON.stringify({ package_ids }) });
}

export type ContinuidadServicio = {
  id: string;
  codigo: string;
  nombre: string;
  tipo: string;
  criticidad: string;
  rto_valor: number | null;
  rto_unidad: string | null;
  rpo_valor: number | null;
  rpo_unidad: string | null;
  estado_operacional: string;
  proveedor_ref?: string | null;
};

export type ContinuidadTablero = {
  servicios_criticos: ContinuidadServicio[];
  servicios_degradados: ContinuidadServicio[];
  incidentes_abiertos: number;
  backups_recientes: Array<{ recurso: string; resultado: string; estado_registro: string }>;
  backups_fallidos: number;
  restauraciones_verificadas: number;
  acciones_pendientes: number;
  alertas: Array<{
    id?: string;
    tipo: string;
    mensaje: string;
    severidad?: string;
    entidad_ref?: string | null;
    created_at?: string | null;
    resuelta?: boolean;
  }>;
  centro_control_adapter?: Record<string, unknown>;
  integracion_1330_prep?: Record<string, unknown>;
  integracion_1260_prep?: Record<string, unknown>;
};

export async function fetchContinuidadTablero(): Promise<ContinuidadTablero> {
  return api("/api/continuidad/tablero");
}

// --- Gobierno de datos (1350) ---

export type GovDashboard = {
  fuentes_catalogadas: number;
  sin_clasificar: number;
  riesgo_alto: number;
  retencion_vencida: number;
  exportaciones: number;
  solicitudes_abiertas: number;
  hallazgos_abiertos: number;
  acciones_pendientes: number;
};

export type GovClassification = {
  id: string;
  code: string;
  name: string;
  sensitivity_rank: number;
};

export type GovDataCategory = {
  id: string;
  code: string;
  name: string;
};

export type GovCatalogEntry = {
  id: string;
  name: string;
  classification_name?: string | null;
  classification_level_id?: string | null;
  data_environment: string;
  status: string;
  functional_owner?: string | null;
  secret_status?: string | null;
};

export type GovRetentionPolicy = {
  id: string;
  name: string;
  scope_type: string;
  duration_unit: string;
  duration_value?: number | null;
  disposition: string;
};

export type GovSubjectRequest = {
  id: string;
  request_type: string;
  status: string;
  subject_ref?: string | null;
  created_at?: string | null;
};

export type GovFinding = {
  id: string;
  finding_type: string;
  severity: string;
  description: string;
  status: string;
};

export type GovProviderPolicy = {
  id: string;
  organization_id: string | null;
  classification_level_id: string | null;
  category_id: string | null;
  decision: string;
  minimization_action: string | null;
  provider_scope: string | null;
  is_mandatory_global: boolean;
};

export async function fetchGovProviderPolicies(): Promise<GovProviderPolicy[]> {
  return api("/api/gobierno-datos/politicas-proveedor");
}

export async function evaluateGovProvider(data: Record<string, unknown>): Promise<{
  result: string;
  reasons: string[];
  minimization_action?: string | null;
}> {
  return api("/api/gobierno-datos/evaluar-proveedor", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchGovLineage(entryId: string): Promise<Array<Record<string, unknown>>> {
  return api(`/api/gobierno-datos/catalogo/${entryId}/linaje`);
}

export async function fetchGovDashboard(): Promise<GovDashboard> {
  return api("/api/gobierno-datos/dashboard");
}

export async function fetchGovCatalog(): Promise<GovCatalogEntry[]> {
  return api("/api/gobierno-datos/catalogo");
}

export async function createGovCatalogEntry(data: Record<string, unknown>): Promise<GovCatalogEntry> {
  return api("/api/gobierno-datos/catalogo", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchGovClassifications(): Promise<GovClassification[]> {
  return api("/api/gobierno-datos/clasificaciones");
}

export async function fetchGovCategories(): Promise<GovDataCategory[]> {
  return api("/api/gobierno-datos/categorias");
}

export async function fetchGovRetentionPolicies(): Promise<GovRetentionPolicy[]> {
  return api("/api/gobierno-datos/retencion");
}

export async function fetchGovAccessLogs(): Promise<Array<Record<string, unknown>>> {
  return api("/api/gobierno-datos/accesos");
}

export async function fetchGovSubjectRequests(): Promise<GovSubjectRequest[]> {
  return api("/api/gobierno-datos/solicitudes");
}

export async function fetchGovFindings(): Promise<GovFinding[]> {
  return api("/api/gobierno-datos/hallazgos");
}

export async function scanGovFindings(): Promise<GovFinding[]> {
  return api("/api/gobierno-datos/hallazgos/escanear", { method: "POST", body: JSON.stringify({}) });
}

// --- Integraciones reales y conectores (1330) ---

export type IntegrationCatalogItem = {
  type: string;
  name: string;
  descripcion: string;
};

export type IntegrationConnector = {
  id: string;
  code: string;
  name: string;
  descripcion: string | null;
  connector_type: string;
  status: string;
  auth_type: string;
  secret_configured: boolean;
  config: Record<string, unknown> | null;
  mapping: unknown[] | null;
  schema: Record<string, unknown> | null;
  destination_type: string | null;
  signal_source_code: string | null;
  trigger_mode: string;
  health: {
    last_success_at: string | null;
    last_error_at: string | null;
    last_error_message: string | null;
    last_latency_ms: number | null;
    consecutive_failures: number;
    circuit_open: boolean;
  };
  gov_catalog_entry_id?: string | null;
  webhook_token?: string;
  webhook_url_hint?: string;
  created_at: string | null;
};

export type IntegrationConnectorOverview = IntegrationConnector & {
  organization_name?: string;
  proveedor_ref?: string;
  continuidad_estado?: string | null;
  continuidad_servicio_id?: string | null;
  politica_decision?: string | null;
  politica_restricciones?: string[];
  ultima_ejecucion?: {
    id: string;
    status: string;
    started_at: string | null;
    correlation_id?: string | null;
  } | null;
};

export type IntegrationExecution = {
  id: string;
  status: string;
  started_at: string | null;
  latency_ms: number | null;
  records_processed: number;
  records_valid: number;
  records_rejected: number;
  error_category: string | null;
  error_message: string | null;
  correlation_id?: string | null;
};

export type IntegrationHealth = {
  connector_id: string;
  status: string;
  circuit_open: boolean;
  consecutive_failures: number;
  last_success_at: string | null;
  last_error_at: string | null;
  last_latency_ms: number | null;
  total_executions: number;
  success_rate: number | null;
};

export async function fetchIntegrationCatalog(): Promise<IntegrationCatalogItem[]> {
  return api("/api/integraciones/catalogo");
}

export async function fetchIntegrationConnectors(): Promise<IntegrationConnector[]> {
  return api("/api/integraciones/conectores");
}

export async function fetchIntegrationConnectorsOverview(): Promise<IntegrationConnectorOverview[]> {
  return api("/api/integraciones/conectores?vista=operativa");
}

export type IntegrationWiringDetail = {
  connector: IntegrationConnector;
  catalog_entry: Record<string, unknown> | null;
  policy: Record<string, unknown> | null;
  preflight: {
    allowed: boolean;
    decision: string;
    reasons: string[];
    minimization_action?: string | null;
  } | null;
  executions: IntegrationExecution[];
  health: IntegrationHealth;
  lineage: Array<Record<string, unknown>>;
  access_logs: Array<Record<string, unknown>>;
  continuidad: {
    proveedor_ref: string;
    servicio_id: string | null;
    servicio_nombre: string | null;
    estado_operacional: string | null;
  };
  eventos: Array<{
    id: string;
    tipo: string;
    mensaje: string;
    severidad: string;
    entidad_ref: string | null;
    created_at: string | null;
    resuelta: boolean;
  }>;
  auditoria: Array<{
    id: string;
    action: string;
    detail: string | null;
    user_id: string | null;
    created_at: string | null;
  }>;
};

export type IntegrationTraceStep = {
  etapa: string;
  origen: string;
  referencia: string;
  estado: string;
  detalle: string;
  timestamp: string | null;
};

export async function fetchIntegrationWiringDetail(id: string): Promise<IntegrationWiringDetail> {
  return api(`/api/integraciones/conectores/${id}/cableado`);
}

export async function fetchIntegrationTrace(correlationId: string): Promise<{
  correlation_id: string;
  pasos: IntegrationTraceStep[];
}> {
  return api(`/api/integraciones/trazabilidad/${encodeURIComponent(correlationId)}`);
}

export async function fetchIntegrationConnector(id: string): Promise<IntegrationConnector> {
  return api(`/api/integraciones/conectores/${id}`);
}

export async function createIntegrationConnector(data: Record<string, unknown>): Promise<IntegrationConnector> {
  return api("/api/integraciones/conectores", { method: "POST", body: JSON.stringify(data) });
}

export async function updateIntegrationConnector(id: string, data: Record<string, unknown>): Promise<IntegrationConnector> {
  return api(`/api/integraciones/conectores/${id}`, { method: "PUT", body: JSON.stringify(data) });
}

export async function testIntegrationConnector(id: string): Promise<{ resultado: string; mensaje: string; latencia_ms?: number }> {
  return api(`/api/integraciones/conectores/${id}/probar`, { method: "POST", body: JSON.stringify({}) });
}

export async function executeIntegrationConnector(
  id: string,
  data: { idempotency_key?: string; payload?: Record<string, unknown> },
): Promise<{
  execution_id?: string;
  status: string;
  records_processed: number;
  records_valid: number;
  records_rejected: number;
  signals_created?: number;
  idempotent?: boolean;
  correlation_id?: string;
}> {
  return api(`/api/integraciones/conectores/${id}/ejecutar`, { method: "POST", body: JSON.stringify(data) });
}

export async function fetchIntegrationExecutions(id: string): Promise<IntegrationExecution[]> {
  return api(`/api/integraciones/conectores/${id}/ejecuciones`);
}

export async function fetchIntegrationHealth(id: string): Promise<IntegrationHealth> {
  return api(`/api/integraciones/conectores/${id}/salud`);
}

// —— Aprendizaje y repriorización (1260) ——

export type CicloAprendizajeItem = {
  id: string;
  organization_id?: string;
  opportunity_id: string;
  work_plan_id?: string | null;
  signal_id?: string | null;
  estado: string;
  impacto_esperado?: number | null;
  valor_esperado?: number | null;
  costo_esperado?: number | null;
  tiempo_esperado_dias?: number | null;
  impacto_real?: number | null;
  valor_real?: number | null;
  costo_real?: number | null;
  tiempo_real_dias?: number | null;
  desviaciones?: Record<string, unknown> | null;
  calidad_recomendacion?: string | null;
  prioridad_anterior?: number | null;
  prioridad_propuesta?: number | null;
  explicacion_prioridad?: Record<string, unknown> | null;
  referencias?: Record<string, unknown> | null;
  evaluado_at?: string | null;
  created_at?: string | null;
};

export type RetroalimentacionItem = {
  id: string;
  ciclo_id: string;
  opportunity_id: string;
  tipo_explicacion: string;
  calidad_recomendacion?: string | null;
  resumen?: string | null;
  detalle?: string | null;
  lecciones?: unknown[] | null;
  created_at?: string | null;
};

export type RecalibracionItem = {
  id: string;
  ciclo_id: string;
  opportunity_id: string;
  estado: string;
  campo: string;
  valor_anterior?: string | null;
  valor_nuevo?: string | null;
  justificacion: string;
  factores?: Record<string, unknown> | null;
  motivo_rechazo?: string | null;
};

export type PatronAprendizajeItem = {
  id: string;
  tipo_patron: string;
  clave_patron: string;
  dominio?: string | null;
  tipo_oportunidad?: string | null;
  ocurrencias: number;
  resumen: string;
};

export async function fetchCiclosAprendizaje(opportunityId?: string): Promise<CicloAprendizajeItem[]> {
  const params = opportunityId ? `?opportunity_id=${encodeURIComponent(opportunityId)}` : "";
  return api(`/api/aprendizaje/ciclos${params}`);
}

export async function fetchCicloAprendizaje(id: string): Promise<CicloAprendizajeItem & {
  retroalimentaciones?: RetroalimentacionItem[];
  recalibraciones?: RecalibracionItem[];
}> {
  return api(`/api/aprendizaje/ciclos/${id}`);
}

export async function crearCicloAprendizaje(body: {
  opportunity_id: string;
  impacto_real?: number;
  valor_real?: number;
  costo_real?: number;
  tiempo_real_dias?: number;
}): Promise<CicloAprendizajeItem> {
  return api("/api/aprendizaje/ciclos", { method: "POST", body: JSON.stringify(body) });
}

export async function evaluarCicloAprendizaje(
  cicloId: string,
  body: {
    impacto_real?: number;
    valor_real?: number;
    costo_real?: number;
    tiempo_real_dias?: number;
    tipo_explicacion?: string;
    notas?: string;
  },
): Promise<unknown> {
  return api(`/api/aprendizaje/ciclos/${cicloId}/evaluar`, { method: "POST", body: JSON.stringify(body) });
}

export async function fetchRecalibraciones(cicloId?: string): Promise<RecalibracionItem[]> {
  const params = cicloId ? `?ciclo_id=${encodeURIComponent(cicloId)}` : "";
  return api(`/api/aprendizaje/recalibraciones${params}`);
}

export async function aprobarRecalibracion(id: string): Promise<RecalibracionItem> {
  return api(`/api/aprendizaje/recalibraciones/${id}/aprobar`, { method: "POST", body: JSON.stringify({}) });
}

export async function rechazarRecalibracion(id: string, motivo: string): Promise<RecalibracionItem> {
  return api(`/api/aprendizaje/recalibraciones/${id}/rechazar`, { method: "POST", body: JSON.stringify({ motivo }) });
}

export async function aplicarRecalibracion(id: string): Promise<RecalibracionItem> {
  return api(`/api/aprendizaje/recalibraciones/${id}/aplicar`, { method: "POST", body: JSON.stringify({}) });
}

export async function fetchPatronesAprendizaje(): Promise<PatronAprendizajeItem[]> {
  return api("/api/aprendizaje/patrones");
}

export async function fetchHistorialAprendizaje(cicloId?: string): Promise<unknown[]> {
  const params = cicloId ? `?ciclo_id=${encodeURIComponent(cicloId)}` : "";
  return api(`/api/aprendizaje/historial${params}`);
}

// —— Optimización y recomendaciones (1290) ——

export type OptimizacionRecomendacion = {
  id: string;
  codigo: string;
  estado: string;
  objetivo: string;
  factible: boolean;
  valor_esperado_total: number;
  costo_esperado_total: number;
  impacto_esperado_total: number;
  roi_esperado?: number | null;
  riesgo_promedio?: number | null;
  confianza_promedio?: number | null;
  created_at?: string | null;
  explicacion?: Record<string, unknown> | null;
  conflictos?: string[] | null;
  aprendizaje_influencia?: Record<string, unknown> | null;
  ejecucion?: {
    tipo?: string | null;
    estado?: string | null;
    correlation_id?: string | null;
    execution_reference?: string | null;
    referencia_externa?: string | null;
    executed_at?: string | null;
    executed_by?: string | null;
    approved_at?: string | null;
    error?: unknown;
    idempotent?: boolean;
    learning_refs?: Array<Record<string, unknown>>;
    oportunidades?: Array<Record<string, unknown>>;
  } | null;
  items?: OptimizacionItem[];
};

export type OptimizacionItem = {
  opportunity_id: string;
  seleccionado: boolean;
  orden?: number | null;
  puntuacion_total?: number | null;
  factores?: Record<string, unknown> | null;
  exclusion_razon?: string | null;
  valor_esperado?: number | null;
  costo_esperado?: number | null;
  riesgo?: number | null;
  confianza?: number | null;
  aprendizaje?: Record<string, unknown> | null;
};

export async function fetchOptimizacionRecomendaciones(): Promise<OptimizacionRecomendacion[]> {
  return api("/api/optimizacion/recomendaciones");
}

export async function fetchOptimizacionRecomendacion(id: string): Promise<OptimizacionRecomendacion> {
  return api(`/api/optimizacion/recomendaciones/${id}`);
}

export async function simularOptimizacion(body: Record<string, unknown>): Promise<unknown> {
  return api("/api/optimizacion/simular", { method: "POST", body: JSON.stringify(body) });
}

export async function crearRecomendacionOptimizacion(body: Record<string, unknown>): Promise<OptimizacionRecomendacion> {
  return api("/api/optimizacion/recomendaciones", { method: "POST", body: JSON.stringify(body) });
}

export async function compararEscenariosOptimizacion(body: Record<string, unknown>): Promise<unknown> {
  return api("/api/optimizacion/comparar", { method: "POST", body: JSON.stringify(body) });
}

export async function aprobarRecomendacionOptimizacion(id: string, justificacion: string): Promise<OptimizacionRecomendacion> {
  return api(`/api/optimizacion/recomendaciones/${id}/aprobar`, {
    method: "POST",
    body: JSON.stringify({ justificacion }),
  });
}

export async function ejecutarRecomendacionOptimizacion(
  id: string,
  tipoEjecucion: "AUTOMATICA" | "HUMANA_EXTERNA" = "AUTOMATICA",
): Promise<OptimizacionRecomendacion> {
  return api(`/api/optimizacion/recomendaciones/${id}/ejecutar`, {
    method: "POST",
    body: JSON.stringify({ tipo_ejecucion: tipoEjecucion }),
  });
}

export async function confirmarEjecucionHumanaOptimizacion(
  id: string,
  referenciaExterna: string,
  notas?: string,
): Promise<OptimizacionRecomendacion> {
  return api(`/api/optimizacion/recomendaciones/${id}/confirmar-ejecucion`, {
    method: "POST",
    body: JSON.stringify({ referencia_externa: referenciaExterna, notas }),
  });
}

export type LlmInferenceLog = {
  id: string;
  trace_id: string;
  employee_id?: string | null;
  provider?: string | null;
  model?: string | null;
  tokens_in?: number | null;
  tokens_out?: number | null;
  tokens_total?: number | null;
  latency_ms?: number | null;
  cost?: number | null;
  status: string;
  error_category?: string | null;
  error_message?: string | null;
  fallback_used: boolean;
  initial_provider?: string | null;
  fallback_provider?: string | null;
  created_at?: string | null;
};

export type LlmModelCatalog = {
  id: string;
  provider_type: string;
  model_id: string;
  display_name: string;
  estado: string;
  capabilities: Record<string, unknown>;
  context_window?: number | null;
  priority: number;
  is_enabled: boolean;
};

export async function fetchLlmInferenceLogs(limit = 50): Promise<LlmInferenceLog[]> {
  return api(`/api/llm/inference-logs?limit=${limit}`);
}

export async function fetchLlmModels(): Promise<LlmModelCatalog[]> {
  return api("/api/llm/models");
}

export async function fetchLlmObservability(periodo = "mtd"): Promise<LlmObservabilitySummary> {
  return api(`/api/llm/observability?periodo=${encodeURIComponent(periodo)}`);
}

export async function fetchLlmProvidersHealth(): Promise<LlmProviderHealth[]> {
  return api("/api/llm/health");
}

export async function fetchLlmRoutingPolicies(): Promise<LlmRoutingPolicy[]> {
  return api("/api/llm/routing/policies");
}

export async function createLlmRoutingPolicy(data: Record<string, unknown>): Promise<LlmRoutingPolicy> {
  return api("/api/llm/routing/policies", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchLlmRoutingExplain(preferredProvider?: string): Promise<LlmRoutingExplain> {
  const q = preferredProvider ? `?preferred_provider=${encodeURIComponent(preferredProvider)}` : "";
  return api(`/api/llm/routing/explain${q}`);
}

// --- Mesa de Ayuda y Soporte (MB-12) ---

export type SupportCase = {
  id: string;
  organization_id: string;
  numero: number;
  referencia: string;
  tipo: string;
  categoria?: string | null;
  asunto: string;
  descripcion?: string | null;
  prioridad: string;
  impacto: string;
  urgencia: string;
  estado: string;
  solicitante_id: string;
  responsable_id?: string | null;
  sla_estado?: string | null;
  correlation_id?: string | null;
  modulo_relacionado?: string | null;
  entidad_relacionada?: string | null;
  resolucion?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type SupportCaseDetail = SupportCase & {
  historial: Array<{ id: string; accion: string; detalle?: Record<string, unknown> | null; created_at?: string | null }>;
  comentarios: Array<{ id: string; usuario_id: string; cuerpo: string; es_interno: boolean; created_at?: string | null }>;
};

export async function fetchSupportCases(params?: {
  estado?: string;
  q?: string;
  solo_mios?: boolean;
}): Promise<SupportCase[]> {
  const qs = new URLSearchParams();
  if (params?.estado) qs.set("estado", params.estado);
  if (params?.q) qs.set("q", params.q);
  if (params?.solo_mios) qs.set("solo_mios", "true");
  const query = qs.toString();
  return api(`/api/soporte/casos${query ? `?${query}` : ""}`);
}

export async function fetchSupportCase(id: string): Promise<SupportCaseDetail> {
  return api(`/api/soporte/casos/${id}`);
}

export async function createSupportCase(data: Record<string, unknown>): Promise<SupportCase> {
  return api("/api/soporte/casos", { method: "POST", body: JSON.stringify(data) });
}

export async function assignSupportCase(id: string, data: { responsable_id?: string | null; grupo?: string | null }): Promise<SupportCase> {
  return api(`/api/soporte/casos/${id}/asignar`, { method: "POST", body: JSON.stringify(data) });
}

export async function updateSupportCaseStatus(id: string, data: { estado: string; nota?: string }): Promise<SupportCase> {
  return api(`/api/soporte/casos/${id}/estado`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function resolveSupportCase(id: string, data: { resolucion: string; cerrar?: boolean }): Promise<SupportCase> {
  return api(`/api/soporte/casos/${id}/resolver`, { method: "POST", body: JSON.stringify(data) });
}

export async function closeSupportCase(id: string, data: { nota?: string }): Promise<SupportCase> {
  return api(`/api/soporte/casos/${id}/cerrar`, { method: "POST", body: JSON.stringify(data) });
}

export async function addSupportComment(id: string, data: { cuerpo: string; es_interno?: boolean }): Promise<unknown> {
  return api(`/api/soporte/casos/${id}/comentarios`, { method: "POST", body: JSON.stringify(data) });
}

export async function fetchSupportTipos(): Promise<{ tipos: string[]; estados: string[]; prioridades: string[] }> {
  return api("/api/soporte/tipos");
}
