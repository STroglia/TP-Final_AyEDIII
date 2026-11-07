"""Iteración 3 (TDD) — Gestión de tickets.

CU001 Crear ticket · CU002 Consultar ticket (cliente) · estados y asignación.
"""
import pytest

from app.errores import NoEncontradoError, PermisoError, ReglaNegocioError, ValidacionError
from app.models import EstadoTicket, TipoProducto


class TestCrearTicket:
    """CU001 - Crear Ticket de Soporte."""

    def test_crear_ticket(self, tickets, representante, cliente):
        ticket = tickets.crear_ticket(representante, cliente.id, "El lavarropas no centrifuga.")
        assert ticket.numero_ticket is not None  # el sistema informa el número
        assert ticket.estado is EstadoTicket.ABIERTO  # paso 5: estado "abierto"
        assert ticket.cliente is cliente
        assert ticket.representante is representante

    def test_numeros_de_ticket_correlativos(self, tickets, representante, cliente):
        t1 = tickets.crear_ticket(representante, cliente.id, "Primer problema del cliente")
        t2 = tickets.crear_ticket(representante, cliente.id, "Segundo problema del cliente")
        assert t2.numero_ticket == t1.numero_ticket + 1

    def test_crear_ticket_con_producto(self, tickets, representante, cliente, producto):
        ticket = tickets.crear_ticket(
            representante, cliente.id, "La heladera hace ruido.", producto_id=producto.id_producto
        )
        assert ticket.producto is producto
        # El tipo de producto queda guardado en el ticket (para estadísticas)
        assert ticket.tipo_producto is TipoProducto.LINEA_BLANCA

    def test_crear_ticket_con_tipo_y_producto(self, tickets, representante, cliente, producto):
        ticket = tickets.crear_ticket(
            representante, cliente.id, "La heladera hace ruido.",
            producto_id=producto.id_producto, tipo_producto="LINEA_BLANCA", exigir_producto=True,
        )
        assert ticket.tipo_producto is TipoProducto.LINEA_BLANCA
        assert ticket.producto is producto

    def test_el_producto_debe_ser_del_tipo_elegido(self, tickets, representante, cliente, producto):
        with pytest.raises(ValidacionError):
            tickets.crear_ticket(
                representante, cliente.id, "La heladera hace ruido.",
                producto_id=producto.id_producto, tipo_producto="COCINA",
            )

    def test_tipo_y_producto_obligatorios_en_el_alta(self, tickets, representante, cliente, producto):
        with pytest.raises(ValidacionError):
            tickets.crear_ticket(representante, cliente.id, "Descripción suficientemente larga", exigir_producto=True)
        with pytest.raises(ValidacionError):
            tickets.crear_ticket(
                representante, cliente.id, "Descripción suficientemente larga",
                tipo_producto="LINEA_BLANCA", exigir_producto=True,
            )

    def test_tickets_por_tipo_de_producto(self, tickets, representante, cliente, producto):
        tickets.crear_ticket(representante, cliente.id, "La heladera hace ruido.", producto_id=producto.id_producto)
        tickets.crear_ticket(representante, cliente.id, "Otra consulta sin producto.")
        conteo = dict(tickets.tickets_por_tipo_producto())
        assert conteo[TipoProducto.LINEA_BLANCA] == 1
        assert conteo[None] == 1

    def test_se_guarda_quien_creo_el_ticket(self, tickets, representante, cliente):
        del_rep = tickets.crear_ticket(representante, cliente.id, "Lo carga el representante.")
        del_cliente = tickets.crear_ticket(cliente, None, "Lo abre el propio cliente.")
        assert del_rep.creado_por is representante
        assert del_cliente.creado_por is cliente
        assert del_cliente.representante is None  # entra en la cola; nadie lo tomó todavía

    def test_al_crear_el_ticket_se_notifica_al_cliente(self, ticket, notificaciones, cliente):
        avisos = notificaciones.listar(cliente)
        assert len(avisos) == 1
        assert f"#{ticket.numero_ticket}" in avisos[0].mensaje

    def test_sin_descripcion_no_se_crea(self, tickets, representante, cliente):
        with pytest.raises(ValidacionError):
            tickets.crear_ticket(representante, cliente.id, "   ")
        assert tickets.listar(representante) == []

    def test_cliente_inexistente(self, tickets, representante):
        with pytest.raises(NoEncontradoError):
            tickets.crear_ticket(representante, 999, "Descripción suficientemente larga")

    def test_producto_inexistente(self, tickets, representante, cliente):
        with pytest.raises(NoEncontradoError):
            tickets.crear_ticket(representante, cliente.id, "Descripción suficientemente larga", producto_id=999)

    def test_no_se_le_crean_tickets_a_un_cliente_dado_de_baja(self, tickets, usuarios, representante, cliente):
        usuarios.cambiar_activo(cliente.id, False)
        with pytest.raises(ReglaNegocioError):
            tickets.crear_ticket(representante, cliente.id, "Descripción suficientemente larga")


class TestClienteCreaTicket:
    """El cliente también puede abrir tickets, pero solo a su propio nombre."""

    def test_el_cliente_crea_su_propio_ticket(self, tickets, cliente, representante):
        ticket = tickets.crear_ticket(cliente, None, "La pava eléctrica no calienta.")
        assert ticket.numero_ticket is not None
        assert ticket.cliente is cliente
        assert ticket.estado is EstadoTicket.ABIERTO

    def test_el_cliente_no_puede_crear_tickets_para_otro_cliente(self, tickets, cliente, otro_cliente, representante):
        ticket = tickets.crear_ticket(cliente, otro_cliente.id, "Intento abrir un ticket ajeno")
        assert ticket.cliente is cliente  # se ignora el cliente elegido
        assert tickets.listar(otro_cliente) == []

    def test_el_ticket_del_cliente_entra_en_la_cola(self, tickets, cliente, representante, otro_representante):
        ticket = tickets.crear_ticket(cliente, None, "Ticket nuevo abierto por el cliente")
        assert ticket.representante is None
        assert ticket.en_cola
        assert ticket.estado is EstadoTicket.ABIERTO
        assert tickets.contar_cola() == 1

    def test_se_avisa_a_todos_los_representantes(self, tickets, notificaciones, cliente, representante, otro_representante):
        ticket = tickets.crear_ticket(cliente, None, "La pava eléctrica no calienta.")
        for rep in (representante, otro_representante):
            avisos = notificaciones.listar(rep)
            assert len(avisos) == 1
            assert f"#{ticket.numero_ticket}" in avisos[0].mensaje and "Carla Cliente" in avisos[0].mensaje

    def test_el_cliente_tambien_debe_describir_la_incidencia(self, tickets, cliente, representante):
        with pytest.raises(ValidacionError):
            tickets.crear_ticket(cliente, None, "corta")
        assert tickets.listar(cliente) == []


class TestColaDeTickets:
    """Backlog: los tickets de clientes esperan en la cola hasta que un representante los toma."""

    def test_tomar_un_ticket(self, tickets, notificaciones, cliente, representante):
        ticket = tickets.crear_ticket(cliente, None, "La pava eléctrica no calienta.")
        tickets.tomar(ticket.numero_ticket, representante)
        assert ticket.representante is representante
        assert ticket.estado is EstadoTicket.EN_PROCESO
        assert not ticket.en_cola and tickets.contar_cola() == 0
        assert any("tomó tu ticket" in n.mensaje for n in notificaciones.listar(cliente))

    def test_no_se_puede_tomar_un_ticket_que_ya_tomo_otro(self, tickets, cliente, representante, otro_representante):
        ticket = tickets.crear_ticket(cliente, None, "La pava eléctrica no calienta.")
        tickets.tomar(ticket.numero_ticket, representante)
        with pytest.raises(ReglaNegocioError):
            tickets.tomar(ticket.numero_ticket, otro_representante)

    def test_tomar_el_siguiente_respeta_el_orden_de_llegada(self, tickets, cliente, otro_cliente, representante):
        primero = tickets.crear_ticket(cliente, None, "Llegó primero a la cola.")
        segundo = tickets.crear_ticket(otro_cliente, None, "Llegó segundo a la cola.")
        assert tickets.tomar_siguiente(representante) is primero
        assert tickets.tomar_siguiente(representante) is segundo
        with pytest.raises(ReglaNegocioError):
            tickets.tomar_siguiente(representante)  # la cola quedó vacía

    def test_un_cliente_no_puede_tomar_tickets(self, tickets, cliente, representante):
        ticket = tickets.crear_ticket(cliente, None, "La pava eléctrica no calienta.")
        with pytest.raises(PermisoError):
            tickets.tomar(ticket.numero_ticket, cliente)

    def test_responder_un_ticket_en_cola_lo_toma(self, tickets, cliente, representante):
        ticket = tickets.crear_ticket(cliente, None, "La pava eléctrica no calienta.")
        tickets.registrar_hito(ticket.numero_ticket, representante, "Hola, ya lo estoy viendo.")
        assert ticket.representante is representante
        assert ticket.estado is EstadoTicket.EN_PROCESO

    def test_listar_solo_la_cola(self, tickets, cliente, otro_cliente, representante):
        en_cola = tickets.crear_ticket(cliente, None, "Ticket esperando en la cola.")
        tickets.crear_ticket(representante, otro_cliente.id, "Ticket que ya tiene representante.")
        assert tickets.listar(representante, en_cola=True) == [en_cola]

    def test_los_tickets_cerrados_no_estan_en_la_cola(self, tickets, cliente, representante):
        ticket = tickets.crear_ticket(cliente, None, "Lo cierra el cliente antes de que lo tomen.")
        tickets.cerrar(ticket.numero_ticket, cliente)
        assert tickets.contar_cola() == 0


class TestConsultarTickets:
    """CU002 - Consultar Ticket (cliente) y listados del representante."""

    def test_el_cliente_ve_solo_sus_tickets(self, tickets, representante, cliente, otro_cliente):
        propio = tickets.crear_ticket(representante, cliente.id, "Problema de Carla")
        tickets.crear_ticket(representante, otro_cliente.id, "Problema de Diego")
        assert tickets.listar(cliente) == [propio]

    def test_cliente_sin_tickets(self, tickets, cliente):
        assert tickets.listar(cliente) == []

    def test_el_cliente_ve_tickets_en_todos_los_estados(self, tickets, representante, cliente):
        abierto = tickets.crear_ticket(representante, cliente.id, "Ticket que sigue abierto")
        cerrado = tickets.crear_ticket(representante, cliente.id, "Ticket que se va a cerrar")
        tickets.cerrar(cerrado.numero_ticket, representante)
        assert set(tickets.listar(cliente)) == {abierto, cerrado}

    def test_el_representante_ve_todos(self, tickets, representante, otro_representante, cliente, otro_cliente):
        tickets.crear_ticket(representante, cliente.id, "Problema de Carla")
        tickets.crear_ticket(otro_representante, otro_cliente.id, "Problema de Diego")
        assert len(tickets.listar(representante)) == 2
        assert len(tickets.listar(representante, solo_mios=True)) == 1

    def test_filtrar_por_estado(self, tickets, representante, cliente):
        t1 = tickets.crear_ticket(representante, cliente.id, "Ticket que sigue abierto")
        t2 = tickets.crear_ticket(representante, cliente.id, "Ticket que se va a cerrar")
        tickets.cerrar(t2.numero_ticket, representante)
        assert tickets.listar(representante, estado="ABIERTO") == [t1]
        assert tickets.listar(representante, estado="CERRADO") == [t2]

    def test_estado_invalido(self, tickets, representante):
        with pytest.raises(ValidacionError):
            tickets.listar(representante, estado="PERDIDO")

    def test_buscar_por_numero(self, tickets, representante, cliente):
        t1 = tickets.crear_ticket(representante, cliente.id, "Primer problema del cliente")
        tickets.crear_ticket(representante, cliente.id, "Segundo problema del cliente")
        assert tickets.listar(representante, busqueda=f"#{t1.numero_ticket}") == [t1]

    def test_buscar_por_texto_o_nombre_del_cliente(self, tickets, representante, cliente, otro_cliente):
        t1 = tickets.crear_ticket(representante, cliente.id, "El microondas no calienta")
        t2 = tickets.crear_ticket(representante, otro_cliente.id, "La cocina pierde gas")
        assert tickets.listar(representante, busqueda="microondas") == [t1]
        assert tickets.listar(representante, busqueda="diego") == [t2]

    def test_obtener_ticket_ajeno(self, tickets, ticket, otro_cliente):
        with pytest.raises(PermisoError):
            tickets.obtener(ticket.numero_ticket, otro_cliente)

    def test_obtener_ticket_inexistente(self, tickets, representante):
        with pytest.raises(NoEncontradoError):
            tickets.obtener(999, representante)

    def test_estadisticas(self, tickets, representante, cliente):
        tickets.crear_ticket(representante, cliente.id, "Ticket que sigue abierto")
        t2 = tickets.crear_ticket(representante, cliente.id, "Ticket que se va a cerrar")
        tickets.cerrar(t2.numero_ticket, representante)
        assert tickets.estadisticas(representante) == {"total": 2, "abiertos": 1, "en_proceso": 0, "cerrados": 1}


class TestEstadosYAsignacion:
    def test_asignar_a_otro_representante(self, tickets, notificaciones, ticket, representante, otro_representante):
        tickets.asignar(ticket.numero_ticket, representante, otro_representante.id)
        assert ticket.representante is otro_representante
        assert notificaciones.contar_no_leidas(otro_representante) == 1

    def test_un_cliente_no_puede_asignar(self, tickets, ticket, cliente, representante):
        with pytest.raises(PermisoError):
            tickets.asignar(ticket.numero_ticket, cliente, representante.id)

    def test_el_cliente_cierra_su_ticket_y_se_notifica_al_representante(
        self, tickets, notificaciones, ticket, cliente, representante
    ):
        tickets.cerrar(ticket.numero_ticket, cliente)
        assert ticket.estado is EstadoTicket.CERRADO
        assert notificaciones.contar_no_leidas(representante) == 1

    def test_reabrir_ticket(self, tickets, ticket, cliente, representante):
        tickets.cerrar(ticket.numero_ticket, representante)
        tickets.reabrir(ticket.numero_ticket, cliente)
        assert ticket.estado is EstadoTicket.ABIERTO

    def test_poner_en_proceso(self, tickets, ticket, representante):
        tickets.poner_en_proceso(ticket.numero_ticket, representante)
        assert ticket.estado is EstadoTicket.EN_PROCESO
