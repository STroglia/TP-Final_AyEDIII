"""Gestión de productos y categorías (RF15–RF17)."""
from typing import List, Optional

from sqlalchemy import func, select

from app.errores import DuplicadoError, NoEncontradoError, ValidacionError
from app.models import Categoria, Producto, TipoProducto
from app.services.base import Servicio, transaccional
from app.utilidades import a_entero, texto_limpio


class ProductoService(Servicio):
    # ------------------------------------------------------------ categorías
    def listar_categorias(self) -> List[Categoria]:
        return list(self.session.scalars(select(Categoria).order_by(func.lower(Categoria.nombre))))

    def obtener_categoria(self, categoria_id) -> Categoria:
        if categoria_id in (None, ""):
            raise ValidacionError("Elegí una categoría.")
        categoria = self.session.get(Categoria, a_entero(categoria_id, "Categoría inválida."))
        if categoria is None:
            raise NoEncontradoError("La categoría seleccionada no existe.")
        return categoria

    @transaccional
    def crear_categoria(self, nombre: str) -> Categoria:
        nombre = self._validar_nombre(nombre, "categoría", 80)
        existente = self.session.scalar(
            select(Categoria).where(func.lower(Categoria.nombre) == nombre.lower())
        )
        if existente is not None:
            raise DuplicadoError(f"Ya existe la categoría «{existente.nombre}».")
        categoria = Categoria(nombre=nombre)
        self.session.add(categoria)
        self.session.flush()
        return categoria

    # ------------------------------------------------------------ productos
    def obtener(self, producto_id) -> Producto:
        producto = self.session.get(Producto, a_entero(producto_id, "Producto inválido."))
        if producto is None:
            raise NoEncontradoError("El producto no existe.")
        return producto

    def listar_productos(
        self, tipo: Optional[str] = None, categoria_id=None, busqueda: Optional[str] = None
    ) -> List[Producto]:
        consulta = select(Producto)
        if tipo:
            consulta = consulta.where(Producto.tipo == self._a_tipo(tipo))
        if categoria_id not in (None, ""):
            consulta = consulta.where(Producto.categoria_id == a_entero(categoria_id, "Categoría inválida."))
        texto = texto_limpio(busqueda).lower()
        if texto:
            consulta = consulta.where(func.lower(Producto.nombre).like(f"%{texto}%"))
        consulta = consulta.order_by(func.lower(Producto.nombre))
        return list(self.session.scalars(consulta))

    @transaccional
    def registrar_producto(self, nombre: str, tipo, categoria_id) -> Producto:
        nombre = self._validar_nombre(nombre, "producto", 120)
        tipo = self._a_tipo(tipo)
        categoria = self.obtener_categoria(categoria_id)
        self._verificar_nombre_disponible(nombre)
        producto = Producto(nombre=nombre, tipo=tipo, categoria=categoria)
        self.session.add(producto)
        self.session.flush()
        return producto

    @transaccional
    def actualizar_producto(self, producto_id, nombre: str, tipo, categoria_id) -> Producto:
        producto = self.obtener(producto_id)
        nombre = self._validar_nombre(nombre, "producto", 120)
        tipo = self._a_tipo(tipo)
        categoria = self.obtener_categoria(categoria_id)
        self._verificar_nombre_disponible(nombre, excepto=producto)
        producto.nombre, producto.tipo, producto.categoria = nombre, tipo, categoria
        return producto

    # ------------------------------------------------------------ auxiliares
    @staticmethod
    def _validar_nombre(nombre: str, que: str, largo_maximo: int) -> str:
        nombre = " ".join(texto_limpio(nombre).split())
        if not nombre:
            raise ValidacionError(f"El nombre del {que} es obligatorio." if que == "producto"
                                  else f"El nombre de la {que} es obligatorio.")
        if len(nombre) > largo_maximo:
            raise ValidacionError(f"El nombre no puede superar los {largo_maximo} caracteres.")
        return nombre

    @staticmethod
    def _a_tipo(valor) -> TipoProducto:
        if isinstance(valor, TipoProducto):
            return valor
        try:
            return TipoProducto[str(valor).strip().upper()]
        except KeyError:
            raise ValidacionError("Elegí un tipo de producto válido.") from None

    def _verificar_nombre_disponible(self, nombre: str, excepto: Optional[Producto] = None) -> None:
        existente = self.session.scalar(select(Producto).where(func.lower(Producto.nombre) == nombre.lower()))
        if existente is not None and existente is not excepto:
            raise DuplicadoError(f"Ya existe un producto llamado «{existente.nombre}».")
