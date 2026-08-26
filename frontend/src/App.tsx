import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./AppShell";
import { RequireAuth } from "./RequireAuth";
import { ApprovalsPage } from "./pages/ApprovalsPage";
import { AutomationRunsPage } from "./pages/AutomationRunsPage";
import { AutomationWizardPage } from "./pages/AutomationWizardPage";
import { AutomationsPage } from "./pages/AutomationsPage";
import { AuditPage } from "./pages/AuditPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DirectoryPage } from "./pages/DirectoryPage";
import { EmployeeDetailPage } from "./pages/EmployeeDetailPage";
import { EmployeeWizardPage } from "./pages/EmployeeWizardPage";
import { ExecutionDetailPage } from "./pages/ExecutionDetailPage";
import { ExecutionsPage } from "./pages/ExecutionsPage";
import { LoginPage } from "./pages/LoginPage";
import { OperationsCenterPage } from "./pages/OperationsCenterPage";
import { OrganizationPage } from "./pages/OrganizationPage";
import { NotificationsPage } from "./pages/NotificationsPage";
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
          <Route index element={<DashboardPage />} />
          <Route path="operaciones" element={<OperationsCenterPage />} />
          <Route path="ejecuciones" element={<ExecutionsPage />} />
          <Route path="ejecuciones/:planId" element={<ExecutionDetailPage />} />
          <Route path="aprobaciones" element={<ApprovalsPage />} />
          <Route path="directorio" element={<DirectoryPage />} />
          <Route path="automatizaciones" element={<AutomationsPage />} />
          <Route path="automatizaciones/nueva" element={<AutomationWizardPage />} />
          <Route path="automatizaciones/:automationId/editar" element={<AutomationWizardPage />} />
          <Route path="automatizaciones/:automationId/ejecuciones" element={<AutomationRunsPage />} />
          <Route path="empleados/nuevo" element={<EmployeeWizardPage />} />
          <Route path="empleados/:employeeId/editar" element={<EmployeeWizardPage />} />
          <Route path="empleados/:employeeId" element={<EmployeeDetailPage />} />
          <Route path="organizacion" element={<OrganizationPage />} />
          <Route path="auditoria" element={<AuditPage />} />
          <Route path="notificaciones" element={<NotificationsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
