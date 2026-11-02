#!/usr/bin/env python3
"""El depurador por la red (tools/amiga/dbgserver.dash, el de la extensión de VS Code): en el A1200 emulado,
dbgserver con depurar/depurado_datos.dash compilado con --debug, y este test conectado por TCP como lo hace la
extensión (el bsdsocket de FS-UAE usa los sockets del PC). Comprueba un punto de parada en una línea, la pila, las
variables y las globales, pasar, salir de una función, la salida y el código del final; y en otro programa que no
acaba, su salida mientras corre, pausa y acabarlo.

    flock /run/user/1000/dash-emu-red.lock python3 tests/depurar_vscode.py [--a500]

Luego, si hay node, el adaptador de VS Code (editor/vscode/test/dashc_emu.js) contra el mismo servidor."""
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "tools"))
import emu_run  # noqa: E402

D = HERE / "depurar"
FALLOS = []


def check(nombre, ok, detalle=""):
    print(("ok   " if ok else "MAL  ") + nombre + ("" if ok else f": {detalle}"), flush=True)
    if not ok:
        FALLOS.append(nombre)


def unescape(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            out.append({"n": "\n", "t": "\t", "r": "\r"}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


class Cliente:
    """Las órdenes de una línea y sus respuestas; los avisos (*out, *stopped, *ended) aparte"""

    def __init__(self, port):
        self.s = socket.create_connection(("127.0.0.1", port), timeout=120)
        self.buf = b""
        self.avisos = []
        self.salida = ""

    def linea(self):
        while b"\n" not in self.buf:
            d = self.s.recv(4096)
            if not d:
                raise EOFError("conexión cerrada")
            self.buf += d
        raw, self.buf = self.buf.split(b"\n", 1)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        campos = [unescape(c) for c in text.split("\t")]
        if campos[0] == "*out":
            self.salida += campos[1]
        return campos

    def orden(self, *campos):
        self.s.sendall(("\t".join(str(c) for c in campos) + "\n").encode("utf-8"))
        datos = []
        while True:
            c = self.linea()
            if c[0].startswith("*"):
                self.avisos.append(c)
            elif c[0] in ("ok", "error"):
                return c, datos
            else:
                datos.append(c)

    def aviso(self, clase, tope=60):
        """El siguiente aviso de esa clase (stopped, ended)"""
        fin = time.time() + tope
        while time.time() < fin:
            for i, a in enumerate(self.avisos):
                if a[0] == "*" + clase:
                    return self.avisos.pop(i)
            c = self.linea()
            if c[0].startswith("*") and c[0] != "*out":
                self.avisos.append(c)
        raise TimeoutError(clase)


def main():
    a500 = "--a500" in sys.argv
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        env = dict(os.environ, DASH_PRINT_FLUSH="1")
        for nombre in ("depurado_datos", "depurado"):
            subprocess.run([str(REPO / "dash"), "--debug", str(D / (nombre + ".dash")), "-o", str(tmp / nombre)],
                           check=True, env=env)
        port = emu_run._free_port()
        res = []

        def emulador():
            res.extend(emu_run.run_programs(
                [str(tmp / "depurado_datos")], timeout=600, dbgserver=port,
                kickstart=os.environ["DASH_KICKSTART_A500" if a500 else "DASH_KICKSTART"],
                system=os.environ.get("DASH_EMU_SYS"), extra_config="amiga_model = A500\n" if a500 else "",
                on_disk=lambda hd: shutil.copy(tmp / "depurado", Path(hd) / "depurado")))

        hilo = threading.Thread(target=emulador, daemon=True)
        hilo.start()
        emu_run._wait_listening(port, 300)
        c = Cliente(port)
        try:
            check("saludo", c.linea() == ["dbgserver", "1"])
            r, _ = c.orden("start", "", "")
            check("start", r == ["ok"], r)
            fuente = str(D / "depurado_datos.dash")
            r1, _ = c.orden("break", fuente, 12)                  # el nombre entero
            r2, _ = c.orden("break", "depurado_datos.dash", 2)    # sin código
            check("break", r1 == ["ok", "true"] and r2 == ["ok", "false"], (r1, r2))
            c.orden("continue")
            a = c.aviso("stopped")
            check("parado en la línea 12", a == ["*stopped", "breakpoint", fuente, "12", "mira"], a)
            _, frames = c.orden("frames")
            check("pila", frames == [["frame", "12", "mira", fuente], ["frame", "23", "Main", fuente]], frames)
            _, vs = c.orden("vars", 0)
            check("variables", vs == [["var", "p", "Punto", 'Punto(x: 4, nombre: "dos \\"x\\"", hijos: [Punto(...)])'],
                                      ["var", "n", "Int", "2"]], vs)
            _, vals = c.orden("values", 1, "lista", "lista[7]", "f", "nada")
            _, vals0 = c.orden("values", 0, "p.hijos[0].nombre")
            _, glob = c.orden("values", -1, "cuenta", "p")             # -1: solo las globales
            check("valores", vals == [["val", "[Int]", "[10, 20, 30]"], ["val", "", "? fuera de la lista"],
                                      ["val", "Float", "1.5"], ["val", "", "? no existe: nada"]]
                  and vals0 == [["val", "String", '"uno"']]
                  and glob == [["val", "Int", "7"], ["val", "", "? no existe: p"]], (vals, vals0, glob))
            _, gs = c.orden("globals")
            check("globales", gs == [["var", "cuenta", "Int", "7"], ["var", "saludo", "String", '"hola"']], gs)
            c.orden("next")
            a = c.aviso("stopped")
            check("pasar", a[1:] == ["step", fuente, "13", "mira"], a)
            c.orden("out")
            a = c.aviso("stopped")
            check("salir", a[1:] == ["step", fuente, "24", "Main"], a)
            _, vals = c.orden("values", 0, "r")
            check("r tras la llamada", vals == [["val", "Int", "6"]], vals)
            c.orden("unbreak", fuente, 12)
            c.orden("continue")
            a = c.aviso("ended")
            check("acabado con su código", a == ["*ended", "0"], a)
            check("su salida", c.salida == "r: 6\n", repr(c.salida))

            c.salida = ""
            r, _ = c.orden("start", "DH0:depurado", "bucle")
            check("otro programa con argumentos", r == ["ok"], r)
            c.orden("continue")
            fin = time.time() + 30
            while "c: 11" not in c.salida and time.time() < fin:
                c.s.settimeout(max(0.1, fin - time.time()))
                c.avisos.append(c.linea())
            c.s.settimeout(120)
            check("la salida mientras corre", c.salida == "b: 10\nc: 11\n", repr(c.salida))
            r, _ = c.orden("state")
            check("corriendo", r == ["ok", "2"], r)
            c.orden("pause")
            a = c.aviso("stopped")
            check("pausa", a[1] == "pause" and a[4] == "vueltas", a)
            r, _ = c.orden("quit")
            check("acabarlo", r == ["ok", "20"], r)
        except Exception as e:  # noqa: BLE001
            check("sin errores", False, repr(e))
        finally:
            c.s.close()
        hilo.join(120)
        check("el servidor acaba", bool(res) and res[0].rc == 0 and not (res[0].output or "").strip(),
              res and (res[0].rc, res[0].output))

        if shutil.which("node") and "--sin-node" not in sys.argv:
            print("--- el adaptador de VS Code", flush=True)
            r = subprocess.run(["node", str(REPO / "editor" / "vscode" / "test" / "dashc_emu.js")]
                               + (["--a500"] if a500 else []))
            check("adaptador de VS Code (dashc_emu.js)", r.returncode == 0)
    print("todo bien" if not FALLOS else f"{len(FALLOS)} mal")
    return 1 if FALLOS else 0


if __name__ == "__main__":
    sys.exit(main())
