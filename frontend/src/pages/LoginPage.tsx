import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  api,
  ApiError,
  setToken,
  verifyMfaLogin,
  discoverLogin,
  beginPublicOidc,
  completeOidcCallback,
  type UserMe,
} from "../api";
import { saveUser } from "../auth/session";
import { BrandMark } from "../components/identity/BrandMark";
import { EIAAX_BRAND } from "../lib/brand";

const SESSION_EXPIRED_KEY = "eaios_session_expired";

export function LoginPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [mfaCode, setMfaCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sessionNotice, setSessionNotice] = useState<string | null>(null);
  const [orgCode, setOrgCode] = useState("");
  const [ssoProviders, setSsoProviders] = useState<{ id: string; name: string; provider_type: string }[]>([]);
  const [showSso, setShowSso] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const expiredParam = searchParams.get("expired") === "1";
    const hadRealExpiry = sessionStorage.getItem(SESSION_EXPIRED_KEY) === "1";
    if (expiredParam && hadRealExpiry) {
      setSessionNotice("Su sesión ha vencido. Inicie sesión nuevamente.");
      sessionStorage.removeItem(SESSION_EXPIRED_KEY);
      const next = new URLSearchParams(searchParams);
      next.delete("expired");
      setSearchParams(next, { replace: true });
    } else if (expiredParam) {
      const next = new URLSearchParams(searchParams);
      next.delete("expired");
      setSearchParams(next, { replace: true });
    }
  }, [searchParams, setSearchParams]);

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

  async function completeLogin(accessToken: string) {
    sessionStorage.removeItem(SESSION_EXPIRED_KEY);
    setToken(accessToken);
    const user = await api<UserMe>("/api/auth/me");
    saveUser(user);
    navigate("/", { replace: true });
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSessionNotice(null);
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
      <div className="login-page">
        <div className="login-layout">
          <aside className="login-brand-panel">
            <BrandMark level="hero" />
            <p className="login-brand-copy">{EIAAX_BRAND.loginTagline}</p>
          </aside>
          <form className="login-card login-card-elevated" onSubmit={onMfaSubmit}>
            <h1>Verificación en dos pasos</h1>
            <p className="muted">Ingrese el código de su aplicación de autenticación o un código de recuperación.</p>
            <label>
              Código de verificación
              <input
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value)}
                autoComplete="one-time-code"
                placeholder="000000"
                disabled={loading}
              />
            </label>
            {error && <p className="error" role="alert">{error}</p>}
            <button type="submit" className="btn primary login-submit" disabled={loading}>
              {loading ? "Verificando…" : "Verificar"}
            </button>
            <button type="button" className="link-button" onClick={() => { setMfaToken(null); setMfaCode(""); }}>
              Volver al inicio de sesión
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page">
      <div className="login-layout">
        <aside className="login-brand-panel">
          <BrandMark level="hero" />
          <p className="login-brand-copy">{EIAAX_BRAND.descriptor}</p>
          <p className="login-brand-sub">{EIAAX_BRAND.loginTagline}</p>
        </aside>

        <div className="login-forms">
          <form className="login-card login-card-elevated" onSubmit={onSubmit}>
            <header className="login-card-header">
              <h1>Iniciar sesión</h1>
              <p className="muted small">Acceso a la plataforma {EIAAX_BRAND.name}</p>
            </header>

            {sessionNotice && (
              <p className="login-notice" role="status">{sessionNotice}</p>
            )}

            <label>
              Usuario
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                placeholder="Su usuario corporativo"
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
                  {showPassword ? "Ocultar" : "Ver"}
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
              </div>
            )}
            {error && <p className="error" role="alert">{error}</p>}
            <button type="submit" className="btn primary login-submit" disabled={loading}>
              {loading ? "Entrando…" : "Entrar"}
            </button>

            <div className="login-enterprise-block">
              <div className="login-enterprise-head">
                <strong>Acceso empresarial</strong>
                <span className="muted small" title="Código proporcionado por su organización">
                  ¿Qué es el código?
                </span>
              </div>
              <p className="muted small">
                Ingrese el código de su organización para continuar con su proveedor de identidad (SSO).
              </p>
              <div className="login-enterprise-row">
                <input
                  value={orgCode}
                  onChange={(e) => setOrgCode(e.target.value)}
                  placeholder="Código organización"
                  disabled={loading}
                  aria-label="Código de organización"
                />
                <button type="button" className="btn secondary small" onClick={() => void onDiscoverSso()} disabled={loading}>
                  Continuar
                </button>
              </div>
              {showSso && (
                <div className="form-stack login-sso-providers">
                  {ssoProviders.map((p) => (
                    <button key={p.id} type="button" className="btn secondary" onClick={() => void onSsoLogin(p.id)} disabled={loading}>
                      Continuar con {p.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
