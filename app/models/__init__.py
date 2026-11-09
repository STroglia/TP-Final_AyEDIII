"""Modelos del dominio (las clases del diagrama de clases, mapeadas con SQLAlchemy)."""
from app.models.enums import EstadoTicket
from app.models.usuario import Cliente, Representante, Usuario
from app.models.hito import Hito
from app.models.ticket import Ticket
from app.models.notificacion import Notificacion
from app.models.producto import TIPOS_PRODUCTO_INICIALES, Categoria, Producto, TipoProducto

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
    "TIPOS_PRODUCTO_INICIALES",
]
