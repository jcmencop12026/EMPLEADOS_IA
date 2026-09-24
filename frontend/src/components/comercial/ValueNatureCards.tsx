import { formatMoney, TOOLTIPS, type NatureBreakdown } from "../../lib/comercialLabels";
import { HelpTooltip } from "./HelpTooltip";

type Props = {
  breakdown: NatureBreakdown;
  currency?: string;
  showPriceNote?: boolean;
};

export function ValueNatureCards({ breakdown, currency = "USD", showPriceNote = true }: Props) {
  const verificado = breakdown.valor_verificado_atribuible ?? 0;
  const estimado = breakdown.valor_estimado_atribuible ?? 0;
  const potencial = breakdown.valor_potencial_atribuible ?? 0;
  const paraPrecio = breakdown.valor_atribuible_precio ?? breakdown.valor_atribuible_para_precio ?? verificado + estimado;

  return (
    <div className="value-nature-grid">
      <div className="value-nature-card verified">
        <div className="value-nature-head">
          <strong>Valor verificado</strong>
          <HelpTooltip text={TOOLTIPS.valorVerificado} />
        </div>
        <span className="value-nature-amount">{formatMoney(verificado, currency)}</span>
        <small>Evidencia real · HECHO</small>
      </div>
      <div className="value-nature-card estimated">
        <div className="value-nature-head">
          <strong>Valor estimado</strong>
          <HelpTooltip text={TOOLTIPS.valorEstimado} />
        </div>
        <span className="value-nature-amount">{formatMoney(estimado, currency)}</span>
        <small>Proyección sustentada · INFERENCIA</small>
      </div>
      <div className="value-nature-card potential">
        <div className="value-nature-head">
          <strong>Valor potencial</strong>
          <HelpTooltip text={TOOLTIPS.valorPotencial} />
        </div>
        <span className="value-nature-amount">{formatMoney(potencial, currency)}</span>
        <small>No materializado · INFERENCIA</small>
      </div>
      {showPriceNote && (
        <div className="value-nature-card price-base">
          <div className="value-nature-head">
            <strong>Base para precio sugerido</strong>
            <HelpTooltip text={TOOLTIPS.precioSugerido} />
          </div>
          <span className="value-nature-amount">{formatMoney(paraPrecio, currency)}</span>
          <small className="potential-excluded">El potencial no entra al precio</small>
        </div>
      )}
    </div>
  );
}
