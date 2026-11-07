"""Usuarios del sistema: Usuario (abstracta), Cliente y Representante.

Se usa *herencia de tabla única* (single table inheritance): los tres comparten
la tabla `usuarios` y la columna `tipo` indica si la fila es un cliente o un
representante. Así se respeta la herencia del diagrama de clases.
"""
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.database import Base
from app.errores import PermisoError, ValidacionError

if TYPE_CHECKING:
    from app.models.hito import Hito
    from app.models.notificacion import Notificacion
    from app.models.producto import Producto
    from app.models.ticket import Ticket

LARGO_MINIMO_PASSWORD = 6


class Usuario(Base):
    """Clase abstracta: no se crean usuarios "sueltos", solo Clientes o Representantes."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    telefono: Mapped[Optional[str]] = mapped_column(String(30))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    tipo: Mapped[str] = mapped_column(String(20))

    # Usuario 1 ── * Hito        (crea)
    hitos: Mapped[List["Hito"]] = relationship(back_populates="autor")
    # Usuario 1 ── * Notificacion (recibe)
    notificaciones: Mapped[List["Notificacion"]] = relationship(
        back_populates="destinatario", cascade="all, delete-orphan"
    )

    __mapper_args__ = {"polymorphic_on": "tipo", "polymorphic_abstract": True}

    def __init__(self, password: Optional[str] = None, **kwargs):
        kwargs.setdefault("activo", True)
        super().__init__(**kwargs)
        if password is not None:
            self.set_password(password)

    # ---------------------------------------------------------------- seguridad
    def set_password(self, password: str) -> None:
        """Guarda la contraseña *hasheada* (nunca en texto plano)."""
        if not password or len(password) < LARGO_MINIMO_PASSWORD:
            raise ValidacionError(
                f"La contraseña debe tener al menos {LARGO_MINIMO_PASSWORD} caracteres."
            )
        self.password_hash = generate_password_hash(password)

    def login(self, password: str) -> bool:
        """login(): bool del diagrama. True si la contraseña es correcta y el usuario está activo."""
        if not self.activo or not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password or "")

    def logout(self) -> None:
        """logout(): void del diagrama. La sesión web se limpia en la capa web."""
        return None

    # ---------------------------------------------------------------- roles
    @property
    def es_cliente(self) -> bool:
        return False

    @property
    def es_representante(self) -> bool:
        return False

    @property
    def rol(self) -> str:
        return "Usuario"

    @property
    def iniciales(self) -> str:
        partes = (self.nombre or "?").split()
        return "".join(p[0] for p in partes[:2]).upper()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id} {self.email}>"


class Cliente(Usuario):
    """Cliente: posee tickets, los consulta y registra hitos en ellos."""

    dni: Mapped[Optional[str]] = mapped_column(String(15), unique=True)

    # Cliente 1 ── * Ticket (posee)
    tickets: Mapped[List["Ticket"]] = relationship(
        back_populates="cliente", foreign_keys="Ticket.cliente_id"
    )

    __mapper_args__ = {"polymorphic_identity": "cliente"}

    @property
    def es_cliente(self) -> bool:
        return True

    @property
    def rol(self) -> str:
        return "Cliente"

    def crear_ticket(
        self,
        descripcion: str,
        producto: Optional["Producto"] = None,
        representante: Optional["Representante"] = None,
        tipo_producto=None,
    ) -> "Ticket":
        """crearTicket(): el cliente abre un ticket a su propio nombre (no puede hacerlo para otro)."""
        from app.models.ticket import Ticket

        return Ticket(
            cliente=self, representante=representante, descripcion=descripcion,
            producto=producto, tipo_producto=tipo_producto,
        )

    def consultar_tickets(self) -> List["Ticket"]:
        """consultarTickets(): todos sus tickets, del más nuevo al más viejo."""
        return sorted(self.tickets, key=lambda t: t.fecha_creacion, reverse=True)

    def registrar_hito(self, ticket: "Ticket", mensaje: str) -> "Hito":
        """registrarHito(): solo puede escribir en sus propios tickets."""
        if ticket.cliente is not self:
            raise PermisoError("Solo podés escribir en tus propios tickets.")
        return ticket.agregar_hito(self, mensaje)


class Representante(Usuario):
    """Representante de atención: crea, gestiona y responde tickets."""

    # Representante 1 ── * Ticket (gestiona)
    tickets_gestionados: Mapped[List["Ticket"]] = relationship(
        back_populates="representante", foreign_keys="Ticket.representante_id"
    )

    __mapper_args__ = {"polymorphic_identity": "representante"}

    @property
    def es_representante(self) -> bool:
        return True

    @property
    def rol(self) -> str:
        return "Representante"

    def crear_ticket(
        self, cliente: Cliente, descripcion: str, producto: Optional["Producto"] = None, tipo_producto=None
    ) -> "Ticket":
        """crearTicket(): el representante que lo crea queda asignado al ticket (CU001)."""
        from app.models.ticket import Ticket

        return Ticket(
            cliente=cliente, representante=self, descripcion=descripcion,
            producto=producto, tipo_producto=tipo_producto,
        )

    def asignar_ticket(self, ticket: "Ticket", representante: Optional["Representante"] = None) -> None:
        """asignarTicket(): se lo asigna a sí mismo o a otro representante."""
        ticket.asignar(representante or self)

    def registrar_hito(self, ticket: "Ticket", mensaje: str) -> "Hito":
        """registrarHito(): un representante puede responder cualquier ticket."""
        return ticket.agregar_hito(self, mensaje)
