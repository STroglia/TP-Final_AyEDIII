"""Iteración 2 (TDD) — Gestión de usuarios, clientes y representantes.

Cubre RF01–RF04 y los RNF de seguridad (login) y no duplicación de usuarios.
"""
import pytest

from app.errores import DuplicadoError, ReglaNegocioError, ValidacionError
from app.models import Cliente, Representante

from conftest import PASSWORD


class TestAltaDeUsuarios:
    def test_registrar_cliente(self, usuarios):
        cliente = usuarios.registrar_cliente("Juan Pérez", "juan@mail.com", PASSWORD, dni="30.111.222")
        assert isinstance(cliente, Cliente)
        assert cliente.id is not None
        assert cliente.dni == "30111222"  # se guardan solo los números

    def test_registrar_representante(self, usuarios):
        rep = usuarios.registrar_representante("Laura Gómez", "laura@soporte.com", PASSWORD)
        assert isinstance(rep, Representante)

    def test_el_email_se_guarda_en_minusculas(self, usuarios):
        cliente = usuarios.registrar_cliente("Juan Pérez", "  Juan@Mail.COM ", PASSWORD)
        assert cliente.email == "juan@mail.com"

    def test_no_se_duplican_usuarios_con_el_mismo_email(self, usuarios, cliente):
        with pytest.raises(DuplicadoError):
            usuarios.registrar_cliente("Otra Persona", "CARLA@mail.com", PASSWORD)

    def test_un_representante_no_puede_usar_el_email_de_un_cliente(self, usuarios, cliente):
        with pytest.raises(DuplicadoError):
            usuarios.registrar_representante("Otra Persona", "carla@mail.com", PASSWORD)

    def test_no_se_duplican_clientes_con_el_mismo_dni(self, usuarios, cliente):
        with pytest.raises(DuplicadoError):
            usuarios.registrar_cliente("Otra Persona", "otra@mail.com", PASSWORD, dni="30111222")

    @pytest.mark.parametrize(
        "nombre,email,password,dni",
        [
            ("", "a@mail.com", PASSWORD, None),  # nombre vacío
            ("Juan Pérez", "no-es-un-email", PASSWORD, None),  # email inválido
            ("Juan Pérez", "a@mail.com", "123", None),  # contraseña corta
            ("Juan Pérez", "a@mail.com", PASSWORD, "12AB"),  # DNI inválido
        ],
    )
    def test_datos_invalidos(self, usuarios, nombre, email, password, dni):
        with pytest.raises(ValidacionError):
            usuarios.registrar_cliente(nombre, email, password, dni=dni)
        assert usuarios.listar_usuarios() == []  # no quedó nada guardado


class TestLogin:
    def test_autenticar_con_datos_correctos(self, usuarios, cliente):
        assert usuarios.autenticar("carla@mail.com", PASSWORD) is cliente

    def test_el_email_no_distingue_mayusculas(self, usuarios, cliente):
        assert usuarios.autenticar("Carla@Mail.com", PASSWORD) is cliente

    def test_password_incorrecta(self, usuarios, cliente):
        assert usuarios.autenticar("carla@mail.com", "incorrecta") is None

    def test_email_inexistente(self, usuarios):
        assert usuarios.autenticar("nadie@mail.com", PASSWORD) is None

    def test_un_usuario_dado_de_baja_no_puede_ingresar(self, usuarios, cliente, representante):
        usuarios.cambiar_activo(cliente.id, False, actor=representante)
        assert usuarios.autenticar("carla@mail.com", PASSWORD) is None


class TestListados:
    def test_listar_usuarios_ordenados_por_nombre(self, usuarios, representante, cliente, otro_cliente):
        nombres = [u.nombre for u in usuarios.listar_usuarios()]
        assert nombres == ["Ana Soporte", "Carla Cliente", "Diego Cliente"]

    def test_listar_solo_clientes(self, usuarios, representante, cliente, otro_cliente):
        assert usuarios.listar_clientes() == [cliente, otro_cliente]

    def test_listar_solo_representantes(self, usuarios, representante, otro_representante, cliente):
        assert usuarios.listar_representantes() == [representante, otro_representante]

    @pytest.mark.parametrize("texto", ["carla", "CARLA@", "30111"])
    def test_buscar_cliente_por_nombre_email_o_dni(self, usuarios, cliente, otro_cliente, texto):
        assert usuarios.listar_clientes(busqueda=texto) == [cliente]


class TestModificaciones:
    def test_actualizar_datos(self, usuarios, cliente):
        usuarios.actualizar(cliente.id, "Carla Gómez", "carla.g@mail.com", telefono="11-5555-0000", dni="30111222")
        assert cliente.nombre == "Carla Gómez"
        assert cliente.email == "carla.g@mail.com"
        assert cliente.telefono == "11-5555-0000"

    def test_actualizar_con_el_email_de_otro_usuario(self, usuarios, cliente, otro_cliente):
        with pytest.raises(DuplicadoError):
            usuarios.actualizar(cliente.id, "Carla", "diego@mail.com")

    def test_cambiar_password(self, usuarios, cliente):
        usuarios.actualizar(cliente.id, cliente.nombre, cliente.email, dni=cliente.dni, password="nueva-clave")
        assert usuarios.autenticar("carla@mail.com", "nueva-clave") is cliente

    def test_un_representante_no_puede_darse_de_baja_a_si_mismo(self, usuarios, representante):
        with pytest.raises(ReglaNegocioError):
            usuarios.cambiar_activo(representante.id, False, actor=representante)
