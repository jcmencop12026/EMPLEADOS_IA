import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { fetchPlatformOrganizations, type PlatformOrganization } from "../api";
import { getCachedUser } from "../auth/session";

const STORAGE_KEY = "eaios_selected_org_id";
const CONTEXT_EVENT = "organization-context-changed";

export type OrganizationContextValue = {
  homeOrganizationId: string;
  homeOrganizationName: string;
  canSelectOrganization: boolean;
  selectedOrganizationId: string | null;
  effectiveOrganizationId: string;
  effectiveOrganizationName: string;
  organizations: PlatformOrganization[];
  loadingOrganizations: boolean;
  setSelectedOrganizationId: (orgId: string | null) => void;
  /** Query param para APIs cuando el contexto activo difiere de la org home del usuario. */
  organizationQueryParam: string | undefined;
  isViewingOtherOrganization: boolean;
};

const OrganizationContext = createContext<OrganizationContextValue | null>(null);

function buildFallback(): OrganizationContextValue {
  const user = getCachedUser();
  const homeId = user?.organization_id ?? "";
  const homeName = user?.organization_name ?? "";
  return {
    homeOrganizationId: homeId,
    homeOrganizationName: homeName,
    canSelectOrganization: false,
    selectedOrganizationId: null,
    effectiveOrganizationId: homeId,
    effectiveOrganizationName: homeName,
    organizations: [],
    loadingOrganizations: false,
    setSelectedOrganizationId: () => undefined,
    organizationQueryParam: undefined,
    isViewingOtherOrganization: false,
  };
}

export function OrganizationProvider({ children }: { children: ReactNode }) {
  const user = getCachedUser();
  const homeOrganizationId = user?.organization_id ?? "";
  const homeOrganizationName = user?.organization_name ?? "";
  const canSelectOrganization = Boolean(user?.permissions?.includes("platform.organization.view"));

  const [selectedOrganizationId, setSelectedOrganizationIdState] = useState<string | null>(() => {
    if (!canSelectOrganization) return null;
    return sessionStorage.getItem(STORAGE_KEY) || null;
  });
  const [organizations, setOrganizations] = useState<PlatformOrganization[]>([]);
  const [loadingOrganizations, setLoadingOrganizations] = useState(false);

  useEffect(() => {
    if (!canSelectOrganization) {
      setSelectedOrganizationIdState(null);
      sessionStorage.removeItem(STORAGE_KEY);
      return;
    }
    setLoadingOrganizations(true);
    fetchPlatformOrganizations()
      .then((orgs) => setOrganizations(orgs.filter((o) => o.status === "ACTIVE")))
      .catch(() => setOrganizations([]))
      .finally(() => setLoadingOrganizations(false));
  }, [canSelectOrganization]);

  useEffect(() => {
    if (!canSelectOrganization) return;
    if (selectedOrganizationId && selectedOrganizationId !== homeOrganizationId) {
      sessionStorage.setItem(STORAGE_KEY, selectedOrganizationId);
    } else {
      sessionStorage.removeItem(STORAGE_KEY);
    }
  }, [selectedOrganizationId, canSelectOrganization, homeOrganizationId]);

  const setSelectedOrganizationId = useCallback(
    (orgId: string | null) => {
      if (!canSelectOrganization) return;
      const next = orgId && orgId !== homeOrganizationId ? orgId : null;
      setSelectedOrganizationIdState(next);
      window.dispatchEvent(new Event(CONTEXT_EVENT));
    },
    [canSelectOrganization, homeOrganizationId],
  );

  const effectiveOrganizationId = selectedOrganizationId ?? homeOrganizationId;
  const isViewingOtherOrganization = Boolean(
    selectedOrganizationId && selectedOrganizationId !== homeOrganizationId,
  );

  const effectiveOrganizationName = useMemo(() => {
    if (!isViewingOtherOrganization) return homeOrganizationName;
    return organizations.find((o) => o.id === selectedOrganizationId)?.name ?? homeOrganizationName;
  }, [
    isViewingOtherOrganization,
    homeOrganizationName,
    organizations,
    selectedOrganizationId,
  ]);

  const organizationQueryParam = isViewingOtherOrganization ? selectedOrganizationId ?? undefined : undefined;

  const value = useMemo<OrganizationContextValue>(
    () => ({
      homeOrganizationId,
      homeOrganizationName,
      canSelectOrganization,
      selectedOrganizationId,
      effectiveOrganizationId,
      effectiveOrganizationName,
      organizations,
      loadingOrganizations,
      setSelectedOrganizationId,
      organizationQueryParam,
      isViewingOtherOrganization,
    }),
    [
      homeOrganizationId,
      homeOrganizationName,
      canSelectOrganization,
      selectedOrganizationId,
      effectiveOrganizationId,
      effectiveOrganizationName,
      organizations,
      loadingOrganizations,
      setSelectedOrganizationId,
      organizationQueryParam,
      isViewingOtherOrganization,
    ],
  );

  return <OrganizationContext.Provider value={value}>{children}</OrganizationContext.Provider>;
}

export function useOrganizationContext(): OrganizationContextValue {
  const ctx = useContext(OrganizationContext);
  return ctx ?? buildFallback();
}

export const ORGANIZATION_CONTEXT_EVENT = CONTEXT_EVENT;
