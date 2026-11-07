# `tests/` · Pruebas automáticas

El TP pide **codificar usando iteraciones TDD** (*Test Driven Development*). Cada iteración sigue el ciclo:

1. **Rojo:** se escribe un test que describe el comportamiento esperado y falla.
2. **Verde:** se escribe el código mínimo para que el test pase.
3. **Refactor:** se mejora el código sin romper los tests.

## Cómo correrlos

**Opción fácil:** doble clic en `correr_tests.bat`, en la raíz del proyecto.

**Desde una terminal**, en la carpeta del proyecto y con el entorno activado:

```bash
pytest -v
```

Otros comandos útiles:

```bash
pytest tests/test_tickets.py -v
```

```bash
pytest -k "hito" -v
```

```bash
pytest --tb=short -q
```

El primero corre un solo archivo, el segundo solo los tests cuyo nombre contiene "hito" y el tercero muestra un resumen corto.

> Cada test usa una **base de datos SQLite en memoria** nueva y vacía. Los tests no se afectan entre sí y **no modifican** la base real (`instancia/tecnosol.db`).

## Iteraciones TDD y archivos

| Iteración | Archivo | Qué prueba | Historias / CU |
|---|---|---|---|
| 1 | `test_modelos.py` | Reglas de las clases del dominio **sin base de datos**: login y hash de contraseña, herencia de roles, workflow de estados del ticket, validación de hitos, destinatarios de notificaciones. | HU01, HU11, HU12 |
| 2 | `test_usuarios.py` | `UsuarioService`: alta de clientes y representantes, **no duplicación** por email o DNI, validaciones, login, listados y búsquedas, edición y baja lógica. | HU01, HU04–HU07 |
| 3 | `test_tickets.py` | `TicketService`: **CU001** (crear ticket), ticket creado por el cliente con **asignación automática al representante con menos carga**, **CU002** (consultar), filtros y búsquedas, estadísticas, permisos, asignación, cierre y reapertura. | HU08–HU10, HU12, HU13, HU17, HU18 |
| 4 | `test_hitos_notificaciones.py` | **CU003** (registrar hito), notificación al otro actor, orden cronológico, notificaciones leídas y no leídas. | HU11, HU14 |
| 5 | `test_productos.py` | `ProductoService`: categorías, productos, tipos, duplicados, filtros y edición. | HU15, HU16 |
| 6 | `test_web.py` | **Integración** desde el "navegador" (cliente de prueba de Flask): login, redirecciones, permisos por rol (403), CSRF, alta de tickets, respuesta del cliente, gestión de usuarios y productos. | HU01–HU04, HU08, HU09, HU11, HU15 |
| 7 | `test_mejoras.py` | Función `paginar()` (casos borde: lista vacía, última página incompleta, página inválida), **filtro por período** de tickets y **cambio de contraseña** (servicio y web). | HU19, HU20 |

## Fixtures (`conftest.py`)

Las *fixtures* son datos o recursos que pytest prepara automáticamente para cada test:

| Fixture | Qué da |
|---|---|
| `session` | Sesión de SQLAlchemy sobre una base en memoria vacía |
| `usuarios`, `tickets`, `productos`, `notificaciones` | Los servicios, listos para usar |
| `representante`, `otro_representante`, `cliente`, `otro_cliente` | Usuarios ya registrados (contraseña `clave123`) |
| `categoria`, `producto` | Una categoría y un producto |
| `ticket` | Un ticket abierto de `cliente`, creado por `representante` |
| `app`, `web` | La aplicación Flask de prueba y su cliente HTTP |
| `datos_web` | Usuarios y producto cargados en la app de prueba |
| `login` | Función para iniciar sesión: `login("ana@soporte.com")` |

## Convenciones

- Los nombres de los tests describen el comportamiento en castellano. Por ejemplo, `test_no_se_duplican_usuarios_con_el_mismo_email`.
- Cada test verifica **una sola idea**.
- Los casos con varias entradas usan `@pytest.mark.parametrize`. Por ejemplo, descripciones vacías, con solo espacios o demasiado cortas.
