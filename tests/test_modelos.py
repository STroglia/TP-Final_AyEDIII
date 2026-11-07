"""Iteración 1 (TDD) — Reglas del dominio en los modelos, sin base de datos.

Se prueban las clases del diagrama "en memoria": herencia de usuarios,
login, workflow de estados del ticket, hitos y notificaciones.
"""
from datetime import datetime, timedelta

import pytest

from app.errores import PermisoError, ReglaNegocioError, ValidacionError
from app.models import Cliente, EstadoTicket, Hito, Notificacion, Representante, Ticket


@pytest.fixture
def cli():
    return Cliente(nombre="Carla Cliente", email="carla@mail.com", password="clave123")


@pytest.fixture
def rep():
    return Representante(nombre="Ana Soporte", email="ana@soporte.com", password="clave123")


@pytest.fixture
def tk(cli, rep):
    return rep.crear_ticket(cli, "La heladera no enfría desde ayer.")


# ---------------------------------------------------------------- Usuario
class TestUsuario:
    def test_la_password_se_guarda_hasheada(self, cli):
        assert cli.password_hash != "clave123"
        assert cli.password_hash  # no está vacía

    def test_login_con_password_correcta(self, cli):
        assert cli.login("clave123") is True

    def test_login_con_password_incorrecta(self, cli):
        assert cli.login("otra-clave") is False

    def test_login_falla_si_el_usuario_esta_inactivo(self, cli):
        cli.activo = False
        assert cli.login("clave123") is False

    def test_password_demasiado_corta(self):
        with pytest.raises(ValidacionError):
            Cliente(nombre="X Y", email="x@mail.com", password="123")

    def test_roles_por_herencia(self, cli, rep):
        assert cli.es_cliente and not cli.es_representante
        assert rep.es_representante and not rep.es_cliente
        assert cli.rol == "Cliente" and rep.rol == "Representante"

    def test_iniciales(self, cli):
        assert cli.iniciales == "CC"


# ---------------------------------------------------------------- Ticket
class TestTicket:
    def test_un_ticket_nuevo_queda_abierto_y_con_fecha(self, tk, cli, rep):
        assert tk.estado is EstadoTicket.ABIERTO
        assert isinstance(tk.fecha_creacion, datetime)
        assert tk.cliente is cli
        assert tk.representante is rep

    def test_el_ticket_queda_asociado_al_cliente(self, tk, cli):
        assert tk in cli.tickets

    @pytest.mark.parametrize("descripcion", ["", "   ", "corta"])
    def test_descripcion_obligatoria_y_con_largo_minimo(self, cli, rep, descripcion):
        with pytest.raises(ValidacionError):
            rep.crear_ticket(cli, descripcion)

    def test_requiere_un_cliente(self, rep):
        with pytest.raises(ValidacionError):
            Ticket(cliente=None, representante=rep, descripcion="Descripción suficientemente larga")

    def test_no_se_crean_tickets_para_clientes_dados_de_baja(self, cli, rep):
        cli.activo = False
        with pytest.raises(ReglaNegocioError):
            rep.crear_ticket(cli, "Descripción suficientemente larga")

    def test_cerrar_ticket(self, tk):
        tk.cerrar_ticket()
        assert tk.estado is EstadoTicket.CERRADO
        assert tk.fecha_cierre is not None

    def test_no_se_puede_cerrar_dos_veces(self, tk):
        tk.cerrar_ticket()
        with pytest.raises(ReglaNegocioError):
            tk.cerrar_ticket()

    def test_reabrir_un_ticket_cerrado(self, tk):
        tk.cerrar_ticket()
        tk.abrir_ticket()
        assert tk.estado is EstadoTicket.ABIERTO
        assert tk.fecha_cierre is None

    def test_no_se_puede_reabrir_un_ticket_que_no_esta_cerrado(self, tk):
        with pytest.raises(ReglaNegocioError):
            tk.abrir_ticket()

    def test_poner_en_proceso_solo_desde_abierto(self, tk):
        tk.poner_en_proceso()
        assert tk.estado is EstadoTicket.EN_PROCESO
        with pytest.raises(ReglaNegocioError):
            tk.poner_en_proceso()

    def test_asignar_a_otro_representante(self, tk):
        otro = Representante(nombre="Bruno", email="b@soporte.com", password="clave123")
        tk.asignar(otro)
        assert tk.representante is otro

    def test_no_se_puede_asignar_a_un_cliente(self, tk, cli):
        with pytest.raises(ValidacionError):
            tk.asignar(cli)

    def test_puede_ver(self, tk, cli, rep):
        otro_cliente = Cliente(nombre="Diego", email="d@mail.com", password="clave123")
        assert tk.puede_ver(cli)
        assert tk.puede_ver(rep)
        assert not tk.puede_ver(otro_cliente)
        assert not tk.puede_ver(None)


# ---------------------------------------------------------------- Hitos
class TestHitos:
    def test_agregar_hito(self, tk, cli):
        hito = cli.registrar_hito(tk, "  ¿Hay novedades?  ")
        assert hito in tk.hitos
        assert hito.mensaje == "¿Hay novedades?"
        assert hito.autor is cli

    @pytest.mark.parametrize("mensaje", ["", "    ", None])
    def test_no_se_permite_un_hito_vacio(self, tk, cli, mensaje):
        with pytest.raises(ValidacionError):
            cli.registrar_hito(tk, mensaje)
        assert tk.hitos == []

    def test_no_se_agregan_hitos_a_un_ticket_cerrado(self, tk, rep):
        tk.cerrar_ticket()
        with pytest.raises(ReglaNegocioError):
            rep.registrar_hito(tk, "Mensaje")

    def test_respuesta_del_representante_pasa_el_ticket_a_en_proceso(self, tk, rep):
        rep.registrar_hito(tk, "Mañana va un técnico.")
        assert tk.estado is EstadoTicket.EN_PROCESO

    def test_mensaje_del_cliente_no_cambia_el_estado(self, tk, cli):
        cli.registrar_hito(tk, "Sigo esperando.")
        assert tk.estado is EstadoTicket.ABIERTO

    def test_un_cliente_no_puede_escribir_en_un_ticket_ajeno(self, tk):
        intruso = Cliente(nombre="Diego", email="d@mail.com", password="clave123")
        with pytest.raises(PermisoError):
            intruso.registrar_hito(tk, "Hola")

    def test_registrar_mensaje_valida_el_texto(self):
        hito = Hito(mensaje="Texto original")
        hito.registrar_mensaje("Texto corregido")
        assert hito.mensaje == "Texto corregido"
        with pytest.raises(ValidacionError):
            hito.registrar_mensaje("")

    def test_destinatarios_de_las_notificaciones(self, tk, cli, rep):
        assert tk.destinatarios_para(cli) == [rep]
        assert tk.destinatarios_para(rep) == [cli]


# ---------------------------------------------------------------- Cliente / Notificación
def test_consultar_tickets_del_mas_nuevo_al_mas_viejo(cli, rep):
    viejo = rep.crear_ticket(cli, "Primer problema reportado")
    nuevo = rep.crear_ticket(cli, "Segundo problema reportado")
    viejo.fecha_creacion = datetime.now() - timedelta(days=3)
    assert cli.consultar_tickets() == [nuevo, viejo]


def test_enviar_notificacion_registra_la_fecha_de_envio(cli):
    notificacion = Notificacion(destinatario=cli, mensaje="Hola")
    assert not notificacion.enviada
    notificacion.enviar()
    assert notificacion.enviada
    assert notificacion.leida is False
