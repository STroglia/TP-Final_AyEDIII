"""Inicia el servidor web y abre la aplicación en el navegador.

Uso:  python run.py      (o doble clic en iniciar.bat / TECNOSOL.exe)
Puerto: 5000 por defecto; se puede cambiar con la variable de entorno TECNOSOL_PUERTO.
"""
import os
import socket
import threading
import webbrowser

HOST = "127.0.0.1"
PUERTO = int(os.environ.get("TECNOSOL_PUERTO", "5000"))
URL = f"http://{HOST}:{PUERTO}"


def puerto_en_uso() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, PUERTO)) == 0


if __name__ == "__main__":
    if puerto_en_uso():
        # La app ya está abierta (por ejemplo, doble clic dos veces): solo se abre el navegador.
        print(f"  La aplicación ya está corriendo. Abriendo {URL} ...")
        webbrowser.open(URL)
    else:
        from app import create_app

        app = create_app()
        print()
        print("  TECNOSOL Mar del Plata - Sistema de Ticketing")
        print(f"  La aplicación está corriendo en {URL}")
        print("  Para detenerla, cerrá esta ventana o presioná Ctrl + C.")
        print()
        threading.Timer(1.5, lambda: webbrowser.open(URL)).start()
        app.run(host=HOST, port=PUERTO, debug=False)
