"""Iteración 6 (TDD) — Interfaz web: login, permisos y flujos completos desde el navegador."""
from app import create_app
from app.database import db_session
from app.models import EstadoTicket, Ticket


def _crear_ticket(web, datos, descripcion="El lavarropas pierde agua por abajo."):
    return web.post(
        "/tickets/nuevo",
        data={
            "cliente_id": datos.cli_id, "tipo_producto": "LINEA_BLANCA",
            "producto_id": datos.prod_id, "descripcion": descripcion,
        },
    )


class TestColaWeb:
    def _ticket_de_cliente(self, web, login, datos):
        login("carla@mail.com")
        web.post("/tickets/nuevo", data={
            "tipo_producto": "LINEA_BLANCA", "producto_id": datos.prod_id, "descripcion": "El lavarropas no centrifuga.",
        })
        web.post("/logout")
        login("ana@soporte.com")

    def test_la_cola_muestra_el_ticket_y_se_puede_tomar(self, app, web, datos_web, login):
        self._ticket_de_cliente(web, login, datos_web)
        html = web.get("/tickets/?cola=1").get_data(as_text=True)
        assert "Cola de tickets" in html and "#1" in html and "Tomar el siguiente" in html
        assert "Tomar ticket" in web.get("/tickets/1").get_data(as_text=True)
        web.post("/tickets/1/tomar")
        with app.app_context():
            ticket = db_session.get(Ticket, 1)
            assert ticket.representante_id == datos_web.rep_id and ticket.estado is EstadoTicket.EN_PROCESO

    def test_tomar_el_siguiente_lleva_al_ticket(self, web, datos_web, login):
        self._ticket_de_cliente(web, login, datos_web)
        respuesta = web.post("/tickets/cola/tomar-siguiente")
        assert respuesta.headers["Location"].endswith("/tickets/1")

    def test_el_panel_avisa_cuantos_hay_en_cola(self, web, datos_web, login):
        self._ticket_de_cliente(web, login, datos_web)
        assert "esperando en la cola" in web.get("/").get_data(as_text=True)

    def test_el_cliente_no_ve_la_cola(self, web, datos_web, login):
        login("carla@mail.com")
        assert web.post("/tickets/cola/tomar-siguiente").status_code == 403
        assert "Cola de tickets" not in web.get("/").get_data(as_text=True)


class TestProductosEnTickets:
    def test_el_alta_de_ticket_exige_tipo_y_producto(self, app, web, datos_web, login):
        login("ana@soporte.com")
        html = web.post(
            "/tickets/nuevo",
            data={"cliente_id": datos_web.cli_id, "descripcion": "El lavarropas pierde agua por abajo."},
        ).get_data(as_text=True)
        assert "Elegí el tipo de producto" in html
        with app.app_context():
            assert db_session.query(Ticket).count() == 0

    def test_el_ticket_guarda_tipo_y_producto(self, app, web, datos_web, login):
        login("ana@soporte.com")
        _crear_ticket(web, datos_web)
        with app.app_context():
            ticket = db_session.query(Ticket).one()
            assert ticket.tipo_producto.name == "LINEA_BLANCA"
            assert ticket.producto_id == datos_web.prod_id

    def test_el_cliente_puede_escribir_un_producto_que_no_esta(self, app, web, datos_web, login):
        login("carla@mail.com")
        respuesta = web.post("/tickets/nuevo", data={
            "tipo_producto": "OTRO", "producto_id": "OTRO", "producto_otro": "Freezer horizontal 300L",
            "descripcion": "El freezer no congela desde ayer.",
        })
        assert respuesta.status_code == 302
        with app.app_context():
            ticket = db_session.query(Ticket).one()
            assert ticket.producto_otro == "Freezer horizontal 300L"
            assert ticket.producto_id is None and ticket.tipo_producto is None

    def test_el_cliente_elige_tipo_y_escribe_el_producto(self, app, web, datos_web, login):
        login("carla@mail.com")
        web.post("/tickets/nuevo", data={
            "tipo_producto": "LINEA_BLANCA", "producto_id": "OTRO", "producto_otro": "Secarropas",
            "descripcion": "El secarropas no gira el tambor.",
        })
        with app.app_context():
            ticket = db_session.query(Ticket).one()
            assert ticket.tipo_producto.name == "LINEA_BLANCA" and ticket.producto_otro == "Secarropas"

    def test_si_elige_otro_tiene_que_escribirlo(self, app, web, datos_web, login):
        login("carla@mail.com")
        html = web.post("/tickets/nuevo", data={
            "tipo_producto": "OTRO", "producto_id": "OTRO", "descripcion": "El freezer no congela desde ayer.",
        }).get_data(as_text=True)
        assert "Escribí qué producto es" in html
        with app.app_context():
            assert db_session.query(Ticket).count() == 0

    def _ticket_con_producto_escrito(self, web, login):
        login("carla@mail.com")
        web.post("/tickets/nuevo", data={
            "tipo_producto": "LINEA_BLANCA", "producto_id": "OTRO", "producto_otro": "Secarropas",
            "descripcion": "El secarropas no gira el tambor.",
        })
        web.post("/logout")
        login("ana@soporte.com")

    def test_el_representante_debe_vincular_antes_de_cerrar(self, app, web, datos_web, login):
        self._ticket_con_producto_escrito(web, login)
        html = web.get("/tickets/1").get_data(as_text=True)
        assert "Falta vincular el producto" in html
        html = web.post("/tickets/1/cerrar", follow_redirects=True).get_data(as_text=True)
        assert "vinculá «Secarropas»" in html
        with app.app_context():
            assert db_session.get(Ticket, 1).estado is not EstadoTicket.CERRADO
        web.post("/tickets/1/producto", data={"producto_id": datos_web.prod_id})
        web.post("/tickets/1/cerrar")
        with app.app_context():
            ticket = db_session.get(Ticket, 1)
            assert ticket.producto_id == datos_web.prod_id
            assert ticket.producto_otro == "Secarropas"  # queda como referencia
            assert ticket.estado is EstadoTicket.CERRADO

    def test_registrar_el_producto_desde_el_ticket_lo_vincula(self, app, web, datos_web, login):
        self._ticket_con_producto_escrito(web, login)
        web.post("/productos/nuevo?volver=ticket-1", data={
            "nombre": "Secarropas 6kg", "tipo": "LINEA_BLANCA", "categoria_id": datos_web.cat_id,
        })
        with app.app_context():
            ticket = db_session.get(Ticket, 1)
            assert ticket.producto.nombre == "Secarropas 6kg"
            assert not ticket.producto_pendiente

    def test_desde_el_ticket_se_crean_tipo_y_categoria_nuevos(self, app, web, datos_web, login):
        """Bug: el cliente escribió «Caloventor vertical» (tipo Otro) y el representante no podía
        crear un tipo de producto ni una categoría nuevos para registrarlo y cerrar el ticket."""
        login("carla@mail.com")
        web.post("/tickets/nuevo", data={
            "tipo_producto": "OTRO", "producto_id": "OTRO", "producto_otro": "Caloventor vertical",
            "descripcion": "El caloventor no calienta, solo tira aire frío.",
        })
        web.post("/logout")
        login("ana@soporte.com")
        html = web.get("/productos/nuevo?nombre=Caloventor+vertical&volver=ticket-1").get_data(as_text=True)
        assert "Crear nuevo tipo" in html and "Crear nueva categoría" in html
        web.post("/productos/nuevo?volver=ticket-1", data={
            "nombre": "Caloventor vertical", "tipo": "__nuevo__", "tipo_nuevo": "Climatización",
            "categoria_id": "__nuevo__", "categoria_nueva": "Caloventores",
        })
        web.post("/tickets/1/cerrar")
        with app.app_context():
            ticket = db_session.get(Ticket, 1)
            assert ticket.producto.nombre == "Caloventor vertical"
            assert ticket.tipo_producto.nombre == "Climatización"
            assert ticket.producto.categoria.nombre == "Caloventores"
            assert ticket.estado is EstadoTicket.CERRADO

    def test_crear_nuevo_sin_escribir_el_nombre_avisa(self, app, web, datos_web, login):
        login("ana@soporte.com")
        html = web.post("/productos/nuevo", data={
            "nombre": "Caloventor", "tipo": "__nuevo__", "tipo_nuevo": "", "categoria_id": datos_web.cat_id,
        }).get_data(as_text=True)
        assert "Escribí el nombre del nuevo tipo de producto" in html

    def test_el_representante_crea_un_tipo_desde_productos(self, app, web, datos_web, login):
        login("ana@soporte.com")
        web.post("/productos/tipos", data={"nombre": "Climatización"})
        assert "Climatización" in web.get("/productos/").get_data(as_text=True)

    def test_el_historial_dice_quien_abrio_el_ticket(self, web, datos_web, login):
        self._ticket_con_producto_escrito(web, login)  # lo abre Carla; queda logueada Ana
        html = web.get("/tickets/1").get_data(as_text=True)
        assert "Abierto por Carla" in html
        assert "Registrado por Ana" not in html

    def test_el_cliente_no_puede_vincular(self, app, web, datos_web, login):
        login("carla@mail.com")
        web.post("/tickets/nuevo", data={
            "tipo_producto": "OTRO", "producto_id": "OTRO", "producto_otro": "Freezer",
            "descripcion": "El freezer no congela desde ayer.",
        })
        assert web.post("/tickets/1/producto", data={"producto_id": datos_web.prod_id}).status_code == 403

    def test_el_representante_tambien_puede_escribir_el_producto(self, app, web, datos_web, login):
        login("ana@soporte.com")
        web.post("/tickets/nuevo", data={
            "cliente_id": datos_web.cli_id, "tipo_producto": "OTRO", "producto_id": "OTRO",
            "producto_otro": "Freezer vertical", "descripcion": "Descripción suficientemente larga.",
        })
        with app.app_context():
            ticket = db_session.query(Ticket).one()
            assert ticket.producto_otro == "Freezer vertical" and ticket.producto_pendiente

    def test_otro_en_el_tipo_sin_escribir_avisa_que_falta_el_producto(self, app, web, datos_web, login):
        # Caso de la captura: "Otro / no lo encuentro" + "Otro (lo escribo)" con el campo vacío.
        login("carla@mail.com")
        html = web.post("/tickets/nuevo", data={
            "tipo_producto": "OTRO", "producto_id": "OTRO", "producto_otro": "", "descripcion": "No enciende",
        }).get_data(as_text=True)
        assert "Escribí qué producto es" in html
        assert "tipo de producto válido" not in html

    def test_el_representante_crea_producto_desde_el_catalogo(self, app, web, datos_web, login):
        login("ana@soporte.com")
        assert "/productos/nuevo?volver=catalogo" in web.get("/productos/catalogo").get_data(as_text=True)
        respuesta = web.post("/productos/nuevo?volver=catalogo", data={
            "nombre": "Freezer 300L", "tipo": "LINEA_BLANCA", "categoria_id": datos_web.cat_id,
        })
        assert respuesta.headers["Location"].endswith("/productos/catalogo")

    def test_el_cliente_no_ve_el_boton_de_nuevo_producto(self, web, datos_web, login):
        login("carla@mail.com")
        assert "/productos/nuevo" not in web.get("/productos/catalogo").get_data(as_text=True)

    def test_el_catalogo_lo_ve_cualquier_usuario(self, web, datos_web, login):
        login("carla@mail.com")
        html = web.get("/productos/catalogo").get_data(as_text=True)
        assert "Lavarropas 8kg" in html
        assert "Línea blanca" in html

    def test_el_alta_muestra_los_selectores(self, web, datos_web, login):
        login("carla@mail.com")
        html = web.get("/tickets/nuevo").get_data(as_text=True)
        assert 'name="tipo_producto"' in html
        assert 'data-tipo="LINEA_BLANCA"' in html



class TestSeguridad:
    def test_la_pantalla_de_login_carga(self, web):
        respuesta = web.get("/login")
        assert respuesta.status_code == 200
        assert "Ingresar" in respuesta.get_data(as_text=True)

    def test_sin_sesion_redirige_al_login(self, web):
        for ruta in ["/", "/tickets/", "/usuarios/", "/productos/", "/notificaciones/"]:
            respuesta = web.get(ruta)
            assert respuesta.status_code == 302
            assert "/login" in respuesta.headers["Location"]

    def test_login_incorrecto(self, web, datos_web, login):
        html = login("ana@soporte.com", "incorrecta").get_data(as_text=True)
        assert "Email o contraseña incorrectos" in html

    def test_login_correcto_muestra_el_panel(self, web, datos_web, login):
        html = login("ana@soporte.com").get_data(as_text=True)
        assert "Hola, Ana" in html

    def test_logout(self, web, datos_web, login):
        login("ana@soporte.com")
        web.post("/logout")
        assert web.get("/").status_code == 302

    def test_un_cliente_no_accede_a_la_gestion(self, web, datos_web, login):
        login("carla@mail.com")
        assert web.get("/usuarios/").status_code == 403
        assert web.get("/productos/").status_code == 403

    def test_el_registro_publico_crea_un_cliente(self, app, web):
        respuesta = web.post(
            "/registro",
            data={"nombre": "Nueva Persona", "email": "nueva@mail.com", "password": "clave123", "password2": "clave123"},
            follow_redirects=True,
        )
        assert "Hola, Nueva" in respuesta.get_data(as_text=True)
        with app.app_context():
            from app.services import UsuarioService
            assert UsuarioService(db_session).buscar_por_email("nueva@mail.com").es_cliente

    def test_el_registro_publico_no_permite_crear_representantes(self, app, web):
        assert 'value="representante"' not in web.get("/registro").get_data(as_text=True)
        web.post(
            "/registro",
            data={"nombre": "Intruso", "email": "intruso@mail.com", "password": "clave123",
                  "password2": "clave123", "rol": "representante"},
        )
        with app.app_context():
            from app.services import UsuarioService
            usuario = UsuarioService(db_session).buscar_por_email("intruso@mail.com")
            assert usuario.es_cliente and not usuario.es_representante
        assert web.get("/usuarios/").status_code == 403

    def test_el_registro_exige_contrasenas_iguales(self, app, web):
        respuesta = web.post(
            "/registro",
            data={"nombre": "Nueva Persona", "email": "nueva@mail.com", "password": "clave123", "password2": "otra-clave"},
        )
        assert "Las contraseñas no coinciden" in respuesta.get_data(as_text=True)

    def test_un_cliente_no_puede_registrar_clientes(self, app, web, datos_web, login):
        login("carla@mail.com")
        assert web.get("/usuarios/nuevo?tipo=cliente").status_code == 403
        respuesta = web.post(
            "/usuarios/nuevo?tipo=cliente",
            data={"nombre": "Cliente Trucho", "email": "trucho@mail.com", "password": "clave123"},
        )
        assert respuesta.status_code == 403
        with app.app_context():
            from app.services import UsuarioService
            assert UsuarioService(db_session).buscar_por_email("trucho@mail.com") is None

    def test_el_cliente_ve_el_formulario_sin_elegir_cliente(self, web, datos_web, login):
        login("carla@mail.com")
        html = web.get("/tickets/nuevo").get_data(as_text=True)
        assert "Tu consulta" in html
        assert 'name="cliente_id"' not in html
        assert "Registrar cliente" not in html

    def test_el_cliente_crea_un_ticket_desde_la_web(self, app, web, datos_web, login):
        login("carla@mail.com")
        respuesta = web.post(
            "/tickets/nuevo",
            data={"cliente_id": datos_web.otro_id, "tipo_producto": "LINEA_BLANCA",
                  "producto_id": datos_web.prod_id, "descripcion": "El lavarropas hace mucho ruido."},
        )
        assert respuesta.status_code == 302
        with app.app_context():
            ticket = db_session.query(Ticket).one()
            assert ticket.cliente_id == datos_web.cli_id  # siempre a su nombre
            assert ticket.representante_id is None  # entra en la cola hasta que un representante lo tome

    def test_csrf_rechaza_formularios_sin_token(self):
        app = create_app({"TESTING": True, "SECRET_KEY": "x", "DATABASE_URL": "sqlite://", "CARGAR_DATOS_EJEMPLO": False})
        respuesta = app.test_client().post("/login", data={"email": "a@a.com", "password": "123456"})
        assert respuesta.status_code == 400
        db_session.remove()


class TestTicketsWeb:
    def test_el_representante_crea_un_ticket(self, app, web, datos_web, login):
        login("ana@soporte.com")
        respuesta = _crear_ticket(web, datos_web)
        assert respuesta.status_code == 302
        with app.app_context():
            ticket = db_session.query(Ticket).one()
            assert ticket.estado is EstadoTicket.ABIERTO
            assert respuesta.headers["Location"].endswith(f"/tickets/{ticket.numero_ticket}")

    def test_formulario_incompleto_muestra_error(self, app, web, datos_web, login):
        login("ana@soporte.com")
        respuesta = _crear_ticket(web, datos_web, descripcion="")
        assert respuesta.status_code == 200
        assert "La descripción de la incidencia es obligatoria" in respuesta.get_data(as_text=True)
        with app.app_context():
            assert db_session.query(Ticket).count() == 0

    def test_cliente_sin_tickets_ve_la_leyenda(self, web, datos_web, login):
        login("carla@mail.com")
        assert "No tenés tickets asociados" in web.get("/tickets/").get_data(as_text=True)

    def test_el_cliente_ve_su_ticket_y_responde(self, web, datos_web, login):
        login("ana@soporte.com")
        _crear_ticket(web, datos_web)
        web.post("/logout")
        login("carla@mail.com")
        assert "#1" in web.get("/tickets/").get_data(as_text=True)
        web.post("/tickets/1/hitos", data={"mensaje": "¿Cuándo pasa el técnico?"})
        assert "¿Cuándo pasa el técnico?" in web.get("/tickets/1").get_data(as_text=True)

    def test_un_cliente_no_ve_tickets_ajenos(self, web, datos_web, login):
        login("ana@soporte.com")
        _crear_ticket(web, datos_web)
        web.post("/logout")
        login("diego@mail.com")
        assert web.get("/tickets/1").status_code == 403

    def test_ticket_inexistente(self, web, datos_web, login):
        login("ana@soporte.com")
        assert web.get("/tickets/999").status_code == 404

    def test_cerrar_y_reabrir_desde_la_web(self, app, web, datos_web, login):
        login("ana@soporte.com")
        _crear_ticket(web, datos_web)
        web.post("/tickets/1/cerrar")
        with app.app_context():
            assert db_session.get(Ticket, 1).estado is EstadoTicket.CERRADO
        web.post("/tickets/1/reabrir")
        with app.app_context():
            assert db_session.get(Ticket, 1).estado is EstadoTicket.ABIERTO


class TestGestionWeb:
    def test_registrar_cliente_desde_el_formulario(self, web, datos_web, login):
        login("ana@soporte.com")
        respuesta = web.post(
            "/usuarios/nuevo?tipo=cliente",
            data={"nombre": "Lucía Martínez", "email": "lucia@mail.com", "password": "clave123", "dni": "35123456"},
            follow_redirects=True,
        )
        assert "Lucía Martínez" in respuesta.get_data(as_text=True)

    def test_no_permite_duplicar_usuarios(self, web, datos_web, login):
        login("ana@soporte.com")
        respuesta = web.post(
            "/usuarios/nuevo?tipo=cliente",
            data={"nombre": "Otra Carla", "email": "carla@mail.com", "password": "clave123"},
        )
        assert "Ya existe un usuario registrado" in respuesta.get_data(as_text=True)

    def test_registrar_producto(self, web, datos_web, login):
        login("ana@soporte.com")
        respuesta = web.post(
            "/productos/nuevo",
            data={"nombre": "Cafetera Express", "tipo": "PEQUENIOS_ELECTRODOMESTICOS", "categoria_id": datos_web.cat_id},
            follow_redirects=True,
        )
        assert "Cafetera Express" in respuesta.get_data(as_text=True)

    def test_el_cliente_ve_sus_notificaciones(self, web, datos_web, login):
        login("ana@soporte.com")
        _crear_ticket(web, datos_web)
        web.post("/logout")
        login("carla@mail.com")
        assert "Se creó el ticket #1" in web.get("/notificaciones/").get_data(as_text=True)
