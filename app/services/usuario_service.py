"""Gestión de usuarios, clientes y representantes (RF01–RF04, RNF login y no duplicación)."""
import re
from typing import List, Optional

from sqlalchemy import func, or_, select

from app.errores import DuplicadoError, NoEncontradoError, ReglaNegocioError, ValidacionError
from app.models import Cliente, Representante, Usuario
from app.services.base import Servicio, transaccional
from app.utilidades import a_entero, texto_limpio

PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PATRON_DNI = re.compile(r"^\d{7,8}$")


class UsuarioService(Servicio):
    # ------------------------------------------------------------ consultas
    def obtener(self, usuario_id) -> Usuario:
        usuario = self.session.get(Usuario, a_entero(usuario_id, "Usuario inválido."))
        if usuario is None:
            raise NoEncontradoError("El usuario no existe.")
        return usuario

    def obtener_cliente(self, cliente_id) -> Cliente:
        usuario = self.obtener(cliente_id) if cliente_id not in (None, "") else None
        if not isinstance(usuario, Cliente):
            raise NoEncontradoError("Seleccioná un cliente válido.")
        return usuario

    def obtener_representante(self, representante_id) -> Representante:
        usuario = self.obtener(representante_id) if representante_id not in (None, "") else None
        if not isinstance(usuario, Representante):
            raise NoEncontradoError("Seleccioná un representante válido.")
        return usuario

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        email = self._normalizar_email(email)
        return self.session.scalar(select(Usuario).where(Usuario.email == email))

    def listar_usuarios(
        self, tipo: Optional[str] = None, busqueda: Optional[str] = None, solo_activos: bool = False
    ) -> List[Usuario]:
        """Lista usuarios ordenados por nombre. tipo: 'cliente', 'representante' o None (todos)."""
        modelo = {"cliente": Cliente, "representante": Representante}.get(tipo or "", Usuario)
        consulta = select(modelo)
        if solo_activos:
            consulta = consulta.where(Usuario.activo.is_(True))
        texto = texto_limpio(busqueda).lower()
        if texto:
            patron = f"%{texto}%"
            consulta = consulta.where(
                or_(
                    func.lower(Usuario.nombre).like(patron),
                    func.lower(Usuario.email).like(patron),
                    Usuario.__table__.c.dni.like(patron),
                )
            )
        consulta = consulta.order_by(func.lower(Usuario.nombre))
        return list(self.session.scalars(consulta))

    def listar_clientes(self, busqueda: Optional[str] = None, solo_activos: bool = False) -> List[Cliente]:
        return self.listar_usuarios("cliente", busqueda, solo_activos)

    def listar_representantes(self, busqueda: Optional[str] = None, solo_activos: bool = False) -> List[Representante]:
        return self.listar_usuarios("representante", busqueda, solo_activos)

    def contar(self) -> dict:
        return {
            "todos": len(self.listar_usuarios()),
            "cliente": len(self.listar_clientes()),
            "representante": len(self.listar_representantes()),
        }

    # ------------------------------------------------------------ login
    def autenticar(self, email: str, password: str) -> Optional[Usuario]:
        """Devuelve el usuario si email y contraseña son correctos; si no, None."""
        usuario = self.buscar_por_email(email)
        if usuario is not None and usuario.login(password):
            return usuario
        return None

    # ------------------------------------------------------------ altas
    @transaccional
    def registrar_cliente(
        self, nombre: str, email: str, password: str, dni: Optional[str] = None, telefono: Optional[str] = None
    ) -> Cliente:
        nombre = self._validar_nombre(nombre)
        email = self._validar_email(email)
        dni = self._validar_dni(dni)
        self._verificar_email_disponible(email)
        self._verificar_dni_disponible(dni)
        cliente = Cliente(
            nombre=nombre, email=email, password=password, dni=dni, telefono=texto_limpio(telefono) or None
        )
        self.session.add(cliente)
        self.session.flush()
        return cliente

    @transaccional
    def registrar_representante(
        self, nombre: str, email: str, password: str, telefono: Optional[str] = None
    ) -> Representante:
        nombre = self._validar_nombre(nombre)
        email = self._validar_email(email)
        self._verificar_email_disponible(email)
        representante = Representante(
            nombre=nombre, email=email, password=password, telefono=texto_limpio(telefono) or None
        )
        self.session.add(representante)
        self.session.flush()
        return representante

    # ------------------------------------------------------------ modificaciones
    @transaccional
    def actualizar(
        self,
        usuario_id,
        nombre: str,
        email: str,
        telefono: Optional[str] = None,
        dni: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Usuario:
        usuario = self.obtener(usuario_id)
        nombre = self._validar_nombre(nombre)
        email = self._validar_email(email)
        self._verificar_email_disponible(email, excepto=usuario)
        if usuario.es_cliente:
            dni = self._validar_dni(dni)
            self._verificar_dni_disponible(dni, excepto=usuario)
            usuario.dni = dni
        usuario.nombre = nombre
        usuario.email = email
        usuario.telefono = texto_limpio(telefono) or None
        if password:
            usuario.set_password(password)
        return usuario

    @transaccional
    def cambiar_password(self, usuario: Usuario, actual: str, nueva: str, repetida: str) -> Usuario:
        """El propio usuario cambia su contraseña (debe conocer la actual)."""
        if not usuario.login(actual):
            raise ValidacionError("La contraseña actual no es correcta.")
        if nueva != repetida:
            raise ValidacionError("Las contraseñas nuevas no coinciden.")
        if nueva == actual:
            raise ValidacionError("La contraseña nueva tiene que ser distinta de la actual.")
        usuario.set_password(nueva)
        return usuario

    @transaccional
    def cambiar_activo(self, usuario_id, activo: bool, actor: Optional[Usuario] = None) -> Usuario:
        """Baja / alta lógica: no se borran usuarios para no perder el historial de tickets."""
        usuario = self.obtener(usuario_id)
        if actor is not None and usuario is actor and not activo:
            raise ReglaNegocioError("No podés darte de baja a vos mismo.")
        usuario.activo = bool(activo)
        return usuario

    # ------------------------------------------------------------ validaciones
    @staticmethod
    def _normalizar_email(email: str) -> str:
        return texto_limpio(email).lower()

    @staticmethod
    def _validar_nombre(nombre: str) -> str:
        nombre = " ".join(texto_limpio(nombre).split())
        if len(nombre) < 2:
            raise ValidacionError("Ingresá el nombre completo.")
        if len(nombre) > 100:
            raise ValidacionError("El nombre no puede superar los 100 caracteres.")
        return nombre

    def _validar_email(self, email: str) -> str:
        email = self._normalizar_email(email)
        if not PATRON_EMAIL.match(email):
            raise ValidacionError("Ingresá un email válido (por ejemplo, nombre@mail.com).")
        return email

    @staticmethod
    def _validar_dni(dni: Optional[str]) -> Optional[str]:
        dni = texto_limpio(dni).replace(".", "").replace(" ", "")
        if not dni:
            return None
        if not PATRON_DNI.match(dni):
            raise ValidacionError("El DNI debe tener 7 u 8 números, sin puntos.")
        return dni

    def _verificar_email_disponible(self, email: str, excepto: Optional[Usuario] = None) -> None:
        existente = self.buscar_por_email(email)
        if existente is not None and existente is not excepto:
            raise DuplicadoError(f"Ya existe un usuario registrado con el email {email}.")

    def _verificar_dni_disponible(self, dni: Optional[str], excepto: Optional[Usuario] = None) -> None:
        if not dni:
            return
        existente = self.session.scalar(select(Cliente).where(Cliente.dni == dni))
        if existente is not None and existente is not excepto:
            raise DuplicadoError(f"Ya existe un cliente registrado con el DNI {dni}.")
