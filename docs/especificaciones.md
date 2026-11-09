# Especificaciones · Sistema de Ticketing TECNOSOL Mar del Plata

Documento de especificación funcional del TP Final Integrador 2026 (Algoritmos y Estructuras de Datos III).
Toma como base los documentos de la carpeta del TP: *Ticket to Ride*, *Requerimientos*, *Requerimientos - Modificación*, *Casos de Uso* y *Diagrama de Clases (versión 2)*.

---

## 1. Contexto

Un sistema de ticketing ayuda a un área de atención al cliente a administrar sus casos de soporte. Para cada caso se crea un **ticket** que documenta la solicitud. Cliente y representante se comunican dentro del ticket mediante un hilo de mensajes llamado **hitos**, y el sistema **notifica** a cada parte cuando la otra responde.

Cuando el problema se resuelve, el representante o el propio cliente **cierran** el ticket. Si surge una nueva consulta sobre el mismo tema, el ticket se puede **reabrir** y la conversación continúa con el mismo representante.

## 2. Actores

| Actor | Descripción |
|---|---|
| **Cliente** | Persona que plantea una incidencia. Consulta sus tickets, responde y puede cerrarlos o reabrirlos. |
| **Representante** | Empleado de atención. Registra clientes y tickets, responde, cambia estados, reasigna tickets y gestiona usuarios y productos. |

Ambos son **Usuarios** del sistema, que es la clase abstracta del diagrama.

---

## 3. Requerimientos funcionales

Los requerimientos RF01 a RF14 provienen del documento original y RF15 a RF17 de la modificación.

| ID | Requerimiento | Cómo se cumple |
|---|---|---|
| RF01 | Gestionar usuarios | Alta, edición y baja lógica en *Usuarios* (`UsuarioService`). |
| RF02 | Listar usuarios | *Usuarios* con pestañas Todos / Clientes / Representantes y buscador. |
| RF03 | Gestionar representantes | Alta, edición y baja de representantes. |
| RF04 | Listar representantes | Pestaña *Representantes*. |
| RF05 | Gestionar hitos | Registrar respuestas en el ticket (CU003). |
| RF06 | Listar hitos | Historial cronológico en el detalle del ticket. |
| RF07 | Enviar notificaciones | Se generan al crear un ticket, al responder, cerrar, reabrir, asignar o pasar a *En proceso*. |
| RF08 | Gestionar estados | Workflow ABIERTO → EN_PROCESO → CERRADO, con reapertura. |
| RF09 | Gestionar tickets | Crear, consultar, buscar, filtrar, cerrar, reabrir y asignar. |
| RF10 | Asociar clientes con tickets | Todo ticket pertenece a un cliente (obligatorio). |
| RF11 | Asociar representantes con tickets | El representante que crea el ticket queda asignado y se puede reasignar. |
| RF12 | Asociar hitos con tickets | Composición Ticket ◆── Hito. |
| RF13 | Gestionar el estado de cada ticket | Acciones *Tomar*, *Cerrar* y *Reabrir* en el detalle. |
| RF14 | Gestionar las notificaciones de los tickets | Bandeja con marcar como leída, marcar todas y acceso directo al ticket. |
| RF15 | Asociar productos con tickets | Selector de producto (opcional) al crear el ticket. |
| RF16 | Gestionar el tipo de producto asociado | Tabla `TipoProducto`: arranca con Línea blanca, Cocina, Electro y Pequeños electrodomésticos; los representantes pueden crear tipos nuevos. |
| RF17 | Gestionar productos (17.1 registrar · 17.2 listar) | *Productos*: alta, edición, categorías y listado con filtros. |

## 4. Requerimientos no funcionales

| ID | Requerimiento | Cómo se cumple |
|---|---|---|
| RNF01 | Codificado utilizando **TDD** | 6 iteraciones de tests con pytest (ver `tests/README.md`). |
| RNF02 | Gestionar **seguridad (login)** | Login con email y contraseña. Contraseñas con hash (Werkzeug), sesiones, control de permisos por rol y protección CSRF en formularios. |
| RNF03 | **No duplicar usuarios** | Email único (sin distinguir mayúsculas) y DNI único, validados en el servicio y en la base (índice `UNIQUE`). |
| RNF04 | **Accesible vía web** | Aplicación Flask que se usa desde el navegador en `http://127.0.0.1:5000`. Diseño responsive. |
| RNF05 | Funciona en **Windows 10 en adelante** | Python + SQLite. `iniciar.bat` prepara y abre todo con doble clic. |

---

## 5. Historias de usuario

Formato: *Como [rol], quiero [acción], para [beneficio].* Los criterios de aceptación usan el formato *Dado / Cuando / Entonces*.
Prioridad: **Alta** (vital), **Media** (importante), **Baja** (quedaría bien).

### Épica 1 · Acceso y seguridad

#### HU01 · Iniciar sesión
**Como** usuario del sistema, **quiero** ingresar con mi email y contraseña, **para** acceder solo a la información que me corresponde.
*Prioridad: Alta · RNF02*

- **Dado** un usuario activo, **cuando** ingresa email y contraseña correctos, **entonces** accede a su panel de inicio.
- **Dado** un email o contraseña incorrectos, **cuando** intenta ingresar, **entonces** ve el mensaje *"Email o contraseña incorrectos"* y no accede.
- **Dado** un usuario dado de baja, **cuando** intenta ingresar, **entonces** no puede acceder.
- El email no distingue mayúsculas de minúsculas.
- Las contraseñas se guardan con hash, nunca en texto plano.

#### HU02 · Cerrar sesión
**Como** usuario, **quiero** cerrar sesión, **para** que nadie use mi cuenta en una computadora compartida.
*Prioridad: Alta · RNF02*

- **Cuando** presiono *Cerrar sesión*, **entonces** vuelvo al login y las páginas internas ya no son accesibles sin ingresar de nuevo.

#### HU03 · Permisos por rol
**Como** responsable del sistema, **quiero** que cada rol vea solo lo que le corresponde, **para** proteger la información de los clientes.
*Prioridad: Alta · RNF02*

- Un cliente **no** puede acceder a *Usuarios* ni *Productos* (error 403), y por lo tanto **no puede registrar clientes**.
- Un cliente **sí** puede abrir tickets, pero solo a su propio nombre (ver HU18).
- El registro público (*Crear cuenta* en el login) crea **solo clientes**. Aunque se manipule el formulario, no se puede crear un representante desde ahí: los representantes los da de alta otro representante desde *Usuarios*.
- Un cliente **no** puede ver ni responder tickets de otros clientes.
- Si alguien sin sesión intenta entrar a una página interna, se lo redirige al login.

### Épica 2 · Usuarios

#### HU04 · Registrar cliente
**Como** representante, **quiero** registrar un cliente nuevo, **para** poder crearle tickets.
*Prioridad: Alta · RF01, RF10, RNF03 · CU001 paso 2.1/2.2*

- Datos: nombre (obligatorio), email (obligatorio y único), contraseña (mínimo 6 caracteres), DNI (opcional, 7 u 8 números, único) y teléfono (opcional).
- **Dado** un email ya registrado, **cuando** intento guardar, **entonces** veo *"Ya existe un usuario registrado con el email…"* y no se crea el cliente.
- **Dado** que llegué desde *Nuevo ticket*, **cuando** registro al cliente, **entonces** vuelvo al alta del ticket con ese cliente ya seleccionado.

#### HU05 · Registrar representante
**Como** representante, **quiero** dar de alta a otro representante, **para** sumar personas al equipo de atención.
*Prioridad: Media · RF03, RNF03*

- Mismas validaciones de nombre, email único y contraseña que HU04.

#### HU06 · Listar y buscar usuarios
**Como** representante, **quiero** ver la lista de usuarios filtrada por rol y buscar por nombre, email o DNI, **para** encontrar rápidamente a una persona.
*Prioridad: Media · RF02, RF04*

- La lista se ordena alfabéticamente y muestra rol, contacto y estado (Activo / De baja).
- Las pestañas *Todos*, *Clientes* y *Representantes* muestran la cantidad de cada grupo.

#### HU07 · Editar y dar de baja usuarios
**Como** representante, **quiero** modificar los datos de un usuario o darlo de baja, **para** mantener la información actualizada.
*Prioridad: Media · RF01, RF03*

- La contraseña solo cambia si se completa el campo.
- La baja es **lógica**: el usuario no puede ingresar, pero su historial de tickets se conserva. Se puede reactivar.
- Un representante no puede darse de baja a sí mismo.

### Épica 3 · Tickets

#### HU08 · Crear ticket de soporte (CU001)
**Como** representante, **quiero** registrar un ticket para un cliente, **para** documentar la incidencia que me plantea.
*Prioridad: Alta · RF09, RF10, RF11, RF15*

- **Dado** el formulario de nuevo ticket, **cuando** busco al cliente, **entonces** puedo filtrar por nombre, email o DNI y seleccionarlo.
- **Dado** que faltan datos obligatorios (cliente o descripción de al menos 10 caracteres), **cuando** confirmo, **entonces** el sistema no crea el ticket y me indica qué falta.
- **Cuando** confirmo con datos válidos, **entonces** el sistema crea el ticket, **muestra su número**, lo deja en estado **Abierto**, me asigna como representante y **notifica al cliente**.
- El producto es opcional.
- No se pueden crear tickets para clientes dados de baja.

#### HU18 · El cliente abre su propio ticket
**Como** cliente, **quiero** abrir un ticket yo mismo desde el sistema, **para** reportar un problema sin tener que llamar a un representante.
*Prioridad: Alta · RF09, RF10, RF11, RF15*

- **Cuando** entro a *Nuevo ticket*, **entonces** no tengo que elegir cliente: el ticket queda a mi nombre.
- **Dado** que intento enviar el formulario con otro cliente, **entonces** el sistema lo ignora y el ticket igual queda a mi nombre.
- **Cuando** confirmo con una descripción válida, **entonces** el ticket se crea **Abierto** y entra en la **cola de atención** sin representante asignado.
- Todos los representantes activos reciben una notificación. Un representante **toma** el ticket (uno en particular o "el siguiente", por orden de llegada): queda asignado a él, pasa a **En proceso** y se me avisa.
- El cliente **no** puede registrar clientes nuevos ni entrar a la gestión de usuarios.

#### HU09 · Consultar mis tickets (CU002)
**Como** cliente, **quiero** ver la lista de mis tickets y el detalle de cada uno, **para** conocer el estado y los avances de mis consultas.
*Prioridad: Alta · RF06, RF09*

- *Mis tickets* muestra **todos** mis tickets, en todos los estados, del más reciente al más antiguo.
- **Dado** que no tengo tickets, **entonces** veo la leyenda *"No tenés tickets asociados"*.
- **Cuando** selecciono un ticket, **entonces** veo sus datos y el **historial de hitos** en orden cronológico.

#### HU10 · Listar, buscar y filtrar tickets
**Como** representante, **quiero** buscar tickets por número, cliente o descripción y filtrarlos por estado, **para** encontrar rápido el caso que tengo que gestionar.
*Prioridad: Alta · RF09*

- Filtros por estado con contador: Todos, Abiertos, En proceso, Cerrados.
- Opción *Solo asignados a mí*.
- Orden: más recientes, más antiguos o por número.
- **Dado** que busco un número exacto (por ejemplo `#12` o `12`), **entonces** voy directo al ticket.

#### HU11 · Registrar hito (CU003)
**Como** cliente o representante, **quiero** agregar un mensaje al historial del ticket, **para** comunicarme con la otra parte y dejar registro de cada avance.
*Prioridad: Alta · RF05, RF07, RF12*

- **Dado** un comentario vacío, **cuando** intento confirmarlo, **entonces** el sistema no lo guarda.
- **Cuando** confirmo un comentario válido, **entonces** se guarda con fecha, hora y autor, y se **notifica al otro actor**.
- **Dado** un ticket **Abierto**, **cuando** responde un representante, **entonces** pasa a **En proceso**.
- **Dado** un ticket **Cerrado**, **entonces** no se pueden agregar hitos hasta reabrirlo.

#### HU12 · Gestionar el estado del ticket
**Como** representante o cliente, **quiero** cerrar un ticket resuelto y reabrirlo si surge otra consulta, **para** reflejar en qué situación está el caso.
*Prioridad: Alta · RF08, RF13*

- El representante puede **tomar** un ticket abierto, que pasa a *En proceso*.
- Representante o cliente pueden **cerrar** un ticket que no esté cerrado. Se registra la fecha de cierre.
- Representante o cliente pueden **reabrir** un ticket cerrado, que vuelve a *Abierto* con el mismo representante.
- Cada cambio de estado notifica a la otra parte.

#### HU13 · Reasignar ticket
**Como** representante, **quiero** asignar un ticket a otro representante, **para** derivar el caso a quien corresponda.
*Prioridad: Media · RF11*

- Solo se puede asignar a representantes activos y en tickets no cerrados.
- Se notifica al nuevo representante y al cliente.

### Épica 4 · Notificaciones

#### HU14 · Recibir notificaciones
**Como** usuario, **quiero** recibir avisos cuando hay novedades en mis tickets, **para** responder a tiempo.
*Prioridad: Alta · RF07, RF14*

- La campanita y el menú muestran la cantidad de notificaciones **no leídas**.
- En *Notificaciones* puedo ver todas o solo las no leídas, marcar una o todas como leídas e ir directo al ticket.
- Al abrir un ticket, sus notificaciones se marcan como leídas.

### Épica 5 · Productos

#### HU15 · Registrar productos
**Como** representante, **quiero** registrar productos con su tipo y categoría, **para** asociarlos a los tickets.
*Prioridad: Media · RF16, RF17.1*

- Datos obligatorios: nombre (único), tipo de producto y categoría.
- Si el tipo o la categoría no existen, se crean desde el mismo formulario del producto
  ("+ Crear nuevo tipo…" / "+ Crear nueva categoría…"). Esto cubre el caso del producto escrito
  a mano por el cliente (opción "Otro"), que el representante debe vincular para cerrar el ticket.
- Tipos y categorías no se pueden repetir (sin distinguir mayúsculas).

#### HU16 · Listar productos
**Como** representante, **quiero** listar los productos y filtrarlos por tipo, categoría o nombre, **para** consultarlos fácilmente.
*Prioridad: Media · RF17.2*

- La lista muestra nombre, tipo, categoría y cantidad de tickets asociados.

#### HU17 · Asociar producto a un ticket
**Como** representante, **quiero** indicar sobre qué producto es la incidencia, **para** tener más contexto del caso.
*Prioridad: Media · RF15*

- Al crear el ticket se puede elegir un producto. El detalle del ticket muestra producto, tipo y categoría.

#### HU19 · Filtrar por período y paginar el listado
**Como** usuario (cliente o representante), **quiero** filtrar los tickets por fecha de creación y verlos de a páginas, **para** encontrar casos recientes sin recorrer una lista interminable.
*Prioridad: Media · RF09*

- El listado ofrece los períodos *Cualquier fecha*, *Últimos 7 días*, *Últimos 30 días* y *Últimos 90 días*, combinables con el estado, la búsqueda y el orden.
- **Dado** un período inválido (texto, cero o negativo), **entonces** el sistema avisa *"Período inválido."* y muestra el listado sin ese filtro.
- El listado muestra **10 tickets por página**, con *Anterior* / *Siguiente* y el rango visible (*"11–12 de 12"*). Si hay 10 o menos, no se muestra la paginación.
- **Dado** un número de página inválido o fuera de rango, **entonces** se muestra la página válida más cercana.

#### HU20 · Cambiar mi contraseña
**Como** usuario, **quiero** cambiar mi contraseña desde el menú *Cuenta*, **para** mantener segura mi cuenta.
*Prioridad: Media · RNF02*

- Tengo que ingresar la contraseña **actual**, la **nueva** y repetir la nueva.
- **Dado** que la actual es incorrecta, que las nuevas no coinciden, que la nueva es igual a la actual o que tiene menos de 6 caracteres, **entonces** el sistema no la cambia y me indica el motivo.
- **Cuando** los datos son válidos, **entonces** la contraseña se guarda *hasheada* y a partir de ese momento solo sirve la nueva.

---

## 6. Reglas de negocio

| ID | Regla |
|---|---|
| RN01 | Un ticket siempre pertenece a un cliente activo. |
| RN02 | La descripción del ticket tiene entre 10 y 2000 caracteres. |
| RN03 | Un ticket nuevo nace en estado **Abierto**. |
| RN04 | Solo un ticket **Abierto** puede pasar a **En proceso**. |
| RN05 | Un ticket **Cerrado** no admite hitos ni reasignaciones. Primero hay que reabrirlo. |
| RN06 | Solo se puede reabrir un ticket **Cerrado**. Vuelve a **Abierto**. |
| RN07 | Un hito no puede estar vacío (máximo 2000 caracteres). |
| RN08 | Cada hito y cada cambio de estado generan una notificación para la otra parte. |
| RN09 | El email de un usuario es único. El DNI de un cliente, si se carga, también. |
| RN10 | Los usuarios no se borran: se dan de baja (baja lógica) para conservar el historial. |
| RN11 | La contraseña tiene al menos 6 caracteres. |

---

## 7. Matriz de trazabilidad

| Historia | Requerimientos | Caso de uso | Tests principales |
|---|---|---|---|
| HU01 | RNF02 | — | `test_usuarios.py::TestLogin`, `test_web.py::TestSeguridad` |
| HU02 | RNF02 | — | `test_web.py::TestSeguridad::test_logout` |
| HU03 | RNF02 | — | `test_web.py::TestSeguridad::test_un_cliente_no_accede_a_la_gestion`, `test_tickets.py::test_obtener_ticket_ajeno` |
| HU04 | RF01, RF10, RNF03 | CU001 (2.1) | `test_usuarios.py::TestAltaDeUsuarios`, `test_web.py::TestGestionWeb` |
| HU05 | RF03, RNF03 | — | `test_usuarios.py::test_registrar_representante` |
| HU06 | RF02, RF04 | — | `test_usuarios.py::TestListados` |
| HU07 | RF01, RF03 | — | `test_usuarios.py::TestModificaciones` |
| HU08 | RF09, RF10, RF11, RF15 | CU001 | `test_tickets.py::TestCrearTicket`, `test_web.py::TestTicketsWeb` |
| HU09 | RF06, RF09 | CU002 | `test_tickets.py::TestConsultarTickets`, `test_web.py::test_cliente_sin_tickets_ve_la_leyenda` |
| HU10 | RF09 | — | `test_tickets.py::test_filtrar_por_estado`, `test_buscar_por_numero`, `test_buscar_por_texto_o_nombre_del_cliente` |
| HU11 | RF05, RF07, RF12 | CU003 | `test_hitos_notificaciones.py::TestRegistrarHito`, `test_modelos.py::TestHitos` |
| HU12 | RF08, RF13 | — | `test_modelos.py::TestTicket`, `test_tickets.py::TestEstadosYAsignacion` |
| HU13 | RF11 | — | `test_tickets.py::test_asignar_a_otro_representante` |
| HU14 | RF07, RF14 | CU003 (5) | `test_hitos_notificaciones.py::TestNotificaciones` |
| HU15 | RF16, RF17.1 | — | `test_productos.py::TestProductos`, `TestCategorias` |
| HU16 | RF17.2 | — | `test_productos.py::test_listar_y_filtrar` |
| HU17 | RF15 | CU001 | `test_tickets.py::test_crear_ticket_con_producto` |
| HU18 | RF09, RF10, RF11, RF15 | CU001 (variante cliente) | `test_tickets.py::TestClienteCreaTicket`, `test_web.py::test_el_cliente_crea_un_ticket_desde_la_web`, `test_un_cliente_no_puede_registrar_clientes` |
| HU19 | RF09 | — | `test_mejoras.py::TestPaginar`, `TestFiltroPeriodo`, `TestMejorasWeb::test_listado_paginado` |
| HU20 | RNF02, RN11 | — | `test_mejoras.py::TestCambiarPassword`, `TestMejorasWeb::test_cambiar_contrasena_desde_la_web` |

---

## 8. Casos de uso implementados

| Caso de uso | Pantalla | Comentario |
|---|---|---|
| **CU001** Crear Ticket de Soporte | *Nuevo ticket* | Pasos 1 a 5 completos, con alternativa 2.1/2.2 (registrar cliente) y validación de campos obligatorios. La excepción *"Error al guardar"* se resuelve con una transacción: si falla, no queda nada guardado y se informa el error. |
| **CU002** Consultar Ticket - Cliente | *Mis tickets* → detalle | Lista en todos los estados y muestra la leyenda cuando no hay tickets. |
| **CU003** Registrar Hito | Detalle del ticket → *Responder* | Valida el comentario vacío, guarda el hito y notifica al otro actor. |

> **Rendimiento:** los casos de uso piden respuesta en menos de 2 o 3 segundos. Con SQLite local, cada operación tarda milisegundos.
