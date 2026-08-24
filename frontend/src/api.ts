const TOKEN_KEY = "eaios_token";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function parseDetail(text: string): string {
  try {
    const data = JSON.parse(text) as { detail?: unknown };
    if (typeof data.detail === "string") return data.detail;
  } catch {
    /* plain */
  }
  return text;
}

function userMessage(status: number, detail: string): string {
  if (status === 401) return "Su sesión ha vencido. Inicie sesión nuevamente.";
  if (status === 403) return "No tiene permisos para realizar esta acción.";
  if (status === 404) return "El recurso solicitado no fue encontrado.";
  if (status >= 500) return "Ocurrió un error al procesar la solicitud.";
  return detail || "No se pudo completar la solicitud.";
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

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    const text = await res.text();
    const detail = parseDetail(text);
    const message = userMessage(res.status, detail);
    console.error("[api]", res.status, path, detail);
    throw new ApiError(res.status, message);
  }
  return res.json() as Promise<T>;
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
  permissions?: string[];
};

export type Organization = {
  id: string;
  name: string;
  status?: string;
  timezone?: string;
  created_at: string;
  updated_at?: string | null;
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

export async function fetchAdminUsers(q?: string, status?: string): Promise<AdminUser[]> {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (status) params.set("status", status);
  const qs = params.toString();
  return api<AdminUser[]>(`/api/admin/users${qs ? `?${qs}` : ""}`);
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

export async function fetchMe(): Promise<UserMe> {
  return api<UserMe>("/api/auth/me");
}
