// Capítulo 3 del tutorial: la ventana en el editor visual, Ver en Amiga y del evento al código (docs/IDE_VIDEO_LOOP.md, v5)
const fs = require('fs');
const path = require('path');
const { projectFiles } = require('../../newProject');

module.exports = {
    titulo: '3. La ventana',
    resumen: 'El editor visual, la ventana en el Amiga y su código',
    carpeta: 'hola',
    preparar(dir) {
        for (const [rel, text] of Object.entries(projectFiles('hola').files)) {
            fs.mkdirSync(path.dirname(path.join(dir, rel)), { recursive: true });
            fs.writeFileSync(path.join(dir, rel), text);
        }
    },
    open: ['hola.dash'],
    async guion(r) {
        await r.clic('.explorer-folders-view .monaco-list-row >> text=ventana.dashui');
        await r.esperar(2500);
        await r.decir('ventana.dashui se abre en el editor visual: objetos, la ventana en árbol y sus propiedades', 5000);
        // a new button, after the text
        await r.clic(r.web('.tree-row:has-text("saludo")'));
        r.subtitulo('Un botón nuevo: se elige dónde y se pulsa en la paleta', 4500);
        await r.esperar(1200);
        await r.clic(r.web('#palette button[data-type="button"]'));
        await r.esperar(1500);
        // its properties
        r.subtitulo('Sus propiedades: el nombre, el texto y el número de su evento', 6000);
        await r.clic(r.web('#prop-name'));
        await r.escribir('otro', 120);
        await r.tecla('Tab', 300);
        await r.clic(r.web('#prop-label'));
        await r.tecla('Control+a', 100);
        await r.escribir('_Otro', 120);
        await r.tecla('Tab', 300);
        await r.clic(r.web('#prop-event'));
        await r.escribir('3', 120);
        await r.tecla('Tab', 1200);
        // the keyboard in the tree, and undo
        await r.clic(r.web('.tree-row:has-text("otro")'));
        r.subtitulo('Con el teclado: Alt y las flechas lo mueven', 4000);
        await r.tecla('Alt+ArrowDown', 1200);
        await r.tecla('Alt+ArrowUp', 1500);
        r.subtitulo('Y se deshace como en cualquier fichero', 3500);
        await r.clic(r.web('#undo'));
        await r.esperar(1000);
        await r.clic(r.web('#redo'));
        await r.esperar(1500);
        // the real window, in the emulated Amiga
        r.subtitulo('"Ver en Amiga" la enseña en el Amiga emulado, con MUI de verdad', 7000);
        await r.clic(r.web('#amiga'));
        await r.page.waitForTimeout(500);
        await r.web('#amiga-shot[src^="data:"]').waitFor({ state: 'attached', timeout: 120000 });
        await r.esperar(1000);
        await r.mover(r.web('#amiga-shot'));
        await r.decir('La primera vez arranca el emulador; después tarda un par de segundos', 4500);
        // from the event to its code
        await r.clic(r.web('.tree-row:has-text("otro")'));
        r.subtitulo('La flecha junto al evento lleva a su código en el programa…', 4500);
        await r.clic(r.web('#props button.goto'));
        await r.esperar(1500);
        await r.clic(r.page.getByRole('button', { name: 'Crear' }).last());
        await r.esperar(2500);
        await r.decir('…y como no existía, lo crea: la constante y su if en el bucle de eventos', 5000);
        await r.decir('En el capítulo siguiente: compilar y ejecutar en el emulador', 3000);
    },
};
