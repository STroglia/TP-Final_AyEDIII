"""Login y logout (RNF: el sistema deberá gestionar seguridad)."""
from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for

from app.database import db_session
from app.errores import ErrorDeNegocio
from app.services import UsuarioService
from app.web.seguridad import cerrar_sesion, destino_seguro, iniciar_sesion, login_requerido

bp = Blueprint("auth", __name__)

USUARIOS_DEMO = [
    ("Representante", "admin@tickettoride.com", "admin123"),
    ("Representante", "laura@tickettoride.com", "laura123"),
    ("Cliente", "juan@mail.com", "cliente123"),
    ("Cliente", "maria@mail.com", "cliente123"),
]


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.usuario is not None:
        return redirect(url_for("panel.inicio"))

    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        usuario = UsuarioService(db_session).autenticar(email, request.form.get("password", ""))
        if usuario is not None:
            iniciar_sesion(usuario)
            flash(f"¡Bienvenido/a, {usuario.nombre.split()[0]}!", "exito")
            return redirect(destino_seguro(request.args.get("next")) or url_for("panel.inicio"))
        flash("Email o contraseña incorrectos.", "error")

    demo = USUARIOS_DEMO if current_app.config.get("MOSTRAR_USUARIOS_DEMO") else []
    return render_template("auth/login.html", email=email, usuarios_demo=demo)


@bp.route("/registro", methods=["GET", "POST"])
def registro():
    """Alta pública de una cuenta nueva desde la pantalla de ingreso.

    Solo crea CLIENTES. Los representantes los da de alta otro representante desde
    /usuarios (si el registro público permitiera elegir "representante", cualquiera
    podría darse acceso a todos los tickets y a la gestión de usuarios).
    """
    if g.usuario is not None:
        return redirect(url_for("panel.inicio"))

    datos = {"nombre": "", "email": "", "telefono": "", "dni": ""}
    if request.method == "POST":
        datos = {campo: request.form.get(campo, "").strip() for campo in datos}
        password = request.form.get("password", "")
        try:
            if password != request.form.get("password2", ""):
                raise ErrorDeNegocio("Las contraseñas no coinciden.")
            # Aunque el formulario se manipule para enviar otro rol, siempre se crea un cliente.
            usuario = UsuarioService(db_session).registrar_cliente(
                datos["nombre"], datos["email"], password, datos["dni"], datos["telefono"]
            )
            iniciar_sesion(usuario)
            flash(f"¡Cuenta creada! Bienvenido/a, {usuario.nombre.split()[0]}.", "exito")
            return redirect(url_for("panel.inicio"))
        except ErrorDeNegocio as error:
            flash(str(error), "error")

    return render_template("auth/registro.html", datos=datos)


@bp.route("/cuenta/contrasena", methods=["GET", "POST"])
@login_requerido
def cambiar_password():
    """Cualquier usuario (cliente o representante) cambia su propia contraseña."""
    if request.method == "POST":
        try:
            UsuarioService(db_session).cambiar_password(
                g.usuario,
                request.form.get("actual", ""),
                request.form.get("nueva", ""),
                request.form.get("nueva2", ""),
            )
            flash("Tu contraseña se actualizó correctamente.", "exito")
            return redirect(url_for("panel.inicio"))
        except ErrorDeNegocio as error:
            flash(str(error), "error")
    return render_template("auth/password.html")


@bp.post("/logout")
def logout():
    if g.usuario is not None:
        g.usuario.logout()
    cerrar_sesion()
    flash("Cerraste sesión correctamente.", "info")
    return redirect(url_for("auth.login"))
