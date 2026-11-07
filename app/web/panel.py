"""Pantalla inicial (panel) con el resumen de tickets y notificaciones."""
from flask import Blueprint, g, render_template

from app.database import db_session
from app.services import NotificacionService, TicketService
from app.web.seguridad import login_requerido

bp = Blueprint("panel", __name__)


@bp.get("/")
@login_requerido
def inicio():
    tickets = TicketService(db_session)
    return render_template(
        "panel.html",
        resumen=tickets.estadisticas(g.usuario),
        mis_asignados=tickets.estadisticas(g.usuario, solo_mios=True) if g.usuario.es_representante else None,
        en_cola=tickets.contar_cola() if g.usuario.es_representante else 0,
        recientes=tickets.listar(g.usuario)[:6],
        avisos=NotificacionService(db_session).listar(g.usuario, limite=5),
    )
