"""Seguridad de la capa web: sesión de usuario, permisos y protección CSRF."""
import secrets
from functools import wraps
from typing import Optional
from urllib.parse import urlparse

from flask import abort, flash, g, redirect, request, session, url_for

from app.database import db_session
from app.models import Usuario


def init_app(app) -> None:
    @app.before_request
    def cargar_usuario_actual():
        """Antes de cada petición, carga en `g.usuario` al usuario logueado (o None)."""
        g.usuario = None
        usuario_id = session.get("usuario_id")
        if usuario_id is not None:
            usuario = db_session.get(Usuario, usuario_id)
            if usuario is not None and usuario.activo:
                g.usuario = usuario
            else:
                session.pop("usuario_id", None)

    @app.before_request
    def verificar_csrf():
        """Todo formulario (POST) debe traer el token que generó el servidor."""
        if not app.config.get("CSRF_HABILITADO") or request.method != "POST":
            return None
        esperado = session.get("csrf_token")
        recibido = request.form.get("csrf_token", "")
        if not esperado or not secrets.compare_digest(esperado, recibido):
            abort(400, description="El formulario venció. Recargá la página e intentá de nuevo.")
        return None


def csrf_token() -> str:
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


def iniciar_sesion(usuario: Usuario) -> None:
    session.clear()
    session["usuario_id"] = usuario.id
    session.permanent = False


def cerrar_sesion() -> None:
    session.clear()


def destino_seguro(destino: Optional[str]) -> Optional[str]:
    """Solo permite redirigir a rutas internas (evita redirecciones a otros sitios)."""
    if not destino:
        return None
    partes = urlparse(destino)
    if partes.scheme or partes.netloc or not destino.startswith("/") or destino.startswith("//"):
        return None
    return destino


def login_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if g.get("usuario") is None:
            flash("Iniciá sesión para continuar.", "info")
            return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
        return vista(*args, **kwargs)

    return envoltura


def solo_representantes(vista):
    @wraps(vista)
    @login_requerido
    def envoltura(*args, **kwargs):
        if not g.usuario.es_representante:
            abort(403)
        return vista(*args, **kwargs)

    return envoltura
