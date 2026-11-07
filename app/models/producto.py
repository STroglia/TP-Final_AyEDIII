"""Producto y Categoria (agregados en la versión 2 del diagrama de clases)."""
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import TipoProducto

if TYPE_CHECKING:
    from app.models.ticket import Ticket


class Categoria(Base):
    __tablename__ = "categorias"

    id_categoria: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)

    # Categoria 1 ── * Producto (pertenece)
    productos: Mapped[List["Producto"]] = relationship(back_populates="categoria")


class Producto(Base):
    __tablename__ = "productos"

    id_producto: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[TipoProducto] = mapped_column(SAEnum(TipoProducto, name="tipo_producto"))
    categoria_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categorias.id_categoria"))

    categoria: Mapped[Optional["Categoria"]] = relationship(back_populates="productos")
    # Ticket ── Producto (registra). Un mismo producto puede aparecer en varios tickets.
    tickets: Mapped[List["Ticket"]] = relationship(back_populates="producto")

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} ({self.tipo.value})"
