// @ts-check
// "Dash: Nuevo proyecto" (docs/IDE_LOOP.md, task 21): a folder with a program that opens a MUI window made
// with the visual editor, ready to compile, run, see on the Amiga and debug. Without VS Code (tests):
// projectFiles(name) gives the files.
const path = require('path');
const fs = require('fs');

/** The name of the program as a file name and a window name: letters, digits and _ */
function cleanName(name) {
    const n = String(name || '').trim().replace(/[^A-Za-z0-9_]+/g, '_').replace(/^_+|_+$/g, '');
    return /^[A-Za-z]/.test(n) ? n : 'Programa' + (n ? '_' + n : '');
}

/**
 * The files of a new project: { relative path: text }
 * @param {string} name
 * @param {string} [dashPath] the Dash compiler's folder, for .vscode/settings.json (when it is not the workspace)
 */
function projectFiles(name, dashPath) {
    const n = cleanName(name);
    const window = n.charAt(0).toUpperCase() + n.slice(1);
    const dashui = {
        dashui: 1,
        windows: [{
            name: window, title: n, id: 1, menus: [{ title: 'Proyecto', items: [{ label: 'Salir', key: 'Q', event: 9 }] }],
            root: { type: 'vgroup', children: [
                { type: 'text', name: 'saludo', text: 'Hola desde Dash' },
                { type: 'hgroup', children: [
                    { type: 'button', name: 'contar', label: '_Contar', event: 1 },
                    { type: 'button', name: 'salir', label: '_Salir', event: 9 },
                ] },
            ] },
        }],
    };
    const program = [
        `# ${n}: una ventana MUI hecha con el editor visual (ventana.dashui) y su lógica.`,
        '# F5 lo depura en el Amiga emulado; "Dash: Ejecutar en emulador" lo ejecuta; en el editor de la',
        '# ventana, "Ver en Amiga" la enseña y la flecha de un evento lleva a su código.',
        '# Necesita MUI y un 68020 (A1200).',
        '',
        'import "ventana.dashui"',
        '',
        'const ID_CONTAR = 1',
        'const ID_SALIR = 9',
        '',
        'Main',
        `    if mui_app_begin("${n}", "${n.toUpperCase()}") == 0`,
        '        Print "Hace falta MUI y un 68020"',
        '    else',
        `        v = ${window}_create()`,
        '        mui_window_open(v.window)',
        '        veces = 0',
        '        while true',
        '            ev = mui_wait_event()',
        '            if ev == -1 or ev == ID_SALIR',
        '                break',
        '            end',
        '            if ev == ID_CONTAR',
        '                veces = veces + 1',
        '                mui_set_text(v.saludo, "Pulsado #{veces} veces")',
        '            end',
        '        end',
        '        mui_app_end()',
        '    end',
        'end',
        '',
    ].join('\n');
    const launch = {
        version: '0.2.0',
        configurations: [
            { type: 'dash', request: 'launch', name: 'Depurar en el Amiga', program: `\${workspaceFolder}/${n}.dash` },
            { type: 'dash', request: 'attach', name: 'Amiga real', target: 'amiga.local:2345', program: `\${workspaceFolder}/${n}.dash` },
        ],
    };
    const files = {
        [`${n}.dash`]: program,
        'ventana.dashui': JSON.stringify(dashui, null, 2) + '\n',
        '.vscode/launch.json': JSON.stringify(launch, null, 2) + '\n',
        '.gitignore': 'bin/\nbuild/\n',
    };
    if (dashPath) files['.vscode/settings.json'] = JSON.stringify({ 'dash.path': dashPath }, null, 2) + '\n';
    return { name: n, files };
}

/** Write them in folder (which must not have them already); the program's path */
function writeProject(folder, name, dashPath) {
    const { name: n, files } = projectFiles(name, dashPath);
    for (const rel of Object.keys(files)) {
        if (fs.existsSync(path.join(folder, rel))) throw new Error(`ya existe ${rel} en ${folder}`);
    }
    for (const [rel, text] of Object.entries(files)) {
        fs.mkdirSync(path.dirname(path.join(folder, rel)), { recursive: true });
        fs.writeFileSync(path.join(folder, rel), text);
    }
    return path.join(folder, `${n}.dash`);
}

module.exports = { projectFiles, writeProject, cleanName };
