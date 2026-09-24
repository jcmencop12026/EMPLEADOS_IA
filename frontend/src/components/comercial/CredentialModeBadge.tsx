import { credentialModeLabel } from "../../lib/comercialLabels";
import { HelpTooltip } from "./HelpTooltip";

type Props = { mode?: string | null };

export function CredentialModeBadge({ mode }: Props) {
  const isByok = mode === "CREDENCIALES_PROPIAS";
  return (
    <span className={`cred-badge ${isByok ? "byok" : "managed"}`}>
      {credentialModeLabel(mode ?? undefined)}
      <HelpTooltip
        text={
          isByok
            ? "La institución conecta sus propias credenciales de proveedor IA. No se muestran secretos."
            : "EMPLEADOS IA gestiona el consumo y el costo proveedor de forma trazable."
        }
      />
    </span>
  );
}
