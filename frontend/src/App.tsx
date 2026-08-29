import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./AppShell";
import { RequireAuth } from "./RequireAuth";
import { RequirePermission } from "./RequirePermission";
import { ApprovalsPage } from "./pages/ApprovalsPage";
import { AutomationRunsPage } from "./pages/AutomationRunsPage";
import { AutomationWizardPage } from "./pages/AutomationWizardPage";
import { AutomationsPage } from "./pages/AutomationsPage";
import { AdminCompaniesPage } from "./pages/admin/AdminCompaniesPage";
import { AdminLlmProvidersPage } from "./pages/admin/AdminLlmProvidersPage";
import { AdminConfigPage } from "./pages/admin/AdminConfigPage";
import { AdminOrganizationPage } from "./pages/admin/AdminOrganizationPage";
import { AdminRolesPage } from "./pages/admin/AdminRolesPage";
import { AdminSecurityPage } from "./pages/admin/AdminSecurityPage";
import { AdminIdentidadPage } from "./pages/admin/AdminIdentidadPage";
import { AdminUsersPage } from "./pages/admin/AdminUsersPage";
import { AuditPage } from "./pages/AuditPage";
import { CapabilitiesPage } from "./pages/CapabilitiesPage";
import { CentroControlPage } from "./pages/CentroControlPage";
import { CostosValorPage } from "./pages/CostosValorPage";
import { GobernanzaDatosPage } from "./pages/GobernanzaDatosPage";
import { LineasBasePage } from "./pages/LineasBasePage";
import { LineaBaseDetailPage } from "./pages/LineaBaseDetailPage";
import { OportunidadesPage } from "./pages/OportunidadesPage";
import { OportunidadDetailPage } from "./pages/OportunidadDetailPage";
import { SenalesPage } from "./pages/SenalesPage";
import { SenalDetailPage } from "./pages/SenalDetailPage";
import { DiagnosticosPage } from "./pages/DiagnosticosPage";
import { DiagnosticoDetailPage } from "./pages/DiagnosticoDetailPage";
import { InteligenciaExternaPage } from "./pages/InteligenciaExternaPage";
import { InteligenciaExternaDetailPage } from "./pages/InteligenciaExternaDetailPage";
import { ContinuidadPage } from "./pages/ContinuidadPage";
import { SoportePage } from "./pages/SoportePage";
import { SoporteCasoDetailPage } from "./pages/SoporteCasoDetailPage";
import { IntegracionesPage } from "./pages/IntegracionesPage";
import { IntegracionWizardPage } from "./pages/IntegracionWizardPage";
import { IntegracionDetailPage } from "./pages/IntegracionDetailPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DiagnosticoIpsPage } from "./pages/DiagnosticoIpsPage";
import { DirectoryPage } from "./pages/DirectoryPage";
import { EmployeeDetailPage } from "./pages/EmployeeDetailPage";
import { EmployeeWizardPage } from "./pages/EmployeeWizardPage";
import { ExecutionDetailPage } from "./pages/ExecutionDetailPage";
import { ExecutionsPage } from "./pages/ExecutionsPage";
import { KnowledgeDetailPage } from "./pages/KnowledgeDetailPage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { LoginPage } from "./pages/LoginPage";
import { MiSeguridadPage } from "./pages/MiSeguridadPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { TrabajoPage } from "./pages/TrabajoPage";
import { OperationDetailPage } from "./pages/OperationDetailPage";
import { OperationsCenterPage } from "./pages/OperationsCenterPage";
import { OperationsHubPage } from "./pages/OperationsHubPage";
import { TestLabPage } from "./pages/TestLabPage";
import { ToolsPage } from "./pages/ToolsPage";
import { getToken } from "./api";

export default function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={getToken() ? <Navigate to="/" replace /> : <LoginPage />}
      />
      <Route element={<RequireAuth />}>
        <Route element={<AppShell />}>
          <Route index element={<CentroControlPage />} />
          <Route path="panel" element={<Navigate to="/" replace />} />
          <Route path="operaciones" element={<OperationsHubPage />} />
          <Route path="operaciones/solicitud" element={<OperationsCenterPage />} />
          <Route path="operaciones/:operationId" element={<OperationDetailPage />} />
          <Route path="salud/diagnostico" element={<DiagnosticoIpsPage />} />
          <Route path="ejecuciones" element={<ExecutionsPage />} />
          <Route path="ejecuciones/:planId" element={<ExecutionDetailPage />} />
          <Route path="aprobaciones" element={<ApprovalsPage />} />
          <Route
            element={
              <RequirePermission
                anyOf={[
                  "operations.view",
                  "notification.view",
                  "oportunidades.view",
                  "continuidad.view",
                  "integraciones.view",
                  "finops.view",
                  "automation.view",
                  "linea_base.view",
                  "diagnosticos.view",
                  "support.view",
                  "support.create",
                  "support.assign",
                ]}
              />
            }
          >
            <Route path="trabajo" element={<TrabajoPage />} />
          </Route>
          <Route path="directorio" element={<DirectoryPage />} />
          <Route path="automatizaciones" element={<AutomationsPage />} />
          <Route path="automatizaciones/nueva" element={<AutomationWizardPage />} />
          <Route path="automatizaciones/:automationId/editar" element={<AutomationWizardPage />} />
          <Route path="automatizaciones/:automationId/ejecuciones" element={<AutomationRunsPage />} />
          <Route path="conocimiento" element={<KnowledgePage />} />
          <Route path="conocimiento/:documentId" element={<KnowledgeDetailPage />} />
          <Route path="empleados/nuevo" element={<EmployeeWizardPage />} />
          <Route path="empleados/:employeeId/editar" element={<EmployeeWizardPage />} />
          <Route path="empleados/:employeeId" element={<EmployeeDetailPage />} />
          <Route path="capacidades" element={<CapabilitiesPage />} />
          <Route path="herramientas" element={<ToolsPage />} />
          <Route path="test-lab" element={<TestLabPage />} />
          <Route path="costos-valor" element={<CostosValorPage />} />
          <Route path="gobernanza-datos" element={<GobernanzaDatosPage />} />
          <Route path="lineas-base" element={<LineasBasePage />} />
          <Route path="lineas-base/:lineaBaseId" element={<LineaBaseDetailPage />} />
          <Route path="oportunidades" element={<OportunidadesPage />} />
          <Route path="oportunidades/:opportunityId" element={<OportunidadDetailPage />} />
          <Route path="senales" element={<SenalesPage />} />
          <Route path="senales/:signalId" element={<SenalDetailPage />} />
          <Route path="diagnosticos" element={<DiagnosticosPage />} />
          <Route path="diagnosticos/:diagnosticId" element={<DiagnosticoDetailPage />} />
          <Route path="inteligencia-externa" element={<InteligenciaExternaPage />} />
          <Route path="inteligencia-externa/senales/:signalId" element={<InteligenciaExternaDetailPage />} />
          <Route path="continuidad" element={<ContinuidadPage />} />
          <Route path="soporte" element={<SoportePage />} />
          <Route path="soporte/casos/:caseId" element={<SoporteCasoDetailPage />} />
          <Route path="integraciones" element={<IntegracionesPage />} />
          <Route path="integraciones/nueva" element={<IntegracionWizardPage />} />
          <Route path="integraciones/:connectorId" element={<IntegracionDetailPage />} />
          <Route path="organizacion" element={<Navigate to="/administracion/organizacion" replace />} />
          <Route element={<RequirePermission anyOf={["platform.organization.view"]} />}>
            <Route path="administracion/empresas" element={<AdminCompaniesPage />} />
          </Route>
          <Route element={<RequirePermission anyOf={["admin.user.view"]} />}>
            <Route path="administracion/usuarios" element={<AdminUsersPage />} />
          </Route>
          <Route element={<RequirePermission anyOf={["admin.role.view"]} />}>
            <Route path="administracion/roles" element={<AdminRolesPage />} />
          </Route>
          <Route element={<RequirePermission anyOf={["admin.organization.view"]} />}>
            <Route path="administracion/organizacion" element={<AdminOrganizationPage />} />
          </Route>
          <Route element={<RequirePermission anyOf={["admin.config.view"]} />}>
            <Route path="administracion/configuracion" element={<AdminConfigPage />} />
          </Route>
          <Route element={<RequirePermission anyOf={["llm.view"]} />}>
            <Route path="administracion/proveedores-ia" element={<AdminLlmProvidersPage />} />
          </Route>
          <Route element={<RequirePermission anyOf={["admin.security.view", "seguridad.view"]} />}>
            <Route path="administracion/seguridad" element={<AdminSecurityPage />} />
          </Route>
          <Route element={<RequirePermission anyOf={["identidad.view"]} />}>
            <Route path="administracion/identidad" element={<AdminIdentidadPage />} />
          </Route>
          <Route element={<RequirePermission anyOf={["audit.view"]} />}>
            <Route path="auditoria" element={<AuditPage />} />
          </Route>
          <Route path="notificaciones" element={<NotificationsPage />} />
          <Route path="mi-seguridad" element={<MiSeguridadPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
