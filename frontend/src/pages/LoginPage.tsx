import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError, setToken, verifyMfaLogin, type UserMe } from "../api";
import { saveUser } from "../auth/session";

export function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [mfaCode, setMfaCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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
          <h1>Verificación MFA</h1>
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
        <h1>Enterprise AI OS</h1>
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
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            placeholder="Contraseña"
            disabled={loading}
          />
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? "Entrando…" : "Entrar"}
        </button>
      </form>
    </div>
  );
}
