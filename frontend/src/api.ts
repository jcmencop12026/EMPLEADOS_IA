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
    const text = await res.text();
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
  return res.json() as Promise<T>;
}

export type UserMe = {
  id: string;
  username: string;
  role: string;
  organization_id: string;
  organization_name: string;
};

export type Organization = {
  id: string;
  name: string;
  created_at: string;
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
