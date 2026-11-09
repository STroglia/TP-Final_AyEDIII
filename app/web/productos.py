"""Gestión de productos y categorías (solo representantes)."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.database import db_session
from app.errores import ErrorDeNegocio, ValidacionError
from app.services import ProductoService, TicketService
from app.web.seguridad import login_requerido, solo_representantes

bp = Blueprint("productos", __name__, url_prefix="/productos")

# Valor de la opción "+ Crear nuevo…" en los selectores de tipo y categoría.
NUEVO = "__nuevo__"


@bp.get("/catalogo")
@login_requerido
def catalogo():
    """Catálogo de consulta (todos los usuarios): productos agrupados por tipo."""
    servicio = ProductoService(db_session)
    busqueda = request.args.get("q", "").strip()
    productos = servicio.listar_productos(busqueda=busqueda or None)
    grupos = [(tipo, [p for p in productos if p.tipo_codigo == tipo.codigo]) for tipo in servicio.listar_tipos()]
    return render_template(
        "productos/catalogo.html",
        grupos=[(tipo, lista) for tipo, lista in grupos if lista],
        busqueda=busqueda,
        total=len(productos),
    )


@bp.get("/")
@solo_representantes
def lista():
    servicio = ProductoService(db_session)
    filtros = {
        "tipo": request.args.get("tipo") or None,
        "categoria_id": request.args.get("categoria") or None,
        "busqueda": request.args.get("q", "").strip() or None,
    }
    try:
        productos = servicio.listar_productos(**filtros)
    except ErrorDeNegocio as error:
        flash(str(error), "error")
        productos = servicio.listar_productos()
    return render_template(
        "productos/lista.html", productos=productos, categorias=servicio.listar_categorias(), filtros=filtros,
        por_tipo=TicketService(db_session).tickets_por_tipo_producto(),
    )


def _ticket_a_vincular():
    volver = request.args.get("volver", "")
    return int(volver[7:]) if volver.startswith("ticket-") and volver[7:].isdigit() else None


def _destino_volver() -> str:
    """A dónde volver después de guardar: catálogo, un ticket o (por defecto) la gestión de productos."""
    volver = request.args.get("volver", "")
    if volver == "catalogo":
        return url_for("productos.catalogo")
    if volver.startswith("ticket-") and volver[7:].isdigit():
        return url_for("tickets.detalle", numero=int(volver[7:]))
    return url_for("productos.lista")


def _formulario(producto=None):
    servicio = ProductoService(db_session)
    datos = {
        # Al crear, se puede llegar con nombre y tipo precargados (p. ej. un producto que escribió un cliente).
        "nombre": producto.nombre if producto else request.args.get("nombre", "").strip(),
        "tipo": producto.tipo.name if producto else request.args.get("tipo", "").strip(),
        "categoria_id": str(producto.categoria_id or "") if producto else "",
        "tipo_nuevo": "",
        "categoria_nueva": "",
    }
    destino = _destino_volver()
    if request.method == "POST":
        datos = {campo: request.form.get(campo, "").strip() for campo in datos}
        # "+ Crear nuevo…": el tipo / la categoría se crean junto con el producto.
        tipo_nuevo = datos["tipo_nuevo"] if datos["tipo"] == NUEVO else None
        categoria_nueva = datos["categoria_nueva"] if datos["categoria_id"] == NUEVO else None
        try:
            if datos["tipo"] == NUEVO and not tipo_nuevo:
                raise ValidacionError("Escribí el nombre del nuevo tipo de producto.")
            if datos["categoria_id"] == NUEVO and not categoria_nueva:
                raise ValidacionError("Escribí el nombre de la nueva categoría.")
            extra = {"tipo_nuevo": tipo_nuevo, "categoria_nueva": categoria_nueva}
            if producto is None:
                nuevo = servicio.registrar_producto(datos["nombre"], datos["tipo"], datos["categoria_id"], **extra)
                numero = _ticket_a_vincular()
                if numero is not None:
                    # Se registró desde un ticket con producto escrito por el cliente: queda vinculado.
                    try:
                        TicketService(db_session).vincular_producto(numero, g.usuario, nuevo.id_producto)
                        flash(f"Producto «{nuevo.nombre}» registrado y vinculado al ticket #{numero}.", "exito")
                    except ErrorDeNegocio as error:
                        flash(f"Producto «{nuevo.nombre}» registrado, pero no se pudo vincular: {error}", "error")
                else:
                    flash(f"Producto «{nuevo.nombre}» registrado.", "exito")
            else:
                servicio.actualizar_producto(
                    producto.id_producto, datos["nombre"], datos["tipo"], datos["categoria_id"], **extra
                )
                flash("Producto actualizado.", "exito")
            return redirect(destino)
        except ErrorDeNegocio as error:
            flash(str(error), "error")
    return render_template(
        "productos/form.html", datos=datos, producto=producto, categorias=servicio.listar_categorias(),
        destino=destino, NUEVO=NUEVO,
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@solo_representantes
def nuevo():
    return _formulario()


@bp.route("/<int:producto_id>/editar", methods=["GET", "POST"])
@solo_representantes
def editar(producto_id: int):
    return _formulario(ProductoService(db_session).obtener(producto_id))


@bp.post("/tipos")
@solo_representantes
def crear_tipo():
    try:
        tipo = ProductoService(db_session).crear_tipo(request.form.get("nombre", ""))
        flash(f"Tipo de producto «{tipo.nombre}» creado.", "exito")
    except ErrorDeNegocio as error:
        flash(str(error), "error")
    return redirect(request.referrer or url_for("productos.lista"))


@bp.post("/categorias")
@solo_representantes
def crear_categoria():
    try:
        categoria = ProductoService(db_session).crear_categoria(request.form.get("nombre", ""))
        flash(f"Categoría «{categoria.nombre}» creada.", "exito")
    except ErrorDeNegocio as error:
        flash(str(error), "error")
    return redirect(request.referrer or url_for("productos.lista"))
