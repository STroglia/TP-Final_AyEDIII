"""Fixtures compartidas por todos los tests.

Cada test usa una base de datos SQLite *en memoria* nueva y vacía: los tests
nunca tocan la base real (instancia/tecnosol.db) y no dependen entre sí.
"""
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import sessionmaker

from app import create_app
from app.database import crear_engine, crear_tablas, db_session
from app.services import NotificacionService, ProductoService, TicketService, UsuarioService

PASSWORD = "clave123"


# ---------------------------------------------------------------- capa de servicios
@pytest.fixture
def session():
    engine = crear_engine("sqlite://")
    crear_tablas(engine)
    sesion = sessionmaker(bind=engine, expire_on_commit=False)()
    yield sesion
    sesion.close()
    engine.dispose()


@pytest.fixture
def usuarios(session):
    return UsuarioService(session)


@pytest.fixture
def tickets(session):
    return TicketService(session)


@pytest.fixture
def productos(session):
    return ProductoService(session)


@pytest.fixture
def notificaciones(session):
    return NotificacionService(session)


@pytest.fixture
def representante(usuarios):
    return usuarios.registrar_representante("Ana Soporte", "ana@soporte.com", PASSWORD)


@pytest.fixture
def otro_representante(usuarios):
    return usuarios.registrar_representante("Bruno Soporte", "bruno@soporte.com", PASSWORD)


@pytest.fixture
def cliente(usuarios):
    return usuarios.registrar_cliente("Carla Cliente", "carla@mail.com", PASSWORD, dni="30111222")


@pytest.fixture
def otro_cliente(usuarios):
    return usuarios.registrar_cliente("Diego Cliente", "diego@mail.com", PASSWORD)


@pytest.fixture
def categoria(productos):
    return productos.crear_categoria("Heladeras")


@pytest.fixture
def producto(productos, categoria):
    return productos.registrar_producto("Heladera No Frost 360L", "LINEA_BLANCA", categoria.id_categoria)


@pytest.fixture
def ticket(tickets, representante, cliente):
    return tickets.crear_ticket(representante, cliente.id, "La heladera no enfría desde ayer.")


# ---------------------------------------------------------------- capa web
@pytest.fixture
def app():
    aplicacion = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "clave-solo-para-tests",
            "DATABASE_URL": "sqlite://",
            "CARGAR_DATOS_EJEMPLO": False,
            "CSRF_HABILITADO": False,
            "MOSTRAR_USUARIOS_DEMO": False,
        }
    )
    yield aplicacion
    db_session.remove()


@pytest.fixture
def web(app):
    """Cliente HTTP de prueba (simula el navegador)."""
    return app.test_client()


@pytest.fixture
def datos_web(app):
    """Carga un representante, dos clientes y un producto en la base de la app."""
    with app.app_context():
        usuarios = UsuarioService(db_session)
        productos = ProductoService(db_session)
        rep = usuarios.registrar_representante("Ana Soporte", "ana@soporte.com", PASSWORD)
        cli = usuarios.registrar_cliente("Carla Cliente", "carla@mail.com", PASSWORD, dni="30111222")
        otro = usuarios.registrar_cliente("Diego Cliente", "diego@mail.com", PASSWORD)
        cat = productos.crear_categoria("Lavarropas")
        prod = productos.registrar_producto("Lavarropas 8kg", "LINEA_BLANCA", cat.id_categoria)
        datos = SimpleNamespace(
            rep_id=rep.id, cli_id=cli.id, otro_id=otro.id, cat_id=cat.id_categoria, prod_id=prod.id_producto
        )
    return datos


@pytest.fixture
def login(web):
    """login("ana@soporte.com") inicia sesión en el cliente de prueba."""

    def _login(email, password=PASSWORD):
        return web.post("/login", data={"email": email, "password": password}, follow_redirects=True)

    return _login
