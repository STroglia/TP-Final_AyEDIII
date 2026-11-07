"""Enumeraciones del diagrama de clases: EstadoTicket y TipoProducto.

El *nombre* (ABIERTO) es lo que se guarda en la base; el *valor* ("Abierto")
es el texto que se muestra en pantalla.
"""
import enum


class EstadoTicket(enum.Enum):
    ABIERTO = "Abierto"
    EN_PROCESO = "En proceso"
    CERRADO = "Cerrado"


class TipoProducto(enum.Enum):
    LINEA_BLANCA = "Línea blanca"
    COCINA = "Cocina"
    ELECTRO = "Electro"
    PEQUENIOS_ELECTRODOMESTICOS = "Pequeños electrodomésticos"
