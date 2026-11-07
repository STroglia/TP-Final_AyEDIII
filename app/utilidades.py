"""Funciones auxiliares reutilizadas en todo el sistema."""
from datetime import datetime
from typing import Optional

from app.errores import ValidacionError


def ahora() -> datetime:
    """Fecha y hora actual (hora local de la computadora)."""
    return datetime.now()


def a_entero(valor, mensaje: str = "El valor ingresado no es válido.") -> int:
    """Convierte un valor (por ejemplo, lo que llega de un formulario) a entero."""
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        raise ValidacionError(mensaje) from None


def texto_limpio(valor) -> str:
    """Devuelve el texto sin espacios sobrantes ('' si es None)."""
    return (valor or "").strip()


def formatear_fecha(valor: Optional[datetime], con_hora: bool = True) -> str:
    """05/11/2026 14:30"""
    if valor is None:
        return "—"
    return valor.strftime("%d/%m/%Y %H:%M" if con_hora else "%d/%m/%Y")


def fecha_relativa(valor: Optional[datetime]) -> str:
    """Expresa una fecha de forma amigable: 'recién', 'hace 5 min', 'hace 2 h'..."""
    if valor is None:
        return "—"
    segundos = int((ahora() - valor).total_seconds())
    if segundos < 60:
        return "recién"
    if segundos < 3600:
        return f"hace {segundos // 60} min"
    if segundos < 86400:
        return f"hace {segundos // 3600} h"
    dias = segundos // 86400
    if dias < 7:
        return "hace 1 día" if dias == 1 else f"hace {dias} días"
    return formatear_fecha(valor, con_hora=False)


def paginar(elementos: list, pagina=1, por_pagina: int = 10) -> dict:
    """Divide una lista en páginas y devuelve la página pedida.

    Si la página pedida no es válida (texto, 0, negativa o mayor a la última),
    se ajusta a la más cercana. Costo O(por_pagina) por el recorte de la lista.
    """
    total = len(elementos)
    paginas = max(1, -(-total // por_pagina))  # división redondeando hacia arriba
    try:
        pagina = int(pagina)
    except (TypeError, ValueError):
        pagina = 1
    pagina = min(max(pagina, 1), paginas)
    inicio = (pagina - 1) * por_pagina
    return {
        "elementos": elementos[inicio : inicio + por_pagina],
        "pagina": pagina,
        "paginas": paginas,
        "total": total,
        "desde": inicio + 1 if total else 0,
        "hasta": min(inicio + por_pagina, total),
        "anterior": pagina - 1 if pagina > 1 else None,
        "siguiente": pagina + 1 if pagina < paginas else None,
    }


def resumir(texto: Optional[str], largo: int = 70) -> str:
    """Recorta un texto largo agregando '…'."""
    texto = " ".join((texto or "").split())
    return texto if len(texto) <= largo else texto[: largo - 1].rstrip() + "…"
