"""Configuración de SQLAlchemy.

- `Base`: clase de la que heredan todos los modelos (tablas).
- `db_session`: sesión que usa la aplicación web (una por petición).
- `iniciar_base_de_datos()`: conecta con la base y crea las tablas si no existen.
"""
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    """Clase base de todos los modelos del sistema."""


# Sesión "por hilo": Flask atiende cada petición en un hilo y al final la cerramos.
db_session = scoped_session(sessionmaker(expire_on_commit=False))


def crear_engine(url: str) -> Engine:
    """Crea el motor de conexión. Para SQLite activa las claves foráneas."""
    opciones = {}
    es_sqlite = url.startswith("sqlite")
    if es_sqlite:
        opciones["connect_args"] = {"check_same_thread": False}
        if url in ("sqlite://", "sqlite:///:memory:"):
            # Base en memoria (tests): todas las conexiones comparten la misma base.
            opciones["poolclass"] = StaticPool

    engine = create_engine(url, **opciones)

    if es_sqlite:
        @event.listens_for(engine, "connect")
        def _activar_claves_foraneas(conexion, _registro):
            cursor = conexion.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def crear_tablas(engine: Engine) -> None:
    """Crea todas las tablas definidas en los modelos (si no existen)."""
    import app.models  # noqa: F401  (importarlos los registra en Base.metadata)

    Base.metadata.create_all(engine)
    _actualizar_esquema(engine)


def _actualizar_esquema(engine: Engine) -> None:
    """Agrega a una base ya existente las columnas nuevas que `create_all` no crea.

    - tickets.tipo_producto: se completa con el tipo del producto de cada ticket.
    - tickets.producto_otro: producto escrito por el cliente (queda vacío en los tickets viejos).
    """
    columnas = {c["name"] for c in inspect(engine).get_columns("tickets")}
    if "creado_por_id" not in columnas:
        with engine.begin() as conexion:
            conexion.execute(text("ALTER TABLE tickets ADD COLUMN creado_por_id INTEGER REFERENCES usuarios(id)"))
            # Tickets existentes: se deduce quién lo abrió por el aviso que generó al crearse.
            # "X abrió el ticket #N" -> lo abrió el cliente; "Se creó el ticket #N" -> un representante.
            conexion.execute(text(
                "UPDATE tickets SET creado_por_id = cliente_id WHERE EXISTS (SELECT 1 FROM notificaciones n "
                "WHERE n.ticket_id = tickets.numero_ticket AND n.mensaje LIKE '% abrió el ticket #%')"
            ))
            conexion.execute(text(
                "UPDATE tickets SET creado_por_id = representante_id WHERE creado_por_id IS NULL AND EXISTS "
                "(SELECT 1 FROM notificaciones n WHERE n.ticket_id = tickets.numero_ticket "
                "AND n.mensaje LIKE 'Se creó el ticket #%')"
            ))
    if "producto_otro" not in columnas:
        with engine.begin() as conexion:
            conexion.execute(text("ALTER TABLE tickets ADD COLUMN producto_otro VARCHAR(120)"))
    if "tipo_producto" not in columnas:
        with engine.begin() as conexion:
            conexion.execute(text("ALTER TABLE tickets ADD COLUMN tipo_producto VARCHAR(27)"))
            conexion.execute(text(
                "UPDATE tickets SET tipo_producto = "
                "(SELECT p.tipo FROM productos p WHERE p.id_producto = tickets.producto_id) "
                "WHERE producto_id IS NOT NULL"
            ))


def iniciar_base_de_datos(url: str) -> Engine:
    """Conecta la sesión de la aplicación con la base indicada y crea las tablas."""
    engine = crear_engine(url)
    crear_tablas(engine)
    db_session.remove()
    db_session.configure(bind=engine)
    return engine
