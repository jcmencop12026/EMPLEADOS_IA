import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./AppShell";
import { RequireAuth } from "./RequireAuth";
import { AuditPage } from "./pages/AuditPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { OrganizationPage } from "./pages/OrganizationPage";
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
          <Route path="organizacion" element={<OrganizationPage />} />
          <Route path="auditoria" element={<AuditPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
