"""Envío y gestión de notificaciones (RF07 y RF14)."""
from typing import List, Optional

from sqlalchemy import func, select

from app.errores import NoEncontradoError, PermisoError
from app.models import Notificacion, Ticket, Usuario
from app.services.base import Servicio, transaccional
from app.utilidades import a_entero


class NotificacionService(Servicio):
    def notificar(self, destinatario: Optional[Usuario], ticket: Optional[Ticket], mensaje: str) -> Optional[Notificacion]:
        """Crea y envía una notificación. No hace commit: forma parte de la operación que la origina."""
        if destinatario is None:
            return None
        notificacion = Notificacion(destinatario=destinatario, ticket=ticket, mensaje=mensaje)
        notificacion.enviar()
        self.session.add(notificacion)
        return notificacion

    def listar(self, usuario: Usuario, solo_no_leidas: bool = False, limite: Optional[int] = None) -> List[Notificacion]:
        consulta = select(Notificacion).where(Notificacion.destinatario_id == usuario.id)
        if solo_no_leidas:
            consulta = consulta.where(Notificacion.leida.is_(False))
        consulta = consulta.order_by(Notificacion.fecha_envio.desc(), Notificacion.id.desc())
        if limite:
            consulta = consulta.limit(limite)
        return list(self.session.scalars(consulta))

    def contar_no_leidas(self, usuario: Usuario) -> int:
        consulta = select(func.count(Notificacion.id)).where(
            Notificacion.destinatario_id == usuario.id, Notificacion.leida.is_(False)
        )
        return self.session.scalar(consulta) or 0

    def obtener(self, notificacion_id, usuario: Usuario) -> Notificacion:
        notificacion = self.session.get(Notificacion, a_entero(notificacion_id, "Notificación inválida."))
        if notificacion is None:
            raise NoEncontradoError("La notificación no existe.")
        if notificacion.destinatario_id != usuario.id:
            raise PermisoError("Esa notificación no es tuya.")
        return notificacion

    @transaccional
    def marcar_leida(self, notificacion_id, usuario: Usuario) -> Notificacion:
        notificacion = self.obtener(notificacion_id, usuario)
        notificacion.marcar_leida()
        return notificacion

    @transaccional
    def marcar_todas_leidas(self, usuario: Usuario) -> int:
        pendientes = self.listar(usuario, solo_no_leidas=True)
        for notificacion in pendientes:
            notificacion.marcar_leida()
        return len(pendientes)

    @transaccional
    def marcar_leidas_de_ticket(self, usuario: Usuario, ticket: Ticket) -> int:
        """Al abrir un ticket se dan por leídas sus notificaciones."""
        pendientes = [n for n in self.listar(usuario, solo_no_leidas=True) if n.ticket_id == ticket.numero_ticket]
        for notificacion in pendientes:
            notificacion.marcar_leida()
        return len(pendientes)
