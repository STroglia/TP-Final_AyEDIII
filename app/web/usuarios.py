"""Gestión de usuarios: clientes y representantes (solo representantes)."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.database import db_session
from app.errores import ErrorDeNegocio
from app.services import UsuarioService
from app.web.seguridad import solo_representantes

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")

TIPOS = {"cliente": "Cliente", "representante": "Representante"}


@bp.get("/")
@solo_representantes
def lista():
    servicio = UsuarioService(db_session)
    tipo = request.args.get("tipo") if request.args.get("tipo") in TIPOS else None
    busqueda = request.args.get("q", "").strip()
    return render_template(
        "usuarios/lista.html",
        usuarios=servicio.listar_usuarios(tipo, busqueda),
        tipo=tipo,
        busqueda=busqueda,
        conteo=servicio.contar(),
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@solo_representantes
def nuevo():
    tipo = request.args.get("tipo", "cliente")
    if tipo not in TIPOS:
        abort(404)
    volver = request.args.get("volver")  # "ticket": vuelve al alta de ticket con el cliente elegido
    datos = {"nombre": "", "email": "", "telefono": "", "dni": ""}

    if request.method == "POST":
        datos = {campo: request.form.get(campo, "").strip() for campo in datos}
        servicio = UsuarioService(db_session)
        try:
            if tipo == "cliente":
                usuario = servicio.registrar_cliente(
                    datos["nombre"], datos["email"], request.form.get("password", ""), datos["dni"], datos["telefono"]
                )
            else:
                usuario = servicio.registrar_representante(
                    datos["nombre"], datos["email"], request.form.get("password", ""), datos["telefono"]
                )
            flash(f"{TIPOS[tipo]} «{usuario.nombre}» registrado correctamente.", "exito")
            if volver == "ticket" and tipo == "cliente":
                return redirect(url_for("tickets.nuevo", cliente_id=usuario.id))
            return redirect(url_for("usuarios.lista", tipo=tipo))
        except ErrorDeNegocio as error:
            flash(str(error), "error")

    return render_template("usuarios/form.html", datos=datos, tipo=tipo, usuario=None, volver=volver)


@bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@solo_representantes
def editar(usuario_id: int):
    servicio = UsuarioService(db_session)
    usuario = servicio.obtener(usuario_id)
    tipo = "cliente" if usuario.es_cliente else "representante"
    datos = {
        "nombre": usuario.nombre,
        "email": usuario.email,
        "telefono": usuario.telefono or "",
        "dni": getattr(usuario, "dni", None) or "",
    }
    if request.method == "POST":
        datos = {campo: request.form.get(campo, "").strip() for campo in datos}
        try:
            servicio.actualizar(
                usuario.id, datos["nombre"], datos["email"], datos["telefono"], datos["dni"],
                request.form.get("password") or None,
            )
            flash("Datos actualizados.", "exito")
            return redirect(url_for("usuarios.lista", tipo=tipo))
        except ErrorDeNegocio as error:
            flash(str(error), "error")

    return render_template("usuarios/form.html", datos=datos, tipo=tipo, usuario=usuario, volver=None)


@bp.post("/<int:usuario_id>/estado")
@solo_representantes
def cambiar_estado(usuario_id: int):
    activar = request.form.get("activo") == "1"
    try:
        usuario = UsuarioService(db_session).cambiar_activo(usuario_id, activar, actor=g.usuario)
        flash(f"«{usuario.nombre}» {'reactivado' if activar else 'dado de baja'}.", "exito")
    except ErrorDeNegocio as error:
        flash(str(error), "error")
    return redirect(request.referrer or url_for("usuarios.lista"))
