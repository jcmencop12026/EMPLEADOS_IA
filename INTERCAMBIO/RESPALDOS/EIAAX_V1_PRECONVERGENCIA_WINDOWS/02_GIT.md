# 02 — Respaldo Git

## SHA respaldado

```
d0345663f0fcc286d9b68146735a05208839bd7e
```

## Rama y remoto

| Campo | Valor |
|-------|-------|
| Rama | `cursor/windows-demo-arranque-85e4` |
| Remoto | `origin` → `https://github.com/jcmencop12026/EMPLEADOS_IA` |
| HEAD remoto (al respaldar) | `d034566` |

## Tag anotado

```
eiaax-v1-preconvergencia-windows-operativo
```

Apunta a `d034566`. Mensaje: *EIAAX V1: punto operativo Windows preconvergencia A+B+C+D*.

## Bundle Git

| Archivo | Tamaño |
|---------|--------|
| `eiaax-v1-preconvergencia-windows-d034566-20260901T182500Z.bundle` | 6.7 MB |

### Refs incluidas

- `refs/heads/cursor/windows-demo-arranque-85e4` → `d034566`
- `refs/tags/eiaax-v1-preconvergencia-windows-operativo` → `d034566`

### Verificación

```
git bundle verify eiaax-v1-preconvergencia-windows-d034566-20260901T182500Z.bundle
→ is okay
```

## Árbol reproducible (tarball)

| Archivo | Contenido |
|---------|-----------|
| `eiaax-v1-preconvergencia-windows-d034566-20260901T182500Z-tree.tar.gz` | Árbol completo en `d034566` |
| `eiaax-v1-preconvergencia-windows-docs-20260901T182500Z.tar.gz` | Guía Windows + scripts `scripts/windows/` |

## Prueba de restauración Git

**Resultado: PASS**

```bash
git clone eiaax-v1-preconvergencia-windows-d034566-20260901T182500Z.bundle /tmp/eiaax-recovery-preconv
cd /tmp/eiaax-recovery-preconv
git checkout cursor/windows-demo-arranque-85e4
git rev-parse HEAD
# → d0345663f0fcc286d9b68146735a05208839bd7e
git rev-parse eiaax-v1-preconvergencia-windows-operativo^{commit}
# → d0345663f0fcc286d9b68146735a05208839bd7e
```

## Genealogía relevante

```
75fc689  (candidato funcional Lote 3 — docs puesta en marcha)
   └── 791b7a4 … d034566  (14 commits correcciones Windows)
```

## Publicación del tag

Tras commit del respaldo, publicar:

```
git push origin eiaax-v1-preconvergencia-windows-operativo
git push origin cursor/windows-demo-arranque-85e4
```
