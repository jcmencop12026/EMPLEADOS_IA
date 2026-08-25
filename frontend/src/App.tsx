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
import { OrganizationPage } from "./pages/OrganizationPage";
import { CostosValorPage } from "./pages/CostosValorPage";
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
          <Route path="organizacion" element={<OrganizationPage />} />
          <Route path="costos-valor" element={<CostosValorPage />} />
          <Route path="auditoria" element={<AuditPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
