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
  cost_label: string;
  currency?: string;
  created_at: string;
};

export async function fetchFinOpsDashboard(): Promise<FinOpsDashboard> {
  return api<FinOpsDashboard>("/api/finops/dashboard");
}

export async function fetchFinOpsConsumptions(): Promise<FinOpsConsumption[]> {
  return api<FinOpsConsumption[]>("/api/finops/consumptions");
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
  estado: string;
  urgencia: string;
  impacto_estimado: number | null;
  valor_potencial: number | null;
  valor_potencial_certidumbre: string;
  valor_materializado: number | null;
  confianza: number;
  pertinencia: string | null;
  momento: string | null;
  prioridad_score: number | null;
  siguiente_accion: Record<string, unknown> | null;
  fecha_deteccion: string | null;
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

export async function activateOpportunity(id: string): Promise<Record<string, unknown>> {
  return api(`/api/oportunidades/${id}/activar`, { method: "POST", body: JSON.stringify({}) });
}

export async function fetchOpportunityTrace(id: string): Promise<Record<string, unknown>> {
  return api(`/api/oportunidades/${id}/trazabilidad`);
}

export async function prioritizeOpportunities(): Promise<Record<string, unknown>> {
  return api("/api/oportunidades/priorizar", { method: "POST", body: JSON.stringify({}) });
}

export type LlmProvider = {
  id: string;
  organization_id: string;
  name: string;
  provider_type: string;
  model_default: string | null;
  endpoint: string | null;
  timeout_seconds: number;
  priority: number;
  is_enabled: boolean;
  is_fallback: boolean;
  secret_ref: string | null;
  secret_configured: boolean;
  secret_masked: string | null;
  config_json: Record<string, unknown> | null;
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
