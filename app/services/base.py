"""Base común de los servicios."""
from functools import wraps

from sqlalchemy.orm import Session

from app.errores import PermisoError


def transaccional(metodo):
    """Confirma (commit) si el método termina bien; si falla, deshace (rollback) todo.

    Así una operación nunca queda "a medias" en la base de datos.
    """

    @wraps(metodo)
    def envoltura(self, *args, **kwargs):
        try:
            resultado = metodo(self, *args, **kwargs)
            self.session.commit()
            return resultado
        except Exception:
            self.session.rollback()
            raise

    return envoltura


class Servicio:
    """Todos los servicios reciben la sesión de base de datos con la que trabajan."""

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def exigir_representante(usuario) -> None:
        if usuario is None or not usuario.es_representante:
            raise PermisoError("Esta acción solo la puede realizar un representante.")
