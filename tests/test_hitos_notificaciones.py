"""Iteración 4 (TDD) — CU003 Registrar hito y notificaciones."""
import pytest

from app.errores import PermisoError, ReglaNegocioError, ValidacionError
from app.models import EstadoTicket, Hito


class TestRegistrarHito:
    def test_el_representante_responde_y_se_notifica_al_cliente(
        self, tickets, notificaciones, ticket, representante, cliente
    ):
        antes = notificaciones.contar_no_leidas(cliente)
        hito = tickets.registrar_hito(ticket.numero_ticket, representante, "Mañana va un técnico.")
        assert hito.id is not None
        assert hito in ticket.hitos
        assert notificaciones.contar_no_leidas(cliente) == antes + 1
        assert ticket.estado is EstadoTicket.EN_PROCESO

    def test_el_cliente_responde_y_se_notifica_al_representante(
        self, tickets, notificaciones, ticket, representante, cliente
    ):
        tickets.registrar_hito(ticket.numero_ticket, cliente, "¿A qué hora viene el técnico?")
        avisos = notificaciones.listar(representante)
        assert len(avisos) == 1
        assert "Carla Cliente" in avisos[0].mensaje

    def test_un_hito_vacio_no_se_guarda(self, tickets, session, ticket, cliente):
        with pytest.raises(ValidacionError):
            tickets.registrar_hito(ticket.numero_ticket, cliente, "   ")
        assert session.query(Hito).count() == 0

    def test_los_hitos_quedan_en_orden_cronologico(self, tickets, ticket, representante, cliente):
        tickets.registrar_hito(ticket.numero_ticket, cliente, "Primero")
        tickets.registrar_hito(ticket.numero_ticket, representante, "Segundo")
        tickets.registrar_hito(ticket.numero_ticket, cliente, "Tercero")
        assert [h.mensaje for h in ticket.hitos] == ["Primero", "Segundo", "Tercero"]

    def test_no_se_registran_hitos_en_un_ticket_cerrado(self, tickets, ticket, representante, cliente):
        tickets.cerrar(ticket.numero_ticket, representante)
        with pytest.raises(ReglaNegocioError):
            tickets.registrar_hito(ticket.numero_ticket, cliente, "Hola")

    def test_un_cliente_no_puede_escribir_en_un_ticket_ajeno(self, tickets, ticket, otro_cliente):
        with pytest.raises(PermisoError):
            tickets.registrar_hito(ticket.numero_ticket, otro_cliente, "Hola")


class TestNotificaciones:
    def test_contar_y_marcar_como_leida(self, notificaciones, ticket, cliente):
        aviso = notificaciones.listar(cliente)[0]
        assert notificaciones.contar_no_leidas(cliente) == 1
        notificaciones.marcar_leida(aviso.id, cliente)
        assert notificaciones.contar_no_leidas(cliente) == 0

    def test_marcar_todas_como_leidas(self, tickets, notificaciones, ticket, representante, cliente):
        tickets.registrar_hito(ticket.numero_ticket, representante, "Respuesta 1")
        tickets.registrar_hito(ticket.numero_ticket, representante, "Respuesta 2")
        assert notificaciones.marcar_todas_leidas(cliente) == 3
        assert notificaciones.contar_no_leidas(cliente) == 0

    def test_no_se_puede_marcar_una_notificacion_ajena(self, notificaciones, ticket, cliente, otro_cliente):
        aviso = notificaciones.listar(cliente)[0]
        with pytest.raises(PermisoError):
            notificaciones.marcar_leida(aviso.id, otro_cliente)

    def test_al_ver_el_ticket_se_marcan_sus_notificaciones(self, notificaciones, ticket, cliente):
        assert notificaciones.marcar_leidas_de_ticket(cliente, ticket) == 1
        assert notificaciones.contar_no_leidas(cliente) == 0

    def test_las_notificaciones_se_listan_de_la_mas_nueva_a_la_mas_vieja(
        self, tickets, notificaciones, ticket, representante, cliente
    ):
        tickets.registrar_hito(ticket.numero_ticket, representante, "Respuesta")
        avisos = notificaciones.listar(cliente)
        assert "respondió" in avisos[0].mensaje
        assert "Se creó" in avisos[1].mensaje
