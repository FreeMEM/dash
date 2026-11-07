// @ts-check
// "Dash: Nuevo proyecto" (docs/IDE_LOOP.md, task 21): a folder with a program that opens a MUI window made
// with the visual editor, ready to compile, run, see on the Amiga and debug. Without VS Code (tests):
// projectFiles(name) gives the files.
const path = require('path');
const fs = require('fs');

/** The name of the program as a file name and a window name: letters, digits and _ (accents off: Ñandú, Nandu) */
function cleanName(name) {
    const n = String(name || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim()
        .replace(/[^A-Za-z0-9_]+/g, '_').replace(/^_+|_+$/g, '');
    return /^[A-Za-z]/.test(n) ? n : 'Programa' + (n ? '_' + n : '');
}

/**
 * The files of a new project: { relative path: text }
 * @param {string} name
 * @param {string} [dashPath] the Dash compiler's folder, for .vscode/settings.json (when it is not the workspace)
 * @param {string} [kind] 'mui' (a program with a MUI window, the default) or 'game'
 */
function projectFiles(name, dashPath, kind) {
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
        `# ${n}: una ventana MUI (ventana.dashui) y lo que hacen sus botones.`,
        '# ▶ lo ejecuta en el Amiga emulado y F5 lo depura.',
        '# ventana.dashui se abre en el editor visual: "Ver en Amiga" la enseña.',
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
    const files = kind === 'game' ? gameFiles(n) : {
        [`${n}.dash`]: program,
        'ventana.dashui': JSON.stringify(dashui, null, 2) + '\n',
    };
    Object.assign(files, {
        '.vscode/launch.json': JSON.stringify(launch, null, 2) + '\n',
        '.gitignore': 'bin/\nbuild/\n',
    });
    if (dashPath) files['.vscode/settings.json'] = JSON.stringify({ 'dash.path': dashPath }, null, 2) + '\n';
    return { name: n, files };
}

// --- a game: a player (a hardware sprite), a tileset (a BOB), a level (a tile map with collisions and the player's
// start) and a program that moves the player with the joystick or the arrow keys (V6 of docs/VSCODE_JUEGOS_LOOP.md)

/** A picture from rows of characters: each one the colour of `colours` at its place (others: 0) */
function art(rows, colours) {
    const out = new Uint8Array(rows.length * rows[0].length);
    rows.forEach((r, y) => { for (let x = 0; x < r.length; x++) out[y * r.length + x] = Math.max(0, colours.indexOf(r[x])); });
    return out;
}

const PLAYER = [   // two frames of 16 x 16: . transparent, w white, o orange, b blue
    ['.....oooooo.....', '....oooooooo....', '....owwowwoo....', '....owwowwoo....', '.....oooooo.....', '......oooo......',
     '....bbbbbbbb....', '...bbbbbbbbbb...', '...bbwbbbbwbb...', '...oobbbbbboo...', '....bbbbbbbb....', '....bbb..bbb....',
     '....bbb..bbb....', '...bbb....bbb...', '...ooo....ooo...', '................'],
    ['.....oooooo.....', '....oooooooo....', '....owwowwoo....', '....owwowwoo....', '.....oooooo.....', '......oooo......',
     '....bbbbbbbb....', '...bbbbbbbbbb...', '...bbwbbbbwbb...', '...oobbbbbboo...', '....bbbbbbbb....', '.....bbbbbb.....',
     '.....bb..bb.....', '....bbb..bb.....', '....ooo..ooo....', '................'],
];
const TILES = [    // 1 earth, 2 grass on earth, 3 brick: . sky (0), e d earth, g h grass, r s brick
    ['eeeeeeeeeeeeeeee', 'eedeeeeeeedeeeee', 'eeeeeeedeeeeeeee', 'eeeeeeeeeeeeeede', 'edeeeeeeeeeeeeee', 'eeeeeeeeedeeeeee',
     'eeeedeeeeeeeeeee', 'eeeeeeeeeeeeedee', 'eeeeeeeeeeeeeeee', 'eedeeeeedeeeeeee', 'eeeeeeeeeeeeeeee', 'eeeeeedeeeeeedee',
     'eeeeeeeeeeeeeeee', 'edeeeeeeeeedeeee', 'eeeeeedeeeeeeeee', 'eeeeeeeeeeeeeeee'],
    ['gggggggggggggggg', 'ghggggghgggggghg', 'hhghhhhhhghhhhgh', 'hhhhhhhhhhhhhhhh', 'eeheeeeeeeeheeee', 'eeeeeeeeeeeeeeee',
     'eedeeeeeeedeeeee', 'eeeeeeedeeeeeeee', 'eeeeeeeeeeeeeede', 'edeeeeeeeeeeeeee', 'eeeeeeeeedeeeeee', 'eeeedeeeeeeeeeee',
     'eeeeeeeeeeeeedee', 'eeeeeeeeeeeeeeee', 'eedeeeeedeeeeeee', 'eeeeeeeeeeeeeeee'],
    ['rrrrrrrsrrrrrrrs', 'rrrrrrrsrrrrrrrs', 'rrrrrrrsrrrrrrrs', 'ssssssssssssssss', 'rrrsrrrrrrrsrrrr', 'rrrsrrrrrrrsrrrr',
     'rrrsrrrrrrrsrrrr', 'ssssssssssssssss', '................', '................', '................', '................',
     '................', '................', '................', '................'],
];

function gameFiles(n) {
    const IFF = require('./media/iff.js');
    const player = IFF.newSprite('sprite', 16, 16, 0);
    player.frames = PLAYER.map((f) => art(f, '.wob'));
    player.palette.splice(0, 4, 0x000000, 0xFFFFFF, 0xFF8800, 0x0055AA);
    player.speed = 8;
    const tiles = IFF.newSprite('bob', 16, 16, 3);
    tiles.frames = TILES.map((f) => art(f, '.edghrs'));
    tiles.palette.splice(0, 7, 0x6688CC, 0x885533, 0x664422, 0x55AA33, 0x338822, 0xAA4433, 0x662211);
    const map = IFF.newMap(20, 16, 16, 'tiles.iff');
    const ground = map.layers[0].cells;
    const hit = new Uint16Array(20 * 16);
    map.layers.push({ name: 'choques', type: 1, visible: true, cells: hit });
    const put = (x, y, tile, kind) => { ground[y * 20 + x] = tile; hit[y * 20 + x] = kind; };
    for (let x = 0; x < 20; x++) { put(x, 14, 2, 1); put(x, 15, 1, 1); }
    for (let x = 4; x < 9; x++) put(x, 10, 3, 2);           // platforms: crossed from below
    for (let x = 11; x < 16; x++) put(x, 7, 3, 2);
    for (let y = 12; y < 14; y++) put(17, y, 1, 1);          // a step
    map.objects.push({ x: 32, y: 13 * 16, kind: 'jugador', name: '', sprite: 'jugador.iff' });
    const program = [
        `# ${n}: un juego. El jugador (jugador.iff, un sprite de hardware) corre y salta por el nivel (nivel.fmap,`,
        '# un mapa de tiles con tiles.iff). Los tres se abren en sus editores; "Ver en Amiga" los enseña.',
        '# Joystick o flechas para moverse, disparo, espacio o arriba para saltar, Esc para salir.',
        '# La capa 1 del mapa es de choques: 1 sólido, 2 plataforma (se cruza desde abajo).',
        '',
        'const TILE = 16',
        'const ESC = 0x45',
        'const ESPACIO = 0x40',
        'const ARRIBA = 0x4C',
        'const DERECHA = 0x4E',
        'const IZQUIERDA = 0x4F',
        '',
        '# Lo que hay en el píxel x, y del nivel (la capa de choques); fuera, sólido a los lados y nada abajo',
        'func choque(x: Int, y: Int) -> Int',
        '    if x < 0 or x >= tilemap_width(0) * TILE',
        '        return 1',
        '    end',
        '    return tilemap_get(0, 1, x / TILE, y / TILE)',
        'end',
        '',
        'Main',
        `    if not screen_open_mode(0x21000, 320, 256, 3, "${n}")`,
        '        Print "No se puede abrir la pantalla"',
        '        return',
        '    end',
        '    if not tilemap_load(0, "nivel.fmap") or not bob_load(1, "tiles.iff") or not sprite_load(0, "jugador.iff")',
        '        Print "No se pueden cargar nivel.fmap, tiles.iff y jugador.iff: tienen que estar junto al programa"',
        '        screen_close()',
        '        return',
        '    end',
        '    bob_load_colors("tiles.iff", 0)',
        '    sprite_load_colors(0, "jugador.iff")',
        '    tilemap_draw(0, 0, 1, 0, 0, 20, 16, 0, 0)',
        '    # donde empieza: el objeto "jugador" del mapa',
        '    x0 = 32',
        '    y0 = 13 * TILE',
        '    o = tilemap_object_find(0, "jugador", 0)',
        '    if o >= 0',
        '        x0 = tilemap_object_x(0, o)',
        '        y0 = tilemap_object_y(0, o)',
        '    end',
        '    x = x0',
        '    y = y0',
        '    vy = 0',
        '    en_suelo = false',
        '    cuenta = 0',
        '    sprite_show(0)',
        '    while not key_down(ESC)',
        '        dx = 0',
        '        if joy_left(1) or key_down(IZQUIERDA)',
        '            dx = -2',
        '        elif joy_right(1) or key_down(DERECHA)',
        '            dx = 2',
        '        end',
        '        # de lado, solo si no hay nada sólido delante (arriba y abajo del jugador)',
        '        if dx != 0',
        '            lado = x + dx',
        '            if dx > 0',
        '                lado = x + 15 + dx',
        '            end',
        '            if choque(lado, y) != 1 and choque(lado, y + 15) != 1',
        '                x = x + dx',
        '            end',
        '            sprite_frame(0, (cuenta / 8) % 2)',
        '        end',
        '        if en_suelo and (joy_fire(1) or key_down(ESPACIO) or key_down(ARRIBA))',
        '            vy = -9',
        '        end',
        '        vy = vy + 1',
        '        if vy > 6',
        '            vy = 6',
        '        end',
        '        # arriba y abajo de píxel en píxel: cae hasta un suelo o una plataforma; sube hasta un techo sólido',
        '        en_suelo = false',
        '        paso = 0',
        '        while paso < vy',
        '            pie = y + TILE',
        '            if pie % TILE == 0 and (choque(x + 3, pie) != 0 or choque(x + 12, pie) != 0)',
        '                en_suelo = true',
        '                vy = 0',
        '                break',
        '            end',
        '            y = y + 1',
        '            paso = paso + 1',
        '        end',
        '        paso = 0',
        '        while paso < -vy',
        '            if choque(x + 3, y - 1) == 1 or choque(x + 12, y - 1) == 1',
        '                vy = 0',
        '                break',
        '            end',
        '            y = y - 1',
        '            paso = paso + 1',
        '        end',
        '        if y > 256',
        '            x = x0',
        '            y = y0',
        '            vy = 0',
        '        end',
        '        sprite_pos(0, x, y)',
        '        wait_vblank()',
        '        cuenta = cuenta + 1',
        '    end',
        '    sprite_hide(0)',
        '    screen_close()',
        'end',
        '',
    ].join('\n');
    return { [`${n}.dash`]: program, 'jugador.iff': IFF.writeIlbm(player), 'tiles.iff': IFF.writeIlbm(tiles), 'nivel.fmap': IFF.writeFmap(map) };
}

/** Write them in folder (which must not have them already); the program's path */
function writeProject(folder, name, dashPath, kind) {
    const { name: n, files } = projectFiles(name, dashPath, kind);
    for (const rel of Object.keys(files)) {
        if (fs.existsSync(path.join(folder, rel))) throw new Error(`ya existe ${rel} en ${folder}`);
    }
    for (const [rel, text] of Object.entries(files)) {   // (text, or the bytes of a picture or a map)
        fs.mkdirSync(path.dirname(path.join(folder, rel)), { recursive: true });
        fs.writeFileSync(path.join(folder, rel), text);
    }
    return path.join(folder, `${n}.dash`);
}

module.exports = { projectFiles, writeProject, cleanName };
