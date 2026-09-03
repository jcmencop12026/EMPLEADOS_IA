import { useOrganizationContext } from "../hooks/useOrganizationContext";

/** Selector de organización activa para usuarios de plataforma (SUPERADMIN). */
export function OrganizationContextBar() {
  const {
    canSelectOrganization,
    homeOrganizationId,
    homeOrganizationName,
    selectedOrganizationId,
    effectiveOrganizationName,
    organizations,
    loadingOrganizations,
    setSelectedOrganizationId,
    isViewingOtherOrganization,
  } = useOrganizationContext();

  if (!canSelectOrganization) return null;

  const selectValue = selectedOrganizationId ?? homeOrganizationId;

  return (
    <div className="org-context-bar" title="Organización activa para Centro de Control y Mi Trabajo">
      <label className="org-context-label" htmlFor="org-context-select">
        Organización:
      </label>
      <select
        id="org-context-select"
        value={selectValue}
        disabled={loadingOrganizations}
        onChange={(e) => {
          const next = e.target.value;
          setSelectedOrganizationId(next === homeOrganizationId ? null : next);
        }}
      >
        <option value={homeOrganizationId}>
          {homeOrganizationName} (mi organización)
        </option>
        {organizations
          .filter((o) => o.id !== homeOrganizationId)
          .map((o) => (
            <option key={o.id} value={o.id}>
              {o.name}
            </option>
          ))}
      </select>
      {isViewingOtherOrganization && (
        <span className="org-context-badge" title="Viendo datos de otra organización">
          Viendo: {effectiveOrganizationName}
        </span>
      )}
    </div>
  );
}
