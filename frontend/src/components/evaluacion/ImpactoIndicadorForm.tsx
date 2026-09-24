import { useState } from "react";
import { crearIndicador } from "../../api";

type Props = {
  expedienteId: string;
  onCreated: () => void;
};

export function ImpactoIndicadorForm({ expedienteId, onCreated }: Props) {
  const [nombre, setNombre] = useState("");
  const [antes, setAntes] = useState("");
  const [proyectado, setProyectado] = useState("");
  const [real, setReal] = useState("");

  async function onAdd() {
    if (!nombre.trim()) return;
    await crearIndicador(expedienteId, {
      nombre,
      valor_antes: antes || undefined,
      valor_proyectado: proyectado || undefined,
      valor_real: real || undefined,
    });
    setNombre("");
    setAntes("");
    setProyectado("");
    setReal("");
    onCreated();
  }

  return (
    <div className="impacto-form panel compact-panel">
      <h3>Agregar indicador</h3>
      <div className="form-grid">
        <label>Nombre<input value={nombre} onChange={(e) => setNombre(e.target.value)} /></label>
        <label>Antes<input value={antes} onChange={(e) => setAntes(e.target.value)} /></label>
        <label>Proyectado<input value={proyectado} onChange={(e) => setProyectado(e.target.value)} /></label>
        <label>Real<input value={real} onChange={(e) => setReal(e.target.value)} /></label>
      </div>
      <button type="button" className="btn small primary" onClick={() => void onAdd()}>Guardar indicador</button>
    </div>
  );
}
