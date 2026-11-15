# Dash para PPC: MorphOS, AmigaOS 4 y WarpOS (notas para el plan)

Sin empezar. Va después de la fusión de ide-piezas (D13 en `docs/DASHC_LOOP.md`): el camino `./dash --c` (el C de
dash1) compilado con el gcc de cada sistema, adaptando el runtime. El gcc de bebbo solo da 68k.

## Lo que hay que adaptar del runtime

Lo que depende del 68000: `TRAP_RUNTIME` (`tc_TrapCode`), el float por software en ensamblador
(`runtime/softfloat`, `fastfp.c`), el `swapstack` de libnix, las macros de librería con `register asm` y el código
`@native` de `lib/amiga`. En OS4 las librerías van por interfaces (`IExec->...`; `__USE_INLINE__` deja las llamadas
de siempre).

## Notas de Jaime Cagigal (Telegram, privado, 2026-10-24)

- **MorphOS:** tiene el compilador cruzado instalado sin Docker; hay un script que lo baja y lo compila. Pedírselo
  al empezar.
- **WarpOS:** Hedeon prepara elf2exe3 para compilar en cruzado a WarpOS (PPC en el Amiga clásico; la PiStorm tendrá
  emulación de PPC, de Michal). Pasar de PPC a 68k y al revés es muy caro: solo merece la pena para cálculo pesado
  sin llamadas a 68k por medio. Jaime portó MPlayer a WarpOS (parado): hay cosas que van en MorphOS y no en WarpOS,
  y meter código 68k en el binario PPC le dio problemas.
- **Shaders (WebGL en Tachyon):** solo en PiStorm, MorphOS (limitados) y OS4.
- **Vídeo:** la PiStorm tiene desde hace poco descompresión de vídeo por hardware; YouTube con eso en Tachyon
  "lo petaría". Wayfarer tiene un modo que reproduce YouTube desde su propia página, sin su JavaScript.
- **Consejos:** decidir bien qué sistemas se soportan; MUI funciona en todos (no dibujar la interfaz a mano con
  Intuition). Hacer lo que vaya a usar uno mismo: por ejemplo, un cliente SSH con pestañas y árbol de servidores
  (como mRemote), para clásico y MorphOS.
- **Herramientas con IA:** las IAs leen bien binarios (ingeniería inversa, https://github.com/morluto/rea): se
  podría arreglar o ampliar MiamiDX. Un MCP para el Amiga (real o emulado): órdenes ARexx, capturas de pantalla y la
  salida de depuración del puerto serie (como Sashimi) para que la lea la IA.
