// The tile map editor (V4): its model (media/mapModel.js) as Forja's, and the webview in a headless Chromium
// (test/map.html), with real clicks and keys and the tileset served as the extension would.
const fs = require('fs');
const path = require('path');

async function mapTests(check, assert) {
    const I = require('../media/iff.js');
    const D = require('../media/mapModel.js');
    const fixture = (n) => new Uint8Array(fs.readFileSync(path.join(__dirname, 'fixtures', n)));

    await check('map model: cells, line, box and fill as Forja', () => {
        const m = I.newMap(6, 4, 16, '');
        assert(D.set(m, 0, 1, 1, 3) && !D.set(m, 0, 1, 1, 3) && !D.set(m, 0, 9, 1, 3));
        assert.strictEqual(D.get(m, 0, 1, 1), 3);
        assert.strictEqual(D.line(m, 0, 0, 0, 5, 0, 2), 6);
        assert.strictEqual(D.box(m, 0, 4, 3, 2, 2, 7), 6);
        assert.strictEqual(D.fill(m, 0, 0, 3, 9), 5);                          // the zeros joined to 0, 3
        assert.strictEqual(D.fill(m, 0, 0, 3, 9), 0);
        assert.strictEqual(D.value(m, 0, 5, I.MIRROR_H, 1), 5 + I.MIRROR_H);
        assert.strictEqual(D.value(m, 0, 0, I.MIRROR_H, 1), 0);
    });
    await check('map model: layers (8 at most), collisions, size and tile side', () => {
        const m = I.newMap(4, 3, 16, '');
        m.layers[0].cells[5] = 2;
        let r = D.addLayer(m, 0);
        assert.deepStrictEqual([r.ok, r.layer, m.layers[1].name], [true, 1, 'capa 2']);
        for (let i = 0; i < 6; i++) D.addLayer(m, 0);
        assert.match(D.addLayer(m, 0).message, /8 capas/);
        assert.deepStrictEqual(D.moveLayer(m, 0, 1), { ok: true, layer: 1 });
        assert.strictEqual(m.layers[1].cells[5], 2);
        assert.deepStrictEqual(D.moveLayer(m, 7, 1), {});
        D.toggleType(m, 1);
        assert(D.isCollisions(m, 1));
        assert.strictEqual(D.value(m, 1, 5, 0, 3), 3);
        D.removeLayer(m, 0);                                                    // the original stays (at 1, now 0)
        while (m.layers.length > 1) D.removeLayer(m, m.layers.length - 1);
        assert.match(D.removeLayer(m, 0).message, /única capa/);
        assert(D.renameLayer(m, 0, 'suelo').ok && m.layers[0].name === 'suelo');
        assert(D.resize(m, 2, 5).ok);
        assert.deepStrictEqual([m.width, m.height, m.layers[0].cells.length, m.layers[0].cells[1 * 2 + 1]], [2, 5, 10, 2]);
        assert.deepStrictEqual(D.resize(m, 2000, 5), {});
        m.objects.push({ x: 32, y: 16, kind: 'moneda', name: '', sprite: '' });
        assert(D.setTileSize(m, 8).ok);
        assert.deepStrictEqual([m.tile, m.objects[0].x, m.objects[0].y], [8, 16, 8]);
    });
    await check('map model: objects (at a cell, the one on top first, moved a cell at a time)', () => {
        const m = I.newMap(10, 10, 16, '');
        assert.deepStrictEqual(D.addObject(m, 2, 3, 'jugador'), { ok: true, object: 0 });
        D.addObject(m, 2, 3, 'moneda');
        assert.deepStrictEqual(m.objects[0], { x: 32, y: 48, kind: 'jugador', name: '', sprite: '' });
        assert.strictEqual(D.objectAt(m, 40, 50), 1);
        assert.strictEqual(D.objectAt(m, 31, 50), -1);
        assert(D.moveObject(m, 1, 20, -4) && m.objects[1].x === 144 && m.objects[1].y === 0);
        assert(D.setObject(m, 0, { name: 'heroe', sprite: 'p.iff' }).ok && !D.setObject(m, 0, { name: 'heroe' }).ok);
        assert.deepStrictEqual(D.removeObject(m, 1), { ok: true, object: -1 });
        for (let i = 0; i < 255; i++) D.addObject(m, 0, 0, 'otro');
        assert.match(D.addObject(m, 0, 0, 'otro').message, /256 objetos/);
    });
    await check('map model: the copied code is Forja\'s', () => {
        const m = I.readFmap(fixture('mapa.fmap'));
        assert.strictEqual(D.code(m, 'nivel.fmap'), '# nivel.fmap: mapa de 3 x 2 tiles de 16, 2 capas\n' +
            'if not tilemap_load(0, "nivel.fmap")\n    Print "No se puede cargar nivel.fmap"\nend\n' +
            'if not bob_load(1, "tiles.iff")\n    Print "No se puede cargar tiles.iff"\nend\n' +
            '# los colores del tileset, en la paleta de la pantalla\nbob_load_colors("tiles.iff", 0)\n' +
            '# pintar la pantalla (aquí, 320 x 256 de tiles de 16): la capa 0 y las demás encima\n' +
            'tilemap_draw(0, 0, 1, 0, 0, 20, 16, 0, 0)\n' +
            '# la capa 1 es de choques: no se pinta; tilemap_get(0, 1, x, y) dice qué hay en la celda x, y (1 sólido, 2 plataforma, 3 escalera, 4 daño)\n' +
            '# 2 objetos: tilemap_object_find busca los de una clase; x e y en píxeles del mapa\n' +
            'o = tilemap_object_find(0, "jugador", 0)\nwhile o >= 0\n    # jugador: tilemap_object_x(0, o), tilemap_object_y(0, o)\n' +
            '    o = tilemap_object_find(0, "jugador", o + 1)\nend\n' +
            'o = tilemap_object_find(0, "moneda", 0)\nwhile o >= 0\n    # moneda: tilemap_object_x(0, o), tilemap_object_y(0, o)\n' +
            '    o = tilemap_object_find(0, "moneda", o + 1)\nend\n');
    });

    // --- the webview ---------------------------------------------------------------------------------------------
    const { findChromium, openPage } = require('./webview.js');
    const chromium = findChromium();
    if (!chromium) { console.log('SKIP map webview: no Chromium (set $CHROMIUM)'); return; }
    // a tileset of 4 tiles of 16: tile n is filled with colour n (and its top left pixel with colour 3)
    const ts = I.newSprite('bob', 16, 16, 2);
    ts.frames = [1, 2, 3, 1].map((c) => { const f = new Uint8Array(256).fill(c); f[0] = 3; return f; });
    const tilesetBytes = Array.from(I.writeIlbm(ts));
    const page = await openPage(chromium, 'file://' + path.join(__dirname, 'map.html'));
    const E = (expr) => page.eval(`(() => { const E = window.DashMapEditor; return ${expr}; })()`);
    const lastEdit = async () => I.readFmap(new Uint8Array(await page.eval('(window.__posted || []).filter((m) => m.type === "edit").pop().bytes')));
    const settle = () => page.eval('new Promise((r) => setTimeout(r, 60))');
    // what the extension does: files next to the map, and the file dialog
    const serve = async (picked) => {
        await page.eval(`(() => { for (const m of (window.__posted || [])) {
            if (m.served) continue;
            if (m.type === 'readFile') { m.served = true; window.postMessage({ type: 'file', id: m.id, path: m.path,
                bytes: m.path === 'tiles.iff' ? ${JSON.stringify(tilesetBytes)} : null }, '*'); }
            if (m.type === 'pickFile') { m.served = true; window.postMessage({ type: 'picked', id: m.id, path: ${JSON.stringify(picked || null)} }, '*'); }
        } })()`);
        await settle();
    };
    const loadBytes = async (bytes, keep) => {
        await page.eval(`window.postMessage({ type: 'load', name: 'nivel.fmap', keep: ${!!keep}, bytes: ${JSON.stringify(Array.from(bytes))} }, '*')`);
        await settle();
        await serve();
    };
    const cellAt = (x, y) => page.eval(`(() => { const c = document.getElementById('view'), r = c.getBoundingClientRect(), E = window.DashMapEditor;
        const z = E.zoom, t = E.m.tile; return [r.left + ((${x} + 0.5) * t - E.ox) * z, r.top + ((${y} + 0.5) * t - E.oy) * z]; })()`);
    const mouse = async (x, y, opts = {}) => {
        const mods = (opts.alt ? 1 : 0) | (opts.ctrl ? 2 : 0) | (opts.shift ? 8 : 0);
        const button = opts.button || 'left';
        const [ax, ay] = await cellAt(x, y);
        await page.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: ax, y: ay, button, buttons: 1, clickCount: 1, modifiers: mods });
        let [ex, ey] = [ax, ay];
        if (opts.to) {
            [ex, ey] = await cellAt(opts.to[0], opts.to[1]);
            await page.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: (ax + ex) / 2, y: (ay + ey) / 2, button, buttons: 1, modifiers: mods });
            await page.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: ex, y: ey, button, buttons: 1, modifiers: mods });
        }
        await page.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: ex, y: ey, button, buttons: 0, clickCount: 1, modifiers: mods });
        await settle();
    };
    const press = async (key, mods) => { await page.eval('document.getElementById("view").focus()'); await page.key(key, mods); await settle(); };
    try {
        await page.eval('new Promise((r) => { const t = () => (window.__posted || []).some((m) => m.type === "ready") ? r() : setTimeout(t, 20); t(); })');
        await loadBytes(fixture('mapa.fmap'));
        await check('map webview: opens a map of Dash and reads its tileset next to it', async () => {
            assert.deepStrictEqual(await E('[E.m.width, E.m.height, E.m.layers.length, E.m.objects.length]'), [3, 2, 2, 2]);
            assert.strictEqual(await E('E.tileset && E.tileset.frames.length'), 4, await E('E.tilesetError') + JSON.stringify(await page.eval('(window.__posted || []).map((m) => m.type + ":" + (m.path || "") + ":" + !!m.served)')));
            assert.strictEqual(await page.eval('document.querySelectorAll("#page .tile").length'), 4);
            assert.match(await page.eval('document.getElementById("status").textContent'), /3 x 2 tiles de 16 · capa 0: fondo/);
        });
        await check('map webview: pencil with the chosen tile and its mirror; Alt erases; Ctrl picks', async () => {
            await page.eval('document.querySelectorAll("#page .tile")[2].click()');                // tile 3
            await press('h');
            await mouse(0, 1, { to: [2, 1] });
            let m = await lastEdit();
            assert.deepStrictEqual([...m.layers[0].cells.slice(3)], [3 + I.MIRROR_H, 3 + I.MIRROR_H, 3 + I.MIRROR_H]);
            await mouse(1, 1, { alt: true });
            m = await lastEdit();
            assert.strictEqual(m.layers[0].cells[4], 0);
            await press('h');
            await mouse(2, 0, { ctrl: true });                                                   // 16387: tile 3, mirrored
            assert.deepStrictEqual(await E('[E.tile, E.mirror]'), [3, I.MIRROR_H]);
            await press('.');
            assert.strictEqual(await E('E.tile'), 4);
            await press(',');
            await press(',');
            assert.strictEqual(await E('E.tile'), 2);
        });
        await check('map webview: box and fill (B, F); E erases', async () => {
            await press('b');
            await mouse(0, 0, { to: [1, 1] });
            let m = await lastEdit();
            assert.deepStrictEqual([m.layers[0].cells[0], m.layers[0].cells[1], m.layers[0].cells[3], m.layers[0].cells[4]],
                Array(4).fill(2 + I.MIRROR_H));
            await press('h');
            await press('f');
            await mouse(0, 0);
            m = await lastEdit();
            assert.strictEqual(m.layers[0].cells[0], 2);
            await press('e');
            await mouse(2, 1);
            assert.strictEqual((await lastEdit()).layers[0].cells[5], 0);
            await press('p');
        });
        await check('map webview: layers (new, collisions, hide, move) on the Capas page', async () => {
            await page.eval('document.querySelector("#pages [data-page=layers]").click()');
            await page.eval('[...document.querySelectorAll("#page button")].find((b) => b.textContent === "Nueva").click()');
            let m = await lastEdit();
            assert.deepStrictEqual([m.layers.length, m.layers[1].name, await E('E.layer')], [3, 'capa 3', 1]);
            await page.eval('[...document.querySelectorAll("#page button")].find((b) => /choques/.test(b.textContent)).click()');
            assert.strictEqual((await lastEdit()).layers[1].type, 1);
            await page.eval('document.querySelector("#pages [data-page=tiles]").click()');
            assert.strictEqual(await page.eval('document.querySelectorAll("#page .collision").length'), 4);
            await page.eval('document.querySelectorAll("#page .collision")[3].click()');          // daño
            await mouse(1, 0);
            assert.strictEqual((await lastEdit()).layers[1].cells[1], 4);
            await page.eval('document.querySelector("#pages [data-page=layers]").click()');
            await page.eval('document.querySelectorAll("#page .list-row input[type=checkbox]")[0].click()');
            assert.strictEqual((await lastEdit()).layers[0].visible, false);
            await page.eval('[...document.querySelectorAll("#page button")].find((b) => b.textContent === "Atrás").click()');
            m = await lastEdit();
            assert.deepStrictEqual([m.layers[0].type, await E('E.layer')], [1, 0]);
        });
        await check('map webview: objects (put, choose, drag, name, sprite, Delete)', async () => {
            await page.eval('document.querySelector("#pages [data-page=objects]").click()');
            await page.eval('[...document.querySelectorAll("#page button")].find((b) => b.textContent === "puerta").click()');
            await mouse(2, 1);
            let m = await lastEdit();
            assert.deepStrictEqual(m.objects[2], { x: 32, y: 16, kind: 'puerta', name: '', sprite: '' });
            assert.strictEqual(await E('E.object'), 2);
            await mouse(2, 1, { to: [0, 1] });
            m = await lastEdit();
            assert.deepStrictEqual([m.objects[2].x, m.objects[2].y], [0, 16]);
            await page.eval(`(() => { const i = document.querySelector('#page input[aria-label="Nombre del objeto"]'); i.value = 'salida'; i.dispatchEvent(new Event('change')); })()`);
            assert.strictEqual((await lastEdit()).objects[2].name, 'salida');
            await page.eval('[...document.querySelectorAll("#page button")].find((b) => b.textContent === "Sprite...").click()');
            await serve('tiles.iff');
            assert.strictEqual((await lastEdit()).objects[2].sprite, 'tiles.iff');
            await press('Delete');
            m = await lastEdit();
            assert.strictEqual(m.objects.length, 2);
        });
        await check('map webview: size, view keys, zoom and grid; C copies the code', async () => {
            await page.eval('document.querySelector("#pages [data-page=map]").click()');
            await page.eval(`(() => { const i = document.querySelector('#page input[aria-label=Ancho]'); i.value = 80; i.dispatchEvent(new Event('change')); })()`);
            await page.eval(`(() => { const i = document.querySelector('#page input[aria-label=Alto]'); i.value = 60; i.dispatchEvent(new Event('change')); })()`);
            const m = await lastEdit();
            assert.deepStrictEqual([m.width, m.height, m.layers[1].cells.length], [80, 60, 4800]);
            await press('ArrowRight');
            assert.strictEqual(await E('E.ox'), 16);
            await press('ArrowDown', { shift: true });
            assert(await E('E.oy') > 16);
            const z = await E('E.zoom');
            await press('+');
            assert.strictEqual(await E('E.zoom'), z + 1);
            await press('g');
            assert.strictEqual(await E('E.grid'), false);
            await press('c');
            const clip = await page.eval('(window.__posted || []).filter((m) => m.type === "clipboard").pop()');
            assert.match(clip.text, /^# nivel.fmap: mapa de 80 x 60 tiles de 16, 3 capas/);
        });
        await check('map webview: undo reloads and keeps the layer; the tileset is chosen with the dialog', async () => {
            await loadBytes(fixture('mapa.fmap'), true);
            assert.deepStrictEqual(await E('[E.m.width, E.layer]'), [3, 0]);
            const noTileset = I.readFmap(fixture('mapa.fmap'));
            noTileset.tileset = '';
            await loadBytes(I.writeFmap(noTileset));
            assert.strictEqual(await E('E.tileset'), null);
            await page.eval('document.querySelector("#pages [data-page=tiles]").click()');
            await page.eval('[...document.querySelectorAll("#page button")].find((b) => b.textContent === "Elegir...").click()');
            await serve('tiles.iff');
            await serve();
            assert.strictEqual((await lastEdit()).tileset, 'tiles.iff');
            assert.strictEqual(await E('E.tileset && E.tileset.frames.length'), 4);
            await loadBytes(fixture('bob_forja.iff'));
            assert.match(await page.eval('document.getElementById("error").textContent'), /FMAP/);
        });
    } finally {
        page.close();
    }
}

module.exports = { mapTests };
