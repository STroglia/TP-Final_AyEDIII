"""Modelos del dominio (las clases del diagrama de clases, mapeadas con SQLAlchemy)."""
from app.models.enums import EstadoTicket, TipoProducto
from app.models.usuario import Cliente, Representante, Usuario
from app.models.hito import Hito
from app.models.ticket import Ticket
from app.models.notificacion import Notificacion
from app.models.producto import Categoria, Producto

__all__ = [
    "Usuario",
    "Cliente",
    "Representante",
    "Ticket",
    "Hito",
    "Notificacion",
    "Producto",
    "Categoria",
    "EstadoTicket",
    "TipoProducto",
]
