"""Notificación: aviso que recibe un usuario cuando pasa algo en uno de sus tickets.

Las notificaciones se "envían" a la bandeja interna del sistema (campanita),
que es el sistema de mensajería del ticket descripto en el enunciado.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utilidades import ahora

if TYPE_CHECKING:
    from app.models.ticket import Ticket
    from app.models.usuario import Usuario


class Notificacion(Base):
    __tablename__ = "notificaciones"

    LARGO_MAXIMO = 255

    id: Mapped[int] = mapped_column(primary_key=True)
    mensaje: Mapped[str] = mapped_column(String(LARGO_MAXIMO))
    fecha_envio: Mapped[Optional[datetime]] = mapped_column(DateTime)
    leida: Mapped[bool] = mapped_column(Boolean, default=False)
    destinatario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    ticket_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tickets.numero_ticket"))

    destinatario: Mapped["Usuario"] = relationship(back_populates="notificaciones")
    ticket: Mapped[Optional["Ticket"]] = relationship(back_populates="notificaciones")

    def __init__(self, **kwargs):
        kwargs.setdefault("leida", False)
        if "mensaje" in kwargs:
            kwargs["mensaje"] = (kwargs["mensaje"] or "")[: self.LARGO_MAXIMO]
        super().__init__(**kwargs)

    @property
    def enviada(self) -> bool:
        return self.fecha_envio is not None

    def enviar(self) -> "Notificacion":
        """enviar(): la deja disponible en la bandeja del destinatario."""
        if self.fecha_envio is None:
            self.fecha_envio = ahora()
        return self

    def marcar_leida(self) -> None:
        self.leida = True
