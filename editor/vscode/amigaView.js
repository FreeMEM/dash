// @ts-check
// "Ver en Amiga" for a sprite, a BOB or a tile map (V5): a small Dash program loads the file as a game would
// (bob_load, sprite_load, tilemap_load) on a PAL low resolution screen, and tools/emu_run.py runs it in FS-UAE and
// takes a picture of the screen. What the editor has, saved or not, is what goes to the Amiga.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFile } = require('child_process');

const q = (t) => String(t).replace(/["\\]/g, '');            // (a name inside a Dash string)

/** The program that shows a sprite or BOB s (DashIFF's), read from file: every frame, and one animated */
function spriteProgram(s, file) {
    const f = q(file), n = s.frames.length;
    const lines = [`# Ver en Amiga: ${f}`, 'Main'];
    if (s.hardware) {
        const attached = s.planes === 4;
        lines.push(
            `    if not screen_open_mode(0x21000, 320, 256, 2, "${f}")`, '        Print "No se puede abrir la pantalla"', '        return', '    end',
            `    gfx_rgb(0, ${(s.palette[0] >> 16) & 255}, ${(s.palette[0] >> 8) & 255}, ${s.palette[0] & 255})`,
            `    if not ${attached ? 'sprite_load_attached' : 'sprite_load'}(0, "${f}")`,
            `        Print "No se puede cargar ${f}"`, '        screen_close()', '        return', '    end',
            `    sprite_load_colors(0, "${f}")`,
            `    Print "cargado: ${attached ? 'sprite acoplado' : 'sprite'} de ${n} fotogramas"`,
            '    sprite_pos(0, 152, 120)', '    sprite_show(0)',
            '    cuenta = 0', '    while cuenta < 500',
            `        sprite_frame(0, (cuenta / ${s.speed}) % ${n})`, '        wait_vblank()', '        cuenta = cuenta + 1', '    end',
            '    sprite_hide(0)', '    screen_close()', 'end', '');
        return lines.join('\n');
    }
    const gap = 8, w = s.width, h = s.height;
    lines.push(
        `    if not screen_open_mode(0x21000, 320, 256, ${Math.max(1, Math.min(8, s.planes))}, "${f}")`,
        '        Print "No se puede abrir la pantalla"', '        return', '    end',
        `    if not bob_load(0, "${f}")`, `        Print "No se puede cargar ${f}"`, '        screen_close()', '        return', '    end',
        `    bob_load_colors("${f}", 0)`,
        `    Print "cargado: BOB de ${w} x ${h}, ${n} fotogramas"`,
        // every frame, one after the other from the top left corner, in rows
        `    x = 16`, `    y = 20`, '    f = 0', `    while f < ${n}`,
        `        if x + ${w} > 304`, '            x = 16', `            y = y + ${h + gap}`, '        end',
        '        bob_paste(0, f, x, y)', `        x = x + ${w + gap}`, '        f = f + 1', '    end',
        // and one animated below them
        `    bob_pos(0, ${Math.max(0, 160 - Math.floor(w / 2))}, y + ${h + 24})`,
        '    cuenta = 0', '    while cuenta < 500',
        `        bob_frame(0, (cuenta / ${s.speed}) % ${n})`, '        bob_draw(0)', '        wait_vblank()', '        cuenta = cuenta + 1', '    end',
        '    screen_close()', 'end', '');
    return lines.join('\n');
}

/**
 * The program that shows a map m (DashIFF's) read from file, with its tileset (tileset: the file's name on the
 * Amiga, or '' if none), from cell tx, ty: the layers that are seen, the first one with tilemap_draw and the rest
 * with tilemap_draw_masked, as the copied code does; collision layers are not drawn
 */
function mapProgram(m, file, tileset, tx, ty, depth) {
    const f = q(file), t = q(tileset), ts = m.tile;
    const cols = Math.floor(320 / ts), rows = Math.floor((256 - 12) / ts);
    const lines = [`# Ver en Amiga: ${f}`, 'Main',
        `    if not screen_open_mode(0x21000, 320, 256, ${Math.max(1, Math.min(8, depth || 4))}, "${f}")`,
        '        Print "No se puede abrir la pantalla"', '        return', '    end',
        `    if not tilemap_load(0, "${f}")`, `        Print "No se puede cargar ${f}"`, '        screen_close()', '        return', '    end',
        `    Print "cargado: mapa de #{tilemap_width(0)} x #{tilemap_height(0)}, #{tilemap_layers(0)} capas"`];
    if (t) {
        lines.push(`    if not bob_load(1, "${t}")`, `        Print "No se puede cargar ${t}"`, '        screen_close()', '        return', '    end',
            `    bob_load_colors("${t}", 0)`);
        let first = true;
        m.layers.forEach((l, i) => {
            if (!l.visible || l.type === 1) return;
            lines.push(`    ${first ? 'tilemap_draw' : 'tilemap_draw_masked'}(0, ${i}, 1, ${tx | 0}, ${ty | 0}, ${cols}, ${rows}, 0, 12)`);
            first = false;
        });
    } else lines.push('    Print "sin tileset: no hay con qué pintarlo"');
    lines.push('    time_delay(500)', '    screen_close()', 'end', '');
    return lines.join('\n');
}

/**
 * Runs program with files ({name, bytes}) next to it on the emulated disk; resolves with {png: Buffer, output},
 * or rejects with an Error saying what failed. shotAt: seconds after boot for the picture.
 */
function runView({ dashDir, program, files, env, machine, shotAt }) {
    return new Promise((resolve, reject) => {
        let dir;
        try {
            dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash-ver-'));
            for (const f of files) fs.writeFileSync(path.join(dir, f.name), f.bytes);
            fs.writeFileSync(path.join(dir, 'ver.dash'), program);
        } catch (e) { reject(e); return; }
        const png = path.join(dir, 'shot.png');
        const args = [path.join(dashDir, 'tools', 'emu_run.py'), '--dash2', '--timeout', '120',
            '--screenshot', String(shotAt || 7), png];
        if (machine) args.push('--machine', machine);
        for (const f of files) args.push('--file', path.join(dir, f.name));
        args.push(path.join(dir, 'ver.dash'));
        execFile('python3', args, { cwd: dashDir, env: Object.assign({}, process.env, env || {}), timeout: 240000,
            maxBuffer: 4 * 1024 * 1024 }, (err, stdout, stderr) => {
            const output = (stdout || '') + (stderr || '');
            try {
                const said = /No se puede[^\n]*/.exec(output);
                if (said) reject(new Error(said[0]));
                else if (fs.existsSync(png)) resolve({ png: fs.readFileSync(png), output });
                else reject(new Error(output.trim().split('\n').slice(-3).join(' ') || (err ? err.message : 'sin captura')));
            } finally {
                fs.rmSync(dir, { recursive: true, force: true });
            }
        });
    });
}

module.exports = { spriteProgram, mapProgram, runView };
