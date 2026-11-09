"""Producto, Categoria y TipoProducto (agregados en la versión 2 del diagrama de clases)."""
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.ticket import Ticket


# Tipos con los que arranca el sistema. Los representantes pueden crear más.
TIPOS_PRODUCTO_INICIALES = (
    ("LINEA_BLANCA", "Línea blanca"),
    ("COCINA", "Cocina"),
    ("ELECTRO", "Electro"),
    ("PEQUENIOS_ELECTRODOMESTICOS", "Pequeños electrodomésticos"),
)


class TipoProducto(Base):
    """Tipo de producto (Línea blanca, Cocina...).

    Se guarda por su `codigo` (p. ej. LINEA_BLANCA) y se muestra por su `nombre`.
    `name` y `value` son alias para que las plantillas sigan funcionando igual que
    cuando el tipo era una enumeración.
    """

    __tablename__ = "tipos_producto"

    codigo: Mapped[str] = mapped_column(String(40), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), unique=True)

    productos: Mapped[List["Producto"]] = relationship(back_populates="tipo")

    @property
    def name(self) -> str:
        return self.codigo

    @property
    def value(self) -> str:
        return self.nombre

    def __repr__(self) -> str:
        return f"<TipoProducto {self.codigo}>"


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
    # La columna se sigue llamando "tipo" y guarda el código del tipo (compatible con bases anteriores).
    tipo_codigo: Mapped[str] = mapped_column("tipo", ForeignKey("tipos_producto.codigo"))
    categoria_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categorias.id_categoria"))

    tipo: Mapped["TipoProducto"] = relationship(back_populates="productos")
    categoria: Mapped[Optional["Categoria"]] = relationship(back_populates="productos")
    # Ticket ── Producto (registra). Un mismo producto puede aparecer en varios tickets.
    tickets: Mapped[List["Ticket"]] = relationship(back_populates="producto")

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} ({self.tipo.value})"
