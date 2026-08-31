import { useEffect, useState } from "react";
import { getCachedUser, validateSession } from "../auth/session";

export function usePermissions() {
  const [permissions, setPermissions] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const user = getCachedUser() ?? (await validateSession());
        if (active) {
          setPermissions(new Set(user.permissions ?? []));
        }
      } catch {
        if (active) {
          setPermissions(new Set());
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const has = (code: string) => permissions.has(code);

  return { permissions, has, loading };
}
