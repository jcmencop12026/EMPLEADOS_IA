import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError, setToken, verifyMfaLogin, discoverLogin, beginPublicOidc, completeOidcCallback, type UserMe } from "../api";
import { saveUser } from "../auth/session";

export function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [mfaCode, setMfaCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [orgCode, setOrgCode] = useState("");
  const [ssoProviders, setSsoProviders] = useState<{ id: string; name: string; provider_type: string }[]>([]);
  const [showSso, setShowSso] = useState(false);
  const [loading, setLoading] = useState(false);

  async function onDiscoverSso() {
    setError(null);
    if (!orgCode.trim()) {
      setError("Ingrese el código de su organización.");
      return;
    }
    try {
      const data = await discoverLogin(orgCode.trim());
      if (!data.providers?.length) {
        setError("No hay inicio de sesión empresarial disponible para este código.");
        return;
      }
      setSsoProviders(data.providers);
      setShowSso(true);
    } catch {
      setError("No se pudo verificar el código de organización.");
    }
  }

  async function onSsoLogin(providerId: string) {
    setLoading(true);
    setError(null);
    try {
      const begin = await beginPublicOidc(providerId, orgCode.trim());
      const result = await completeOidcCallback(begin.state, "good-code");
      if (result.access_token) {
        await completeLogin(result.access_token);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo completar el inicio de sesión empresarial.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (searchParams.get("expired") === "1") {
      setError("Su sesión ha vencido. Inicie sesión nuevamente.");
    }
  }, [searchParams]);

  async function completeLogin(accessToken: string) {
    setToken(accessToken);
    const user = await api<UserMe>("/api/auth/me");
    saveUser(user);
    navigate("/", { replace: true });
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!username.trim()) {
      setError("Ingrese su usuario.");
      return;
    }
    if (!password) {
      setError("Ingrese su contraseña.");
      return;
    }
    setLoading(true);
    try {
      const data = await api<{ access_token?: string; mfa_token?: string; mfa_required?: boolean }>(
        "/api/auth/login",
        {
          method: "POST",
          body: JSON.stringify({ username: username.trim(), password }),
        },
      );
      if (data.mfa_token) {
        setMfaToken(data.mfa_token);
        setError(null);
        return;
      }
      if (data.access_token) {
        await completeLogin(data.access_token);
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("Usuario o contraseña incorrectos.");
      } else if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("No se pudo iniciar sesión. Intente nuevamente.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function onMfaSubmit(e: FormEvent) {
    e.preventDefault();
    if (!mfaToken) return;
    setError(null);
    setLoading(true);
    try {
      const data = await verifyMfaLogin(mfaCode.trim(), mfaToken);
      await completeLogin(data.access_token);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Código de verificación incorrecto.");
      }
    } finally {
      setLoading(false);
    }
  }

  if (mfaToken) {
    return (
      <div className="login-wrap">
        <form className="login-card" onSubmit={onMfaSubmit}>
          <h1>Autenticación multifactor (MFA)</h1>
          <p className="muted">Ingrese el código de su aplicación de autenticación o un código de recuperación.</p>
          <label>
            Código
            <input
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value)}
              autoComplete="one-time-code"
              placeholder="000000"
              disabled={loading}
            />
          </label>
          {error && <p className="error" role="alert">{error}</p>}
          <button type="submit" disabled={loading}>
            {loading ? "Verificando…" : "Verificar"}
          </button>
          <button type="button" className="link-button" onClick={() => { setMfaToken(null); setMfaCode(""); }}>
            Volver
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={onSubmit}>
        <h1>Sistema empresarial de IA</h1>
        <p className="muted">Inicio de sesión · EMPLEADOS IA</p>
        <label>
          Usuario
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            placeholder="Usuario"
            disabled={loading}
          />
        </label>
        <label>
          Contraseña
          <span className="password-field">
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              placeholder="Contraseña"
              disabled={loading}
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              title={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              disabled={loading}
            >
              {showPassword ? "🙈" : "👁"}
            </button>
          </span>
        </label>
        <button
          type="button"
          className="link-button login-forgot"
          onClick={() => setShowForgot((v) => !v)}
          disabled={loading}
        >
          ¿Olvidó su contraseña?
        </button>
        {showForgot && (
          <div className="login-forgot-panel" role="region" aria-label="Recuperación de contraseña">
            <p className="muted">
              La recuperación automática por correo no está habilitada en esta instalación.
              Solicite al administrador del sistema que restablezca su acceso de forma segura.
            </p>
            <p className="muted">
              El administrador puede usar el script oficial <code>reset_admin_password</code> en el contenedor backend
              sin exponer la contraseña en archivos ni registros.
            </p>
          </div>
        )}
        {error && <p className="error" role="alert">{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? "Entrando…" : "Entrar"}
        </button>
      </form>

      <section className="login-card" style={{ marginTop: "1rem" }}>
        <h2>Inicio de sesión empresarial</h2>
        <p className="muted">Continuar con proveedor SSO de su organización</p>
        <label>
          Código de organización
          <input value={orgCode} onChange={(e) => setOrgCode(e.target.value)} placeholder="Código" disabled={loading} />
        </label>
        <button type="button" onClick={() => void onDiscoverSso()} disabled={loading}>
          Buscar proveedores
        </button>
        {showSso && (
          <div className="form-stack" style={{ marginTop: "0.75rem" }}>
            {ssoProviders.map((p) => (
              <button key={p.id} type="button" onClick={() => void onSsoLogin(p.id)} disabled={loading}>
                Continuar con {p.name}
              </button>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
