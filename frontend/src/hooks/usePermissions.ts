import { useEffect, useState } from "react";
import { getCachedUser, validateSession } from "../auth/session";

export function usePermissions() {
  const cachedUser = getCachedUser();
  const [permissions, setPermissions] = useState<Set<string>>(() => new Set(cachedUser?.permissions ?? []));
  const [loading, setLoading] = useState(!cachedUser);

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
