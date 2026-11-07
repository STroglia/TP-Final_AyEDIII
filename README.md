# TECNOSOL Mar del Plata · Sistema de Ticketing

Trabajo Práctico Final Integrador 2026 («Ticket to Ride») · **Algoritmos y Estructuras de Datos III**
Instituto Superior de Formación Técnica N.º 151 · Analista en Sistemas, 3.er año

Aplicación web para que un área de atención al cliente **registre, siga y resuelva casos de soporte (tickets)**. Cada ticket guarda un historial de mensajes (**hitos**) entre el cliente y el representante, y el sistema **notifica** a la otra parte en cada novedad.

---

## Índice

1. [Qué hace la aplicación](#1-qué-hace-la-aplicación)
2. [Requisitos](#2-requisitos)
3. [Cómo abrir la aplicación](#3-cómo-abrir-la-aplicación)
4. [Usuarios de prueba](#4-usuarios-de-prueba)
5. [Recorrido sugerido para la demostración](#5-recorrido-sugerido-para-la-demostración)
6. [Cómo correr los tests](#6-cómo-correr-los-tests)
7. [Estructura del proyecto](#7-estructura-del-proyecto)
8. [Tecnologías](#8-tecnologías)
9. [Documentación](#9-documentación)
10. [Problemas frecuentes](#10-problemas-frecuentes)

---

## 1. Qué hace la aplicación

| Funcionalidad | Representante | Cliente |
|---|:---:|:---:|
| Iniciar y cerrar sesión (login) | ✔ | ✔ |
| Ver el panel con el resumen de tickets por estado | ✔ (todos) | ✔ (los suyos) |
| Crear un ticket para un cliente (CU001) | ✔ | — |
| Abrir un ticket a su propio nombre (entra en la cola de atención) | — | ✔ |
| Registrar un cliente nuevo desde el alta del ticket | ✔ | — |
| Consultar tickets y su historial de hitos (CU002) | ✔ | ✔ |
| Registrar un hito / responder (CU003) | ✔ | ✔ |
| Cerrar y reabrir tickets | ✔ | ✔ |
| Ver la cola de tickets y tomar uno (o "el siguiente", por orden de llegada) | ✔ | — |
| Pasar un ticket a *En proceso* y reasignarlo | ✔ | — |
| Buscar tickets por número, cliente o descripción y filtrarlos por estado y período | ✔ | ✔ |
| Ver el listado de tickets paginado (10 por página) | ✔ | ✔ |
| Cambiar su propia contraseña | ✔ | ✔ |
| Recibir notificaciones de la actividad de sus tickets | ✔ | ✔ |
| Gestionar y listar usuarios, clientes y representantes | ✔ | — |
| Gestionar y listar productos, tipos de producto y categorías | ✔ | — |

**Workflow de estados de un ticket**

```
            responde un representante / "Tomar ticket"
 ABIERTO ─────────────────────────────────────────────▶ EN PROCESO
    │                                                       │
    └──────────────── cerrar ──────────▶ CERRADO ◀── cerrar ┘
                                            │
 ABIERTO ◀──────────── reabrir ─────────────┘
```

---

## 2. Requisitos

- **Windows 10 o superior** (RNF del enunciado).
- **Python 3.10 o superior.** Si no lo tenés, descargalo de <https://www.python.org/downloads/>.
  Durante la instalación, **marcá la casilla "Add python.exe to PATH"**.
- **Conexión a internet solo la primera vez**, para descargar las librerías (Flask, SQLAlchemy y pytest).
- Un navegador: Chrome, Edge o Firefox.

No hace falta instalar ninguna base de datos. Se usa **SQLite**, que guarda todo en un archivo dentro de la carpeta del proyecto.

---

## 3. Cómo abrir la aplicación

### Opción A: doble clic (recomendada)

1. Abrí la carpeta del proyecto (por ejemplo `D:\TP Final`).
2. Hacé **doble clic en `iniciar.bat`**.
3. La primera vez prepara el entorno, lo que tarda uno o dos minutos. Después arranca enseguida.
4. El navegador se abre solo en **<http://127.0.0.1:5000>**.
5. Para cerrar la aplicación, cerrá la ventana negra (la consola).

### Opción B: desde una terminal

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

> La primera vez que se abre, la aplicación crea la base de datos `instancia/tecnosol.db` y carga **datos de ejemplo**: usuarios, productos y algunos tickets en distintos estados.

---

## 4. Usuarios de prueba

En la pantalla de login también figuran estos usuarios. Con un clic se completa el formulario.

| Rol | Email | Contraseña |
|---|---|---|
| Representante | `admin@tickettoride.com` | `admin123` |
| Representante | `laura@tickettoride.com` | `laura123` |
| Cliente | `juan@mail.com` | `cliente123` |
| Cliente | `maria@mail.com` | `cliente123` |
| Cliente | `lucas@mail.com` | `cliente123` |

> Mostrar los usuarios de prueba en el login sirve para la demostración. En un sistema real no se mostrarían: para ocultarlos, poné `MOSTRAR_USUARIOS_DEMO = False` en `app/config.py`.

---

## 5. Recorrido sugerido para la demostración

1. **Ingresá como representante** (`admin@tickettoride.com`). En el panel vas a ver el resumen por estado.
2. **Nuevo ticket**: buscá un cliente o tocá *Registrar cliente*, elegí un producto, escribí la incidencia y creá el ticket. El sistema muestra el **número de ticket** y lo deja en estado **Abierto** (CU001).
3. Dentro del ticket, **respondé**. El ticket pasa a **En proceso** y el cliente recibe una **notificación** (CU003).
4. **Cerrá sesión e ingresá como el cliente** del ticket. En **Mis tickets** aparece el ticket con su historial (CU002) y la campanita muestra la notificación.
5. Como cliente, **respondé** al representante, o **cerrá** el ticket. Después se puede **reabrir**.
6. Como representante, revisá **Usuarios** (alta, edición, baja lógica) y **Productos** (alta, categorías, filtros).

---

## 6. Cómo correr los tests

El proyecto se desarrolló con **TDD**: cada funcionalidad tiene sus pruebas automáticas en la carpeta [`tests/`](tests/README.md).

- **Doble clic en `correr_tests.bat`**, o
- desde una terminal, con el entorno activado:

```bash
pytest -v
```

Los tests usan una base de datos **en memoria**, así que no modifican los datos reales de la aplicación. En [`tests/README.md`](tests/README.md) está el detalle de qué cubre cada archivo.

---

## 7. Estructura del proyecto

```
TP Final/
├── iniciar.bat               ← abre la aplicación (doble clic)
├── correr_tests.bat          ← corre todos los tests (doble clic)
├── run.py                    ← punto de entrada: levanta el servidor web
├── requirements.txt          ← librerías necesarias
├── pytest.ini                ← configuración de los tests
├── README.md                 ← este archivo
│
├── app/                      ← código de la aplicación (ver app/README.md)
│   ├── models/               ← clases del diagrama (SQLAlchemy)
│   ├── services/             ← lógica de negocio
│   ├── web/                  ← rutas y seguridad (Flask)
│   ├── templates/            ← pantallas HTML
│   └── static/               ← estilos, JavaScript e imágenes
│
├── tests/                    ← pruebas automáticas (ver tests/README.md)
├── docs/
│   ├── especificaciones.md   ← requerimientos, historias de usuario y trazabilidad
│   └── arquitectura.md       ← diseño, modelo de datos y decisiones
├── scripts/                  ← script interno que prepara el entorno
└── instancia/                ← se crea sola: base de datos y clave secreta
```

Los documentos `.docx` del TP (requerimientos, casos de uso y diagramas de clases) están en la carpeta raíz, tal como se entregaron.

---

## 8. Tecnologías

| Capa | Tecnología | Para qué se usa |
|---|---|---|
| Lenguaje | **Python 3.10+** | Todo el back-end |
| Base de datos | **SQLite** | Archivo local, sin instalación |
| ORM | **SQLAlchemy 2.0** | Mapear las clases del diagrama a tablas |
| Web | **Flask 3** | Servidor web, rutas y plantillas (Jinja2) |
| Seguridad | **Werkzeug** | Hash de contraseñas (nunca se guardan en texto plano) |
| Interfaz | HTML + CSS + JavaScript | Diseño propio, responsive, sin frameworks |
| Tests | **pytest** | Pruebas unitarias y de integración (TDD) |

---

## 9. Documentación

- [`docs/especificaciones.md`](docs/especificaciones.md): requerimientos funcionales y no funcionales, **historias de usuario** con criterios de aceptación, reglas de negocio y matriz de trazabilidad (requerimiento → historia → caso de uso → test).
- [`docs/arquitectura.md`](docs/arquitectura.md): arquitectura en capas, diagrama de clases implementado, modelo de datos y decisiones de diseño.
- [`app/README.md`](app/README.md): guía del código fuente.
- [`tests/README.md`](tests/README.md): guía de los tests e iteraciones TDD.

---

## 10. Problemas frecuentes

| Problema | Solución |
|---|---|
| *"No se encontró Python"* | Instalá Python desde python.org y marcá **"Add python.exe to PATH"**. Después volvé a abrir `iniciar.bat`. |
| *"No se pudieron instalar las dependencias"* | La primera vez necesita internet. Conectate y volvé a intentar. |
| El navegador no se abre solo | Abrí manualmente <http://127.0.0.1:5000>. |
| *"Address already in use"* o el puerto 5000 está ocupado | Ya hay otra ventana de la aplicación abierta. Cerrala y volvé a intentar. |
| Quiero volver a los datos de ejemplo | Cerrá la aplicación, borrá el archivo `instancia/tecnosol.db` y volvé a abrirla. |
| Llevé el pendrive a otra computadora | No hace falta hacer nada: `iniciar.bat` detecta que el entorno es de otra PC y lo vuelve a preparar. |
