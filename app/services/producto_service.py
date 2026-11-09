"""Gestión de productos, tipos de producto y categorías (RF15–RF17)."""
import re
import unicodedata
from typing import List, Optional

from sqlalchemy import func, select

from app.errores import DuplicadoError, NoEncontradoError, ValidacionError
from app.models import Categoria, Producto, TipoProducto
from app.services.base import Servicio, transaccional
from app.utilidades import a_entero, texto_limpio


class ProductoService(Servicio):
    # ------------------------------------------------------------ tipos de producto
    def listar_tipos(self) -> List[TipoProducto]:
        return list(self.session.scalars(select(TipoProducto).order_by(func.lower(TipoProducto.nombre))))

    def obtener_tipo(self, valor) -> TipoProducto:
        """Busca un tipo por su código (LINEA_BLANCA) o devuelve el mismo si ya es un TipoProducto."""
        if isinstance(valor, TipoProducto):
            return valor
        codigo = str(valor or "").strip().upper()
        tipo = self.session.get(TipoProducto, codigo) if codigo else None
        if tipo is None:
            raise ValidacionError("Elegí un tipo de producto válido.")
        return tipo

    @transaccional
    def crear_tipo(self, nombre: str) -> TipoProducto:
        return self._crear_tipo(nombre)

    def _crear_tipo(self, nombre: str, reutilizar: bool = False) -> TipoProducto:
        """Crea un tipo de producto. Con `reutilizar=True`, si ya existe uno con ese nombre lo devuelve."""
        nombre = self._validar_nombre(nombre, "tipo de producto", 60)
        existente = self.session.scalar(
            select(TipoProducto).where(func.lower(TipoProducto.nombre) == nombre.lower())
        )
        if existente is not None:
            if reutilizar:
                return existente
            raise DuplicadoError(f"Ya existe el tipo de producto «{existente.nombre}».")
        codigo = self._generar_codigo(nombre)
        if not codigo:
            raise ValidacionError("El nombre del tipo de producto debe tener letras o números.")
        base, numero = codigo, 2
        while self.session.get(TipoProducto, codigo) is not None:
            codigo = f"{base[:36]}_{numero}"
            numero += 1
        tipo = TipoProducto(codigo=codigo, nombre=nombre)
        self.session.add(tipo)
        self.session.flush()
        return tipo

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
        return self._crear_categoria(nombre)

    def _crear_categoria(self, nombre: str, reutilizar: bool = False) -> Categoria:
        """Crea una categoría. Con `reutilizar=True`, si ya existe una con ese nombre la devuelve."""
        nombre = self._validar_nombre(nombre, "categoría", 80)
        existente = self.session.scalar(
            select(Categoria).where(func.lower(Categoria.nombre) == nombre.lower())
        )
        if existente is not None:
            if reutilizar:
                return existente
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
            consulta = consulta.where(Producto.tipo_codigo == self.obtener_tipo(tipo).codigo)
        if categoria_id not in (None, ""):
            consulta = consulta.where(Producto.categoria_id == a_entero(categoria_id, "Categoría inválida."))
        texto = texto_limpio(busqueda).lower()
        if texto:
            consulta = consulta.where(func.lower(Producto.nombre).like(f"%{texto}%"))
        consulta = consulta.order_by(func.lower(Producto.nombre))
        return list(self.session.scalars(consulta))

    @transaccional
    def registrar_producto(
        self, nombre: str, tipo, categoria_id, tipo_nuevo: Optional[str] = None,
        categoria_nueva: Optional[str] = None,
    ) -> Producto:
        """Registra un producto.

        Si se indica `tipo_nuevo` y/o `categoria_nueva`, se crean en la misma operación
        (si ya existen con ese nombre, se usan las existentes). Si algo falla, no se guarda nada.
        """
        nombre = self._validar_nombre(nombre, "producto", 120)
        self._verificar_nombre_disponible(nombre)
        tipo, categoria = self._resolver_tipo_y_categoria(tipo, categoria_id, tipo_nuevo, categoria_nueva)
        producto = Producto(nombre=nombre, tipo=tipo, categoria=categoria)
        self.session.add(producto)
        self.session.flush()
        return producto

    @transaccional
    def actualizar_producto(
        self, producto_id, nombre: str, tipo, categoria_id, tipo_nuevo: Optional[str] = None,
        categoria_nueva: Optional[str] = None,
    ) -> Producto:
        producto = self.obtener(producto_id)
        nombre = self._validar_nombre(nombre, "producto", 120)
        self._verificar_nombre_disponible(nombre, excepto=producto)
        tipo, categoria = self._resolver_tipo_y_categoria(tipo, categoria_id, tipo_nuevo, categoria_nueva)
        producto.nombre, producto.tipo, producto.categoria = nombre, tipo, categoria
        return producto

    # ------------------------------------------------------------ auxiliares
    def _resolver_tipo_y_categoria(self, tipo, categoria_id, tipo_nuevo, categoria_nueva):
        if texto_limpio(tipo_nuevo):
            tipo = self._crear_tipo(tipo_nuevo, reutilizar=True)
        else:
            tipo = self.obtener_tipo(tipo)
        if texto_limpio(categoria_nueva):
            categoria = self._crear_categoria(categoria_nueva, reutilizar=True)
        else:
            categoria = self.obtener_categoria(categoria_id)
        return tipo, categoria

    @staticmethod
    def _generar_codigo(nombre: str) -> str:
        """'Climatización y calefacción' -> 'CLIMATIZACION_Y_CALEFACCION'."""
        sin_acentos = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
        return re.sub(r"[^A-Z0-9]+", "_", sin_acentos.upper()).strip("_")[:40]

    @staticmethod
    def _validar_nombre(nombre: str, que: str, largo_maximo: int) -> str:
        nombre = " ".join(texto_limpio(nombre).split())
        if not nombre:
            raise ValidacionError(f"El nombre de la {que} es obligatorio." if que == "categoría"
                                  else f"El nombre del {que} es obligatorio.")
        if len(nombre) > largo_maximo:
            raise ValidacionError(f"El nombre no puede superar los {largo_maximo} caracteres.")
        return nombre

    def _verificar_nombre_disponible(self, nombre: str, excepto: Optional[Producto] = None) -> None:
        existente = self.session.scalar(select(Producto).where(func.lower(Producto.nombre) == nombre.lower()))
        if existente is not None and existente is not excepto:
            raise DuplicadoError(f"Ya existe un producto llamado «{existente.nombre}».")
