"""Iteración 7 (TDD) — Paginación, filtro por período y cambio de contraseña."""
from datetime import timedelta

import pytest

from app.database import db_session
from app.errores import ValidacionError
from app.services import TicketService, UsuarioService
from app.utilidades import ahora, paginar
from tests.conftest import PASSWORD


# ---------------------------------------------------------------- paginar()
class TestPaginar:
    def test_lista_vacia_tiene_una_pagina(self):
        pagina = paginar([], 1, 10)
        assert pagina["elementos"] == []
        assert pagina["paginas"] == 1
        assert pagina["desde"] == 0 and pagina["hasta"] == 0
        assert pagina["anterior"] is None and pagina["siguiente"] is None

    def test_primera_pagina(self):
        pagina = paginar(list(range(25)), 1, 10)
        assert pagina["elementos"] == list(range(10))
        assert pagina["paginas"] == 3
        assert pagina["siguiente"] == 2 and pagina["anterior"] is None

    def test_ultima_pagina_incompleta(self):
        pagina = paginar(list(range(25)), 3, 10)
        assert pagina["elementos"] == [20, 21, 22, 23, 24]
        assert (pagina["desde"], pagina["hasta"], pagina["total"]) == (21, 25, 25)
        assert pagina["siguiente"] is None and pagina["anterior"] == 2

    def test_cantidad_exacta_no_agrega_pagina_vacia(self):
        assert paginar(list(range(20)), 1, 10)["paginas"] == 2

    @pytest.mark.parametrize("pedida, esperada", [("abc", 1), (None, 1), (0, 1), (-4, 1), (99, 3), ("2", 2)])
    def test_pagina_invalida_se_ajusta(self, pedida, esperada):
        assert paginar(list(range(25)), pedida, 10)["pagina"] == esperada


# ---------------------------------------------------------------- filtro por período
class TestFiltroPeriodo:
    def _envejecer(self, session, ticket, dias):
        ticket.fecha_creacion = ahora() - timedelta(days=dias)
        session.commit()

    def test_filtra_por_fecha_de_creacion(self, session, tickets, representante, cliente):
        reciente = tickets.crear_ticket(representante, cliente.id, "Ticket de esta semana.")
        viejo = tickets.crear_ticket(representante, cliente.id, "Ticket de hace dos meses.")
        self._envejecer(session, viejo, 60)

        assert tickets.listar(representante, periodo=7) == [reciente]
        assert set(tickets.listar(representante, periodo=90)) == {reciente, viejo}
        assert len(tickets.listar(representante)) == 2  # sin período: todos

    def test_se_combina_con_el_estado(self, session, tickets, representante, cliente):
        abierto = tickets.crear_ticket(representante, cliente.id, "Sigue abierto.")
        cerrado = tickets.crear_ticket(representante, cliente.id, "Ya se resolvió.")
        tickets.cerrar(cerrado.numero_ticket, representante)
        assert tickets.listar(representante, estado="ABIERTO", periodo=30) == [abierto]

    @pytest.mark.parametrize("periodo", ["abc", "0", "-5"])
    def test_periodo_invalido(self, tickets, representante, periodo):
        with pytest.raises(ValidacionError):
            tickets.listar(representante, periodo=periodo)


# ---------------------------------------------------------------- cambio de contraseña
class TestCambiarPassword:
    def test_cambia_la_contrasena(self, usuarios, cliente):
        usuarios.cambiar_password(cliente, PASSWORD, "nueva456", "nueva456")
        assert cliente.login("nueva456")
        assert not cliente.login(PASSWORD)

    def test_la_actual_tiene_que_ser_correcta(self, usuarios, cliente):
        with pytest.raises(ValidacionError, match="actual"):
            usuarios.cambiar_password(cliente, "equivocada", "nueva456", "nueva456")

    def test_las_nuevas_tienen_que_coincidir(self, usuarios, cliente):
        with pytest.raises(ValidacionError, match="no coinciden"):
            usuarios.cambiar_password(cliente, PASSWORD, "nueva456", "nueva789")

    def test_la_nueva_tiene_que_ser_distinta(self, usuarios, cliente):
        with pytest.raises(ValidacionError, match="distinta"):
            usuarios.cambiar_password(cliente, PASSWORD, PASSWORD, PASSWORD)

    def test_respeta_el_largo_minimo(self, usuarios, cliente):
        with pytest.raises(ValidacionError, match="al menos"):
            usuarios.cambiar_password(cliente, PASSWORD, "abc", "abc")
        assert cliente.login(PASSWORD)  # no cambió


# ---------------------------------------------------------------- web
class TestMejorasWeb:
    def test_cambiar_contrasena_requiere_sesion(self, web):
        respuesta = web.get("/cuenta/contrasena")
        assert respuesta.status_code == 302
        assert "/login" in respuesta.headers["Location"]

    def test_cambiar_contrasena_desde_la_web(self, web, datos_web, login):
        login("carla@mail.com")
        assert "Cambiar contraseña" in web.get("/cuenta/contrasena").get_data(as_text=True)

        html = web.post(
            "/cuenta/contrasena",
            data={"actual": PASSWORD, "nueva": "otra1234", "nueva2": "otra1234"},
            follow_redirects=True,
        ).get_data(as_text=True)
        assert "Tu contraseña se actualizó" in html

        web.post("/logout")
        assert "Email o contraseña incorrectos" in login("carla@mail.com").get_data(as_text=True)
        assert "Hola, Carla" in login("carla@mail.com", "otra1234").get_data(as_text=True)

    def test_cambiar_contrasena_con_error(self, web, datos_web, login):
        login("ana@soporte.com")
        html = web.post(
            "/cuenta/contrasena",
            data={"actual": "mal", "nueva": "otra1234", "nueva2": "otra1234"},
            follow_redirects=True,
        ).get_data(as_text=True)
        assert "La contraseña actual no es correcta" in html

    def _crear_tickets(self, app, datos, cantidad):
        with app.app_context():
            servicio = TicketService(db_session)
            rep = UsuarioService(db_session).obtener(datos.rep_id)
            for i in range(cantidad):
                servicio.crear_ticket(rep, datos.cli_id, f"Consulta número {i + 1} del cliente.")

    def test_listado_paginado(self, app, web, datos_web, login):
        self._crear_tickets(app, datos_web, 12)
        login("ana@soporte.com")

        primera = web.get("/tickets/").get_data(as_text=True)
        assert "Página 1 de 2" in primera
        assert primera.count('<tr data-href=') == 10

        segunda = web.get("/tickets/?pagina=2").get_data(as_text=True)
        assert "Página 2 de 2" in segunda
        assert segunda.count('<tr data-href=') == 2

    def test_pocos_tickets_no_muestran_paginacion(self, app, web, datos_web, login):
        self._crear_tickets(app, datos_web, 3)
        login("ana@soporte.com")
        assert "Página 1 de" not in web.get("/tickets/").get_data(as_text=True)

    def test_filtro_por_periodo_invalido_muestra_error(self, app, web, datos_web, login):
        self._crear_tickets(app, datos_web, 1)
        login("ana@soporte.com")
        html = web.get("/tickets/?periodo=xyz").get_data(as_text=True)
        assert "Período inválido" in html
