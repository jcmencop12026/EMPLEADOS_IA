# Correcciones realizadas

| # | Defecto | Corrección |
|---|---------|------------|
| 1 | Sin datos demo para recorridos | `seed_lote3_demo.py` + `credentials.example` |
| 2 | Sin pruebas de recorrido integrado | `test_puesta_en_marcha_journeys.py` (8 tests) |
| 3 | BD demo sin migraciones Lote 3 | `alembic upgrade head` en `eiaax_integrado_demo.db` |

No se modificó el tag `eiaax-lote3-integrado-respaldo`.  
No se alteraron refs V1/V2.  
No se crearon migraciones nuevas (head sigue `1770`).
