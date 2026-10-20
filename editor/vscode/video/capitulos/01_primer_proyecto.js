// Capítulo 1 del tutorial: el primer proyecto (se completa en la tarea v3 de docs/IDE_VIDEO_LOOP.md)
const fs = require('fs');
const path = require('path');

module.exports = {
    titulo: '1. Primer proyecto',
    resumen: 'Un programa de Dash abierto en VS Code',
    carpeta: 'hola',
    preparar(dir) {
        fs.writeFileSync(path.join(dir, 'hola.dash'), 'Main\n    Print "hola"\nend\n');
    },
    open: ['hola.dash'],
    async guion(r) {
        await r.decir('Este es un programa de Dash: un lenguaje para el Amiga', 3000);
        await r.clic('.monaco-editor .view-line >> nth=1');
        await r.tecla('End');
        await r.subtitulo('Escribimos otra línea', 3500);
        await r.tecla('Enter');
        await r.escribir('Print "adiós"');
        await r.esperar(1500);
    },
};
