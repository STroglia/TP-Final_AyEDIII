"""Configuración de la aplicación."""
import secrets
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # Ejecutable (TECNOSOL.exe): la base y la clave quedan al lado del .exe.
    RAIZ = Path(sys.executable).resolve().parent
else:
    RAIZ = Path(__file__).resolve().parent.parent  # carpeta del proyecto (D:\TP Final)
CARPETA_INSTANCIA = RAIZ / "instancia"  # base de datos y clave secreta (se crean solas)


class ConfigBase:
    DATABASE_URL = "sqlite:///" + (CARPETA_INSTANCIA / "tecnosol.db").as_posix()
    SECRET_KEY = None  # si no se define, se genera y guarda en instancia/clave_secreta.txt
    CARGAR_DATOS_EJEMPLO = True  # carga datos de ejemplo la primera vez (base vacía)
    CSRF_HABILITADO = True  # protección de formularios
    MOSTRAR_USUARIOS_DEMO = True  # muestra los usuarios de prueba en el login
    TEMPLATES_AUTO_RELOAD = True  # si se edita una plantilla HTML, se ve al recargar (sin reiniciar)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


def cargar_clave_secreta(carpeta: Path) -> str:
    """Lee la clave secreta de la instancia o crea una nueva la primera vez."""
    archivo = carpeta / "clave_secreta.txt"
    if archivo.exists():
        clave = archivo.read_text(encoding="utf-8").strip()
        if clave:
            return clave
    clave = secrets.token_hex(32)
    archivo.write_text(clave, encoding="utf-8")
    return clave
