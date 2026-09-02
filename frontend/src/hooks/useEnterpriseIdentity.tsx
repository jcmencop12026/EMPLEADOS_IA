import { useCallback, useEffect, useState } from "react";
import { fetchOrgConfig, type OrgConfig } from "../api";
import { getCachedUser } from "../auth/session";
import { DEFAULT_ENTERPRISE_IDENTITY, EIAAX_BRAND, type EnterpriseVisualIdentity } from "../lib/brand";

function mapConfigToIdentity(config: OrgConfig, orgName: string): EnterpriseVisualIdentity {
  return {
    displayName: config.enterprise_display_name?.trim() || orgName,
    logoUrl: config.enterprise_logo_url || null,
    logoCompactUrl: config.enterprise_logo_compact_url || null,
    accentColor: config.enterprise_accent_color || DEFAULT_ENTERPRISE_IDENTITY.accentColor,
  };
}

export function useEnterpriseIdentity() {
  const user = getCachedUser();
  const [identity, setIdentity] = useState<EnterpriseVisualIdentity>(() => ({
    ...DEFAULT_ENTERPRISE_IDENTITY,
    displayName: user?.organization_name ?? "",
  }));
  const [loading, setLoading] = useState(true);

  const reload = useCallback(() => {
    const cachedUser = getCachedUser();
    const orgName = cachedUser?.organization_name ?? "";
    setLoading(true);
    fetchOrgConfig()
      .then((config) => setIdentity(mapConfigToIdentity(config, orgName)))
      .catch(() => setIdentity({ ...DEFAULT_ENTERPRISE_IDENTITY, displayName: orgName }))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  return {
    identity,
    loading,
    reload,
    platformName: EIAAX_BRAND.name,
    platformDescriptor: EIAAX_BRAND.descriptor,
    platformAttribution: EIAAX_BRAND.platformAttribution,
  };
}
