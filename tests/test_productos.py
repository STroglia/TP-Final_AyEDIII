"""Iteración 5 (TDD) — Productos, tipos de producto y categorías (RF15–RF17)."""
import pytest

from app.errores import DuplicadoError, NoEncontradoError, ValidacionError


class TestTiposDeProducto:
    def test_hay_tipos_iniciales(self, productos):
        codigos = {t.codigo for t in productos.listar_tipos()}
        assert {"LINEA_BLANCA", "COCINA", "ELECTRO", "PEQUENIOS_ELECTRODOMESTICOS"} <= codigos

    def test_crear_tipo(self, productos):
        tipo = productos.crear_tipo("  Climatización ")
        assert tipo.nombre == "Climatización"
        assert tipo.codigo == "CLIMATIZACION"
        assert tipo in productos.listar_tipos()

    def test_no_se_duplican_tipos(self, productos):
        with pytest.raises(DuplicadoError):
            productos.crear_tipo("línea BLANCA")

    def test_nombre_de_tipo_obligatorio(self, productos):
        with pytest.raises(ValidacionError):
            productos.crear_tipo("   ")


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
        assert producto.tipo.codigo == "LINEA_BLANCA"
        assert producto.categoria is categoria

    def test_registrar_producto_con_tipo_y_categoria_nuevos(self, productos):
        """Caso del producto escrito a mano (p. ej. «Caloventor vertical»): el tipo y la
        categoría no existen y se crean en el mismo paso que el producto."""
        producto = productos.registrar_producto(
            "Caloventor vertical", "", "", tipo_nuevo="Climatización", categoria_nueva="Caloventores"
        )
        assert producto.tipo.nombre == "Climatización"
        assert producto.categoria.nombre == "Caloventores"
        assert producto.categoria in productos.listar_categorias()

    def test_tipo_y_categoria_nuevos_reutilizan_los_existentes(self, productos, categoria):
        producto = productos.registrar_producto("Freezer", "", "", tipo_nuevo="línea blanca", categoria_nueva="heladeras")
        assert producto.tipo.codigo == "LINEA_BLANCA"
        assert producto.categoria is categoria

    def test_si_falla_no_se_crean_tipo_ni_categoria(self, productos, producto):
        with pytest.raises(DuplicadoError):
            productos.registrar_producto(
                "Heladera No Frost 360L", "", "", tipo_nuevo="Refrigeración", categoria_nueva="Frío"
            )
        assert "Refrigeración" not in [t.nombre for t in productos.listar_tipos()]
        assert "Frío" not in [c.nombre for c in productos.listar_categorias()]

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
        assert producto.tipo.codigo == "ELECTRO"
