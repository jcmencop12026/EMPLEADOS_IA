const TOKEN_KEY = "eaios_token";

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
    let message = "Error al procesar la solicitud";
    try {
      const parsed = JSON.parse(text) as { detail?: string | Array<{ msg?: string }> };
      if (typeof parsed.detail === "string") {
        message = parsed.detail;
      } else if (Array.isArray(parsed.detail)) {
        message = parsed.detail.map((d) => d.msg || "").filter(Boolean).join(". ") || message;
      }
    } catch {
      if (text && !text.startsWith("{")) message = text;
    }
    throw new Error(message);
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
  return api<CatalogItem[]>(`/api/knowledge${q}`);
}

export async function createKnowledgeSource(data: Record<string, unknown>): Promise<CatalogItem> {
  return api("/api/knowledge", { method: "POST", body: JSON.stringify(data) });
}

export async function updateKnowledgeSource(id: string, data: Record<string, unknown>): Promise<CatalogItem> {
  return api(`/api/knowledge/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function setKnowledgeStatus(id: string, active: boolean): Promise<CatalogItem> {
  return api(`/api/knowledge/${id}/${active ? "activate" : "deactivate"}`, { method: "POST" });
}

export async function ingestKnowledge(id: string, content: string, contentType?: string): Promise<Record<string, unknown>> {
  return api(`/api/knowledge/${id}/ingest`, {
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
