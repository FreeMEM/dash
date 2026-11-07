// "Ver en Amiga" of the sprite and map editors (V5, amigaView.js): the programs compile with ./dash, and, with
// DASH_PREVIEW_EMU=1 (DASH_KICKSTART, DASH_EMU_SYS), the files the extension writes are loaded by Dash in FS-UAE
// (bob_load, sprite_load_attached, tilemap_load) and pictured.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

async function amigaViewTests(check, assert) {
    const I = require('../media/iff.js');
    const AV = require('../amigaView.js');
    const repo = path.resolve(__dirname, '..', '..', '..');
    // a BOB of 3 frames of 12 x 10 and 8 colours, an attached sprite, a map of 40 x 20 with its tileset
    const bob = I.newSprite('bob', 12, 10, 3);
    bob.frames = [1, 2, 3].map((c) => new Uint8Array(120).map((_, i) => (i % 12 < 6 ? c : c + 3)));
    const att = I.newSprite('attached', 16, 8, 0);
    att.frames.push(new Uint8Array(128).fill(15));
    const tiles = I.newSprite('bob', 16, 16, 2);
    tiles.frames = [1, 2, 3].map((c) => new Uint8Array(256).fill(c));
    const map = I.newMap(40, 20, 16, 'tiles.iff');
    for (let x = 0; x < 40; x++) map.layers[0].cells[19 * 40 + x] = 1;
    map.layers.push({ name: 'delante', type: 0, visible: true, cells: new Uint16Array(800).fill(0) });
    map.layers.push({ name: 'choques', type: 1, visible: true, cells: new Uint16Array(800) });
    map.layers[1].cells[5] = 2 | I.MIRROR_H;
    const programs = {
        bob: AV.spriteProgram(bob, 'nave.iff'),
        att: AV.spriteProgram(att, 'acoplado.iff'),
        map: AV.mapProgram(map, 'nivel.fmap', 'tiles.iff', 2, 3, 2),
        bare: AV.mapProgram(I.newMap(4, 4, 8, ''), 'vacio.fmap', '', 0, 0, 4),
    };

    await check('ver en amiga: the programs load as the copied code does', () => {
        assert.match(programs.bob, /screen_open_mode\(0x21000, 320, 256, 3, "nave.iff"\)[\s\S]*bob_load\(0, "nave.iff"\)[\s\S]*bob_paste\(0, f, x, y\)[\s\S]*bob_frame\(0, \(cuenta \/ 6\) % 3\)/);
        assert.match(programs.att, /sprite_load_attached\(0, "acoplado.iff"\)[\s\S]*sprite_load_colors[\s\S]*sprite_frame\(0, \(cuenta \/ 6\) % 2\)/);
        assert.match(programs.map, /tilemap_load\(0, "nivel.fmap"\)[\s\S]*bob_load\(1, "tiles.iff"\)[\s\S]*tilemap_draw\(0, 0, 1, 2, 3, 20, 15, 0, 12\)\n    tilemap_draw_masked\(0, 1, 1, 2, 3, 20, 15, 0, 12\)\n    time_delay/);
        assert(!/tilemap_draw[^\n]*\(0, 2,/.test(programs.map), 'the collision layer is not drawn');
        assert.match(programs.bare, /sin tileset/);
        assert.match(AV.spriteProgram(bob, 'a "b".iff'), /bob_load\(0, "a b.iff"\)/);
    });
    const dashc = path.join(repo, 'dashc', 'dashc');
    if (!fs.existsSync(dashc)) console.log('SKIP ver en amiga compile: no dashc/dashc (make -C dashc)');
    else await check('ver en amiga: the programs compile with ./dash', () => {
        const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash-ver-test-'));
        try {
            for (const [name, src] of Object.entries(programs)) {
                fs.writeFileSync(path.join(dir, name + '.dash'), src);
                execFileSync(path.join(repo, 'dash'), [path.join(dir, name + '.dash'), '-o', path.join(dir, name)], { stdio: 'pipe' });
                assert(fs.statSync(path.join(dir, name)).size > 1000, name);
            }
        } finally { fs.rmSync(dir, { recursive: true, force: true }); }
    });

    if (process.env.DASH_PREVIEW_EMU !== '1') { console.log('SKIP ver en amiga emulator: DASH_PREVIEW_EMU=1 to run'); return; }
    const run = (program, files) => AV.runView({ dashDir: repo, program, files });
    await check('ver en amiga (emulator): Dash loads the BOB the extension writes, and it is pictured', async () => {
        const r = await run(programs.bob, [{ name: 'nave.iff', bytes: I.writeIlbm(bob) }]);
        assert.match(r.output, /cargado: BOB de 12 x 10, 3 fotogramas/);
        assert.strictEqual(r.png.slice(1, 4).toString(), 'PNG');
    });
    await check('ver en amiga (emulator): an attached sprite of the extension', async () => {
        const r = await run(programs.att, [{ name: 'acoplado.iff', bytes: I.writeIlbm(att) }]);
        assert.match(r.output, /cargado: sprite acoplado de 2 fotogramas/);
    });
    await check('ver en amiga (emulator): Dash loads the map the extension writes (size and layers) with its tileset', async () => {
        const r = await run(programs.map, [{ name: 'nivel.fmap', bytes: I.writeFmap(map) }, { name: 'tiles.iff', bytes: I.writeIlbm(tiles) }]);
        assert.match(r.output, /cargado: mapa de 40 x 20, 3 capas/);
    });
    await check('ver en amiga (emulator): a file Dash cannot load says so', async () => {
        await assert.rejects(run(programs.bob, [{ name: 'nave.iff', bytes: new Uint8Array(40) }]), /No se puede cargar nave.iff/);
    });
}

module.exports = { amigaViewTests };
