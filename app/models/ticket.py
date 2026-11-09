"""Ticket: el caso de soporte. Contiene las reglas del workflow de estados.

Workflow:
    ABIERTO ──(un representante responde / lo toma)──> EN_PROCESO
    ABIERTO | EN_PROCESO ──(cerrar)──> CERRADO
    CERRADO ──(reabrir)──> ABIERTO
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.errores import PermisoError, ReglaNegocioError, ValidacionError
from app.models.enums import EstadoTicket
from app.models.hito import Hito
from app.utilidades import ahora, resumir

if TYPE_CHECKING:
    from app.models.notificacion import Notificacion
    from app.models.producto import Producto, TipoProducto
    from app.models.usuario import Cliente, Representante, Usuario


class Ticket(Base):
    __tablename__ = "tickets"

    LARGO_MINIMO_DESCRIPCION = 10
    LARGO_MAXIMO_DESCRIPCION = 2000

    numero_ticket: Mapped[int] = mapped_column(primary_key=True)
    descripcion: Mapped[str] = mapped_column(Text)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=ahora)
    fecha_cierre: Mapped[Optional[datetime]] = mapped_column(DateTime)
    estado: Mapped[EstadoTicket] = mapped_column(
        SAEnum(EstadoTicket, name="estado_ticket"), default=EstadoTicket.ABIERTO
    )
    cliente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    representante_id: Mapped[Optional[int]] = mapped_column(ForeignKey("usuarios.id"))
    producto_id: Mapped[Optional[int]] = mapped_column(ForeignKey("productos.id_producto"))
    # Quién abrió el ticket: el propio cliente o un representante (vacío en tickets viejos).
    creado_por_id: Mapped[Optional[int]] = mapped_column(ForeignKey("usuarios.id"))
    # Tipo de producto (Línea blanca, Cocina...). Se guarda en el ticket además del producto
    # para poder sacar estadísticas por tipo.
    # La columna guarda el código del tipo (p. ej. LINEA_BLANCA).
    tipo_producto_codigo: Mapped[Optional[str]] = mapped_column(
        "tipo_producto", ForeignKey("tipos_producto.codigo")
    )
    # Producto escrito a mano por el cliente cuando no lo encuentra en el catálogo.
    producto_otro: Mapped[Optional[str]] = mapped_column(String(120))

    cliente: Mapped["Cliente"] = relationship(back_populates="tickets", foreign_keys=[cliente_id])
    representante: Mapped[Optional["Representante"]] = relationship(
        back_populates="tickets_gestionados", foreign_keys=[representante_id]
    )
    creado_por: Mapped[Optional["Usuario"]] = relationship(foreign_keys=[creado_por_id])
    producto: Mapped[Optional["Producto"]] = relationship(back_populates="tickets")
    tipo_producto: Mapped[Optional["TipoProducto"]] = relationship()
    # Composición: si se borra el ticket, se borran sus hitos.
    hitos: Mapped[List["Hito"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by=lambda: (Hito.fecha, Hito.id),
    )
    notificaciones: Mapped[List["Notificacion"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )

    def __init__(self, cliente=None, descripcion: str = "", representante=None, **kwargs):
        # Validaciones antes de construir el objeto.
        texto = self.validar_descripcion(descripcion)
        if cliente is None or not getattr(cliente, "es_cliente", False):
            raise ValidacionError("El ticket debe estar asociado a un cliente.")
        if not cliente.activo:
            raise ReglaNegocioError("El cliente está dado de baja: no se le pueden crear tickets.")
        if representante is not None and not getattr(representante, "es_representante", False):
            raise ValidacionError("Solo un representante puede gestionar un ticket.")
        producto = kwargs.get("producto")
        tipo = kwargs.get("tipo_producto")
        if producto is not None:
            if tipo is not None and tipo.codigo != producto.tipo.codigo:
                raise ValidacionError("El producto elegido no corresponde al tipo de producto seleccionado.")
            kwargs["tipo_producto"] = producto.tipo
        kwargs.setdefault("estado", EstadoTicket.ABIERTO)
        kwargs.setdefault("fecha_creacion", ahora())
        super().__init__(cliente=cliente, descripcion=texto, representante=representante, **kwargs)

    # ---------------------------------------------------------------- validación
    @classmethod
    def validar_descripcion(cls, texto: str) -> str:
        texto = (texto or "").strip()
        if not texto:
            raise ValidacionError("La descripción de la incidencia es obligatoria.")
        if len(texto) < cls.LARGO_MINIMO_DESCRIPCION:
            raise ValidacionError(
                f"La descripción debe tener al menos {cls.LARGO_MINIMO_DESCRIPCION} caracteres."
            )
        if len(texto) > cls.LARGO_MAXIMO_DESCRIPCION:
            raise ValidacionError(
                f"La descripción no puede superar los {cls.LARGO_MAXIMO_DESCRIPCION} caracteres."
            )
        return texto

    # ---------------------------------------------------------------- consultas
    @property
    def esta_cerrado(self) -> bool:
        return self.estado is EstadoTicket.CERRADO

    @property
    def producto_pendiente(self) -> bool:
        """El cliente escribió el producto a mano y todavía no se vinculó con uno del catálogo."""
        return bool(self.producto_otro) and self.producto is None and self.producto_id is None

    def vincular_producto(self, producto: "Producto") -> None:
        """Asocia el ticket a un producto del catálogo (el tipo pasa a ser el del producto).

        Se conserva `producto_otro` para saber qué había escrito el cliente.
        """
        if producto is None:
            raise ValidacionError("Elegí un producto del catálogo.")
        self.producto = producto
        self.tipo_producto = producto.tipo

    @property
    def titulo(self) -> str:
        return resumir(self.descripcion, 70)

    @property
    def ultima_actividad(self) -> datetime:
        return self.hitos[-1].fecha if self.hitos else self.fecha_creacion

    def puede_ver(self, usuario: Optional["Usuario"]) -> bool:
        """Un representante ve todos los tickets; un cliente, solo los suyos."""
        if usuario is None or not usuario.activo:
            return False
        if usuario.es_representante:
            return True
        return self.cliente is usuario or (
            self.cliente_id is not None and self.cliente_id == usuario.id
        )

    def destinatarios_para(self, autor: "Usuario") -> List["Usuario"]:
        """¿A quién hay que notificar cuando `autor` hace algo en el ticket? Al "otro actor"."""
        if autor.es_cliente:
            return [self.representante] if self.representante is not None else []
        destinatarios = [self.cliente]
        if self.representante is not None and self.representante is not autor:
            destinatarios.append(self.representante)
        return destinatarios

    # ---------------------------------------------------------------- workflow
    def abrir_ticket(self) -> None:
        """abrirTicket(): reabre un ticket cerrado (vuelve a ABIERTO)."""
        if not self.esta_cerrado:
            raise ReglaNegocioError("Solo se puede reabrir un ticket cerrado.")
        self.estado = EstadoTicket.ABIERTO
        self.fecha_cierre = None

    def poner_en_proceso(self) -> None:
        if self.estado is not EstadoTicket.ABIERTO:
            raise ReglaNegocioError("Solo un ticket abierto puede pasar a 'En proceso'.")
        self.estado = EstadoTicket.EN_PROCESO

    def cerrar_ticket(self) -> None:
        """cerrarTicket()"""
        if self.esta_cerrado:
            raise ReglaNegocioError("El ticket ya está cerrado.")
        self.estado = EstadoTicket.CERRADO
        self.fecha_cierre = ahora()

    def asignar(self, representante: "Representante") -> None:
        if representante is None or not representante.es_representante:
            raise ValidacionError("El ticket solo se puede asignar a un representante.")
        if not representante.activo:
            raise ReglaNegocioError("No se puede asignar el ticket a un representante dado de baja.")
        if self.esta_cerrado:
            raise ReglaNegocioError("No se puede reasignar un ticket cerrado.")
        self.representante = representante

    @property
    def en_cola(self) -> bool:
        """Está en la cola (backlog): sin representante y sin cerrar."""
        return self.representante is None and self.representante_id is None and not self.esta_cerrado

    def tomar(self, representante: "Representante") -> None:
        """Un representante toma el ticket de la cola: queda asignado a él y pasa a 'En proceso'."""
        if self.esta_cerrado:
            raise ReglaNegocioError("El ticket está cerrado.")
        if self.representante is not None and self.representante is not representante:
            raise ReglaNegocioError(f"Este ticket ya lo tomó {self.representante.nombre}.")
        self.asignar(representante)
        if self.estado is EstadoTicket.ABIERTO:
            self.estado = EstadoTicket.EN_PROCESO

    def agregar_hito(self, autor: "Usuario", mensaje: str) -> Hito:
        """agregarHito(): suma un mensaje al historial del ticket (CU003)."""
        if self.esta_cerrado:
            raise ReglaNegocioError("El ticket está cerrado. Reabrilo para agregar hitos.")
        if not self.puede_ver(autor):
            raise PermisoError("No tenés acceso a este ticket.")
        texto = Hito.validar_mensaje(mensaje)
        hito = Hito(mensaje=texto)
        self.hitos.append(hito)  # primero se agrega al ticket (queda en la sesión)...
        hito.autor = autor  # ...y después se vincula con su autor
        # Si un representante responde un ticket de la cola, lo toma (queda asignado a él).
        if autor.es_representante and self.representante is None:
            self.asignar(autor)
        # Cuando un representante responde un ticket abierto, pasa a "En proceso".
        if autor.es_representante and self.estado is EstadoTicket.ABIERTO:
            self.estado = EstadoTicket.EN_PROCESO
        return hito

    def __repr__(self) -> str:
        return f"<Ticket #{self.numero_ticket} {self.estado.name}>"
