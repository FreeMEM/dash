// Capítulo 1 del tutorial: la guía de primeros pasos y un proyecto nuevo (docs/IDE_VIDEO_LOOP.md, v3)
module.exports = {
    titulo: '1. Primer proyecto',
    resumen: 'La guía de primeros pasos y un proyecto con su ventana',
    sinCarpeta: true,
    carpeta: 'Proyectos',              // where the project is made (shown in the dialog)
    async guion(r, dir) {
        await r.decir('Dash es un lenguaje para programar el Amiga. Esta extensión lo trae a VS Code.', 4000);
        r.subtitulo('Empezamos por la guía de primeros pasos', 4500);
        await r.orden('Welcome: Open Walkthrough');
        await r.escribir('Dash', 90);
        await r.esperar(700);
        await r.tecla('Enter', 2500);
        await r.mover(r.page.getByText('Dónde está el compilador', { exact: true }));
        await r.decir('El primer paso ya está hecho: la extensión encuentra el compilador de Dash', 4000);
        await r.clic(r.page.getByText('Un proyecto nuevo', { exact: true }));
        await r.decir('Un proyecto nuevo es un programa con su ventana, listo para el emulador', 4000);
        await r.clic(r.page.getByText('Nuevo proyecto', { exact: true }).last());
        r.subtitulo('Le damos un nombre…', 3000);
        await r.esperar(800);
        await r.escribir('hola', 150);
        await r.esperar(1200);
        await r.tecla('Enter', 1500);
        r.subtitulo('…y elegimos dónde se crea su carpeta', 4000);
        await r.clic('.quick-input-widget input');
        await r.tecla('Control+a', 200);
        await r.escribir(dir + '/', 15);
        await r.esperar(1500);
        await r.clic(r.page.getByText('Crear el proyecto aquí', { exact: true }));
        await r.recargada();
        await r.decir('VS Code abre la carpeta del proyecto, con el programa', 3500);
        await r.mover('.explorer-folders-view .monaco-list-row >> text=hola.dash');
        await r.decir('hola.dash es el programa: abre la ventana y responde a sus botones', 4000);
        await r.mover('.explorer-folders-view .monaco-list-row >> text=ventana.dashui');
        await r.decir('ventana.dashui es la ventana MUI, para el editor visual', 3500);
        await r.mover('.explorer-folders-view .monaco-list-row >> text=.vscode');
        await r.decir('Y en .vscode está la configuración para depurar con F5', 3500);
        await r.mover({ x: 760, y: 420 });
        await r.decir('En el capítulo siguiente escribimos código', 3000);
    },
};
