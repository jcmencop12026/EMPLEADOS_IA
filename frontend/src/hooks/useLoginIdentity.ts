import { useCallback, useEffect, useState } from "react";
import { fetchLoginIdentity, type LoginIdentity } from "../api";
import { ENTERPRISE_IDENTITY_EVENT, type EnterpriseVisualIdentity } from "../lib/brand";

const CACHE_KEY = "eiaax_login_identity_v1";

function fromCache(): LoginIdentity | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? (JSON.parse(raw) as LoginIdentity) : null;
  } catch {
    return null;
  }
}

function toCache(data: LoginIdentity) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(data));
  } catch {
    /* ignore */
  }
}

export function useLoginIdentity() {
  const [identity, setIdentity] = useState<LoginIdentity | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(() => {
    setLoading(true);
    fetchLoginIdentity()
      .then((data) => {
        setIdentity(data);
        toCache(data);
      })
      .catch(() => {
        const cached = fromCache();
        setIdentity(cached);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    reload();
    const onChange = () => reload();
    window.addEventListener(ENTERPRISE_IDENTITY_EVENT, onChange);
    return () => window.removeEventListener(ENTERPRISE_IDENTITY_EVENT, onChange);
  }, [reload]);

  const asEnterprise: EnterpriseVisualIdentity = {
    displayName: identity?.display_name ?? "",
    logoUrl: identity?.logo_url ?? null,
    logoCompactUrl: identity?.logo_compact_url ?? null,
    accentColor: identity?.accent_color ?? "#1d4ed8",
  };

  return { identity, asEnterprise, loading, reload };
}
