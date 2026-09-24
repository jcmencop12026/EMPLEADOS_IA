import { FormEvent, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

export function SetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") ?? "";
  const nextPath = params.get("next")?.startsWith("/") ? params.get("next")! : "/mi-espacio";
  const invitedUser = params.get("user") ?? "";
  const externalInvite = params.get("external") === "1";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault(); setError(null);
    if (!token) return setError("El enlace de acceso no es válido.");
    if (password.length < 8) return setError("La contraseña debe tener mínimo 8 caracteres.");
    if (password !== confirm) return setError("Las contraseñas no coinciden.");
    setLoading(true);
    try {
      const r = await fetch("/api/auth/reset-password", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token, new_password: password }) });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || "No se pudo activar el acceso.");
      const loginParams = new URLSearchParams({ access: "ready", next: nextPath });
      if (invitedUser) loginParams.set("user", invitedUser);
      if (externalInvite) loginParams.set("external", "1");
      navigate(`/login?${loginParams.toString()}`, { replace: true });
    } catch (e) { setError(e instanceof Error ? e.message : "No se pudo activar el acceso."); }
    finally { setLoading(false); }
  }

  return (
    <div className="login-page eiaax-v1-experience login-theme-aurora">
      <div className="login-layout login-layout--activation">
        <aside className="login-brand-panel"><h1>Active su acceso a EIIAX</h1><p className="login-brand-copy">Defina su propia contraseña. El enlace es personal y de un solo uso.</p></aside>
        <form className="login-card login-card-elevated" onSubmit={submit}>
          <header className="login-card-header"><h1>Crear contraseña</h1><p className="muted small">Acceso seguro al espacio de su empresa</p></header>
          <label>Nueva contraseña<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" disabled={loading} /></label>
          <label>Confirmar contraseña<input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password" disabled={loading} /></label>
          {error && <p className="error" role="alert">{error}</p>}
          <button type="submit" className="btn primary login-submit" disabled={loading}>{loading ? "Activando…" : "Activar acceso"}</button>
          <Link to={`/login?next=${encodeURIComponent(nextPath)}${invitedUser ? `&user=${encodeURIComponent(invitedUser)}` : ""}${externalInvite ? "&external=1" : ""}`} className="link-button">Volver al inicio de sesión</Link>
        </form>
      </div>
    </div>
  );
}
