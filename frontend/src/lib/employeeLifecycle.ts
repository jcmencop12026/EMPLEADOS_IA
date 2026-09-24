import { label, LIFECYCLE_STATUS } from "./labels";

export type EmployeeLifecycleStage = {
  code: string;
  label: string;
  description: string;
  nextAction: string;
  nextActionKey: "validate" | "test" | "certify" | "approve" | "publish" | "activate" | "train" | "retire" | "none";
  canRun: boolean;
};

export function resolveEmployeeLifecycleStage(input: {
  lifecycle?: string | null;
  lastTest?: string | null;
  lastPublication?: string | null;
  lastCertification?: string | null;
}): EmployeeLifecycleStage {
  const lifecycle = input.lifecycle ?? "DRAFT";
  const statusLabel = label(LIFECYCLE_STATUS, lifecycle);

  if (lifecycle === "DRAFT" || lifecycle === "CONFIGURING") {
    return {
      code: lifecycle,
      label: statusLabel,
      description: "El empleado está en configuración. Valide requisitos antes de pruebas.",
      nextAction: "Validar configuración",
      nextActionKey: "validate",
      canRun: true,
    };
  }
  if (lifecycle === "READY_FOR_TEST" || lifecycle === "TESTING" || lifecycle === "FAILED_TEST") {
    return {
      code: lifecycle,
      label: statusLabel,
      description: input.lastTest ? `Última prueba: ${input.lastTest}` : "Sin prueba registrada visible.",
      nextAction: "Ejecutar pruebas",
      nextActionKey: "test",
      canRun: true,
    };
  }
  if (lifecycle === "READY_FOR_CERTIFICATION") {
    return {
      code: lifecycle,
      label: statusLabel,
      description: "Pruebas completadas. Certifique antes de publicar.",
      nextAction: "Certificar empleado",
      nextActionKey: "certify",
      canRun: true,
    };
  }
  if (lifecycle === "CERTIFIED") {
    return {
      code: lifecycle,
      label: statusLabel,
      description: "Certificado. Solicite aprobación y publique para operación.",
      nextAction: "Solicitar aprobación / Publicar",
      nextActionKey: "publish",
      canRun: true,
    };
  }
  if (lifecycle === "PUBLISHED") {
    return {
      code: lifecycle,
      label: statusLabel,
      description: input.lastPublication ? `Publicado ${input.lastPublication}` : "Publicado sin fecha visible.",
      nextAction: "Activar en operación",
      nextActionKey: "activate",
      canRun: true,
    };
  }
  if (lifecycle === "ACTIVE") {
    const gaps: string[] = [];
    if (!input.lastTest) gaps.push("prueba");
    if (!input.lastPublication) gaps.push("publicación");
    return {
      code: lifecycle,
      label: statusLabel,
      description: gaps.length
        ? `Activo con pendientes de evidencia: ${gaps.join(", ")}.`
        : "Operando con evidencia de ciclo visible.",
      nextAction: gaps.length ? "Completar evidencia (prueba/publicación)" : "Capacitar / monitorear",
      nextActionKey: gaps.length ? "test" : "train",
      canRun: true,
    };
  }
  if (lifecycle === "PAUSED") {
    return {
      code: lifecycle,
      label: statusLabel,
      description: "Pausado temporalmente.",
      nextAction: "Reactivar",
      nextActionKey: "activate",
      canRun: true,
    };
  }
  return {
    code: lifecycle,
    label: statusLabel,
    description: "Estado de ciclo de vida del empleado IA.",
    nextAction: "Revisar historial",
    nextActionKey: "none",
    canRun: false,
  };
}
