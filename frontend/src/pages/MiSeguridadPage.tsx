import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  ApiError,
  changePassword,
  confirmMfaEnrollment,
  disableMfa,
  fetchMfaStatus,
  fetchMySessions,
  regenerateMfaRecovery,
  revokeMySession,
  revokeOtherSessions,
  startMfaEnrollment,
  type MfaStatus,
  type UserSession,
} from "../api";
import { ErrorState, LoadingState } from "../components/AsyncState";

export function MiSeguridadPage() {
  const [status, setStatus] = useState<MfaStatus | null>(null);
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [enrollSecret, setEnrollSecret] = useState<string | null>(null);
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(null);
  const [confirmCode, setConfirmCode] = useState("");
  const [recoveryCodes, setRecoveryCodes] = useState<string[] | null>(null);
  const [password, setPassword] = useState("");
  const [pwdCurrent, setPwdCurrent] = useState("");
  const [pwdNew, setPwdNew] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([fetchMfaStatus(), fetchMySessions()])
      .then(([mfa, sess]) => {
        setStatus(mfa);
        setSessions(sess);
        setError(null);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error al cargar seguridad"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onStartMfa() {
    setMessage(null);
    try {
      const data = await startMfaEnrollment();
      setEnrollSecret(data.secret);
      setQrDataUrl(data.qr_data_url);
      setRecoveryCodes(null);
    } catch (e) {
      setMessage(e instanceof ApiError ? e.message : "No se pudo iniciar la configuración MFA.");
    }
  }

  async function onConfirmMfa(e: FormEvent) {
    e.preventDefault();
    setMessage(null);
    try {
      const data = await confirmMfaEnrollment(confirmCode);
      setRecoveryCodes(data.recovery_codes);
      setEnrollSecret(null);
      setQrDataUrl(null);
      setConfirmCode("");
      load();
      setMessage("Autenticación multifactor activada correctamente.");
    } catch (e) {
      setMessage(e instanceof ApiError ? e.message : "Código incorrecto.");
    }
  }

  async function onDisableMfa() {
    setMessage(null);
    try {
      await disableMfa(password);
      setPassword("");
      load();
      setMessage("MFA deshabilitado.");
    } catch (e) {
      setMessage(e instanceof ApiError ? e.message : "No se pudo deshabilitar MFA.");
    }
  }

  async function onRegenerate() {
    setMessage(null);
    try {
      const data = await regenerateMfaRecovery(password);
      setRecoveryCodes(data.recovery_codes);
      setPassword("");
      load();
    } catch (e) {
      setMessage(e instanceof ApiError ? e.message : "No se pudieron regenerar los códigos.");
    }
  }

  async function onChangePassword(e: FormEvent) {
    e.preventDefault();
    setMessage(null);
    try {
      await changePassword(pwdCurrent, pwdNew, true);
      setPwdCurrent("");
      setPwdNew("");
      setMessage("Contraseña actualizada. Las demás sesiones fueron cerradas.");
      load();
    } catch (e) {
      setMessage(e instanceof ApiError ? e.message : "No se pudo cambiar la contraseña.");
    }
  }

  if (loading) return <LoadingState message="Cargando mi seguridad…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Mi seguridad</h1>
        <p className="muted">Autenticación multifactor, códigos de recuperación y sesiones activas</p>
      </header>

      {message && <p className="panel" role="status">{message}</p>}

      <section className="panel">
        <h2>Autenticación multifactor (MFA)</h2>
        <p>
          Estado: <strong>{status?.enabled ? "Activo" : "Inactivo"}</strong>
          {status?.mfa_required_by_policy && !status.enabled && (
            <span className="error"> — Requerido por política de su organización</span>
          )}
        </p>
        {status?.enabled ? (
          <div className="form-stack">
            <p className="muted">Códigos de recuperación restantes: {status.recovery_codes_remaining}</p>
            <label>
              Contraseña para acciones sensibles
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </label>
            <div className="button-row">
              <button type="button" onClick={onRegenerate}>Regenerar códigos de recuperación</button>
              <button type="button" className="danger" onClick={onDisableMfa}>Deshabilitar MFA</button>
            </div>
          </div>
        ) : (
          <button type="button" onClick={onStartMfa}>Configurar MFA</button>
        )}

        {qrDataUrl && (
          <form className="form-stack" onSubmit={onConfirmMfa}>
            <p>Escanee el código QR con su aplicación de autenticación y confirme con un código.</p>
            <img src={qrDataUrl} alt="Código QR MFA" width={180} height={180} />
            {enrollSecret && (
              <p className="muted mono">Clave manual (solo durante configuración): {enrollSecret}</p>
            )}
            <label>
              Código de verificación
              <input value={confirmCode} onChange={(e) => setConfirmCode(e.target.value)} required />
            </label>
            <button type="submit">Confirmar MFA</button>
          </form>
        )}

        {recoveryCodes && (
          <div className="panel">
            <h3>Códigos de recuperación (guárdelos ahora)</h3>
            <p className="muted">No se volverán a mostrar.</p>
            <ul className="mono">
              {recoveryCodes.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section className="panel">
        <h2>Sesiones activas</h2>
        <button type="button" onClick={() => revokeOtherSessions().then(load)}>Cerrar otras sesiones</button>
        <table className="data-table">
          <thead>
            <tr><th>Inicio</th><th>Última actividad</th><th>IP</th><th>Dispositivo</th><th></th></tr>
          </thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.id}>
                <td>{new Date(s.created_at).toLocaleString()}</td>
                <td>{new Date(s.last_activity_at).toLocaleString()}</td>
                <td>{s.ip_address || "—"}</td>
                <td className="cell-truncate">{s.user_agent || "—"}</td>
                <td>
                  {s.current ? (
                    <span className="muted">Actual</span>
                  ) : (
                    <button type="button" onClick={() => revokeMySession(s.id).then(load)}>Cerrar</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <h2>Cambiar contraseña</h2>
        <form className="form-stack" onSubmit={onChangePassword}>
          <label>
            Contraseña actual
            <input type="password" value={pwdCurrent} onChange={(e) => setPwdCurrent(e.target.value)} required />
          </label>
          <label>
            Nueva contraseña
            <input type="password" value={pwdNew} onChange={(e) => setPwdNew(e.target.value)} required minLength={8} />
          </label>
          <button type="submit">Actualizar contraseña</button>
        </form>
      </section>
    </div>
  );
}
