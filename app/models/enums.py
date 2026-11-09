"""Enumeraciones del diagrama de clases: EstadoTicket.

El *nombre* (ABIERTO) es lo que se guarda en la base; el *valor* ("Abierto")
es el texto que se muestra en pantalla.

Nota: TipoProducto dejó de ser una enumeración fija y pasó a ser una tabla
(ver app/models/producto.py) para que los representantes puedan crear tipos nuevos.
"""
import enum


class EstadoTicket(enum.Enum):
    ABIERTO = "Abierto"
    EN_PROCESO = "En proceso"
    CERRADO = "Cerrado"
