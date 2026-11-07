"""Datos de ejemplo para probar la aplicación apenas se abre.

Se cargan una sola vez: cuando la base de datos está vacía.
Para volver a empezar de cero, borrá el archivo instancia/tecnosol.db.
"""
from datetime import timedelta

from sqlalchemy import func, select

from app.models import Usuario
from app.services import ProductoService, TicketService, UsuarioService
from app.utilidades import ahora


def cargar_si_esta_vacia(session) -> bool:
    if session.scalar(select(func.count(Usuario.id))):
        return False
    cargar_datos_ejemplo(session)
    return True


def cargar_datos_ejemplo(session) -> None:
    usuarios = UsuarioService(session)
    productos = ProductoService(session)
    tickets = TicketService(session)

    # ---------------------------------------------------------- usuarios
    admin = usuarios.registrar_representante("Admin Soporte", "admin@tickettoride.com", "admin123", "0800-555-0100")
    laura = usuarios.registrar_representante("Laura Gómez", "laura@tickettoride.com", "laura123", "0800-555-0101")
    juan = usuarios.registrar_cliente("Juan Pérez", "juan@mail.com", "cliente123", "30111222", "11-4444-1234")
    maria = usuarios.registrar_cliente("María López", "maria@mail.com", "cliente123", "32555666", "11-5555-9876")
    lucas = usuarios.registrar_cliente("Lucas Fernández", "lucas@mail.com", "cliente123", "38123456")

    # ---------------------------------------------------------- productos
    cat = {nombre: productos.crear_categoria(nombre).id_categoria
           for nombre in ["Heladeras", "Lavarropas", "Cocinas y hornos", "Microondas", "Cafeteras"]}
    heladera = productos.registrar_producto("Heladera No Frost 360L", "LINEA_BLANCA", cat["Heladeras"])
    lavarropas = productos.registrar_producto("Lavarropas automático 8 kg", "LINEA_BLANCA", cat["Lavarropas"])
    cocina = productos.registrar_producto("Cocina 4 hornallas con horno", "COCINA", cat["Cocinas y hornos"])
    microondas = productos.registrar_producto("Microondas digital 20 L", "ELECTRO", cat["Microondas"])
    productos.registrar_producto("Cafetera express 15 bar", "PEQUENIOS_ELECTRODOMESTICOS", cat["Cafeteras"])

    # ---------------------------------------------------------- tickets
    t1 = tickets.crear_ticket(
        admin, juan.id,
        "La heladera dejó de enfriar en el sector de abajo. El freezer funciona bien. "
        "Ya probé desenchufarla durante una hora.",
        heladera.id_producto,
    )
    tickets.registrar_hito(t1.numero_ticket, admin, "Hola Juan. Coordinamos la visita de un técnico para el jueves entre 9 y 13 h.")
    tickets.registrar_hito(t1.numero_ticket, juan, "Perfecto, voy a estar en casa. ¡Gracias!")

    t2 = tickets.crear_ticket(
        laura, maria.id,
        "El lavarropas no centrifuga y queda agua en el tambor al terminar el ciclo.",
        lavarropas.id_producto,
    )
    tickets.registrar_hito(t2.numero_ticket, maria, "Adjunto el código de error que aparece en el display: E21.")

    t3 = tickets.crear_ticket(
        admin, maria.id,
        "El microondas hace chispas cuando se usa más de dos minutos.",
        microondas.id_producto,
    )
    tickets.registrar_hito(t3.numero_ticket, admin, "Por seguridad, no lo uses. Te enviamos uno de reemplazo.")
    tickets.registrar_hito(t3.numero_ticket, maria, "Ya recibí el nuevo, funciona perfecto.")
    tickets.cerrar(t3.numero_ticket, admin)

    t4 = tickets.crear_ticket(
        laura, lucas.id,
        "Una de las hornallas de la cocina no enciende con el encendido eléctrico.",
        cocina.id_producto,
    )

    # Fechas escalonadas para que el ejemplo se vea realista.
    for ticket, dias in ((t1, 3), (t2, 1), (t3, 6), (t4, 0)):
        inicio = ahora() - timedelta(days=dias, hours=2)
        ticket.fecha_creacion = inicio
        for i, hito in enumerate(ticket.hitos, start=1):
            hito.fecha = inicio + timedelta(hours=3 * i)
        if ticket.fecha_cierre:
            ticket.fecha_cierre = inicio + timedelta(hours=3 * (len(ticket.hitos) + 1))
        # Cada aviso queda con la hora del evento que lo generó (creación, hitos, cierre).
        avisos = sorted(ticket.notificaciones, key=lambda n: n.id)
        for i, notificacion in enumerate(avisos):
            notificacion.fecha_envio = min(inicio + timedelta(hours=3 * i), ahora())
    session.commit()
