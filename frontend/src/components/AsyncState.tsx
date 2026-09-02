import type { ReactNode } from "react";

type LoadingProps = { message?: string };

export function LoadingState({ message = "Cargando…" }: LoadingProps) {
  return (
    <div className="async-state loading-state" role="status">
      <span className="spinner" aria-hidden />
      <span>{message}</span>
    </div>
  );
}

type EmptyProps = { title?: string; message?: string; action?: ReactNode };

export function EmptyState({
  title = "Sin datos",
  message = "No hay información para mostrar en este momento.",
  action,
}: EmptyProps) {
  return (
    <div className="async-state empty-state">
      <strong>{title}</strong>
      <p className="muted">{message}</p>
      {action}
    </div>
  );
}

type ErrorProps = { message: string; onRetry?: () => void };

export function ErrorState({ message, onRetry }: ErrorProps) {
  return (
    <div className="async-state error-state" role="alert">
      <strong>No se pudo cargar la información</strong>
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="btn" onClick={onRetry}>
          Reintentar
        </button>
      )}
    </div>
  );
}
