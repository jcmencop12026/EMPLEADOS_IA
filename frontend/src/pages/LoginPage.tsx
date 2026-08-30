import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError, setToken, type UserMe } from "../api";
import { saveUser } from "../auth/session";

export function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (searchParams.get("expired") === "1") {
      setError("Su sesión ha vencido. Inicie sesión nuevamente.");
    }
  }, [searchParams]);

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
      const data = await api<{ access_token: string }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ username: username.trim(), password }),
      });
      setToken(data.access_token);
      const user = await api<UserMe>("/api/auth/me");
      saveUser(user);
      navigate("/", { replace: true });
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
              La recuperación automática por correo no está habilitada en esta instalación V1.
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
    </div>
  );
}
