import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { useLocation, useParams } from "react-router-dom";
import { EiaaxContextualAssistant } from "../components/EiaaxContextualAssistant";
import { getCachedUser } from "../auth/session";
import { useOrganizationContext } from "../hooks/useOrganizationContext";

export type AssistantIntent =
  | "preguntar"
  | "analizar"
  | "proponer"
  | "explicar"
  | "riesgos"
  | "oportunidades"
  | "comparar"
  | "siguiente_accion";

type AssistantContextValue = {
  module: string;
  intent?: AssistantIntent;
  organization_id?: string;
  empresa?: string;
  expediente_id?: string;
  diagnostico_id?: string;
  oportunidad_id?: string;
  empleado_id?: string;
  tab?: string;
  periodo?: string;
  [key: string]: unknown;
};

type ProviderState = {
  extra: Record<string, unknown>;
  enabled: boolean;
};

type ContextApi = {
  setAssistantContext: (ctx: Record<string, unknown>) => void;
  clearAssistantContext: () => void;
  setAssistantEnabled: (enabled: boolean) => void;
};

const ApiContext = createContext<ContextApi | null>(null);

const V1_ROUTE_PATTERNS: Array<{ test: RegExp; module: string }> = [
  { test: /^\/(centro-control)?$/, module: "centro_control" },
  { test: /^\/evaluaciones\/[^/]+/, module: "evaluacion_cabina" },
  { test: /^\/empresa\/[^/]+/, module: "evaluacion_cabina" },
  { test: /^\/diagnosticos\/[^/]+/, module: "diagnostico" },
  { test: /^\/diagnosticos$/, module: "diagnosticos" },
  { test: /^\/oportunidades\/[^/]+/, module: "oportunidad" },
  { test: /^\/oportunidades$/, module: "oportunidades" },
  { test: /^\/empleados\/[^/]+/, module: "empleado_ia" },
  { test: /^\/directorio$/, module: "empleados_ia" },
  { test: /^\/presentacion\/[^/]+/, module: "presentacion" },
  { test: /^\/demo/, module: "demo_comercial" },
  { test: /^\/centro-estrategico/, module: "centro_estrategico" },
  { test: /^\/centro-confianza/, module: "centro_confianza" },
  { test: /^\/costos-valor/, module: "valor_finops" },
  { test: /^\/resultados/, module: "resultados" },
];

function resolveModule(pathname: string): string | null {
  for (const { test, module } of V1_ROUTE_PATTERNS) {
    if (test.test(pathname)) return module;
  }
  return null;
}

function buildRouteContext(
  pathname: string,
  params: Record<string, string | undefined>,
  organizationId: string | null,
): AssistantContextValue | null {
  const module = resolveModule(pathname);
  if (!module) return null;

  const user = getCachedUser();
  const ctx: AssistantContextValue = {
    module,
    organization_id: organizationId ?? user?.organization_id,
    empresa: user?.organization_name,
  };

  if (params.evaluacionId) ctx.expediente_id = params.evaluacionId;
  if (params.diagnosticId) ctx.diagnostico_id = params.diagnosticId;
  if (params.employeeId) ctx.empleado_id = params.employeeId;
  if (params.opportunityId) ctx.oportunidad_id = params.opportunityId;
  if (params.expedienteId) ctx.expediente_id = params.expedienteId;

  return ctx;
}

export function ContextualAssistantProvider({ children }: { children: ReactNode }) {
  const location = useLocation();
  const params = useParams();
  const { effectiveOrganizationId } = useOrganizationContext();
  const [state, setState] = useState<ProviderState>({ extra: {}, enabled: true });

  const setAssistantContext = useCallback((ctx: Record<string, unknown>) => {
    setState((s) => ({ ...s, extra: { ...s.extra, ...ctx } }));
  }, []);

  const clearAssistantContext = useCallback(() => {
    setState((s) => ({ ...s, extra: {} }));
  }, []);

  const setAssistantEnabled = useCallback((enabled: boolean) => {
    setState((s) => ({ ...s, enabled }));
  }, []);

  const api = useMemo(
    () => ({ setAssistantContext, clearAssistantContext, setAssistantEnabled }),
    [setAssistantContext, clearAssistantContext, setAssistantEnabled],
  );

  const routeContext = useMemo(
    () => buildRouteContext(location.pathname, params, effectiveOrganizationId),
    [location.pathname, params, effectiveOrganizationId],
  );

  const mergedContext = useMemo(() => {
    if (!routeContext) return null;
    return { ...routeContext, ...state.extra, path: location.pathname };
  }, [routeContext, state.extra, location.pathname]);

  const showAssistant = state.enabled && mergedContext != null;

  return (
    <ApiContext.Provider value={api}>
      {children}
      {showAssistant && (
        <div className="contextual-assistant-rail">
          <EiaaxContextualAssistant compact title="Asistente EIAAX" context={mergedContext} />
        </div>
      )}
    </ApiContext.Provider>
  );
}

export function useContextualAssistant() {
  const ctx = useContext(ApiContext);
  if (!ctx) {
    throw new Error("useContextualAssistant debe usarse dentro de ContextualAssistantProvider");
  }
  return ctx;
}
