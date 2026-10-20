// Tests without VS Code: the TextMate grammar (vscode-textmate + oniguruma, the same
// engine VS Code uses) on a Dash sample, and the commands of extension.js with a fake
// 'vscode' module. Run: npm test (from editor/vscode).
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const Module = require('module');

let failures = 0;
function check(name, fn) {
    return Promise.resolve().then(fn).then(
        () => console.log('ok   ' + name),
        (e) => { failures++; console.log('FAIL ' + name + ': ' + e.message); });
}

// --- grammar -----------------------------------------------------------------
const vsctm = require('vscode-textmate');
const oniguruma = require('vscode-oniguruma');

async function grammar() {
    const wasm = fs.readFileSync(require.resolve('vscode-oniguruma/release/onig.wasm')).buffer;
    await oniguruma.loadWASM(wasm);
    const registry = new vsctm.Registry({
        onigLib: Promise.resolve({
            createOnigScanner: (p) => new oniguruma.OnigScanner(p),
            createOnigString: (s) => new oniguruma.OnigString(s),
        }),
        loadGrammar: async (scope) => {
            if (scope === 'source.dash')
                return vsctm.parseRawGrammar(fs.readFileSync(path.join(__dirname, '..', 'syntaxes', 'dash.tmLanguage.json'),
                                                             'utf8'), 'dash.tmLanguage.json');
            if (scope === 'source.c')   // VS Code has its own; a stand-in for the test
                return vsctm.parseRawGrammar(JSON.stringify({ scopeName: 'source.c', patterns: [
                    { match: '\\b(return|volatile)\\b', name: 'keyword.c' }] }), 'c.json');
            return null;
        },
    });
    return registry.loadGrammar('source.dash');
}

/** scopes of each token of each line: [[text, lastScope], ...] */
function tokenize(g, source) {
    let state = vsctm.INITIAL;
    const out = [];
    for (const line of source.split('\n')) {
        const r = g.tokenizeLine(line, state);
        for (const t of r.tokens) out.push([line.slice(t.startIndex, t.endIndex), t.scopes[t.scopes.length - 1]]);
        state = r.ruleStack;
    }
    return out;
}

function scopeOf(tokens, text) {
    const t = tokens.find(([s]) => s === text);
    assert(t, `no token ${JSON.stringify(text)}`);
    return t[1];
}

const SAMPLE = `# un comentario
import "lib/ventana.dashui"
const MAX = 0x1F
struct Punto
    x: Int = 0
end
func suma(a: Int, b: Int) -> Int
    return a + b
end
@native func peek(addr: Pointer) -> Int
"""
    return (LONG)*(volatile UBYTE *)addr;
"""
end
Main
    n = 42
    s = "Hola #{n} amigos \\n"
    if n >= 10 and not false
        mui_text("x")
    end
    EventLoop
        On Close
            Stop
        end
    end
end`;

async function grammarTests() {
    const g = await grammar();
    const tokens = tokenize(g, SAMPLE);
    await check('grammar: comment', () => assert.match(scopeOf(tokens, '# un comentario'), /^comment\.line/));
    await check('grammar: keywords', () => {
        assert.match(scopeOf(tokens, 'import'), /^keyword\.other/);
        assert.match(scopeOf(tokens, 'return'), /^keyword\.control/);
        assert.match(scopeOf(tokens, 'EventLoop'), /^keyword\.other/);
        assert.match(scopeOf(tokens, 'and'), /^keyword\.operator\.logical/);
    });
    await check('grammar: declarations', () => {
        assert.match(scopeOf(tokens, 'suma'), /^entity\.name\.function/);
        assert.match(scopeOf(tokens, 'Punto'), /^entity\.name\.type/);
        assert.match(scopeOf(tokens, 'MAX'), /^variable\.other\.constant/);
    });
    await check('grammar: numbers and constants', () => {
        assert.match(scopeOf(tokens, '0x1F'), /^constant\.numeric\.hex/);
        assert.match(scopeOf(tokens, '42'), /^constant\.numeric\.integer/);
        assert.match(scopeOf(tokens, 'false'), /^constant\.language/);
    });
    await check('grammar: types and builtins', () => {
        assert.match(scopeOf(tokens, 'Int'), /^support\.type/);
        assert.match(scopeOf(tokens, 'mui_text'), /^support\.function\.builtin/);
    });
    await check('grammar: string with interpolation and escape', () => {
        assert.match(scopeOf(tokens, 'n'), /^variable\.other|^entity/);
        assert.match(scopeOf(tokens, '#{'), /punctuation\.section\.interpolation\.begin/);
        assert.match(scopeOf(tokens, '\\n'), /^constant\.character\.escape/);
        assert.match(scopeOf(tokens, ' amigos '), /^string\.quoted/);
    });
    await check('grammar: native C block', () => {
        // the C grammar runs inside: "volatile" is a C keyword, not part of a Dash string
        assert.strictEqual(scopeOf(tokens, 'volatile'), 'keyword.c');
    });
    // generated from the compiler (tools/gen_tmgrammar.py): every builtin, directives, blocks...
    const t2 = tokenize(g, SAMPLE2);
    await check('grammar: directives', () => {
        assert.match(scopeOf(t2, '@stack'), /^keyword\.other\.directive/);
        assert.match(scopeOf(t2, '@workbench_output'), /^keyword\.other\.directive/);
        assert.match(scopeOf(t2, 'borrow'), /^storage\.modifier/);
    });
    await check('grammar: any builtin, not only some prefixes', () => {
        assert.match(scopeOf(t2, 'net_signal'), /^support\.function\.builtin/);
        assert.match(scopeOf(t2, 'task_signal'), /^support\.function\.builtin/);
        assert.match(scopeOf(t2, 'mi_funcion'), /^entity\.name\.function\.call/);
    });
    await check('grammar: Window block and events', () => {
        assert.match(scopeOf(t2, 'title'), /^support\.type\.property-name/);
        assert.match(scopeOf(t2, 'Timer'), /^keyword\.other\.event/);
        assert.match(scopeOf(t2, 'open'), /^support\.function\.window/);
    });
    await check('grammar: structs, types, members', () => {
        assert.match(scopeOf(t2, 'Nodo'), /^entity\.name\.type/);         // after ":"
        assert.match(scopeOf(t2, 'Punto'), /^entity\.name\.type\.constructor/);
        assert.match(scopeOf(t2, 'Fixed'), /^support\.type/);
        assert.match(scopeOf(t2, 'push'), /^support\.function\.method/);
        assert.match(scopeOf(t2, 'length'), /^support\.variable\.property/);
        assert.match(scopeOf(t2, 'self'), /^variable\.language\.self/);
        assert.match(scopeOf(t2, 'weak'), /^storage\.modifier/);
        assert.match(scopeOf(t2, '..'), /^keyword\.operator\.range/);
    });
    await check('grammar: interpolation with an expression', () => {
        assert.match(scopeOf(t2, 'str_upper'), /^support\.function\.builtin/);
    });
    await check('grammar: quotes inside #{} are \\" and the text goes on after', () => {
        const t3 = tokenize(g, 'Print "has #{d.has(\\"k\\")} fin"\nx = 1');
        assert.match(scopeOf(t3, 'has'), /^support\.function\.method/);
        assert.match(scopeOf(t3, ' fin'), /^string\.quoted/);
        assert.match(scopeOf(t3, '1'), /^constant\.numeric/);           // the next line is code again
    });
}

const SAMPLE2 = `@stack 262144
@workbench_output "NIL:"
@native(borrow) func peek2(a: Int) -> Int
"""
    return a;
"""
end
Window Win
    title "Hola"
end
struct Nodo
    weak padre: Nodo = nil
    func ver() -> Int
        return self.padre.length
    end
end
Main
    m = net_signal() | task_signal()
    p = Punto(1, 2)
    f: Fixed = Fixed(1.5)
    l = [1]
    l.push(2)
    mi_funcion(1)
    for i in (1..10)
    end
    Win.open
    Print "x #{str_upper(t) + 1}"
    EventLoop
        On Timer 100
        end
    end
end`;


// --- the .dashui model (media/model.js) ----------------------------------------
async function modelTests() {
    const M = require('../media/model.js');
    const { execFileSync } = require('child_process');
    const repo = path.resolve(__dirname, '..', '..', '..');

    await check('model: new document has one empty window', () => {
        const d = M.newDocument();
        assert.strictEqual(d.dashui, 1);
        assert.strictEqual(d.windows[0].root.type, 'vgroup');
    });
    await check('model: add inside a group and after an object', () => {
        const w = M.newWindow('W');
        const g = M.add(w, [], 'hgroup');
        assert.deepStrictEqual(g, [0]);
        assert.deepStrictEqual(M.add(w, g, 'button'), [0, 0]);
        assert.deepStrictEqual(M.add(w, g, 'string', 0), [0, 0]);
        assert.deepStrictEqual(w.root.children[0].children.map((n) => n.type), ['string', 'button']);
        assert.throws(() => M.add(w, [0, 0], 'text'), /not a group/);
    });
    await check('model: move between groups and within one', () => {
        const w = M.newWindow('W');
        M.add(w, [], 'text'); M.add(w, [], 'hgroup'); M.add(w, [], 'button');
        // move the text (0) into the group (now 0 after removal) -> [0, 0]
        assert.deepStrictEqual(M.move(w, [0], [1]), [0, 0]);
        assert.deepStrictEqual(w.root.children.map((n) => n.type), ['hgroup', 'button']);
        // move the button before the group
        assert.deepStrictEqual(M.move(w, [1], [], 0), [0]);
        assert.deepStrictEqual(w.root.children.map((n) => n.type), ['button', 'hgroup']);
        // reorder forward in the same parent: button (0) to the end
        assert.deepStrictEqual(M.move(w, [0], [], 2), [1]);
        assert.deepStrictEqual(w.root.children.map((n) => n.type), ['hgroup', 'button']);
        assert.throws(() => M.move(w, [0], [0, 0]), /inside itself|not a group/);
    });
    await check('model: properties, names and events', () => {
        const n = M.newNode('slider');
        assert.strictEqual(M.setProp(n, 'max', '50'), null);
        assert.strictEqual(n.max, 50);
        assert.match(M.setProp(n, 'max', 'x'), /entero/);
        assert.strictEqual(M.setProp(n, 'name', 'nivel'), null);
        assert.match(M.setProp(n, 'name', '1mal'), /no válido/);
        assert.match(M.setProp(n, 'name', 'window'), /no válido/);
        assert.strictEqual(M.setProp(n, 'change', '7'), null);
        assert.strictEqual(n.change, 7);
        M.setProp(n, 'change', '');
        assert.strictEqual(n.change, undefined);
        M.setProp(n, 'hidden', true); M.setProp(n, 'hidden', false);
        assert.strictEqual(n.hidden, undefined);
    });
    await check('model: unknown keys survive a round trip', () => {
        const text = JSON.stringify({ dashui: 1, extra: { a: 1 }, windows: [{ name: 'W', root: { type: 'vgroup',
            futuro: true, children: [{ type: 'button', label: 'x', nota: 'mía' }] } }] });
        const d = M.parse(text);
        M.add(d.windows[0], [], 'text');
        const back = JSON.parse(M.serialize(d));
        assert.deepStrictEqual(back.extra, { a: 1 });
        assert.strictEqual(back.windows[0].root.futuro, true);
        assert.strictEqual(back.windows[0].root.children[0].nota, 'mía');
    });
    await check('model: check finds repeated names and unknown types', () => {
        const d = M.newDocument();
        const w = d.windows[0];
        M.setProp(w.root.children[M.add(w, [], 'text')[0]], 'name', 'a');
        M.setProp(w.root.children[M.add(w, [], 'text')[0]], 'name', 'a');
        w.root.children.push({ type: 'boton' });
        const p = M.check(d).join(' | ');
        assert.match(p, /repetido a/);
        assert.match(p, /desconocido boton/);
    });
    await check('model: copy and paste with names made unique', () => {
        const w = M.newWindow('W');
        const g = M.add(w, [], 'hgroup');
        const b = M.add(w, g, 'button');
        M.setProp(M.nodeAt(w, b), 'name', 'boton1');
        M.nodeAt(w, b).extra = { kept: true };
        const c = M.copy(w, g);
        const p = M.paste(w, [], c, 0);
        assert.deepStrictEqual(p, [0]);
        assert.strictEqual(M.nodeAt(w, [0, 0]).name, 'boton2');
        assert.deepStrictEqual(M.nodeAt(w, [0, 0]).extra, { kept: true });
        assert.strictEqual(M.nodeAt(w, [1, 0]).name, 'boton1');
        M.paste(w, [], c);
        assert.strictEqual(M.nodeAt(w, [2, 0]).name, 'boton3');
        assert.deepStrictEqual(M.check({ windows: [w] }), []);
        assert.throws(() => M.paste(w, [0, 0], c), /not a group/);
        assert.throws(() => M.paste(w, [], { name: 'x' }), /not an object/);
    });
    await check('model: move up and down, drop places, tree order', () => {
        const w = M.newWindow('W');
        M.add(w, [], 'text'); M.add(w, [], 'button'); const g = M.add(w, [], 'vgroup'); M.add(w, g, 'checkbox');
        assert.deepStrictEqual(M.moveBy(w, [1], -1), [0]);
        assert.strictEqual(w.root.children[0].type, 'button');
        assert.deepStrictEqual(M.moveBy(w, [0], -1), [0]);
        assert.deepStrictEqual(M.moveBy(w, [2], 1), [2]);
        assert.deepStrictEqual(M.paths(w), [[], [0], [1], [2], [2, 0]]);
        assert.deepStrictEqual(M.dropTarget(w, [1], 'before'), { parentPath: [], index: 1 });
        assert.deepStrictEqual(M.dropTarget(w, [1], 'after'), { parentPath: [], index: 2 });
        assert.deepStrictEqual(M.dropTarget(w, [2], 'into'), { parentPath: [2], index: undefined });
        assert.deepStrictEqual(M.dropTarget(w, [1], 'into'), { parentPath: [], index: 2 });
        assert.strictEqual(M.dropTarget(w, [9], 'after'), null);
    });
    const L = require('../dashuiLinks.js');
    await check('dashui and code: problems with their place', () => {
        const text = JSON.stringify({ dashui: 1, windows: [{ name: 'W', root: { type: 'vgroup', children: [
            { type: 'button', name: 'a', event: 1 }, { type: 'botn', name: 'a' }, { type: 'checkbox', change: 0 }] } },
            { name: 'W', root: { type: 'vgroup', children: [] } }] }, null, 2);
        const ps = L.problems(text);
        const msg = ps.map((p) => p.message).join(' | ');
        assert.match(msg, /tipo desconocido: botn/);
        assert.match(msg, /nombre repetido en W: a/);
        assert.match(msg, /change: un número de evento/);
        assert.match(msg, /ventana repetida: W/);
        const rep = ps.find((p) => /repetido/.test(p.message));
        assert.strictEqual(text.split('\n')[rep.start.line].trim(), '"name": "a"');
        assert.strictEqual(rep.start.line, text.split('\n').findIndex((l, i) => l.includes('"name": "a"') && i > 10));
        const bad = L.problems('{"dashui": 1,\n  "windows": [}');
        assert.strictEqual(bad.length, 1);
        assert.strictEqual(bad[0].start.line, 1);
        assert.deepStrictEqual(L.problems(JSON.stringify(M.newDocument())), []);
    });
    await check('dashui and code: where an event is handled, and its code created', () => {
        const dash = 'import "v.dashui"\n\nconst ID_A = 1  # el botón\n\nfunc f()\nend\n\nMain\n    while true\n' +
                     '        ev = mui_wait_event()\n        if ev == ID_A or ev == 7\n            Print "a == 2"\n        end\n    end\nend\n';
        assert.deepStrictEqual(L.handlers(dash, 1).map((h) => [h.line, !!h.constant]), [[10, false], [2, true]]);
        assert.deepStrictEqual(L.handlers(dash, 7).map((h) => h.line), [10]);
        assert.deepStrictEqual(L.handlers(dash, 2), []);            // not inside a text
        assert(L.importsDashui(dash, 'v.dashui') && !L.importsDashui(dash, 'w.dashui'));
        const plan = L.addHandler(dash, 2, 'boton_ok');
        assert.strictEqual(plan.name, 'ID_BOTON_OK');
        const out = L.applyEdits(dash, plan.edits).split('\n');
        assert.strictEqual(out[3], 'const ID_BOTON_OK = 2');
        assert.strictEqual(out[plan.handler.line - 1], '        if ev == ID_BOTON_OK');
        assert.strictEqual(out[plan.handler.line], '            # boton_ok');
        assert.deepStrictEqual(L.handlers(out.join('\n'), 2).map((h) => h.line), [plan.handler.line - 1, 3]);
        // its constant already there: only the handler; no loop: only the constant
        assert.strictEqual(L.addHandler(dash, 1, 'x').edits.length, 1);
        const p2 = L.addHandler('Main\nend\n', 3);
        assert.strictEqual(p2.name, 'EVENTO_3');
        assert.strictEqual(p2.handler, null);
        assert.deepStrictEqual(p2.edits, [{ line: 0, text: 'const EVENTO_3 = 3' }]);
    });
    await check('model: preview shows every object with its path', () => {
        const w = M.newWindow('W');
        w.title = 'Hola <b>';
        const g = M.add(w, [], 'tabs');
        M.add(w, g, 'canvas'); M.add(w, [], 'button');
        const html = M.preview(w, [1]);
        assert.match(html, /Hola &lt;b&gt;/);
        assert.match(html, /mui-tabs/);
        assert.match(html, /class="mui-button selected"/);
    });
    await check('model: documents it makes are accepted by the compiler (compiler/dashui.py)', () => {
        const d = M.newDocument();
        const w = d.windows[0];
        for (const type of Object.keys(M.TYPES)) {
            const p = M.add(w, [], type);
            const n = M.nodeAt(w, p);
            M.setProp(n, 'name', 'o_' + type);
            for (const e of M.TYPES[type].events) M.setProp(n, e, '5');
            if (M.TYPES[type].group) M.add(w, p, 'text');
        }
        w.menus.push({ title: 'Menú', items: [{ label: 'Salir', key: 'Q', event: 9 }, { separator: true }] });
        const code = execFileSync('python3', ['-c',
            'import sys; from compiler.dashui import generate; print(generate(sys.stdin.read()))'],
            { cwd: repo, input: M.serialize(d) }).toString();
        assert.match(code, /func Principal_create\(\) -> Principal/);
        assert.match(code, /o_tabs = mui_register_begin\("Uno\|Dos"\)/);
        assert.match(code, /mui_on_press\(o_button, 5\)/);
    });
}


// --- "Ver en Amiga" (amigaPreview.js) ----------------------------------------------
async function previewTests() {
    const P = require('../amigaPreview.js');
    await check('preview: program opens the window and waits', () => {
        const prog = P.previewProgram('Principal');
        assert.match(prog, /import "preview.dashui"/);
        assert.match(prog, /v = Principal_create\(\)/);
        assert.match(prog, /mui_window_open\(v.window\)/);
        assert.throws(() => P.previewProgram('mal nombre'), /bad window name/);
    });
    await check('preview: emu_run arguments', () => {
        const a = P.emuArgs('/d', '/t/p.dash', '/t/s.png', { kickstart: '/k.rom', system: '/sys', shotAt: 12 });
        assert.deepStrictEqual(a, ['/d/tools/emu_run.py', '--autoclose', '22', '--timeout', '180',
            '--screenshot', '12', '/t/s.png', '--kickstart', '/k.rom', '--system', '/sys', '/t/p.dash']);
    });
    await check('preview: the program that takes its own picture', () => {
        const prog = P.previewProgram('Principal', true);
        assert.match(prog, /mui_window_open\(v.window\)\n        capturar\(\)\n        mui_app_end\(\)/);
        assert.match(prog, /C:dash_shot 1 DH0:shot.dsh/);
        assert.strictEqual(P.previewMachine('a500'), 'a1200');
        assert.strictEqual(P.previewMachine('rtg'), 'rtg');
    });
    await check('preview: the Amiga that stays on answers in order, and its errors arrive', async () => {
        // a server that speaks tools/emu_preview.py's lines
        const fake = 'const fs = require("fs"); console.log("ready"); let b = "";' +
            'process.stdin.on("data", (d) => { b += d; let i; while ((i = b.indexOf("\\n")) >= 0) { const l = b.slice(0, i).split(" "); b = b.slice(i + 1);' +
            ' if (l[0] === "quit") process.exit(0);' +
            ' if (l[1] === "mal") console.log("error no compila la vista"); else { fs.writeFileSync(l[2], "png " + l[1]); console.log("ok " + l[2]); } } });';
        const server = new P.PreviewServer([process.execPath, '-e', fake]);
        await server.ready;
        const dir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'dash_prev_'));
        const [a, b, c] = await Promise.allSettled([server.show('uno', path.join(dir, 'a.png')),
                                                     server.show('mal', path.join(dir, 'b.png')),
                                                     server.show('dos', path.join(dir, 'c.png'))]);
        assert.strictEqual(fs.readFileSync(a.value, 'utf8'), 'png uno');
        assert.strictEqual(b.status, 'rejected');
        assert.match(b.reason.message, /no compila la vista/);
        assert.strictEqual(fs.readFileSync(c.value, 'utf8'), 'png dos');
        server.stop();
        await new Promise((r) => server.proc.on('exit', r));
        await assert.rejects(server.show('tres', path.join(dir, 'd.png')), /the emulator ended/);
        fs.rmSync(dir, { recursive: true, force: true });
        const broken = new P.PreviewServer([process.execPath, '-e', 'console.log("error no ROM")']);
        await assert.rejects(broken.ready, /no ROM/);
    });
    // The real thing (FS-UAE, about 30 s): only with DASH_PREVIEW_EMU=1
    if (process.env.DASH_PREVIEW_EMU) {
        await check('preview: the Amiga that stays on, twice the same window (the second, not compiled again)', async () => {
            const repo = path.resolve(__dirname, '..', '..', '..');
            const text = fs.readFileSync(path.join(repo, 'tests', 'lib', 'ventana_prueba.dashui'), 'utf8') + ' ';
            const t0 = Date.now();
            const first = await P.preview({ dashDir: repo, dashuiText: text, windowName: 'Prueba', machine: 'a1200' });
            const t1 = Date.now();
            const second = await P.preview({ dashDir: repo, dashuiText: text, windowName: 'Prueba', machine: 'a1200' });
            const t2 = Date.now();
            P.stopServers();
            assert.strictEqual(first.png.slice(1, 4).toString(), 'PNG');
            assert.strictEqual(second.png.slice(1, 4).toString(), 'PNG');
            assert.strictEqual(second.compiled, false);
            assert(t2 - t1 < 8000, `the second took ${t2 - t1} ms (the first ${t1 - t0})`);
        });
        await check('preview: real window in FS-UAE gives a PNG', async () => {
            const repo = path.resolve(__dirname, '..', '..', '..');
            const { png } = await P.runPreview({ dashDir: repo, windowName: 'Prueba',
                dashuiText: fs.readFileSync(path.join(repo, 'tests', 'lib', 'ventana_prueba.dashui'), 'utf8'),
                kickstart: process.env.DASH_KICKSTART, system: process.env.DASH_EMU_SYS_MUI });
            assert.strictEqual(png.slice(1, 4).toString(), 'PNG');
        });
    }
}

// --- extension.js with a fake vscode -------------------------------------------
async function extensionTests() {
    const sent = [];
    const registered = {};
    const settings = { 'dash': { path: '' }, 'dash.emulator': { kickstart: '/roms/ks.rom', system: '', autoclose: 5 } };
    const fakeVscode = {
        workspace: { getConfiguration: (section) => ({ get: (k) => (settings[section] || {})[k] }),
                     onDidChangeTextDocument: () => ({ dispose() {} }),
                     onDidOpenTextDocument: () => ({ dispose() {} }),
                     onDidGrantWorkspaceTrust: () => ({ dispose() {} }), textDocuments: [] },
        window: {
            activeTextEditor: null,
            showWarningMessage: (m) => sent.push('WARN ' + m),
            showErrorMessage: (m) => sent.push('ERR ' + m),
            createTerminal: (opts) => ({ exitStatus: undefined, env: opts.env, show() {}, sendText: (t) => sent.push(t) }),
        },
        commands: { registerCommand: (name, fn) => { registered[name] = fn; return { dispose() {} }; } },
    };
    fakeVscode.window.registerCustomEditorProvider = (viewType) => { registered['editor:' + viewType] = true;
                                                                     return { dispose() {} }; };
    const load = Module._load;
    Module._load = function (request, parent, isMain) {
        if (request === 'vscode') return fakeVscode;
        return load.call(this, request, parent, isMain);
    };
    const ext = require('../extension.js');
    Module._load = load;
    const repo = path.resolve(__dirname, '..', '..', '..');
    const file = path.join(repo, 'examples', 'mui_hola.dash');

    await check('extension: registers its commands', () => {
        ext.activate({ subscriptions: [] });
        assert.deepStrictEqual(Object.keys(registered).sort(),
            ['dash.compile', 'dash.gotoEvent', 'dash.newWindowFile', 'dash.newline', 'dash.restartLanguageServer', 'dash.runInEmulator', 'editor:dash.dashuiEditor']);
    });
    await check('extension: finds the Dash folder from the file', () => assert.strictEqual(ext.findDash(file), repo));
    await check('extension: compile command', () => {
        const c = ext.compileCommand(repo, file);
        assert(c.includes(`'${repo}/dash' '${file}' -o '${repo}/examples/bin/mui_hola'`), c);
    });
    await check('extension: run command with autoclose', () => {
        const c = ext.runCommand(repo, file, 5);
        assert.strictEqual(c, `python3 '${repo}/tools/emu_run.py' --autoclose 5 '${file}'`);
    });
    await check('extension: quotes paths with spaces and quotes', () => {
        const c = ext.runCommand('/a b', "/x/it's.dash", 0);
        assert.strictEqual(c, `python3 '/a b/tools/emu_run.py' '/x/it'\\''s.dash'`);
    });
    await check('extension: compile from the active editor', async () => {
        fakeVscode.window.activeTextEditor = { document: { languageId: 'dash', isDirty: false, fileName: file } };
        await registered['dash.compile']();
        const last = sent[sent.length - 1];
        assert(last.startsWith(`cd '${repo}' && mkdir -p`), last);
    });
    await check('extension: Ver en Amiga without a Dash folder says so', async () => {
        const said = [];
        await ext.showOnAmiga({ fileName: '/', getText: () => '{}' }, 'Principal',
                              { postMessage: (m) => said.push(m) });
        assert.match(said[said.length - 1].error, /dash\.path/);
        assert.strictEqual(said[said.length - 1].busy, false);           // the button is free again
        assert.match(sent[sent.length - 1], /^ERR Ver en Amiga: .*dash\.path/);   // and VS Code says it too
    });
    await check('extension: nothing is compiled in Restricted Mode', async () => {
        fakeVscode.workspace.isTrusted = false;
        fakeVscode.window.activeTextEditor = { document: { languageId: 'dash', isDirty: false, fileName: file } };
        await registered['dash.compile']();
        assert.match(sent[sent.length - 1], /^WARN Carpeta sin confianza/);
        delete fakeVscode.workspace.isTrusted;
    });
    await check('extension: no .dash file open', async () => {
        fakeVscode.window.activeTextEditor = null;
        await registered['dash.runInEmulator']();
        assert.strictEqual(sent[sent.length - 1], 'WARN Abre un fichero .dash');
    });
}

// --- editing: endwise.js, snippets, indentation rules ---------------------------------
async function editingTests() {
    const { needsEnd } = require('../endwise.js');
    const lines = (t) => t.split('\n');
    await check('endwise: a new block gets its end', () => {
        assert.strictEqual(needsEnd(lines('func f(a: Int) -> Int\n    '), 0), true);
        assert.strictEqual(needsEnd(lines('Main\n    if x > 1\n        \nend'), 1), true);
        assert.strictEqual(needsEnd(lines('@native(borrow) func f(x: Int)\n'), 0), true);
        assert.strictEqual(needsEnd(lines('    On Timer 100\n        \n    end'), 0), false);
    });
    await check('endwise: no end where there is one, or none is needed', () => {
        assert.strictEqual(needsEnd(lines('while x\n    x = 1\nend'), 0), false);
        assert.strictEqual(needsEnd(lines('if a\n    b()\nelse\n    c()\nend'), 0), false);   // closed by else...end
        assert.strictEqual(needsEnd(lines('enum E A, B end'), 0), false);                      // one line
        assert.strictEqual(needsEnd(lines('@extern("x.library")\nfunc F(x: Int) -> Int\n'), 1), false);
        assert.strictEqual(needsEnd(lines('x = 1\n'), 0), false);
        assert.strictEqual(needsEnd(lines('else\n'), 0), false);
    });
    await check('outdent: else/elif/end go back to their block', () => {
        const { outdentFor } = require('../endwise.js');
        assert.strictEqual(outdentFor(lines('if a\n    b = 1\n    else'), 2, '    '), '');
        assert.strictEqual(outdentFor(lines('Main\n    if a\n        b()\n        elif c > 1'), 3, '    '), '    ');
        assert.strictEqual(outdentFor(lines('if a\n    while x\n        y()\n    end\n    else'), 4, '    '), '');
        assert.strictEqual(outdentFor(lines('while x\n    end'), 1, '    '), null);        // empty block: same level
        assert.strictEqual(outdentFor(lines('if a\n    b = 1\nelse'), 2, '    '), null);   // already there
        assert.strictEqual(outdentFor(lines('if a\n    b = 1\n    endif = 2'), 2, '    '), null);
    });
    await check('endwise: an inner block before the outer end', () => {
        assert.strictEqual(needsEnd(lines('Main\n    while true\n        \nend'), 1), true);
    });
    const config = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'language-configuration.json'), 'utf8'));
    await check('indentation: opens after a block line, not after a one-line block', () => {
        const inc = new RegExp(config.indentationRules.increaseIndentPattern);
        for (const l of ['func f()', '    if x', 'else', '@native(borrow) func f()', '@c', 'On Close', 'Main'])
            assert(inc.test(l), l);
        for (const l of ['enum E A, B end', 'x = 1', 'endif = 2', '# if x'])
            assert(!inc.test(l), l);
    });
    // every snippet, with its default values, must compile (python3 -m compiler.main, transpile only)
    const snippets = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'snippets', 'dash.json'), 'utf8'));
    const repo = path.resolve(__dirname, '..', '..', '..');
    const os = require('os');
    const { execFileSync } = require('child_process');
    const expand = (body) => body.join('\n').replace(/\$\{\d+:([^}]*)\}/g, '$1').replace(/\$\{\d+\|([^,|]*)[^}]*\}/g, '$1')
        .replace(/\$\{?\d+\}?/g, '').replace(/\t/g, '    ');
    // the snippets that are a part of a program, inside one
    const wrap = {
        if: (s) => `Main\n    condicion = true\n${s}\nend`, 'if else': (s) => `Main\n    condicion = true\n${s}\nend`,
        while: (s) => `Main\n    condicion = false\n${s}\nend`, 'for rango': (s) => `Main\n${s}\nend`,
        'for lista': (s) => `Main\n    lista = [1]\n${s}\nend`, import: null,
        const: (s) => `${s}\nMain\nend`, func: (s) => `${s.replace(/\n    \n/, '\n    return a\n')}\nMain\nend`,
        'func sin tipos': (s) => `${s}\nMain\nend`, struct: (s) => `${s}\nMain\nend`, enum: (s) => `${s}\nMain\nend`,
        '@native': (s) => `${s.replace('\n    \n', '\n    return x;\n')}\nMain\nend`,
        EventLoop: (s) => `Window W\n    title "x"\nend\nMain\n    W.open\n${s}\nend`,
        On: (s) => `Window W\n    title "x"\nend\nMain\n    W.open\n    EventLoop\n${s}\n    end\nend`,
        'Programa MUI con .dashui': null,   // needs the .dashui file
    };
    for (const [name, snip] of Object.entries(snippets)) {
        const w = name in wrap ? wrap[name] : (s) => s;
        if (!w) continue;
        await check(`snippet compiles: ${name}`, () => {
            const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_snip_'));
            const file = path.join(dir, 'snip.dash');
            fs.writeFileSync(file, w(expand(snip.body)) + '\n');
            try {
                execFileSync('python3', ['-m', 'compiler.main', file, '-o', path.join(dir, 'snip.c')],
                             { cwd: repo, stdio: 'pipe' });
            } catch (e) {
                throw new Error(fs.readFileSync(file, 'utf8') + '\n' + String(e.stdout) + String(e.stderr));
            } finally {
                fs.rmSync(dir, { recursive: true, force: true });
            }
        });
    }
}

// --- tasks.js: the commands of the tasks and the problem matcher ------------------------------------
async function taskTests() {
    const { taskCommand } = require('../tasks.js');
    const repo = path.resolve(__dirname, '..', '..', '..');
    await check('tasks: compile, run with --memcheck and with autoclose', () => {
        assert.strictEqual(taskCommand('compile', '/d', '/p/a b.dash'),
                           "mkdir -p '/p/bin' && '/d/dash' '/p/a b.dash' -o '/p/bin/a b'");
        assert.strictEqual(taskCommand('memcheck', '/d', '/p/x.dash', { autoclose: 5 }),
                           "mkdir -p '/p/bin' && DASH_TEST_AUTOCLOSE=5 DASH_PRINT_FLUSH=1 '/d/dash' --memcheck '/p/x.dash' " +
                           "-o '/p/bin/x' && python3 '/d/tools/emu_run.py' --follow --window '/p/bin/x'");
        assert.strictEqual(taskCommand('run', '/d', '/p/x.dash', { machine: 'a500', emulator: 'amiberry', window: false,
                                                                 system: '/s y' }),
                           "mkdir -p '/p/bin' && DASH_PRINT_FLUSH=1 '/d/dash' '/p/x.dash' -o '/p/bin/x' && " +
                           "python3 '/d/tools/emu_run.py' --follow --machine 'a500' --emulator amiberry --system '/s y' '/p/bin/x'");
        assert.throws(() => taskCommand('otra', '/d', '/p/x.dash'));
    });
    await check('tasks: the profile table and the memcheck matcher', () => {
        const { parseProfile } = require('../tasks.js');
        const p = parseProfile('hola\nperfil: 120 muestras (VBlank)\nperfil:  propio   total  llamadas  funcion\n' +
                               'perfil:  62.5%  80.0%         3  suma\nperfil:  10.0%  12.5%        40  Punto.mover\n');
        assert.strictEqual(p.samples, 120);
        assert.deepStrictEqual(p.rows.map((r) => [r.own, r.total, r.calls, r.name]),
                               [[62.5, 80, 3, 'suma'], [10, 12.5, 40, 'Punto.mover']]);
        const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'));
        const mc = pkg.contributes.problemMatchers.find((m) => m.name === 'dash-memcheck');
        const hit = new RegExp(mc.pattern.regexp).exec('memcheck: ERROR campo de nil (en /home/x/prog.dash:15)');
        assert.deepStrictEqual([hit[mc.pattern.message], hit[mc.pattern.file], hit[mc.pattern.line]],
                               ['campo de nil', '/home/x/prog.dash', '15']);
        assert.strictEqual(mc.severity, 'error');
    });
    await check('tasks: the $dash problem matcher reads what the compiler prints', () => {
        const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'));
        const matcher = pkg.contributes.problemMatchers.find((m) => m.name === 'dash');
        const re = new RegExp(matcher.pattern.regexp);
        const { execFileSync } = require('child_process');
        const os = require('os');
        const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_pm_'));
        const file = path.join(dir, 'mal.dash');
        fs.writeFileSync(file, 'Main\n    Print nada\n    x = (1\nend\n');
        let out = '';
        try {
            execFileSync('python3', ['-m', 'compiler.main', file, '-o', path.join(dir, 'mal.c')], { cwd: repo, stdio: 'pipe' });
        } catch (e) {
            out = String(e.stdout) + String(e.stderr);
        }
        fs.rmSync(dir, { recursive: true, force: true });
        const hits = out.split('\n').map((l) => re.exec(l)).filter(Boolean);
        assert(hits.length >= 1, out);
        const [, f, line, col, severity] = hits[0];
        assert.strictEqual(f, file);
        assert.strictEqual(severity, 'Error');
        assert(Number(line) > 0 && Number(col) > 0);
    });
}

// --- debugProxy.js: Dash expressions for gdb ---------------------------------------------------------
async function debugTests() {
    const { dashToC, logMessageToC } = require('../debugProxy.js');
    await check('debugger: Dash expressions become C for gdb', () => {
        const cases = [
            ['p.x + 1', 'p->x + 1'],
            ['self.pos.x', 'self->pos->x'],
            ['l.length', '$len(l)'],
            ['p.items.length > 2', '$len(p->items) > 2'],
            ['l[i + 1]', '$at(l, i + 1)'],
            ['d["clave"]', '$at(d, "clave")'],
            ['p.vecinos[0].x', '$at(p->vecinos, 0)->x'],
            ['a and not b or c == nil', 'a && !b || c == 0'],
            ['activo == true', 'activo == 1'],
            ['c == Color.ROJO', 'c == Color_ROJO'],
            ['x * 1.5', 'x * 1.5'],
            ['s == "a.b and c"', 's == "a.b and c"'],
            ['p->x', 'p->x'],
        ];
        for (const [dash, c] of cases) assert.strictEqual(dashToC(dash), c, dash);
        assert.strictEqual(logMessageToC('vuelta {i}, punto {p.x}'), 'vuelta {i}, punto {p->x}');
    });
}

(async () => {
    await grammarTests();
    await debugTests();
    await taskTests();
    await editingTests();
    await modelTests();
    await require("./webview.js").webviewTests(check, assert);
    await previewTests();
    await extensionTests();
    console.log(failures ? `${failures} test(s) failed` : 'all tests passed');
    process.exit(failures ? 1 : 0);
})();
