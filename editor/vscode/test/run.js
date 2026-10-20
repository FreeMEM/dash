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
    // The real thing (FS-UAE, about 30 s): only with DASH_PREVIEW_EMU=1
    if (process.env.DASH_PREVIEW_EMU) {
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
        workspace: { getConfiguration: (section) => ({ get: (k) => (settings[section] || {})[k] }) },
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
            ['dash.compile', 'dash.newWindowFile', 'dash.runInEmulator', 'editor:dash.dashuiEditor']);
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

(async () => {
    await grammarTests();
    await modelTests();
    await previewTests();
    await extensionTests();
    console.log(failures ? `${failures} test(s) failed` : 'all tests passed');
    process.exit(failures ? 1 : 0);
})();
