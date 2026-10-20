// Capítulo 4 del tutorial: compilar y ejecutar en el emulador (docs/IDE_VIDEO_LOOP.md, v6)
const fs = require('fs');
const path = require('path');

const PROGRAMA = `# Cuenta los números primos hasta un límite
func es_primo(n: Int) -> Bool
    if n < 2
        return false
    end
    d = 2
    while d * d <= n
        if n % d == 0
            return false
        end
        d = d + 1
    end
    return true
end

Main
    cuantos = 0
    for n in (1..2000)
        if es_primo(n)
            cuantos = cuantos + 1
        end
    end
    Print "Hay #{cuantos} primos hasta 2000"
end
`;

/** The terminal shows this text (the emulator's output went there) */
async function enTerminal(r, text, ms = 180000) {
    await r.page.waitForFunction((t) => [...document.querySelectorAll('.terminal .xterm-rows, .xterm-accessibility-tree, .xterm-screen')]
        .some((e) => (e.textContent || '').includes(t)), text, { timeout: ms }).catch(() => {});
}

module.exports = {
    titulo: '4. Compilar y ejecutar',
    resumen: 'En el Amiga emulado, en varias máquinas, con memoria y perfil',
    carpeta: 'primos',
    preparar(dir) {
        fs.writeFileSync(path.join(dir, 'primos.dash'), PROGRAMA);
    },
    open: ['primos.dash'],
    settings: { 'terminal.integrated.fontSize': 15 },
    async guion(r) {
        await r.decir('Un programa de consola que cuenta números primos', 3500);
        // compile
        r.subtitulo('"Compilar" lo pasa a C y lo compila para el Amiga', 5000);
        await r.clic(r.page.locator('.codelens-decoration a', { hasText: 'Compilar' }).first());
        await r.saltar(() => enTerminal(r, 'Success'));
        await r.esperar(3000);
        // a mistake: to Problems, at its line
        await r.irALinea(20);
        await r.tecla('End');
        await r.escribir('x', 200);
        r.subtitulo('Con un error, la compilación lo lleva a Problemas, en su línea', 6000);
        await r.clic(r.page.locator('.codelens-decoration a', { hasText: 'Compilar' }).first());
        await r.saltar(() => r.esperar(6000));
        await r.tecla('Control+Shift+m', 3000);
        await r.tecla('Control+z', 400);
        await r.tecla('Control+s', 1000);
        // run
        r.subtitulo('"Ejecutar" lo lanza en FS-UAE, sin ventana: su salida sale aquí', 7000);
        await r.clic(r.page.locator('.codelens-decoration a', { hasText: 'Ejecutar' }).first());
        await r.saltar(() => enTerminal(r, 'primos hasta 2000'));
        await r.esperar(4000);
        // another machine
        r.subtitulo('La máquina se elige abajo: A1200, A500, A1200 con 3.2 o un 68040 con tarjeta gráfica', 6000);
        await r.clic('.statusbar-item:has-text("A1200")');
        await r.esperar(1800);
        await r.clic(r.page.locator('.quick-input-list .monaco-list-row', { hasText: 'A500' }).first());
        await r.esperar(1000);
        r.subtitulo('En un A500, con su 68000 de 7 MHz', 5000);
        await r.clic(r.page.locator('.codelens-decoration a', { hasText: 'Ejecutar' }).first());
        await r.saltar(() => enTerminal(r, 'primos hasta 2000'));
        await r.esperar(3000);
        // profile
        r.subtitulo('"Perfil" dice cuánto tiempo se va en cada función', 6000);
        await r.clic(r.page.locator('.codelens-decoration a', { hasText: 'Perfil' }).first());
        await r.saltar(() => r.page.waitForSelector('.tab:has-text("Perfil")', { timeout: 240000 }).catch(() => {}));
        await r.esperar(5000);
        await r.decir('En el capítulo siguiente: depurar con puntos de parada', 3000);
    },
};
