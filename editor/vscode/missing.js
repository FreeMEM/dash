// @ts-check
// What is missing, from what Dash's tools say (./dash, tools/emu_run.py, tools/emu_preview.py), in words, with how
// to get it (docs/IDE_VIDEO_LOOP.md, v12). No vscode here: the tests use it as it is.

const KNOWN = [
    [/dash: falta el compilador; /,
     () => 'Falta construir el compilador de Dash: en la carpeta de Dash, ejecuta make -C dashc (una vez, y tras cada git pull).'],
    [/falta el compilador para DashOS/,
     () => 'Falta construir el compilador para DashOS: en la carpeta de Dash, ejecuta make -C dashc dashc-a64.'],
    [/falta libkit_c\.a de DashOS/,
     () => 'El programa tiene ventanas (mui_*) y falta libkit_c.a de DashOS: make -C kernel kit-c en la carpeta de ' +
           'DashOS, y esa carpeta en el ajuste "dash.dashos.folder" (o el fichero en "dash.dashos.kitC").'],
    [/No such file or directory: '(qemu-aarch64(?:_be)?|clang|ld\.lld|llvm-[a-z]+)'/,
     (m) => m[1].startsWith('qemu')
         ? `Falta QEMU para ARM (${m[1]}), que ejecuta los programas de DashOS en el PC: instala el paquete qemu-user.`
         : `Falta ${m[1]} (LLVM), que hace los programas de DashOS: instala clang, lld y llvm.`],
    [/m68k-amigaos-gcc not found|Falta el compilador de Amiga/,
     () => 'Falta el compilador de Amiga (m68k-amigaos-gcc, en /opt/amiga/bin): instálalo como dice el README de Dash ' +
           '(o pon su carpeta en DASH_TOOLCHAIN).'],
    [/(fs-uae|amiberry) not found/,
     (m) => `Falta el emulador ${m[1] === 'amiberry' ? 'Amiberry' : 'FS-UAE'}: instálalo (paquete ${m[1]}) o elige ` +
            'el otro en el ajuste "dash.emulator.program".'],
    [/bgdbserver not found/,
     () => 'Falta bgdbserver para depurar: en la carpeta de Dash, ejecuta tools/get_bgdbserver.sh (lo baja de Aminet).'],
    [/MUI SDK not found/,
     () => 'Falta el SDK de MUI para compilar ventanas MUI: en la carpeta de Dash, ejecuta tools/get_mui_sdk.sh.'],
    [/AmiSSL SDK not found/,
     () => 'Falta el SDK de AmiSSL para TLS: en la carpeta de Dash, ejecuta tools/get_amissl.sh.'],
    [/needs \$DASH_EMU_SYS(_32)?_MUI/,
     (m) => 'El Amiga emulado no tiene MUI: prepara un sistema con MUI (tools/emu_sys_mui.sh de Dash) y pon su ' +
            `carpeta en el ajuste "dash.emulator.${m[1] ? 'muiSystem32' : 'muiSystem'}".`],
    [/needs \$DASH_KICKSTART(_A500|_32)?\b/,
     (m) => 'Falta la ROM de Kickstart de esa máquina: pon su fichero en el ajuste ' +
            `"dash.emulator.${{ _A500: 'kickstartA500', _32: 'kickstart32' }[m[1]] || 'kickstart'}".`],
];

/** The explanation of the first thing missing that text tells of, or null */
function missing(text) {
    for (const [re, say] of KNOWN) {
        const m = re.exec(String(text || ''));
        if (m) return say(m);
    }
    return null;
}

module.exports = { missing };
