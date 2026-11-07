"""Iteración 5 (TDD) — Productos, tipos de producto y categorías (RF15–RF17)."""
import pytest

from app.errores import DuplicadoError, NoEncontradoError, ValidacionError
from app.models import TipoProducto


class TestCategorias:
    def test_crear_categoria(self, productos):
        categoria = productos.crear_categoria("  Microondas ")
        assert categoria.id_categoria is not None
        assert categoria.nombre == "Microondas"

    def test_no_se_duplican_categorias(self, productos, categoria):
        with pytest.raises(DuplicadoError):
            productos.crear_categoria("HELADERAS")

    def test_nombre_obligatorio(self, productos):
        with pytest.raises(ValidacionError):
            productos.crear_categoria("")

    def test_listar_categorias_en_orden_alfabetico(self, productos):
        productos.crear_categoria("Lavarropas")
        productos.crear_categoria("Cafeteras")
        assert [c.nombre for c in productos.listar_categorias()] == ["Cafeteras", "Lavarropas"]


class TestProductos:
    def test_registrar_producto(self, productos, categoria):
        producto = productos.registrar_producto("Heladera Cíclica", "LINEA_BLANCA", categoria.id_categoria)
        assert producto.tipo is TipoProducto.LINEA_BLANCA
        assert producto.categoria is categoria

    def test_tipo_invalido(self, productos, categoria):
        with pytest.raises(ValidacionError):
            productos.registrar_producto("Algo", "AUTOS", categoria.id_categoria)

    def test_categoria_obligatoria(self, productos):
        with pytest.raises(ValidacionError):
            productos.registrar_producto("Algo", "COCINA", None)

    def test_categoria_inexistente(self, productos):
        with pytest.raises(NoEncontradoError):
            productos.registrar_producto("Algo", "COCINA", 999)

    def test_no_se_duplican_productos(self, productos, producto, categoria):
        with pytest.raises(DuplicadoError):
            productos.registrar_producto("heladera no frost 360l", "LINEA_BLANCA", categoria.id_categoria)

    def test_listar_y_filtrar(self, productos, categoria):
        otra = productos.crear_categoria("Pava eléctrica")
        heladera = productos.registrar_producto("Heladera", "LINEA_BLANCA", categoria.id_categoria)
        pava = productos.registrar_producto("Pava 1.7L", "PEQUENIOS_ELECTRODOMESTICOS", otra.id_categoria)
        assert productos.listar_productos() == [heladera, pava]
        assert productos.listar_productos(tipo="PEQUENIOS_ELECTRODOMESTICOS") == [pava]
        assert productos.listar_productos(categoria_id=categoria.id_categoria) == [heladera]
        assert productos.listar_productos(busqueda="pava") == [pava]

    def test_actualizar_producto(self, productos, producto, categoria):
        productos.actualizar_producto(producto.id_producto, "Heladera Inverter", "ELECTRO", categoria.id_categoria)
        assert producto.nombre == "Heladera Inverter"
        assert producto.tipo is TipoProducto.ELECTRO
