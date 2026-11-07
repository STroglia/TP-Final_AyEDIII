"""Gestión de tickets, hitos y estados (RF05, RF06, RF08–RF16; CU001, CU002, CU003)."""
from datetime import timedelta
from typing import List, Optional

from sqlalchemy import func, or_, select

from app.errores import NoEncontradoError, PermisoError, ReglaNegocioError, ValidacionError
from app.models import Cliente, EstadoTicket, Hito, Producto, Representante, Ticket, TipoProducto, Usuario
from app.services.base import Servicio, transaccional
from app.services.notificacion_service import NotificacionService
from app.services.usuario_service import UsuarioService
from app.utilidades import a_entero, ahora, texto_limpio

ORDENES = {
    "recientes": (Ticket.fecha_creacion.desc(), Ticket.numero_ticket.desc()),
    "antiguos": (Ticket.fecha_creacion.asc(), Ticket.numero_ticket.asc()),
    "numero": (Ticket.numero_ticket.asc(),),
}


class TicketService(Servicio):
    def __init__(self, session):
        super().__init__(session)
        self.notificaciones = NotificacionService(session)
        self.usuarios = UsuarioService(session)

    # ------------------------------------------------------------ consultas
    def obtener(self, numero, usuario: Usuario) -> Ticket:
        """Busca un ticket por número verificando que el usuario pueda verlo."""
        numero = a_entero(numero, "Número de ticket inválido.")
        ticket = self.session.get(Ticket, numero)
        if ticket is None:
            raise NoEncontradoError(f"No existe el ticket #{numero}.")
        if not ticket.puede_ver(usuario):
            raise PermisoError("No tenés acceso a este ticket.")
        return ticket

    def listar(
        self,
        usuario: Usuario,
        estado: Optional[str] = None,
        busqueda: Optional[str] = None,
        solo_mios: bool = False,
        orden: str = "recientes",
        periodo: Optional[int] = None,
        en_cola: bool = False,
    ) -> List[Ticket]:
        """Clientes: solo sus tickets (CU002). Representantes: todos, o solo los asignados.

        `periodo`: cantidad de días hacia atrás (7, 30, 90...) según la fecha de creación.
        `en_cola`: solo los tickets de la cola (sin representante y sin cerrar).
        """
        consulta = self._filtro_por_usuario(select(Ticket), usuario, solo_mios)
        if en_cola:
            consulta = consulta.where(Ticket.representante_id.is_(None), Ticket.estado != EstadoTicket.CERRADO)

        if estado:
            consulta = consulta.where(Ticket.estado == self._a_estado(estado))

        if periodo:
            dias = a_entero(periodo, "Período inválido.")
            if dias <= 0:
                raise ValidacionError("Período inválido.")
            consulta = consulta.where(Ticket.fecha_creacion >= ahora() - timedelta(days=dias))

        texto = texto_limpio(busqueda).lstrip("#").strip()
        if texto:
            if texto.isdigit():
                consulta = consulta.where(Ticket.numero_ticket == int(texto))
            else:
                patron = f"%{texto.lower()}%"
                consulta = consulta.join(Ticket.cliente).where(
                    or_(func.lower(Ticket.descripcion).like(patron), func.lower(Cliente.nombre).like(patron))
                )

        consulta = consulta.order_by(*ORDENES.get(orden, ORDENES["recientes"]))
        return list(self.session.scalars(consulta))

    def estadisticas(self, usuario: Usuario, solo_mios: bool = False) -> dict:
        consulta = self._filtro_por_usuario(
            select(Ticket.estado, func.count(Ticket.numero_ticket)), usuario, solo_mios
        ).group_by(Ticket.estado)
        conteo = {estado: 0 for estado in EstadoTicket}
        for estado, cantidad in self.session.execute(consulta):
            conteo[estado] = cantidad
        return {
            "total": sum(conteo.values()),
            "abiertos": conteo[EstadoTicket.ABIERTO],
            "en_proceso": conteo[EstadoTicket.EN_PROCESO],
            "cerrados": conteo[EstadoTicket.CERRADO],
        }

    def tickets_por_tipo_producto(self) -> List[tuple]:
        """Cantidad de tickets por tipo de producto: [(TipoProducto | None, cantidad), ...]."""
        consulta = (
            select(Ticket.tipo_producto, func.count(Ticket.numero_ticket))
            .group_by(Ticket.tipo_producto)
            .order_by(func.count(Ticket.numero_ticket).desc())
        )
        return [(tipo, cantidad) for tipo, cantidad in self.session.execute(consulta)]

    # ------------------------------------------------------------ CU001: crear ticket
    @transaccional
    def crear_ticket(
        self, actor: Usuario, cliente_id, descripcion: str, producto_id=None, tipo_producto=None,
        exigir_producto: bool = False, producto_otro: Optional[str] = None,
    ) -> Ticket:
        """Crea un ticket.

        - Representante: lo crea para el cliente elegido y queda asignado él (CU001).
        - Cliente: lo crea a su propio nombre (se ignora `cliente_id`). El ticket entra
          en la cola (backlog) sin representante, hasta que uno lo toma.
        - Tipo de producto y producto quedan guardados en el ticket (para estadísticas).
          Si se indica solo el producto, el tipo se toma del producto. Con
          `exigir_producto=True` (pantalla de alta) ambos son obligatorios.
        - Si el producto no está en el catálogo se puede escribir a mano (`producto_otro`); en ese
          caso no se elige producto del catálogo, el tipo es opcional y un representante
          tiene que vincularlo con uno del catálogo antes de cerrar el ticket.
        """
        if actor is None or not (actor.es_cliente or actor.es_representante):
            raise PermisoError("Iniciá sesión para crear un ticket.")
        tipo = self._a_tipo_producto(tipo_producto)
        otro = " ".join(texto_limpio(producto_otro).split())
        if otro:
            if len(otro) < 2:
                raise ValidacionError("Escribí qué producto es.")
            if len(otro) > 120:
                raise ValidacionError("El nombre del producto no puede superar los 120 caracteres.")
            producto_id = None
        else:
            if exigir_producto and tipo is None:
                raise ValidacionError("Elegí el tipo de producto.")
            if exigir_producto and producto_id in (None, ""):
                raise ValidacionError("Elegí el producto.")
        producto = self._obtener_producto(producto_id)

        if actor.es_representante:
            cliente = self.usuarios.obtener_cliente(cliente_id)
            ticket = actor.crear_ticket(cliente, descripcion, producto, tipo_producto=tipo)
        else:
            ticket = actor.crear_ticket(descripcion, producto, None, tipo_producto=tipo)
        ticket.producto_otro = otro or None
        ticket.creado_por = actor

        self.session.add(ticket)
        self.session.flush()  # para obtener el número de ticket

        if actor.es_representante:
            self.notificaciones.notificar(
                ticket.cliente, ticket, f"Se creó el ticket #{ticket.numero_ticket}: {ticket.titulo}"
            )
        else:
            # Entra en la cola: se avisa a todos los representantes activos para que alguno lo tome.
            self._avisar_cola(ticket, f"{actor.nombre} abrió el ticket #{ticket.numero_ticket} (en cola): {ticket.titulo}")
        return ticket

    # ------------------------------------------------------------ cola (backlog)
    def _consulta_cola(self):
        """Tickets sin representante y sin cerrar, del más antiguo al más nuevo (orden de llegada)."""
        return (
            select(Ticket)
            .where(Ticket.representante_id.is_(None), Ticket.estado != EstadoTicket.CERRADO)
            .order_by(Ticket.fecha_creacion.asc(), Ticket.numero_ticket.asc())
        )

    def contar_cola(self) -> int:
        return self.session.scalar(
            select(func.count(Ticket.numero_ticket))
            .where(Ticket.representante_id.is_(None), Ticket.estado != EstadoTicket.CERRADO)
        ) or 0

    @transaccional
    def tomar(self, numero, actor: Usuario) -> Ticket:
        """El representante toma un ticket: queda asignado a él y pasa a 'En proceso'."""
        self.exigir_representante(actor)
        ticket = self.obtener(numero, actor)
        ya_era_suyo = ticket.representante is actor
        ticket.tomar(actor)
        if not ya_era_suyo:
            self.notificaciones.notificar(
                ticket.cliente, ticket, f"{actor.nombre} tomó tu ticket #{ticket.numero_ticket} y ya lo está viendo."
            )
        return ticket

    def tomar_siguiente(self, actor: Usuario) -> Ticket:
        """Toma el ticket que hace más tiempo espera en la cola."""
        self.exigir_representante(actor)
        siguiente = self.session.scalars(self._consulta_cola().limit(1)).first()
        if siguiente is None:
            raise ReglaNegocioError("No hay tickets esperando en la cola.")
        return self.tomar(siguiente.numero_ticket, actor)

    def _avisar_cola(self, ticket: Ticket, mensaje: str) -> None:
        for representante in self.usuarios.listar_representantes(solo_activos=True):
            self.notificaciones.notificar(representante, ticket, mensaje)

    # ------------------------------------------------------------ CU003: registrar hito
    @transaccional
    def registrar_hito(self, numero, autor: Usuario, mensaje: str) -> Hito:
        ticket = self.obtener(numero, autor)
        hito = autor.registrar_hito(ticket, mensaje)  # si un representante responde un ticket en cola, lo toma
        self.session.add(hito)
        destinatarios = ticket.destinatarios_para(autor)
        if destinatarios:
            for destinatario in destinatarios:
                self.notificaciones.notificar(
                    destinatario, ticket, f"{autor.nombre} respondió en el ticket #{ticket.numero_ticket}."
                )
        elif ticket.en_cola:
            self._avisar_cola(ticket, f"{autor.nombre} agregó información al ticket #{ticket.numero_ticket} (en cola).")
        return hito

    # ------------------------------------------------------------ estados y asignación
    @transaccional
    def asignar(self, numero, actor: Usuario, representante_id) -> Ticket:
        self.exigir_representante(actor)
        ticket = self.obtener(numero, actor)
        nuevo = self.usuarios.obtener_representante(representante_id)
        anterior = ticket.representante
        actor.asignar_ticket(ticket, nuevo)
        if nuevo is not anterior:
            if nuevo is not actor:
                self.notificaciones.notificar(
                    nuevo, ticket, f"{actor.nombre} te asignó el ticket #{ticket.numero_ticket}."
                )
            self.notificaciones.notificar(
                ticket.cliente, ticket, f"Tu ticket #{ticket.numero_ticket} ahora lo atiende {nuevo.nombre}."
            )
        return ticket

    @transaccional
    def poner_en_proceso(self, numero, actor: Usuario) -> Ticket:
        self.exigir_representante(actor)
        ticket = self.obtener(numero, actor)
        ticket.poner_en_proceso()
        self.notificaciones.notificar(
            ticket.cliente, ticket, f"Tu ticket #{ticket.numero_ticket} está en proceso."
        )
        return ticket

    @transaccional
    def vincular_producto(self, numero, actor: Usuario, producto_id) -> Ticket:
        """El representante asocia un producto del catálogo al ticket (obligatorio si el
        cliente escribió el producto a mano)."""
        self.exigir_representante(actor)
        ticket = self.obtener(numero, actor)
        if producto_id in (None, ""):
            raise ValidacionError("Elegí un producto del catálogo.")
        ticket.vincular_producto(self._obtener_producto(producto_id))
        return ticket

    @transaccional
    def cerrar(self, numero, actor: Usuario) -> Ticket:
        ticket = self.obtener(numero, actor)
        if actor.es_representante and ticket.producto_pendiente:
            raise ReglaNegocioError(
                f"Antes de cerrar el ticket, vinculá «{ticket.producto_otro}» con un producto del catálogo."
            )
        ticket.cerrar_ticket()
        self._avisar(ticket, actor, f"{actor.nombre} cerró el ticket #{ticket.numero_ticket}.")
        return ticket

    @transaccional
    def reabrir(self, numero, actor: Usuario) -> Ticket:
        ticket = self.obtener(numero, actor)
        ticket.abrir_ticket()
        self._avisar(ticket, actor, f"{actor.nombre} reabrió el ticket #{ticket.numero_ticket}.")
        return ticket

    # ------------------------------------------------------------ auxiliares
    def _avisar(self, ticket: Ticket, actor: Usuario, mensaje: str) -> None:
        for destinatario in ticket.destinatarios_para(actor):
            self.notificaciones.notificar(destinatario, ticket, mensaje)

    @staticmethod
    def _filtro_por_usuario(consulta, usuario: Usuario, solo_mios: bool):
        if usuario.es_cliente:
            return consulta.where(Ticket.cliente_id == usuario.id)
        if solo_mios:
            return consulta.where(Ticket.representante_id == usuario.id)
        return consulta

    @staticmethod
    def _a_estado(valor) -> EstadoTicket:
        if isinstance(valor, EstadoTicket):
            return valor
        try:
            return EstadoTicket[str(valor).strip().upper()]
        except KeyError:
            raise ValidacionError("Estado de ticket inválido.") from None

    @staticmethod
    def _a_tipo_producto(valor) -> Optional[TipoProducto]:
        if valor in (None, ""):
            return None
        if isinstance(valor, TipoProducto):
            return valor
        try:
            return TipoProducto[str(valor).strip().upper()]
        except KeyError:
            raise ValidacionError("Elegí un tipo de producto válido.") from None

    def _obtener_producto(self, producto_id) -> Optional[Producto]:
        if producto_id in (None, ""):
            return None
        producto = self.session.get(Producto, a_entero(producto_id, "Producto inválido."))
        if producto is None:
            raise NoEncontradoError("El producto seleccionado no existe.")
        return producto
