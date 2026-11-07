# Amiga de pruebas como CoffinOS

Un Amiga emulado como el CoffinOS del autor, para probar Dash en un sistema de verdad: ROM 3.2.3, 68040 con JIT a
toda velocidad, RTG de 32 bits (1280x1024), MUI, AmiSSL, DOpus5, Trasfondo y los programas de Coffin. No lleva
juegos ni demos. Plan y bitácora: `docs/COFFIN_EMU_LOOP.md`.

## Piezas (no van al repo)

| Qué | Dónde |
|-----|-------|
| Disco (RDB, PFS3): System (DH0, 1 GB), Programs (DH1, 6 GB), MyFiles (DH2, 1,5 GB) | `~/Amiberry/HardDrives/DashCoffin.hdf` |
| Configuración de FS-UAE | `~/Documentos/FS-UAE/Configurations/DashCoffin.fs-uae` |
| Configuración de Amiberry | `~/Amiberry/Configurations/DashCoffin.uae` |
| ROM | `~/Amiberry/kickstarts/ks323_A1200_47.115_noSCSI.rom` |

El disco sale del de Coffin R65: System entero, Programs sin `Games`, `Demos` ni `ScummVM`, MyFiles sin `Videos`
ni `Music`. Lleva instalados Dash (con Forja, Inferencia y dashgit), Trasfondo y Tachyon, y el fondo de `fondo.py`.

Las dos configuraciones son las de Coffin con el disco nuevo. A la de FS-UAE le hace falta `uae_rtg_modes = 0x112`
(la misma lista de modos que Amiberry): sin ella, el Workbench se abre en AGA.

## Usarlo

Abrir la configuración `DashCoffin` en FS-UAE o en Amiberry. En Amiberry también vale `amiberry -f
~/Amiberry/Configurations/DashCoffin.uae`. La carpeta `~/Amiberry/LHA` aparece como `Traspaso:`.

Pruebas desde el PC, con `DASH_KICKSTART_32` (la ROM) y `DASH_EMU_DISK_COFFIN` (el disco):

```bash
tools/emu_run.py --machine coffin --dash2 prog.dash                       # FS-UAE
tools/emu_run.py --machine coffin --emulator amiberry --dash2 prog.dash   # Amiberry (con xvfb-run, si está)
tools/emu_run.py --machine coffin --screenshot 25 shot.png prog.dash      # captura a 1280x1024
python3 tests/run_tests.py --emu-coffin                                   # la batería, en un solo arranque
```

Cada arranque usa una copia del disco (reflink en btrfs: instantánea) que se borra al acabar, así que las pruebas no
lo cambian y pueden ir varias a la vez. Los programas van en una carpeta del PC montada como `DASHRUN:` (DH9). El
`S:Startup-Sequence` del disco ejecuta `DASHRUN:Run-Sequence` tras `LoadWB`, si está.

## Ponerlo al día

```bash
python3 tools/paquete_amiga.py           # el paquete de Dash
tools/coffin/disco.py actualizar         # Dash, Trasfondo (su último lha) y Tachyon, en el propio disco
tools/coffin/disco.py fondo              # rehacer el fondo
tools/coffin/disco.py ejecutar ordenes.txt   # otras órdenes de AmigaDOS
```

`disco.py` arranca el disco de verdad, no una copia. Antes de apagar espera unos segundos: PFS3 guarda en caché lo
escrito, y si el emulador se apaga enseguida se pierde lo último.
