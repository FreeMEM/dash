// Capítulo 2 del tutorial: escribir código (docs/IDE_VIDEO_LOOP.md, v4)
const fs = require('fs');
const path = require('path');
const { projectFiles } = require('../../newProject');

module.exports = {
    titulo: '2. Escribir código',
    resumen: 'Colores, errores al teclear, completar, ayuda y renombrar',
    carpeta: 'hola',
    preparar(dir) {
        for (const [rel, text] of Object.entries(projectFiles('hola').files)) {
            fs.mkdirSync(path.dirname(path.join(dir, rel)), { recursive: true });
            fs.writeFileSync(path.join(dir, rel), text);
        }
    },
    open: ['hola.dash'],
    async guion(r) {
        await r.decir('El programa del proyecto. Los colores separan palabras clave, textos, números y órdenes del Amiga', 5000);
        // a mistake while typing, and its quick fix
        await r.clic(r.linea('veces = veces + 1'));
        await r.tecla('End');
        await r.tecla('Enter');
        await r.escribir('veces = vecs + 1', 110);
        r.subtitulo('Un error al teclear: "vecs" no existe. Sale subrayado al momento', 4500);
        await r.esperar(2500);
        await r.mover('.squiggly-error');
        await r.page.mouse.move(r.pos.x + 2, r.pos.y);   // (a small move: the hover of the mistake opens)
        await r.esperar(3000);
        r.subtitulo('Con Ctrl+. propone el arreglo', 3500);
        await r.clic('.squiggly-error');
        await r.tecla('Control+.', 1800);
        await r.tecla('Enter', 1500);
        // completion with its parameters
        await r.tecla('End');
        await r.tecla('Enter');
        r.subtitulo('Al escribir propone las órdenes de Dash, con sus parámetros', 5000);
        await r.escribir('mui_set_t', 160);
        await r.esperar(2500);
        await r.tecla('Enter', 800);
        r.subtitulo('…y deja un hueco para cada uno', 4000);
        await r.escribir('v.saludo', 110);
        await r.tecla('Escape', 300);                  // (the list of v's fields, open after the dot: closed)
        await r.tecla('Tab', 400);
        await r.escribir('"Otra vez"', 110);
        await r.tecla('Escape', 300);
        await r.tecla('End', 1500);
        // the end of a block, by itself
        await r.tecla('Enter');
        r.subtitulo('Al pulsar Intro tras un if, el end se pone solo', 4500);
        await r.escribir('if veces > 5', 110);
        await r.tecla('Enter', 600);
        await r.escribir('Print "Muchas veces"', 90);
        await r.esperar(2500);
        // help on hover
        await r.mover(r.palabra('mui_wait_event'));
        await r.decir('Con el ratón encima, la ayuda de cada orden', 4000);
        // to the definition: the window of the .dashui
        r.subtitulo('Ctrl y clic lleva a su definición: aquí, la ventana del .dashui', 5000);
        await r.clic(r.palabra('Hola_create'), { modifiers: ['Control'] });
        await r.esperar(4500);
        await r.orden('Go Back', 1500);
        // rename
        await r.clic(r.palabra('veces'), { double: true });
        r.subtitulo('F2 cambia un nombre en todos sus usos', 5000);
        await r.tecla('F2', 900);
        await r.escribir('pulsaciones', 110);
        await r.tecla('Enter', 3500);
        await r.decir('En el capítulo siguiente: la ventana, en el editor visual', 3000);
    },
};
