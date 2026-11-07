"""Pantallas de tickets: listado, alta (CU001), detalle (CU002) e hitos (CU003)."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.database import db_session
from app.errores import ErrorDeNegocio, ValidacionError
from app.services import NotificacionService, ProductoService, TicketService, UsuarioService
from app.utilidades import paginar
from app.web.seguridad import login_requerido, solo_representantes

bp = Blueprint("tickets", __name__, url_prefix="/tickets")
POR_PAGINA = 10  # tickets por página en el listado
OTRO = "OTRO"  # valor de la opción "no lo encuentro" en los selectores de tipo / producto


@bp.get("/")
@login_requerido
def lista():
    servicio = TicketService(db_session)
    filtros = {
        "estado": request.args.get("estado", "").upper() or None,
        "busqueda": request.args.get("q", "").strip() or None,
        "solo_mios": request.args.get("mios") == "1" and g.usuario.es_representante,
        "orden": request.args.get("orden", "recientes"),
        "periodo": request.args.get("periodo", "").strip() or None,
        "en_cola": request.args.get("cola") == "1" and g.usuario.es_representante,
    }
    if filtros["en_cola"] and "orden" not in request.args:
        filtros["orden"] = "antiguos"  # la cola se atiende por orden de llegada
    try:
        tickets = servicio.listar(g.usuario, **filtros)
    except ErrorDeNegocio as error:
        flash(str(error), "error")
        filtros["estado"] = filtros["periodo"] = None
        tickets = servicio.listar(g.usuario, **filtros)

    # Búsqueda por número exacto: ir directo al ticket.
    texto = (filtros["busqueda"] or "").lstrip("#").strip()
    if texto.isdigit() and len(tickets) == 1:
        return redirect(url_for("tickets.detalle", numero=tickets[0].numero_ticket))

    pagina = paginar(tickets, request.args.get("pagina", 1), POR_PAGINA)
    return render_template(
        "tickets/lista.html",
        tickets=pagina["elementos"],
        pagina=pagina,
        args_pagina={k: v for k, v in request.args.items() if k != "pagina"},
        filtros=filtros,
        resumen=servicio.estadisticas(g.usuario, solo_mios=filtros["solo_mios"]),
        en_cola=servicio.contar_cola() if g.usuario.es_representante else 0,
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@login_requerido
def nuevo():
    """Representante: elige el cliente. Cliente: el ticket queda a su nombre."""
    datos = {
        "cliente_id": request.args.get("cliente_id", ""),
        "tipo_producto": request.args.get("tipo", ""),
        "producto_id": request.args.get("producto_id", ""),
        "producto_otro": "",
        "descripcion": "",
    }
    if request.method == "POST":
        datos = {campo: request.form.get(campo, "").strip() for campo in datos}
        # "OTRO": no se encontró el tipo o el producto en el catálogo y se escribe a mano.
        escribe_producto = OTRO in (datos["tipo_producto"], datos["producto_id"])
        try:
            if escribe_producto and not datos["producto_otro"]:
                raise ValidacionError("Escribí qué producto es.")
            ticket = TicketService(db_session).crear_ticket(
                g.usuario, datos["cliente_id"], datos["descripcion"],
                None if escribe_producto else datos["producto_id"] or None,
                None if datos["tipo_producto"] == OTRO else datos["tipo_producto"] or None,
                exigir_producto=True,
                producto_otro=datos["producto_otro"] if escribe_producto else None,
            )
            if g.usuario.es_cliente:
                flash(
                    f"Ticket #{ticket.numero_ticket} creado. Quedó en la cola de atención: "
                    "un representante lo va a tomar y te va a responder por acá.",
                    "exito",
                )
            else:
                flash(f"Ticket #{ticket.numero_ticket} creado. Estado: Abierto.", "exito")
            return redirect(url_for("tickets.detalle", numero=ticket.numero_ticket))
        except ErrorDeNegocio as error:
            flash(str(error), "error")

    return render_template(
        "tickets/nuevo.html",
        datos=datos,
        clientes=UsuarioService(db_session).listar_clientes(solo_activos=True) if g.usuario.es_representante else [],
        productos=ProductoService(db_session).listar_productos(),
    )


@bp.get("/<int:numero>")
@login_requerido
def detalle(numero: int):
    ticket = TicketService(db_session).obtener(numero, g.usuario)
    NotificacionService(db_session).marcar_leidas_de_ticket(g.usuario, ticket)
    representantes = (
        UsuarioService(db_session).listar_representantes(solo_activos=True) if g.usuario.es_representante else []
    )
    productos = (
        ProductoService(db_session).listar_productos() if g.usuario.es_representante and ticket.producto_pendiente else []
    )
    return render_template(
        "tickets/detalle.html", ticket=ticket, representantes=representantes, productos=productos
    )


@bp.post("/<int:numero>/producto")
@solo_representantes
def vincular_producto(numero: int):
    return _accion(numero, "vincular_producto", "Producto vinculado al ticket.", request.form.get("producto_id", ""))


@bp.post("/<int:numero>/hitos")
@login_requerido
def registrar_hito(numero: int):
    try:
        TicketService(db_session).registrar_hito(numero, g.usuario, request.form.get("mensaje", ""))
        flash("Hito registrado. Se notificó al otro participante.", "exito")
    except ErrorDeNegocio as error:
        flash(str(error), "error")
    return redirect(url_for("tickets.detalle", numero=numero) + "#historial")


def _accion(numero: int, metodo: str, mensaje_ok: str, *args):
    try:
        getattr(TicketService(db_session), metodo)(numero, g.usuario, *args)
        flash(mensaje_ok, "exito")
    except ErrorDeNegocio as error:
        flash(str(error), "error")
    return redirect(url_for("tickets.detalle", numero=numero))


@bp.post("/<int:numero>/cerrar")
@login_requerido
def cerrar(numero: int):
    return _accion(numero, "cerrar", f"El ticket #{numero} quedó cerrado.")


@bp.post("/<int:numero>/reabrir")
@login_requerido
def reabrir(numero: int):
    return _accion(numero, "reabrir", f"El ticket #{numero} se reabrió.")


@bp.post("/<int:numero>/tomar")
@solo_representantes
def tomar(numero: int):
    return _accion(numero, "tomar", f"Tomaste el ticket #{numero}. Ya está asignado a vos y en proceso.")


@bp.post("/cola/tomar-siguiente")
@solo_representantes
def tomar_siguiente():
    try:
        ticket = TicketService(db_session).tomar_siguiente(g.usuario)
        flash(f"Tomaste el ticket #{ticket.numero_ticket} (el que más tiempo esperaba en la cola).", "exito")
        return redirect(url_for("tickets.detalle", numero=ticket.numero_ticket))
    except ErrorDeNegocio as error:
        flash(str(error), "info")
        return redirect(url_for("tickets.lista", cola=1))


@bp.post("/<int:numero>/en-proceso")
@solo_representantes
def en_proceso(numero: int):
    return _accion(numero, "poner_en_proceso", f"El ticket #{numero} está en proceso.")


@bp.post("/<int:numero>/asignar")
@solo_representantes
def asignar(numero: int):
    return _accion(numero, "asignar", "Representante asignado.", request.form.get("representante_id", ""))
