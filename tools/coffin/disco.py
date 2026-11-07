#!/usr/bin/env python3
"""El disco del Amiga de pruebas como CoffinOS (tools/coffin/README.md): poner al día lo que lleva de Dash.

    tools/coffin/disco.py actualizar          # Dash, Forja, Inferencia, dashgit, Trasfondo y Tachyon, lo último
    tools/coffin/disco.py fondo               # vuelve a hacer el fondo (tools/coffin/fondo.py) y lo instala
    tools/coffin/disco.py ejecutar orden.txt [fichero...]   # unas líneas de AmigaDOS (DASHRUN: es la carpeta de
                                                            # trabajo, con esos ficheros del PC)

Arranca en FS-UAE el propio disco ($DASH_EMU_DISK_COFFIN, no una copia) con la ROM de $DASH_KICKSTART_32 y le deja
las órdenes en DASHRUN:Run-Sequence, que su Startup-Sequence ejecuta tras LoadWB. Al final espera unos segundos
antes de apagar: PFS3 guarda en caché lo escrito y lo último se perdería.

De dónde sale cada cosa: el paquete de Dash de build/paquete_amiga/Dash (python3 tools/paquete_amiga.py), el lha
más nuevo de ~/Projects/trasfondo/build/release y ~/Projects/tachyon/build/paquete/Tachyon.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
from emu_run import COFFIN_CONFIG, FSUAE_CONFIG   # noqa: E402

TRASFONDO = Path.home() / "Projects/trasfondo/build/release"
TACHYON = Path.home() / "Projects/tachyon/build/paquete"


def arrancar(lineas, trabajo: Path, limite=600):
    """Arranca el disco con estas órdenes en DASHRUN:Run-Sequence (trabajo es DASHRUN:) y espera a que acaben."""
    disco = os.environ.get("DASH_EMU_DISK_COFFIN")
    rom = os.environ.get("DASH_KICKSTART_32")
    if not disco or not Path(disco).is_file() or not rom:
        sys.exit("hacen falta $DASH_EMU_DISK_COFFIN (el disco) y $DASH_KICKSTART_32 (la ROM 3.2.3)")
    lineas = ["FailAt 21"] + lineas + ["C:Wait 12", 'Echo "fin" >DASHRUN:hecho.txt']
    (trabajo / "Run-Sequence").write_text("\n".join(lineas) + "\n", encoding="latin-1")
    (trabajo / "hecho.txt").unlink(missing_ok=True)
    conf = trabajo.parent / "disco.fs-uae"
    base = FSUAE_CONFIG.format(hd=trabajo, kickstart=f"kickstart_file = {rom}\n")
    base = base.replace(f"hard_drive_0 = {trabajo}\nhard_drive_0_label = DH0\n",
                        f"hard_drive_0 = {disco}\nhard_drive_9 = {trabajo}\nhard_drive_9_label = DASHRUN\n"
                        "hard_drive_9_priority = -128\n").replace("fast_memory = 8192\n", "")
    conf.write_text(base + COFFIN_CONFIG)
    env = dict(os.environ, SDL_VIDEODRIVER="offscreen", SDL_AUDIODRIVER="dummy")
    proc = subprocess.Popen(["fs-uae", str(conf)], env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        fin = time.time() + limite
        while time.time() < fin and not (trabajo / "hecho.txt").exists():
            if proc.poll() is not None:
                sys.exit("FS-UAE se cerró antes de acabar")
            time.sleep(1)
        if not (trabajo / "hecho.txt").exists():
            sys.exit(f"sin acabar en {limite} s")
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()


def actualizar(trabajo: Path):
    dash = RAIZ / "build/paquete_amiga/Dash"
    if not (dash / "dash").is_file():
        sys.exit("falta build/paquete_amiga/Dash: python3 tools/paquete_amiga.py")
    shutil.copytree(dash, trabajo / "Dash")
    lineas = ["C:Copy DASHRUN:Dash Programs:Programming/Dash ALL CLONE QUIET"]
    lhas = sorted(TRASFONDO.glob("trasfondo-*.lha"), key=lambda p: p.stat().st_mtime)
    if lhas:
        subprocess.run(["lha", "xqw=" + str(trabajo), str(lhas[-1])], check=True)
        tf = trabajo / "Trasfondo"
        for icono in tf.glob("*.info"):   # los iconos de la instalación de Coffin se quedan como están
            icono.unlink()
        (tf / "Instalar").unlink(missing_ok=True)
        shutil.rmtree(tf / "Arranque", ignore_errors=True)
        catalogo = next(tf.glob("Catalogs/espa*ol/Trasfondo.catalog"), None)
        if catalogo:
            shutil.copy(catalogo, trabajo / "Trasfondo.catalog")
        shutil.move(tf / "TrasfondoPrefs", trabajo / "TrasfondoPrefs")
        lineas += ["C:Copy DASHRUN:Trasfondo SYS:Utilities/Trasfondo ALL CLONE QUIET",
                   "C:Copy DASHRUN:TrasfondoPrefs SYS:Prefs/TrasfondoPrefs CLONE QUIET"]
        if catalogo:
            lineas.append('C:Copy DASHRUN:Trasfondo.catalog "LOCALE:Catalogs/español/Trasfondo.catalog" CLONE QUIET')
    else:
        print(f"sin Trasfondo (no hay trasfondo-*.lha en {TRASFONDO})")
    if (TACHYON / "Tachyon").is_dir():
        shutil.copytree(TACHYON / "Tachyon", trabajo / "Tachyon")
        lineas.append("C:Copy DASHRUN:Tachyon Programs:Network/Tachyon ALL CLONE QUIET")
        if (TACHYON / "Tachyon.info").is_file():
            shutil.copy(TACHYON / "Tachyon.info", trabajo / "Tachyon.info")
            lineas.append("C:Copy DASHRUN:Tachyon.info Programs:Network/Tachyon.info CLONE QUIET")
    else:
        print(f"sin Tachyon (no hay {TACHYON}/Tachyon)")
    # la CA de los servidores TLS del runner (tools/emu_sys_amissl.sh la hace), para los tests de TLS
    ca = Path(os.environ.get("DASH_AMISSL_DIR", Path.home() / ".cache/dash-amissl")) / "testca/ca.pem"
    if ca.is_file():
        nombre = subprocess.run(["openssl", "x509", "-hash", "-noout", "-in", str(ca)], capture_output=True,
                                text=True, check=True).stdout.strip() + ".0"
        shutil.copy(ca, trabajo / nombre)
        lineas.append(f"C:Copy DASHRUN:{nombre} AmiSSL:Certs/{nombre} QUIET")
    lineas.append("Version Programs:Programming/Dash/dash >DASHRUN:version.txt")
    arrancar(lineas, trabajo)
    print((trabajo / "version.txt").read_text(encoding="latin-1").strip())


def fondo(trabajo: Path):
    png = trabajo / "dash.png"
    subprocess.run([sys.executable, str(Path(__file__).parent / "fondo.py"), str(png), "1280", "1024"], check=True)
    from PIL import Image
    Image.open(png).convert("RGB").save(trabajo / "dash.jpg", quality=93)
    arrancar(["C:MakeDir >NIL: SYS:Prefs/Presets/Themes/dash",
              "C:Copy DASHRUN:dash.jpg SYS:Prefs/Presets/Themes/dash/dash.jpg QUIET"], trabajo)


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("actualizar", "fondo", "ejecutar"):
        sys.exit(__doc__)
    with tempfile.TemporaryDirectory(prefix="dash_coffin_") as tmp:
        trabajo = Path(tmp) / "run"
        trabajo.mkdir()
        if sys.argv[1] == "actualizar":
            actualizar(trabajo)
        elif sys.argv[1] == "fondo":
            fondo(trabajo)
        else:
            for f in sys.argv[3:]:
                shutil.copy(f, trabajo / Path(f).name)
            arrancar(Path(sys.argv[2]).read_text(encoding="latin-1").splitlines(), trabajo)
            for f in sorted(trabajo.glob("*.txt")):   # lo que las órdenes dejaron en DASHRUN:x.txt
                if f.name != "hecho.txt":
                    print(f"=== {f.name}\n" + f.read_text(encoding="latin-1"), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
