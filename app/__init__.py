"""TECNOSOL Mar del Plata — Sistema de Ticketing (TP "Ticket to Ride").

`create_app()` arma la aplicación web: configuración, base de datos, rutas y plantillas.
"""
from typing import Optional

from flask import Flask

from app.config import CARPETA_INSTANCIA, ConfigBase, cargar_clave_secreta
from app.database import db_session, iniciar_base_de_datos


def create_app(config: Optional[dict] = None) -> Flask:
    app = Flask(__name__, instance_path=str(CARPETA_INSTANCIA))
    app.config.from_object(ConfigBase)
    if config:
        app.config.update(config)

    CARPETA_INSTANCIA.mkdir(parents=True, exist_ok=True)
    if not app.config.get("TESTING"):
        _registrar_errores_en_archivo(app)
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = cargar_clave_secreta(CARPETA_INSTANCIA)

    # Base de datos (si existe la base con el nombre anterior, se renombra para no perder datos)
    base_anterior = CARPETA_INSTANCIA / "ticket_to_ride.db"
    base_nueva = CARPETA_INSTANCIA / "tecnosol.db"
    usa_base_por_defecto = app.config["DATABASE_URL"] == ConfigBase.DATABASE_URL
    if usa_base_por_defecto and base_anterior.exists() and not base_nueva.exists():
        base_anterior.rename(base_nueva)
    iniciar_base_de_datos(app.config["DATABASE_URL"])

    @app.teardown_appcontext
    def cerrar_sesion_db(_error=None):
        db_session.remove()

    # Capa web
    from app.web import registrar_web

    registrar_web(app)

    # Datos de ejemplo (solo si la base está vacía)
    if app.config["CARGAR_DATOS_EJEMPLO"]:
        from app.datos_ejemplo import cargar_si_esta_vacia

        with app.app_context():
            cargar_si_esta_vacia(db_session)

    return app


def _registrar_errores_en_archivo(app: Flask) -> None:
    """Guarda en instancia/errores.log cada error inesperado (los "Error 500") con su detalle.

    Sirve para diagnosticar problemas en otra computadora: el archivo queda en el pen drive.
    Al arrancar también se anota con qué versión de Python y de las librerías se ejecuta.
    """
    import logging
    import platform
    import sys
    from importlib.metadata import PackageNotFoundError, version

    def version_de(paquete: str) -> str:
        try:
            return version(paquete)
        except PackageNotFoundError:
            return "?"

    try:
        archivo = logging.FileHandler(CARPETA_INSTANCIA / "errores.log", encoding="utf-8")
    except OSError:
        return  # carpeta de solo lectura: se sigue sin registro
    archivo.setLevel(logging.INFO)
    archivo.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    app.logger.addHandler(archivo)
    app.logger.setLevel(logging.INFO)
    app.logger.info(
        "App iniciada en %s · Python %s · Flask %s · Werkzeug %s · SQLAlchemy %s",
        platform.node(), sys.version.split()[0],
        version_de("flask"), version_de("werkzeug"), version_de("sqlalchemy"),
    )
