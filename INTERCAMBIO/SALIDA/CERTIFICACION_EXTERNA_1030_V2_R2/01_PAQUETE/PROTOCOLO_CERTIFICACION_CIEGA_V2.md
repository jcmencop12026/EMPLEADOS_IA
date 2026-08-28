# PROTOCOLO DE CERTIFICACIÓN CIEGA 1030 V2

1. Verificar que el código bajo prueba corresponde al HEAD objetivo del PR #25.
2. NO abrir, imprimir, parsear ni consultar `ORACULO_SELLADO/`.
3. Ejecutar V2-OP-A…V2-OP-F, V2-NS-1/2 y V2-PX-1…4 usando exclusivamente `CASOS/*/entrada.json`.
4. Guardar por caso la salida bruta completa y evidencia persistida en una carpeta nueva `BRUTOS_ANTES_ORACULO/`.
5. Registrar SHA-256 de cada bruto y crear `CONGELADO_SHA256.csv`.
6. Confirmar que todos los brutos quedaron congelados.
7. Solo entonces consultar `ORACULO_SELLADO/` y `MATRIZ_EVALUACION_V2.csv`.
8. Comparar comportamiento semántico y reglas, no cadenas cosméticas.
9. Cualquier incumplimiento de R01–R12 es bloqueante hasta corrección o justificación técnica verificable.
10. Repetir PX-1 para idempotencia y PX-2 para aislamiento sin contaminar tenants.
11. No modificar código durante la fase ciega. Si falla, cerrar la corrida, documentar FAIL y corregir en una iteración posterior.
12. Emitir informe final con PASS/FAIL por caso y criterio, hashes, HEAD, migración, pruebas focales/regresión y CI.
