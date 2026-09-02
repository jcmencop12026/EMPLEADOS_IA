import { useEffect, useRef } from "react";
import { useContextualAssistant } from "../context/ContextualAssistantContext";

/** Enriquece el contexto del asistente global para la página actual. */
export function usePageAssistantContext(context: Record<string, unknown>, enabled = true) {
  const { setAssistantContext, clearAssistantContext, setAssistantEnabled } = useContextualAssistant();
  const snapshot = JSON.stringify(context);
  const prevRef = useRef("");

  useEffect(() => {
    setAssistantEnabled(enabled);
    if (enabled && snapshot !== prevRef.current) {
      setAssistantContext(JSON.parse(snapshot) as Record<string, unknown>);
      prevRef.current = snapshot;
    }
    return () => {
      clearAssistantContext();
      setAssistantEnabled(true);
      prevRef.current = "";
    };
  }, [enabled, snapshot, setAssistantContext, clearAssistantContext, setAssistantEnabled]);
}
