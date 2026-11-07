"""Excepciones de negocio del sistema.

Todas heredan de ErrorDeNegocio: son errores *esperables* (datos inválidos,
duplicados, falta de permisos) cuyo mensaje se puede mostrar tal cual al usuario.
"""


class ErrorDeNegocio(Exception):
    """Error esperable cuyo mensaje es apto para mostrarse al usuario."""


class ValidacionError(ErrorDeNegocio):
    """Un dato ingresado no cumple las reglas (campo vacío, formato inválido, etc.)."""


class DuplicadoError(ErrorDeNegocio):
    """Se intentó registrar algo que ya existe (RNF: no duplicar usuarios)."""


class NoEncontradoError(ErrorDeNegocio):
    """El registro buscado no existe."""


class PermisoError(ErrorDeNegocio):
    """El usuario no tiene permiso para realizar la acción."""


class ReglaNegocioError(ErrorDeNegocio):
    """La acción no está permitida por el estado actual (por ejemplo, ticket cerrado)."""
