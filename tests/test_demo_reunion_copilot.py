from app.services.demo_reunion_copilot_service import _topics, TOPIC_GUIDE


def test_detecta_cruce_glosas_cartera():
    topics = _topics("¿Las glosas se relacionan con cartera?", "glosas")
    assert "glosas" in topics
    assert "facturacion" in topics


def test_contexto_activo_se_conserva():
    assert _topics("¿Qué puede demostrar?", "rrhh")[0] == "rrhh"


def test_detecta_procesos_flujos_y_cuellos():
    topics = _topics("¿Dónde hay reprocesos, errores, tiempos de espera y cuellos de botella en el flujo?", "operaciones")
    assert "operaciones" in topics


def test_catalogo_cubre_seis_frentes():
    assert set(TOPIC_GUIDE) == {"facturacion", "glosas", "rrhh", "operaciones", "compras", "sistemas"}
    assert all(v["need"] for v in TOPIC_GUIDE.values())
