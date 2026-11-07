// The sprite and BOB editor (V2): its model (media/spriteModel.js) as Forja's, the provider (spriteEditor.js) with
// a stand-in for VS Code, and the webview in a headless Chromium (test/sprite.html), with real clicks and keys.
const fs = require('fs');
const path = require('path');
const Module = require('module');

async function spriteTests(check, assert) {
    const I = require('../media/iff.js');
    const M = require('../media/spriteModel.js');
    const fixture = (n) => new Uint8Array(fs.readFileSync(path.join(__dirname, 'fixtures', n)));

    // --- the model ---------------------------------------------------------------------------------------------
    await check('sprite model: line, box and fill as Forja', () => {
        const s = I.newSprite('bob', 8, 6, 3);
        assert.deepStrictEqual(M.linePoints(s, 0, 0, 3, 1), [0, 1, 10, 11]);
        assert.strictEqual(M.boxPoints(s, 1, 1, 3, 3, false).length, 8);
        assert.strictEqual(M.boxPoints(s, 3, 3, 1, 1, true).length, 9);
        assert.strictEqual(M.boxPoints(s, -5, 4, 20, 9, true).length, 16);        // cut at the edges
        M.plot(s, 0, M.boxPoints(s, 1, 1, 4, 4, false), 2);
        assert(M.fill(s, 0, 2, 2, 5));                                          // inside the box only
        assert.strictEqual(s.frames[0].filter((v) => v === 5).length, 4);
        assert(!M.fill(s, 0, 2, 2, 5));                                         // same colour: nothing
        assert.strictEqual(M.px(s, 0, 2, 2), 5);
        assert.strictEqual(M.px(s, 0, 99, 2), 0);
    });
    await check('sprite model: frames (new, duplicate, remove, move, clear, mirror, shift, paste)', () => {
        const s = I.newSprite('bob', 3, 2, 2);
        s.frames[0].set([1, 2, 3, 0, 0, 1]);
        assert.strictEqual(M.newFrame(s, 0, true), 1);
        assert.deepStrictEqual([...s.frames[1]], [1, 2, 3, 0, 0, 1]);
        M.mirror(s, 1, true);
        assert.deepStrictEqual([...s.frames[1]], [3, 2, 1, 1, 0, 0]);
        M.mirror(s, 1, false);
        assert.deepStrictEqual([...s.frames[1]], [1, 0, 0, 3, 2, 1]);
        M.shift(s, 1, 1, 0);
        assert.deepStrictEqual([...s.frames[1]], [0, 1, 0, 1, 3, 2]);
        assert.strictEqual(M.moveFrame(s, 1, -1), 0);
        assert.deepStrictEqual([...s.frames[1]], [1, 2, 3, 0, 0, 1]);
        assert.strictEqual(M.moveFrame(s, 0, -1), -1);
        const t = M.frameText(s, 1);
        assert.strictEqual(M.pasteFrame(s, 1, t), 2);
        assert.deepStrictEqual([...s.frames[2]], [1, 2, 3, 0, 0, 1]);
        assert.strictEqual(M.pasteFrame(s, 0, 'hola'), -1);
        assert(M.clearFrame(s, 2) && !M.clearFrame(s, 2));
        assert.deepStrictEqual(M.removeFrame(s, 2), { frame: 1 });
        M.removeFrame(s, 0);
        assert.match(M.removeFrame(s, 0).message, /al menos un fotograma/);
    });
    await check('sprite model: size and kind as T in Forja (BOB -> sprite -> attached -> BOB)', () => {
        const s = I.newSprite('bob', 20, 10, 5);
        s.frames[0][19] = 31;
        s.grabX = 18;
        assert(M.changeSize(s, -1, 2).ok);
        assert.deepStrictEqual([s.width, s.height, s.frames[0].length, s.grabX], [19, 12, 19 * 12, 18]);
        assert(!M.setSize(s, 0, 4).ok && !M.setSize(s, 300, 4).ok);
        let r = M.cycleKind(s);
        assert.deepStrictEqual([s.hardware, s.width, s.planes, M.kindOf(s)], [true, 16, 2, 'sprite']);
        assert.match(r.message, /sprite de hardware/);
        assert.match(M.changeSize(s, 1, 0).message, /16 de ancho/);
        assert(M.changeSize(s, 0, 1).ok);
        assert.match(M.changePlanes(s, 3).message, /3 colores/);
        M.cycleKind(s);
        assert.strictEqual(M.kindOf(s), 'attached');
        assert.match(M.changePlanes(s, 3).message, /15 colores/);
        M.cycleKind(s);
        assert.strictEqual(M.kindOf(s), 'bob');
        assert(M.changePlanes(s, 1).ok && s.frames[0].every((v) => v <= 1));
        assert.deepStrictEqual(M.setKind(s, 'attached').ok, true);
        assert.strictEqual(M.kindOf(s), 'attached');
    });
    await check('sprite model: colours (4 bits in a hardware sprite) and speed', () => {
        const s = I.newSprite('sprite', 0, 8, 0);
        M.setComponent(s, 1, 0, 100);
        assert.strictEqual((s.palette[1] >> 16) & 255, 102);                   // 6 * 17
        const b = I.newSprite('bob', 4, 4, 2);
        M.setComponent(b, 2, 2, 100);
        assert.strictEqual(b.palette[2] & 255, 100);
        assert(M.setSpeed(b, 99) && b.speed === 50 && !M.setSpeed(b, 50) && M.setSpeed(b, 0) && b.speed === 1);
    });
    await check('sprite model: the copied code is Forja\'s', () => {
        const s = I.readIlbm(fixture('bob_forja.iff'));
        assert.strictEqual(M.code(s, 'nave.iff'), '# nave.iff: BOB de 8 x 5, 8 colores, 3 fotogramas, 4 tics por fotograma\n' +
            'if not bob_load(0, "nave.iff")\n    Print "No se puede cargar nave.iff"\nend\n' +
            '# sus colores, los del fichero, en la paleta de la pantalla (el 0, el transparente, es el fondo)\n' +
            'bob_load_colors("nave.iff", 0)\n# animarlo: en cada wait_vblank(), cuenta = cuenta + 1 y\n' +
            '# bob_frame(0, (cuenta / 4) % 3), bob_pos(0, x, y), bob_draw(0)\n');
        const h = I.readIlbm(fixture('sprite_hw.iff'));
        assert.match(M.code(h, 's.iff'), /^# s.iff: sprite de hardware de 16 x 4, 2 fotogramas, 6 tics/);
        assert.match(M.code(h, 's.iff'), /if not sprite_load\(0, "s.iff"\)[\s\S]*sprite_load_colors\(0, "s.iff"\)[\s\S]*sprite_frame\(0, \(cuenta \/ 6\) % 2\)/);
        M.cycleKind(h);
        assert.match(M.code(h, 's.iff'), /sprite acoplado de 16 x 4[\s\S]*sprite_load_attached/);
    });

    // --- the provider, with a stand-in for VS Code ---------------------------------------------------------------
    const files = new Map();
    const shown = [];
    let clipboard = '';
    const commands = [];
    const uri = (p) => ({ fsPath: p, path: p, toString: () => 'file://' + p, scheme: 'file' });
    const fakeVscode = {
        Uri: { joinPath: (u, ...parts) => uri(path.join(u.fsPath, ...parts)), parse: (s) => uri(s.replace('file://', '')) },
        EventEmitter: class { constructor() { this.l = []; this.event = (f) => { this.l.push(f); return { dispose() {} }; }; } fire(m) { for (const f of this.l) f(m); } dispose() {} },
        workspace: {
            workspaceFolders: [], getConfiguration: () => ({ get: () => undefined }),
            fs: {
                readFile: async (u) => { if (!files.has(u.fsPath)) throw new Error('ENOENT'); return files.get(u.fsPath); },
                writeFile: async (u, b) => { files.set(u.fsPath, new Uint8Array(b)); },
                delete: async (u) => { files.delete(u.fsPath); },
            },
        },
        window: { registerCustomEditorProvider: () => ({ dispose() {} }), showErrorMessage: (m) => shown.push(m),
            setStatusBarMessage: (m) => shown.push(m), showOpenDialog: async () => [uri('/p/naves/nave.iff')] },
        env: { clipboard: { writeText: async (t) => { clipboard = t; } } },
        commands: { executeCommand: async (c) => { commands.push(c); } },
    };
    const load = Module._load;
    Module._load = function (request, parent, isMain) {
        return request === 'vscode' ? fakeVscode : load.call(this, request, parent, isMain);
    };
    let SE;
    delete require.cache[require.resolve('../spriteEditor.js')];   // (extension.js loaded it with another stand-in)
    try { SE = require('../spriteEditor.js'); } finally { Module._load = load; }
    const context = { subscriptions: [], extensionUri: uri(path.join(__dirname, '..')), extensionPath: path.join(__dirname, '..') };
    const fakePanel = () => {
        const p = { posted: [], handlers: [], disposers: [] };
        p.webview = { options: null, html: '', cspSource: 'vscode-resource:', asWebviewUri: (u) => ({ toString: () => 'res:' + u.fsPath }),
            postMessage: (m) => { p.posted.push(m); return Promise.resolve(true); },
            onDidReceiveMessage: (f) => { p.handlers.push(f); return { dispose() {} }; } };
        p.onDidDispose = (f) => { p.disposers.push(f); return { dispose() {} }; };
        p.send = async (m) => { for (const f of p.handlers) await f(m); };
        return p;
    };

    await check('sprite provider: opens, edits with undo and redo, saves, reverts; a new file is a BOB', async () => {
        const provider = SE.registerSpriteEditor(context);
        files.set('/p/nave.iff', fixture('bob_forja.iff'));
        const doc = await provider.openCustomDocument(uri('/p/nave.iff'), {});
        const panel = fakePanel(), other = fakePanel();
        provider.resolveCustomEditor(doc, panel);
        provider.resolveCustomEditor(doc, other);
        assert.match(panel.webview.html, /res:.*media\/sprite\.js/);
        assert(!/\{\{/.test(panel.webview.html), 'all the {{...}} filled');
        await panel.send({ type: 'ready' });
        assert.strictEqual(panel.posted[0].name, 'nave.iff');
        assert.deepStrictEqual(panel.posted[0].bytes, Array.from(fixture('bob_forja.iff')));
        const changes = [];
        provider.onDidChangeCustomDocument((e) => changes.push(e));
        const s = I.readIlbm(fixture('bob_forja.iff'));
        s.frames[0][0] = 7;
        const edited = Array.from(I.writeIlbm(s));
        await panel.send({ type: 'edit', label: 'Dibujar', bytes: edited });
        assert.strictEqual(changes.length, 1);
        assert.strictEqual(changes[0].label, 'Dibujar');
        assert.deepStrictEqual(other.posted.pop().bytes, edited);                // the other editor of the file too
        assert.strictEqual(panel.posted.length, 1);                              // not back to the one that sent it
        changes[0].undo();
        assert.deepStrictEqual(Array.from(doc.bytes), Array.from(fixture('bob_forja.iff')));
        assert.deepStrictEqual(panel.posted.pop(), { type: 'load', bytes: Array.from(fixture('bob_forja.iff')), keep: true });
        changes[0].redo();
        await provider.saveCustomDocument(doc);
        assert.deepStrictEqual(Array.from(files.get('/p/nave.iff')), edited);
        await provider.saveCustomDocumentAs(doc, uri('/p/copia.iff'));
        assert.deepStrictEqual(Array.from(files.get('/p/copia.iff')), edited);
        files.set('/p/nave.iff', fixture('bob_forja.iff'));
        await provider.revertCustomDocument(doc);
        assert.deepStrictEqual(Array.from(doc.bytes), Array.from(fixture('bob_forja.iff')));
        const backup = await provider.backupCustomDocument(doc, { destination: uri('/backup/1') });
        const again = await provider.openCustomDocument(uri('/p/nave.iff'), { backupId: backup.id });
        assert.deepStrictEqual(Array.from(again.bytes), Array.from(fixture('bob_forja.iff')));
        await backup.delete();
        assert(!files.has('/backup/1'));
        const fresh = await provider.openCustomDocument(uri('/p/nuevo.bob'), {});
        const r = I.readIlbm(fresh.bytes);
        assert.deepStrictEqual([r.width, r.height, r.planes, r.hardware], [32, 32, 4, false]);
    });
    await check('sprite provider: the clipboard, undo, and files next to it', async () => {
        const provider = SE.registerSpriteEditor(context);
        files.set('/p/nave.iff', fixture('bob_forja.iff'));
        files.set('/p/tiles/t.iff', fixture('sprite_hw.iff'));
        const doc = await provider.openCustomDocument(uri('/p/nave.iff'), {});
        const panel = fakePanel();
        provider.resolveCustomEditor(doc, panel);
        await panel.send({ type: 'clipboard', text: 'bob_load(0, "x")', say: 'Copiado' });
        assert.strictEqual(clipboard, 'bob_load(0, "x")');
        assert.strictEqual(shown.pop(), 'Copiado');
        await panel.send({ type: 'undo' });
        assert.strictEqual(commands.pop(), 'undo');
        await panel.send({ type: 'readFile', id: 3, path: 'tiles/t.iff' });
        const got = panel.posted.pop();
        assert.deepStrictEqual([got.type, got.id, got.bytes.length], ['file', 3, fixture('sprite_hw.iff').length]);
        await panel.send({ type: 'readFile', id: 4, path: 'no.iff' });
        assert.strictEqual(panel.posted.pop().bytes, null);
        await panel.send({ type: 'pickFile', id: 5, title: 'Tileset' });
        assert.deepStrictEqual(panel.posted.pop(), { type: 'picked', id: 5, path: 'naves/nave.iff' });
    });

    // --- the webview ---------------------------------------------------------------------------------------------
    const { findChromium, openPage } = require('./webview.js');
    const chromium = findChromium();
    if (!chromium) { console.log('SKIP sprite webview: no Chromium (set $CHROMIUM)'); return; }
    const page = await openPage(chromium, 'file://' + path.join(__dirname, 'sprite.html'));
    const E = (expr) => page.eval(`(() => { const E = window.DashSpriteEditor; return ${expr}; })()`);
    const lastEdit = async () => {
        const b = await page.eval('(window.__posted || []).filter((m) => m.type === "edit").pop().bytes');
        return I.readIlbm(new Uint8Array(b));
    };
    const edits = () => page.eval('(window.__posted || []).filter((m) => m.type === "edit").length');
    const loadBytes = (bytes, keep) => page.eval(`window.postMessage({ type: 'load', name: 'nave.iff', keep: ${!!keep}, bytes: ${JSON.stringify(Array.from(bytes))} }, '*')`)
        .then(() => page.eval('new Promise((r) => setTimeout(r, 50))'));
    // a mouse press at pixel x, y of the grid (and a drag to x2, y2)
    const mouse = async (x, y, opts = {}) => {
        const at = (px, py) => page.eval(`(() => { const c = document.getElementById('grid'), r = c.getBoundingClientRect();
            const z = r.width / window.DashSpriteEditor.s.width; return [r.left + (${px} + 0.5) * z, r.top + (${py} + 0.5) * z]; })()`);
        const mods = (opts.alt ? 1 : 0) | (opts.ctrl ? 2 : 0) | (opts.shift ? 8 : 0);
        const [ax, ay] = await at(x, y);
        await page.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: ax, y: ay, button: 'left', buttons: 1, clickCount: 1, modifiers: mods });
        if (opts.to) {
            const [bx, by] = await at(opts.to[0], opts.to[1]);
            await page.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: (ax + bx) / 2, y: (ay + by) / 2, button: 'left', buttons: 1, modifiers: mods });
            await page.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: bx, y: by, button: 'left', buttons: 1, modifiers: mods });
            await page.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: bx, y: by, button: 'left', buttons: 0, clickCount: 1, modifiers: mods });
        } else await page.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: ax, y: ay, button: 'left', buttons: 0, clickCount: 1, modifiers: mods });
    };
    const press = async (key, mods) => {
        await page.eval('document.getElementById("grid").focus()');
        await page.key(key, mods);
    };
    try {
        await page.eval('new Promise((r) => { const t = () => (window.__posted || []).some((m) => m.type === "ready") ? r() : setTimeout(t, 20); t(); })');
        await loadBytes(fixture('bob_forja.iff'));
        await check('sprite webview: opens a file of Forja: its frames, colours and size', async () => {
            assert.deepStrictEqual(await E('[E.s.width, E.s.height, E.s.frames.length, E.frame, E.color]'), [8, 5, 3, 0, 1]);
            assert.strictEqual(await page.eval('document.querySelectorAll("#frames .frame").length'), 3);
            assert.strictEqual(await page.eval('document.querySelectorAll("#palette-pane .swatch").length'), 8);
            assert.match(await page.eval('document.getElementById("status").textContent'), /BOB de 8 x 5 · fotograma 1 de 3/);
            assert.strictEqual(await page.eval('document.getElementById("grid").width > 8 * 10'), true);   // zoomed to fit
        });
        await check('sprite webview: pencil (a drag without gaps), Alt erases, Ctrl picks the colour', async () => {
            await press('7');
            await mouse(0, 4, { to: [7, 4] });
            let s = await lastEdit();
            assert.deepStrictEqual([...s.frames[0].slice(32, 40)], [7, 7, 7, 7, 7, 7, 7, 7]);
            await mouse(3, 4, { alt: true });
            s = await lastEdit();
            assert.strictEqual(s.frames[0][35], 0);
            await press('2');
            await mouse(0, 4, { ctrl: true });
            assert.strictEqual(await E('E.color'), 7);
        });
        await check('sprite webview: line, box (filled with Shift) and fill, with Forja\'s keys', async () => {
            await press('Backspace');                                                // the frame cleared
            let s = await lastEdit();
            assert(s.frames[0].every((v) => !v));
            await press('l');
            await mouse(0, 0, { to: [7, 0] });
            s = await lastEdit();
            assert.deepStrictEqual([...s.frames[0].slice(0, 8)], [7, 7, 7, 7, 7, 7, 7, 7]);
            await press('b');
            await press('3');
            await mouse(1, 1, { to: [3, 3], shift: true });
            s = await lastEdit();
            assert.strictEqual(s.frames[0].filter((v) => v === 3).length, 9);
            await press('f');
            await press('5');
            await mouse(6, 3);
            s = await lastEdit();
            assert.strictEqual(s.frames[0].filter((v) => v === 5).length, 40 - 8 - 9);
            await press('a');
            await mouse(4, 2);
            s = await lastEdit();
            assert.deepStrictEqual([s.grabX, s.grabY], [4, 2]);
            await press('p');
            assert.strictEqual(await E('E.tool'), 0);
        });
        await check('sprite webview: frames with the keys (N, D, arrows, Alt+arrows, H, Delete, Shift+arrows)', async () => {
            const n0 = await edits();
            await press('d');
            assert.deepStrictEqual(await E('[E.frame, E.s.frames.length]'), [1, 4]);
            await press('h');
            let s = await lastEdit();
            assert.strictEqual(s.frames[1][7], 7);
            await press('ArrowLeft', { alt: true });
            assert.strictEqual(await E('E.frame'), 0);
            await press('ArrowRight');
            assert.strictEqual(await E('E.frame'), 1);
            await press('n');
            assert.deepStrictEqual(await E('[E.frame, E.s.frames.length]'), [2, 5]);
            await press('Delete');
            assert.deepStrictEqual(await E('[E.frame, E.s.frames.length]'), [2, 4]);
            const before = await E('Array.from(E.s.frames[2])');
            await press('ArrowDown', { shift: true });
            s = await lastEdit();
            const w = s.width, h = s.height;
            assert.deepStrictEqual([...s.frames[2]], before.map((_, i) => before[((Math.floor(i / w) - 1 + h) % h) * w + i % w]));
            assert(await edits() >= n0 + 5);
        });
        await check('sprite webview: size with Ctrl+arrows, kind with T, speed with + and -', async () => {
            await press('ArrowRight', { ctrl: true });
            assert.deepStrictEqual(await E('[E.s.width, E.s.height]'), [9, 5]);
            await press('t');
            assert.deepStrictEqual(await E('[E.s.hardware, E.s.width, E.s.planes]'), [true, 16, 2]);
            assert.match(await page.eval('document.getElementById("status").textContent'), /Ahora es un sprite de hardware/);
            await press('ArrowRight', { ctrl: true });
            assert.match(await page.eval('document.getElementById("status").textContent'), /16 de ancho/);
            await press('t'); await press('t');
            assert.strictEqual(await E('E.s.hardware'), false);
            await press('+');
            assert.strictEqual((await lastEdit()).speed, 3);
            await press('-'); await press('-');
            assert.strictEqual((await lastEdit()).speed, 5);
        });
        await check('sprite webview: the colour bars and the size fields', async () => {
            await page.eval(`(() => { const r = document.querySelector('#palette-pane input[type=range]'); r.value = 255;
                r.dispatchEvent(new Event('input')); r.dispatchEvent(new Event('change')); })()`);
            const s = await lastEdit();
            const c = await E('E.color');
            assert.strictEqual((s.palette[c] >> 16) & 255, 255);
            await page.eval(`(() => { const i = document.querySelector('#size-pane input[aria-label=Alto]'); i.value = 12;
                i.dispatchEvent(new Event('change')); })()`);
            assert.strictEqual((await lastEdit()).height, 12);
            await page.eval(`(() => { const k = document.querySelector('#size-pane select[aria-label=Tipo]'); k.value = 'attached';
                k.dispatchEvent(new Event('change')); })()`);
            const a = await lastEdit();
            assert.deepStrictEqual([a.hardware, a.planes], [true, 4]);
        });
        await check('sprite webview: copy and paste a frame (clipboard events), C copies the code', async () => {
            const n = await E('E.s.frames.length');
            const copied = await page.eval(`(() => { const e = new ClipboardEvent('copy', { clipboardData: new DataTransfer(),
                bubbles: true, cancelable: true }); document.getElementById('grid').dispatchEvent(e); return e.clipboardData.getData('text/plain'); })()`);
            assert.strictEqual(JSON.parse(copied).dashFrame, 1);
            await page.eval(`(() => { const d = new DataTransfer(); d.setData('text/plain', ${JSON.stringify(copied)});
                document.getElementById('grid').dispatchEvent(new ClipboardEvent('paste', { clipboardData: d, bubbles: true, cancelable: true })); })()`);
            assert.strictEqual(await E('E.s.frames.length'), n + 1);
            await press('c');
            const clip = await page.eval('(window.__posted || []).filter((m) => m.type === "clipboard").pop()');
            assert.match(clip.text, /^# nave.iff: sprite acoplado de 16 x 12[\s\S]*sprite_load_attached\(0, "nave.iff"\)/);
        });
        await check('sprite webview: undo from VS Code reloads and keeps the frame; a file that is not ILBM says so', async () => {
            await press('ArrowRight');
            const f = await E('E.frame');
            await loadBytes(fixture('bob_forja.iff'), true);
            assert.deepStrictEqual(await E('[E.s.frames.length, E.frame]'), [3, Math.min(f, 2)]);
            await press('o');
            await press(' ');
            assert.deepStrictEqual(await E('[E.onion, E.playing]'), [true, true]);
            await press(' ');
            await loadBytes(fixture('mapa.fmap'));
            assert.match(await page.eval('document.getElementById("error").textContent'), /no es una imagen IFF ILBM/i);
            assert.strictEqual(await page.eval('document.getElementById("layout").style.display'), 'none');
            await loadBytes(fixture('sprite_hw.iff'));
            assert.strictEqual(await page.eval('document.getElementById("layout").style.display'), '');
        });
    } finally {
        page.close();
    }
}

module.exports = { spriteTests };
