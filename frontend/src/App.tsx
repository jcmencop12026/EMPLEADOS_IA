import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./AppShell";
import { RequireAuth } from "./RequireAuth";
import { AuditPage } from "./pages/AuditPage";
import { DirectoryPage } from "./pages/DirectoryPage";
import { EmployeeDetailPage } from "./pages/EmployeeDetailPage";
import { EmployeeWizardPage } from "./pages/EmployeeWizardPage";
import { ExecutionDetailPage } from "./pages/ExecutionDetailPage";
import { ExecutionsPage } from "./pages/ExecutionsPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { OperationsCenterPage } from "./pages/OperationsCenterPage";
import { CapabilitiesPage } from "./pages/CapabilitiesPage";
import { KnowledgePage } from "./pages/KnowledgePage";
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
          <Route index element={<HomePage />} />
          <Route path="operaciones" element={<OperationsCenterPage />} />
          <Route path="ejecuciones" element={<ExecutionsPage />} />
          <Route path="ejecuciones/:planId" element={<ExecutionDetailPage />} />
          <Route path="directorio" element={<DirectoryPage />} />
          <Route path="empleados/nuevo" element={<EmployeeWizardPage />} />
          <Route path="empleados/:employeeId" element={<EmployeeDetailPage />} />
          <Route path="capacidades" element={<CapabilitiesPage />} />
          <Route path="herramientas" element={<ToolsPage />} />
          <Route path="conocimiento" element={<KnowledgePage />} />
          <Route path="test-lab" element={<TestLabPage />} />
          <Route path="organizacion" element={<OrganizationPage />} />
          <Route path="auditoria" element={<AuditPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
