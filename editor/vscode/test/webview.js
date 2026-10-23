// The .dashui editor's webview in a headless Chromium (test/webview.html), driven through the DevTools
// protocol: real key presses, the clipboard events VS Code sends to a webview, drag and drop. Skipped
// without Chromium ($CHROMIUM, or chromium / google-chrome on the PATH).
const path = require('path');
const fs = require('fs');
const os = require('os');
const { spawn, execFileSync } = require('child_process');

function findChromium() {
    if (process.env.CHROMIUM) return process.env.CHROMIUM;
    for (const name of ['chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable']) {
        try { return execFileSync('which', [name], { encoding: 'utf8' }).trim(); } catch (e) { /* next */ }
    }
    return null;
}

/** A page of a headless Chromium: send(method, params) over the DevTools protocol, and close() */
async function openPage(chromium, url) {
    const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_cdp_'));
    const proc = spawn(chromium, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`,
                                  '--allow-file-access-from-files', '--no-first-run', '--no-sandbox', 'about:blank'],
                       { stdio: ['ignore', 'ignore', 'pipe'] });
    const wsUrl = await new Promise((resolve, reject) => {
        let err = '';
        const timer = setTimeout(() => reject(new Error('Chromium did not start: ' + err.slice(-300))), 20000);
        proc.stderr.on('data', (d) => {
            err += d.toString();
            const m = /DevTools listening on (ws:\S+)/.exec(err);
            if (m) { clearTimeout(timer); resolve(m[1]); }
        });
    });
    const ws = new WebSocket(wsUrl);
    await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
    let id = 0;
    const waiting = new Map();
    const events = [];
    ws.onmessage = (m) => {
        const msg = JSON.parse(m.data);
        if (msg.id && waiting.has(msg.id)) {
            const { resolve, reject } = waiting.get(msg.id);
            waiting.delete(msg.id);
            if (msg.error) reject(new Error(msg.error.message)); else resolve(msg.result);
        } else if (msg.method) {
            events.push(msg);
        }
    };
    const raw = (method, params, sessionId) => new Promise((resolve, reject) => {
        const n = ++id;
        waiting.set(n, { resolve, reject });
        ws.send(JSON.stringify(Object.assign({ id: n, method, params: params || {} }, sessionId ? { sessionId } : {})));
    });
    const { targetId } = await raw('Target.createTarget', { url: 'about:blank' });
    const { sessionId } = await raw('Target.attachToTarget', { targetId, flatten: true });
    const send = (method, params) => raw(method, params, sessionId);
    await send('Page.enable');
    await send('Page.navigate', { url });
    for (let i = 0; i < 100 && !events.some((e) => e.method === 'Page.loadEventFired'); i++) await new Promise((r) => setTimeout(r, 50));
    return {
        send,
        /** the value of a JavaScript expression in the page (awaited) */
        async eval(expression) {
            const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
            if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception ? r.exceptionDetails.exception.description : r.exceptionDetails.text);
            return r.result.value;
        },
        /** a key pressed and let go: key as in KeyboardEvent.key, modifiers alt, ctrl, shift */
        async key(key, mods) {
            const codes = { ArrowUp: 38, ArrowDown: 40, ArrowLeft: 37, ArrowRight: 39, Delete: 46, Home: 36, End: 35,
                            Enter: 13, F2: 113, d: 68 };
            const modifiers = (mods && mods.alt ? 1 : 0) | (mods && mods.ctrl ? 2 : 0) | (mods && mods.shift ? 8 : 0);
            const base = { key, windowsVirtualKeyCode: codes[key] || 0, modifiers,
                           code: key.length === 1 ? 'Key' + key.toUpperCase() : key };
            await send('Input.dispatchKeyEvent', Object.assign({ type: 'rawKeyDown' }, base));
            await send('Input.dispatchKeyEvent', Object.assign({ type: 'keyUp' }, base));
        },
        close() {
            try { ws.close(); } catch (e) { /* gone */ }
            proc.kill();
            setTimeout(() => fs.rmSync(profile, { recursive: true, force: true }), 500);
        },
    };
}

async function webviewTests(check, assert) {
    const chromium = findChromium();
    if (!chromium) {
        console.log('SKIP webview: no Chromium (set $CHROMIUM)');
        return;
    }
    const page = await openPage(chromium, 'file://' + path.join(__dirname, 'webview.html'));
    const sel = () => page.eval('JSON.stringify(DashUIEditor.selected)');
    const lastEdit = () => page.eval('JSON.parse(window.__posted.filter((m) => m.type === "edit").pop().text)');
    const focused = () => page.eval('(document.activeElement.className || "") + "|" + document.activeElement.getAttribute("aria-selected")');
    try {
        await page.eval('new Promise((r) => { const t = () => DashUIEditor.doc ? r() : setTimeout(t, 20); t(); })');
        await check('webview: tree and palette for keyboards and screen readers', async () => {
            assert.strictEqual(await page.eval('document.getElementById("tree").getAttribute("role")'), 'tree');
            assert.strictEqual(await page.eval('document.querySelectorAll("#tree [role=treeitem]").length'), 6);
            assert.strictEqual(await page.eval('document.querySelector("[data-path=\'[0,1]\']").getAttribute("aria-level")'), '3');
            assert.strictEqual(await page.eval('document.querySelectorAll("#palette button").length') > 10, true);
            assert.strictEqual(await page.eval('document.getElementById("problems").getAttribute("aria-live")'), 'polite');
            assert.strictEqual(await page.eval('document.querySelectorAll("#tree [tabindex=\'0\']").length'), 1);
        });
        await check('webview: arrows move the selection, and the focus stays in the tree', async () => {
            await page.eval('document.querySelector("#tree .tree-row.selected").focus()');
            await page.key('ArrowDown');
            assert.strictEqual(await sel(), '[0]');
            await page.key('ArrowRight');
            assert.strictEqual(await sel(), '[0,0]');
            await page.key('ArrowDown');
            assert.strictEqual(await sel(), '[0,1]');
            await page.key('ArrowLeft');
            assert.strictEqual(await sel(), '[0]');
            await page.key('End');
            assert.strictEqual(await sel(), '[2]');
            await page.key('Home');
            assert.strictEqual(await sel(), '[]');
            assert.match(await focused(), /tree-row.*\|true/);
        });
        await check('webview: Alt+arrow moves the object, Ctrl+D duplicates it', async () => {
            await page.key('ArrowDown');                         // the hgroup
            await page.key('ArrowDown', { alt: true });
            assert.strictEqual(await sel(), '[1]');
            let d = await lastEdit();
            assert.strictEqual(d.windows[0].root.children[0].type, 'canvas');
            assert.strictEqual(d.windows[0].root.children[1].type, 'hgroup');
            await page.key('ArrowRight');
            await page.key('ArrowDown');                         // url
            await page.key('d', { ctrl: true });
            assert.strictEqual(await sel(), '[1,2]');
            d = await lastEdit();
            assert.strictEqual(d.windows[0].root.children[1].children[2].name, 'url2');
            assert.match(await focused(), /tree-row.*\|true/);
        });
        await check('webview: copy and paste (clipboard events), cut, Delete', async () => {
            await page.eval('DashUIEditor.select([1, 0])');      // atras
            const copied = await page.eval(`(() => { const e = new ClipboardEvent('copy', { clipboardData: new DataTransfer(),
                bubbles: true, cancelable: true }); document.body.dispatchEvent(e); return e.clipboardData.getData('text/plain'); })()`);
            assert.strictEqual(JSON.parse(copied).name, 'atras');
            await page.eval('DashUIEditor.select([])');
            await page.eval(`(() => { const dt = new DataTransfer(); dt.setData('text/plain', ${JSON.stringify(copied)});
                document.body.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true })); })()`);
            let d = await lastEdit();
            const root = d.windows[0].root.children;
            assert.strictEqual(root[root.length - 1].name, 'atras2');
            assert.strictEqual(await sel(), JSON.stringify([root.length - 1]));
            await page.eval(`document.body.dispatchEvent(new ClipboardEvent('cut', { clipboardData: new DataTransfer(),
                bubbles: true, cancelable: true }))`);
            d = await lastEdit();
            assert.strictEqual(d.windows[0].root.children.length, root.length - 1);
            await page.eval('DashUIEditor.select([2])');
            await page.eval('document.querySelector("#tree .tree-row.selected").focus()');
            await page.key('Delete');
            d = await lastEdit();
            assert.strictEqual(d.windows[0].root.children.length, root.length - 2);
            // a paste in a field of the properties is the field's
            await page.eval('DashUIEditor.select([0])');
            const before = await page.eval('window.__posted.length');
            await page.eval(`(() => { const dt = new DataTransfer(); dt.setData('text/plain', '{"type":"text"}');
                document.getElementById('prop-name').dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true })); })()`);
            assert.strictEqual(await page.eval('window.__posted.length'), before);
        });
        await check('webview: drop before, after or into, in the tree and in the preview', async () => {
            const dropOn = (selector, type, fy, fx) => page.eval(`(() => {
                const src = document.querySelector('#palette [data-type="${type}"]');
                const dst = document.querySelector(${JSON.stringify(selector)});
                const r = dst.getBoundingClientRect();
                const dt = new DataTransfer();
                const at = { clientX: r.left + r.width * ${fx === undefined ? 0.5 : fx}, clientY: r.top + r.height * ${fy},
                             dataTransfer: dt, bubbles: true, cancelable: true };
                src.dispatchEvent(new DragEvent('dragstart', at));
                dst.dispatchEvent(new DragEvent('dragover', at));
                const shown = dst.className;
                dst.dispatchEvent(new DragEvent('drop', at));
                return shown;
            })()`);
            const shown = await dropOn('#tree [data-path="[0]"]', 'button', 0.1);
            assert.match(shown, /drop-before/);
            let d = await lastEdit();
            assert.strictEqual(d.windows[0].root.children[0].type, 'button');
            assert.strictEqual(await sel(), '[0]');
            await dropOn('#tree [data-path="[2]"]', 'text', 0.5);        // the hgroup: into it
            d = await lastEdit();
            const g = d.windows[0].root.children[2];
            assert.strictEqual(g.children[g.children.length - 1].type, 'text');
            // in the preview: after the canvas
            await dropOn('#preview [data-path="[1]"]', 'checkbox', 0.9);
            d = await lastEdit();
            assert.strictEqual(d.windows[0].root.children[2].type, 'checkbox');
            // the preview's objects can be dragged too: the checkbox to the top
            await page.eval(`(() => {
                const src = document.querySelector('#preview [data-path="[2]"]');
                const dst = document.querySelector('#tree [data-path="[0]"]');
                const r = dst.getBoundingClientRect();
                const at = { clientX: r.left + 4, clientY: r.top + 1, dataTransfer: new DataTransfer(), bubbles: true, cancelable: true };
                src.dispatchEvent(new DragEvent('dragstart', at));
                dst.dispatchEvent(new DragEvent('dragover', at));
                dst.dispatchEvent(new DragEvent('drop', at));
            })()`);
            d = await lastEdit();
            assert.strictEqual(d.windows[0].root.children[0].type, 'checkbox');
        });
        await check('webview: the button of an event asks VS Code for its code', async () => {
            await page.eval('DashUIEditor.load(JSON.stringify({ dashui: 1, windows: [{ name: "W", root: { type: "vgroup", children: [' +
                            '{ type: "button", name: "aceptar", event: 3 }, { type: "button", name: "otro" }] } }] }))');
            await page.eval('DashUIEditor.select([0])');
            const buttons = await page.eval('[...document.querySelectorAll("#props button.goto")].map((b) => b.disabled)');
            assert.deepStrictEqual(buttons, [false]);
            await page.eval('document.querySelector("#props button.goto").click()');
            assert.deepStrictEqual(await page.eval('window.__posted[window.__posted.length - 1]'),
                                   { type: 'gotoEvent', event: 3, name: 'aceptar' });
            await page.eval('DashUIEditor.select([1])');            // no number yet: the button waits for one
            assert.strictEqual(await page.eval('document.querySelector("#props button.goto").disabled'), true);
        });
        await check('webview: F2 goes to the name, the undo button asks VS Code', async () => {
            await page.eval('DashUIEditor.select([1])');
            await page.eval('document.querySelector("#tree .tree-row.selected").focus()');
            await page.key('F2');
            assert.strictEqual(await page.eval('document.activeElement.id'), 'prop-name');
            await page.eval('document.getElementById("undo").click()');
            assert.strictEqual(await page.eval('window.__posted[window.__posted.length - 1].type'), 'undo');
        });
        await check('webview: "al cambiar" shows the window on the Amiga again after each change, one at a time', async () => {
            const asked = () => page.eval('window.__posted.filter((m) => m.type === "amiga").length');
            const wait = (ms) => page.eval(`new Promise((r) => setTimeout(r, ${ms}))`);
            const shot = (m) => page.eval(`window.postMessage(${JSON.stringify(Object.assign({ type: 'screenshot', busy: false }, m))}, '*')`);
            await page.eval('window.__amigaDelay = 50');
            let n = await asked();
            await page.eval('document.getElementById("amiga-auto").click()');      // on: at once
            assert.deepStrictEqual(await page.eval('window.__posted.filter((m) => m.type === "amigaAuto").pop()'),
                                   { type: 'amigaAuto', on: true });
            assert.strictEqual(await asked(), n + 1);
            assert.strictEqual(await page.eval('window.__posted.filter((m) => m.type === "amiga").pop().auto'), true);
            await page.eval('document.getElementById("add-window").click()');       // a change while it runs: it waits
            await wait(150);
            assert.strictEqual(await asked(), n + 1);
            assert.strictEqual(await page.eval('DashUIEditor.amiga.pending'), true);
            await shot({ src: '', status: 'listo' });                                // done: the one waiting goes
            await wait(150);
            assert.strictEqual(await asked(), n + 2);
            await shot({ status: 'listo' });
            await page.eval('document.getElementById("add-window").click()');       // two changes: one question
            await page.eval('document.getElementById("add-window").click()');
            await wait(150);
            assert.strictEqual(await asked(), n + 3);
            await shot({ error: 'no hay emulador' });                               // fails: off, and no more
            assert.strictEqual(await page.eval('document.getElementById("amiga-auto").checked'), false);
            assert.deepStrictEqual(await page.eval('window.__posted.filter((m) => m.type === "amigaAuto").pop()'),
                                   { type: 'amigaAuto', on: false });
            await page.eval('document.getElementById("add-window").click()');
            await wait(150);
            assert.strictEqual(await asked(), n + 3);
        });
    } finally {
        page.close();
    }
}

module.exports = { webviewTests, findChromium, openPage };
