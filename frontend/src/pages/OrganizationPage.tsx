import { useEffect, useState } from "react";
import { api, Organization } from "../api";

export function OrganizationPage() {
  const [org, setOrg] = useState<Organization | null>(null);

  useEffect(() => {
    api<Organization>("/api/organization").then(setOrg).catch(() => setOrg(null));
  }, []);

  return (
    <div>
      <h2>Organización</h2>
      {org ? (
        <table className="grid">
          <tbody>
            <tr>
              <th>Nombre</th>
              <td>{org.name}</td>
            </tr>
            <tr>
              <th>ID</th>
              <td className="mono">{org.id}</td>
            </tr>
            <tr>
              <th>Creada</th>
              <td>{new Date(org.created_at).toLocaleString()}</td>
            </tr>
          </tbody>
        </table>
      ) : (
        <p>Cargando…</p>
      )}
    </div>
  );
}
