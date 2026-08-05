import { useEffect, useState } from "react";
import { api, AuditLog } from "../api";

export function AuditPage() {
  const [rows, setRows] = useState<AuditLog[]>([]);

  useEffect(() => {
    api<AuditLog[]>("/api/audit/logs").then(setRows).catch(() => setRows([]));
  }, []);

  return (
    <div>
      <h2>Auditoría</h2>
      <table className="grid">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Acción</th>
            <th>Detalle</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>{new Date(r.created_at).toLocaleString()}</td>
              <td>{r.action}</td>
              <td>{r.detail ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && <p className="muted">Sin registros</p>}
    </div>
  );
}
