"""Capa web: registra rutas, filtros de plantillas y manejo de errores."""
from flask import g, render_template
from markupsafe import Markup

from app.errores import NoEncontradoError, PermisoError
from app.models import EstadoTicket
from app.services import NotificacionService, ProductoService, TicketService
from app.database import db_session
from app.utilidades import fecha_relativa, formatear_fecha, resumir
from app.web import seguridad
from app.web.iconos import icono


def registrar_web(app) -> None:
    seguridad.init_app(app)

    from app.web.auth import bp as auth_bp
    from app.web.notificaciones import bp as notificaciones_bp
    from app.web.panel import bp as panel_bp
    from app.web.productos import bp as productos_bp
    from app.web.tickets import bp as tickets_bp
    from app.web.usuarios import bp as usuarios_bp

    for blueprint in (auth_bp, panel_bp, tickets_bp, usuarios_bp, productos_bp, notificaciones_bp):
        app.register_blueprint(blueprint)

    # ------------------------------------------------ plantillas
    app.add_template_filter(formatear_fecha, "fecha")
    app.add_template_filter(fecha_relativa, "hace")
    app.add_template_filter(resumir, "resumir")
    app.add_template_global(lambda nombre, clase="icono": Markup(icono(nombre, clase)), "icono")
    app.add_template_global(seguridad.csrf_token, "csrf_token")

    @app.context_processor
    def variables_globales():
        no_leidas = en_cola = 0
        if g.get("usuario") is not None:
            no_leidas = NotificacionService(db_session).contar_no_leidas(g.usuario)
            if g.usuario.es_representante:
                en_cola = TicketService(db_session).contar_cola()
        return {
            "usuario_actual": g.get("usuario"),
            "notificaciones_no_leidas": no_leidas,
            "tickets_en_cola": en_cola,
            "EstadoTicket": EstadoTicket,
            # Tipos de producto (tabla): se consultan solo si la plantilla los usa.
            "tipos_producto": _TiposPerezosos(),
        }

    class _TiposPerezosos:
        """Se puede recorrer con {% for t in tipos_producto %}; consulta la base recién al usarlo."""

        def __iter__(self):
            return iter(ProductoService(db_session).listar_tipos())

    # ------------------------------------------------ errores
    def pagina_error(codigo: int, titulo: str, mensaje: str):
        return render_template("error.html", codigo=codigo, titulo=titulo, mensaje=mensaje), codigo

    @app.errorhandler(400)
    def error_400(error):
        return pagina_error(400, "Solicitud inválida", getattr(error, "description", "") or "")

    @app.errorhandler(403)
    @app.errorhandler(PermisoError)
    def error_403(error):
        mensaje = str(error) if isinstance(error, PermisoError) else "No tenés permiso para ver esta página."
        return pagina_error(403, "Acceso denegado", mensaje)

    @app.errorhandler(404)
    @app.errorhandler(NoEncontradoError)
    def error_404(error):
        mensaje = str(error) if isinstance(error, NoEncontradoError) else "La página que buscás no existe."
        return pagina_error(404, "No encontrado", mensaje)

    @app.errorhandler(500)
    def error_500(_error):
        db_session.rollback()
        return pagina_error(500, "Algo salió mal", "Ocurrió un error inesperado. Intentá de nuevo.")
