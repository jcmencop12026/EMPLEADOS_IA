# Respaldo candidato convergido C2

| Campo | Valor |
|---|---|
| SHA git | `b19b04dd438f5b13b422e9a760f54fa074fb52ed` |
| Rama | `cursor/eiaax-convergencia-v1-v2` |
| Fecha UTC | 2026-08-31T20:29:48Z |
| Archivo | `EIAAX_C2_b19b04d_20260831T202948Z.tar.gz` |
| SHA-256 | `17330d8084a5c9ef2e30cf3b6cdf4c389e05f269babb8103f3aaf02c92d0527f` |

## Verificación

```bash
sha256sum -c EIAAX_C2_b19b04d_20260831T202948Z.tar.gz.sha256
git rev-parse b19b04dd438f5b13b422e9a760f54fa074fb52ed
```

## Regenerar

```bash
git archive --format=tar.gz --prefix=EIAAX_C2_b19b04d/ \
  b19b04dd438f5b13b422e9a760f54fa074fb52ed \
  -o EIAAX_C2_b19b04d_$(date -u +%Y%m%dT%H%M%SZ).tar.gz
sha256sum EIAAX_C2_b19b04d_*.tar.gz > EIAAX_C2_b19b04d_*.tar.gz.sha256
```
