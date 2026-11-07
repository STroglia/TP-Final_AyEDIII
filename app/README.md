# `app/` · Código fuente

Guía rápida para recorrer el código. El diseño completo está en [`docs/arquitectura.md`](../docs/arquitectura.md).

```
app/
├── __init__.py          create_app(): arma la aplicación (config, base, rutas, datos de ejemplo)
├── config.py            configuración (ruta de la base, clave secreta, opciones)
├── database.py          SQLAlchemy: Base de los modelos, sesión, creación de tablas
├── errores.py           excepciones de negocio (ValidacionError, DuplicadoError, ...)
├── utilidades.py        fechas, conversiones y textos
├── datos_ejemplo.py     datos de ejemplo que se cargan con la base vacía
│
├── models/              DOMINIO: las clases del diagrama de clases
│   ├── enums.py         EstadoTicket, TipoProducto
│   ├── usuario.py       Usuario (abstracta), Cliente, Representante
│   ├── ticket.py        Ticket + workflow de estados
│   ├── hito.py          Hito
│   ├── notificacion.py  Notificacion
│   └── producto.py      Producto, Categoria
│
├── services/            LÓGICA DE NEGOCIO (lo que testean los tests)
│   ├── base.py              Servicio base + @transaccional (commit / rollback)
│   ├── usuario_service.py   alta, login, listados, edición, baja lógica
│   ├── ticket_service.py    CU001, CU002, CU003, estados, asignación
│   ├── notificacion_service.py
│   └── producto_service.py
│
├── web/                 CAPA WEB (Flask)
│   ├── __init__.py      registra rutas, filtros de plantillas y páginas de error
│   ├── seguridad.py     sesión, @login_requerido, @solo_representantes, CSRF
│   ├── iconos.py        íconos SVG
│   ├── auth.py          /login, /logout
│   ├── panel.py         /  (inicio)
│   ├── tickets.py       /tickets/...
│   ├── usuarios.py      /usuarios/...
│   ├── productos.py     /productos/...
│   └── notificaciones.py /notificaciones/...
│
├── templates/           PANTALLAS (Jinja2)
│   ├── base.html        estructura común: menú lateral, barra superior, mensajes
│   ├── _macros.html     componentes: badge de estado, avatar, estado vacío...
│   ├── auth/login.html
│   ├── panel.html
│   ├── tickets/         lista, nuevo, detalle
│   ├── usuarios/        lista, form
│   ├── productos/       lista, form
│   ├── notificaciones/  lista
│   └── error.html       403 / 404 / 500
│
└── static/
    ├── css/estilos.css
    ├── js/app.js
    └── img/favicon.svg
```

## Dónde está cada cosa del diagrama

| Diagrama | Código |
|---|---|
| `Usuario.login(): bool` | `models/usuario.py` → `Usuario.login()` |
| `Cliente.consultarTickets()` | `Cliente.consultar_tickets()` |
| `Cliente.registrarHito()` / `Representante.registrarHito()` | `registrar_hito()` en cada clase |
| `Representante.crearTicket()` | `Representante.crear_ticket()` |
| `Representante.asignarTicket()` | `Representante.asignar_ticket()` |
| `Ticket.abrirTicket()` / `cerrarTicket()` / `agregarHito()` | `models/ticket.py` |
| `Hito.registrarMensaje()` | `models/hito.py` |
| `Notificacion.enviar()` | `models/notificacion.py` |

## Rutas principales

| Método | Ruta | Quién | Qué hace |
|---|---|---|---|
| GET/POST | `/login` | todos | Ingresar |
| POST | `/logout` | logueado | Cerrar sesión |
| GET | `/` | logueado | Panel de inicio |
| GET | `/tickets/` | logueado | Lista (cliente: solo los suyos) |
| GET/POST | `/tickets/nuevo` | representante | CU001 Crear ticket |
| GET | `/tickets/<n>` | dueño o representante | CU002 Detalle + historial |
| POST | `/tickets/<n>/hitos` | dueño o representante | CU003 Registrar hito |
| POST | `/tickets/<n>/cerrar` · `/reabrir` | dueño o representante | Cambiar estado |
| POST | `/tickets/<n>/en-proceso` · `/asignar` | representante | Tomar / reasignar |
| GET/POST | `/usuarios/`, `/usuarios/nuevo`, `/usuarios/<id>/editar` | representante | Gestión de usuarios |
| GET/POST | `/productos/`, `/productos/nuevo`, `/productos/<id>/editar` | representante | Gestión de productos |
| GET | `/notificaciones/` | logueado | Bandeja de notificaciones |
