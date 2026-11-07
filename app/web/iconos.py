"""Íconos de línea (SVG) usados en la interfaz. Trazo simple, sin rellenos ni degradados."""

ICONOS = {
    "inicio": '<path d="M3 10.5 12 3l9 7.5V21h-6v-6H9v6H3z"/>',
    "ticket": '<path d="M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v3a2 2 0 0 0 0 4v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-3a2 2 0 0 0 0-4z"/><path d="M14 5v2M14 11v2M14 17v2"/>',
    "usuarios": '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="M16 4a4 4 0 0 1 0 8"/><path d="M22 21a7 7 0 0 0-4-6.3"/>',
    "usuario": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "producto": '<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m3 8 9 5 9-5"/><path d="M12 13v8"/>',
    "campana": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>',
    "salir": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
    "mas": '<path d="M12 5v14M5 12h14"/>',
    "buscar": '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    "menu": '<path d="M3 6h18M3 12h18M3 18h18"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "reabrir": '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>',
    "enviar": '<path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4z"/>',
    "editar": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    "volver": '<path d="M19 12H5M12 19l-7-7 7-7"/>',
    "play": '<path d="m6 4 14 8-14 8z"/>',
    "flecha": '<path d="M5 12h14M12 5l7 7-7 7"/>',
    "etiqueta": '<path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    "reloj": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "cerrar": '<path d="M18 6 6 18M6 6l12 12"/>',
    "bandeja": '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5h13L22 12v7a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-7z"/>',
    "alerta": '<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/>',
    "candado": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "grafico":'<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 6-7"/><path d="M16 7h4v4"/>',
}

# Nombres de Font Awesome que se pueden usar como alias de los íconos propios.
ALIAS = {
    "fa-clock": "reloj",
    "fa-chart-line": "grafico",
    "fa-magnifying-glass": "buscar",
    "fa-bell": "campana",
    "fa-ticket": "ticket",
}


def icono(nombre: str, clase: str = "icono") -> str:
    trazo = ICONOS.get(ALIAS.get(nombre, nombre), "")
    return (
        f'<svg class="{clase}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{trazo}</svg>'
    )
