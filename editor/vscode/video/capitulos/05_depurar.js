// Capítulo 5 del tutorial: depurar en el Amiga emulado (docs/IDE_VIDEO_LOOP.md, v7)
const fs = require('fs');
const path = require('path');

const PROGRAMA = `# Los puntos de una partida
func doble(n: Int) -> Int
    return n * 2
end

Main
    nombre = "Ana"
    puntos = [10, 25, 40, 5]
    suma = 0
    for i in (0..4)
        suma = suma + doble(puntos[i])
    end
    Print "#{nombre}: #{suma} puntos"
end
`;

const LAUNCH = {
    version: '0.2.0',
    configurations: [{ type: 'dash', request: 'launch', name: 'Depurar en el Amiga', program: '${workspaceFolder}/partida.dash' }],
};

/** The debugger stopped: the yellow line of where it is */
async function parado(r, ms = 240000) {
    await r.page.waitForSelector('.monaco-editor .debug-top-stack-frame-line', { timeout: ms }).catch(() => {});
    await r.esperar(800);
}

module.exports = {
    titulo: '5. Depurar',
    resumen: 'Puntos de parada, variables y paso a paso, en el Amiga emulado',
    carpeta: 'partida',
    preparar(dir) {
        fs.writeFileSync(path.join(dir, 'partida.dash'), PROGRAMA);
        fs.mkdirSync(path.join(dir, '.vscode'), { recursive: true });
        fs.writeFileSync(path.join(dir, '.vscode', 'launch.json'), JSON.stringify(LAUNCH, null, 2) + '\n');
    },
    open: ['partida.dash'],
    async guion(r) {
        await r.decir('Este programa suma los puntos de una partida, pero algo falla', 4000);
        // a breakpoint
        r.subtitulo('Un clic a la izquierda de una línea pone un punto de parada', 4000);
        await r.clic(await r.margen('suma = suma + doble'));
        await r.esperar(2500);
        // F5
        r.subtitulo('F5 lo compila, arranca el Amiga emulado y para en el punto', 6000);
        await r.tecla('F5', 500);
        await r.saltar(() => parado(r));
        await r.esperar(4000);
        r.subtitulo('A la izquierda, las variables como las escribe Dash: el texto, la lista, los números', 7000);
        await r.clic('.debug-view-content .monaco-list-row:has-text("Locals")');
        await r.esperar(1500);
        await r.clic('.debug-view-content .monaco-list-row:has-text("puntos")');
        await r.esperar(4500);
        // the debug console
        r.subtitulo('En la consola de depuración se escriben expresiones de Dash', 5000);
        await r.tecla('Control+Shift+y', 1200);
        await r.escribir('puntos[i] * 2', 80);
        await r.tecla('Enter', 1500);
        await r.escribir('nombre.length', 80);
        await r.tecla('Enter', 2500);
        // steps
        r.subtitulo('F11 entra en la función: la pila dice desde dónde se llamó', 6000);
        await r.clic(r.linea('suma = suma + doble'));
        await r.tecla('F11', 500);
        await r.saltar(() => parado(r, 30000));
        await r.esperar(4500);
        r.subtitulo('Mayúsculas+F11 sale de ella, y F10 pasa a la línea siguiente', 5000);
        await r.tecla('Shift+F11', 500);
        await r.saltar(() => parado(r, 30000));
        await r.esperar(2000);
        await r.tecla('F10', 500);
        await r.saltar(() => parado(r, 30000));
        await r.esperar(2500);
        // a condition
        r.subtitulo('Un punto con condición: solo para cuando i vale 3', 7000);
        await r.clic(await r.margen('suma = suma + doble'), { button: 'right' });
        await r.esperar(800);
        await r.clic(r.page.locator('.context-view .action-label', { hasText: /Edit Breakpoint|Editar punto/ }).first());
        await r.esperar(800);
        await r.escribir('i == 3', 90);
        await r.tecla('Enter', 1200);
        await r.tecla('F5', 500);
        await r.saltar(() => parado(r, 60000));
        await r.esperar(3500);
        // the error
        r.subtitulo('Sin el punto, sigue hasta el fallo: para en su línea, como una excepción', 7000);
        await r.clic(await r.margen('suma = suma + doble'));
        await r.esperar(600);
        await r.tecla('F5', 500);
        await r.saltar(() => r.page.waitForSelector('.zone-widget .exception-widget, .debug-exception-widget, .exception-widget', { timeout: 60000 }).catch(() => {}));
        await r.esperar(6000);
        await r.decir('El índice 4 no está en una lista de 4: el bucle debía ir de 0 a 3', 5000);
        await r.tecla('Shift+F5', 1500);
        await r.decir('En el capítulo siguiente: depurar en un Amiga de verdad', 3000);
    },
};
