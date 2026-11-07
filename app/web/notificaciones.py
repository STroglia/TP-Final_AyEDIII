"""Bandeja de notificaciones del usuario logueado."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.database import db_session
from app.services import NotificacionService
from app.web.seguridad import login_requerido

bp = Blueprint("notificaciones", __name__, url_prefix="/notificaciones")


@bp.get("/")
@login_requerido
def lista():
    solo_no_leidas = request.args.get("filtro") == "no-leidas"
    servicio = NotificacionService(db_session)
    return render_template(
        "notificaciones/lista.html",
        notificaciones=servicio.listar(g.usuario, solo_no_leidas=solo_no_leidas),
        solo_no_leidas=solo_no_leidas,
    )


@bp.get("/<int:notificacion_id>/ir")
@login_requerido
def ir(notificacion_id: int):
    """Marca la notificación como leída y lleva al ticket correspondiente."""
    notificacion = NotificacionService(db_session).marcar_leida(notificacion_id, g.usuario)
    if notificacion.ticket_id:
        return redirect(url_for("tickets.detalle", numero=notificacion.ticket_id))
    return redirect(url_for("notificaciones.lista"))


@bp.post("/<int:notificacion_id>/leida")
@login_requerido
def marcar_leida(notificacion_id: int):
    NotificacionService(db_session).marcar_leida(notificacion_id, g.usuario)
    return redirect(request.referrer or url_for("notificaciones.lista"))


@bp.post("/leer-todas")
@login_requerido
def leer_todas():
    cantidad = NotificacionService(db_session).marcar_todas_leidas(g.usuario)
    flash(f"{cantidad} notificaciones marcadas como leídas." if cantidad else "No había notificaciones pendientes.", "info")
    return redirect(url_for("notificaciones.lista"))
