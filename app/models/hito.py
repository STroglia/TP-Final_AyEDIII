"""Hito: cada mensaje del historial de un ticket (composición Ticket ◆── Hito)."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.errores import ValidacionError
from app.utilidades import ahora

if TYPE_CHECKING:
    from app.models.ticket import Ticket
    from app.models.usuario import Usuario


class Hito(Base):
    __tablename__ = "hitos"

    LARGO_MAXIMO = 2000

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=ahora)
    mensaje: Mapped[str] = mapped_column(Text)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.numero_ticket"))
    autor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))

    ticket: Mapped["Ticket"] = relationship(back_populates="hitos")
    autor: Mapped["Usuario"] = relationship(back_populates="hitos")

    def __init__(self, mensaje: str = "", **kwargs):
        # Se valida ANTES de crear el objeto: un hito vacío nunca llega a existir.
        kwargs["mensaje"] = self.validar_mensaje(mensaje)
        kwargs.setdefault("fecha", ahora())
        super().__init__(**kwargs)

    @classmethod
    def validar_mensaje(cls, texto: str) -> str:
        """El comentario no puede estar vacío (CU003, paso 3)."""
        texto = (texto or "").strip()
        if not texto:
            raise ValidacionError("El comentario no puede estar vacío.")
        if len(texto) > cls.LARGO_MAXIMO:
            raise ValidacionError(f"El comentario no puede superar los {cls.LARGO_MAXIMO} caracteres.")
        return texto

    def registrar_mensaje(self, texto: str) -> None:
        """registrarMensaje(): reemplaza el texto del hito validándolo."""
        self.mensaje = self.validar_mensaje(texto)
        self.fecha = ahora()

    def es_de(self, usuario) -> bool:
        return usuario is not None and (self.autor is usuario or self.autor_id == usuario.id)
