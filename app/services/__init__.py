"""Servicios: la lógica de negocio. Usan los modelos y guardan en la base de datos.

La capa web solo llama a estos servicios; así la lógica se puede testear sin navegador.
"""
from app.services.notificacion_service import NotificacionService
from app.services.producto_service import ProductoService
from app.services.ticket_service import TicketService
from app.services.usuario_service import UsuarioService

__all__ = ["UsuarioService", "TicketService", "NotificacionService", "ProductoService"]
