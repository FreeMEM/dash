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

    await check('model: names that are words of the language are refused, as the compiler does (v14)', () => {
        const { execFileSync } = require('child_process');
        const repo = path.resolve(__dirname, '..', '..', '..');
        const py = JSON.parse(execFileSync('python3', ['-c', 'import json; from compiler.dashui import reserved; ' +
                                                       'print(json.dumps(sorted(reserved())))'], { cwd: repo, encoding: 'utf8' }));
        assert.deepStrictEqual([...M.RESERVED].sort(), py);
        const node = { type: 'button' };
        assert(/palabra del lenguaje/.test(M.setProp(node, 'name', 'end')));
        assert(/sin tilde/.test(M.setProp(node, 'name', 'botón')));
        assert.strictEqual(M.setProp(node, 'name', 'Close'), null);          // (only after On)
        const L = require('../dashuiLinks.js');
        const text = JSON.stringify({ dashui: 1, windows: [{ name: 'while', title: 't', id: 1, root: { type: 'vgroup',
            children: [{ type: 'button', name: 'end', label: 'A' }] } }] });
        const msgs = L.problems(text).map((p) => p.message).join(' | ');
        assert(/ventana no válido: "while"/.test(msgs) && /nombre no válido: end/.test(msgs), msgs);
        const own = M.check(M.parse(JSON.stringify({ dashui: 1, windows: [{ name: 'V', title: 't', id: 1, root: { type: 'vgroup',
            children: [{ type: 'button', name: 'botón', label: 'A', event: 'uno' }] } }] }))).join(' | ');
        assert(/nombre no válido botón/.test(own) && /event de botón no es un número/.test(own), own);
    });
    await check('model: check() finds what the compiler refuses: window names twice, #{ in texts; no false repeats', () => {
        const d = M.newDocument();
        d.windows.push(M.newWindow('Principal'));
        assert.ok(M.check(d).some((p) => p.includes('repetido Principal')));
        const d2 = M.newDocument(), w = d2.windows[0];
        M.add(w, [], 'button'); M.setProp(w.root.children[0], 'name', 'constructor');
        M.add(w, [], 'label'); M.setProp(w.root.children[1], 'text', 'Hola #{x}');
        const p = M.check(d2);
        assert.ok(!p.some((x) => x.includes('repetido constructor')), p.join('; '));
        assert.ok(p.some((x) => x.includes('#{')), p.join('; '));
    });
    await check('model: an empty number is refused (not 0); a canvas with weight keeps its minimum size', () => {
        const n = M.newNode('slider');
        assert.ok(M.setProp(n, 'max', ''));
        assert.strictEqual(n.max, 100);
        const w = M.newWindow('V');
        M.add(w, [], 'canvas');
        w.root.children[0].weight = 200;
        const html = M.preview(w, null).match(/<div class="mui-canvas[^>]*>/)[0];
        assert.strictEqual((html.match(/style=/g) || []).length, 1);
        assert.match(html, /min-width:64px.*flex-grow:2/);
    });
    await check('model: check() wants whole numbers in the window id and close and in menu events, as the compiler', () => {
        const d = M.newDocument();
        d.windows[0].id = 1.5;
        d.windows[0].menus = [{ title: 'M', items: [{ label: 'a', event: 2.5 }, { separator: true }] }];
        const p = M.check(d);
        assert.ok(p.some((x) => x.includes('id de la ventana')), p.join('; '));
        assert.ok(p.some((x) => x.includes('evento de la opción a')), p.join('; '));
    });
    await check('model: check() takes menus with marks, submenus and names, as the compiler (Lorraine D47)', () => {
        const d = M.newDocument(), w = d.windows[0];
        w.menus = [{ title: 'Ver', name: 'ver', items: [{ label: 'a', event: 2, check: true, checked: true, name: 'marca' },
            { label: 'Zoom', name: 'zoom', submenu: [{ label: '200', event: 3, name: 'doble' }, { separator: true }] }] }];
        assert.deepStrictEqual(M.check(d), []);
        M.add(w, [], 'label');
        w.root.children[0].name = 'marca';
        w.menus[0].items[1].submenu[0].submenu = [];
        w.menus[0].items.push({ label: 'b', checked: false });
        const p = M.check(d).join('; ');
        for (const s of ['repetido marca', 'está dentro de otro', 'checked sin']) assert.ok(p.includes(s), s + ' in ' + p);
    });
    await check('model: check() takes context menus by name, as the compiler (Lorraine D15)', () => {
        const d = M.newDocument(), w = d.windows[0];
        w.context_menus = [{ name: 'celdas', title: 'Celdas', items: [{ label: 'Copiar', event: 41 }, { separator: true }] }];
        M.add(w, [], 'canvas');
        w.root.children[0].context_menu = 'celdas';
        M.add(w, [], 'label');
        w.root.children[1].context_menu = '';
        assert.deepStrictEqual(M.check(d), []);
        w.root.children[1].context_menu = 'filas';
        w.context_menus.push({ title: 'Sin nombre', items: [] });
        w.context_menus[0].items.push({ label: 'x', event: 1.5 });
        const p = M.check(d).join('; ');
        for (const s of ['menú contextual filas', 'no tiene nombre', 'evento de la opción x']) assert.ok(p.includes(s), s + ' in ' + p);
    });
    await check('model: check() finds the odd documents the compiler refuses (children of a button, tr, size, lists)', () => {
        const d = M.newDocument(), w = d.windows[0];
        w.size = [50];
        w.root.children = [{ type: 'button', label: 'a', children: [{ type: 'text' }] }, { type: 'label', text: 'x', tr: 'uno' },
                           { type: 'frame', title: ['a'], children: [] }, { label: 'sin tipo' }];
        const p = M.check(d).join('; ');
        for (const s of ['size es', 'no es un grupo', 'tr de label', 'title de frame', 'objeto sin tipo']) assert.ok(p.includes(s), s + ' in ' + p);
        const ok = M.newDocument();
        M.add(ok.windows[0], [], 'label');
        ok.windows[0].root.children[0].tr = { text: 3 };
        assert.deepStrictEqual(M.check(ok), []);
    });
    await check('problems: a new menu option (event 0) and an object called constructor are not errors', () => {
        const L = require('../dashuiLinks.js');
        const d = M.newDocument();
        d.windows[0].menus = [{ title: 'Menú', items: [{ label: 'Opción', key: '', event: 0 }] }];
        M.add(d.windows[0], [], 'button');
        d.windows[0].root.children[0].name = 'constructor';
        assert.deepStrictEqual(L.problems(M.serialize(d)).map((p) => p.message), []);
    });
    await check('problems: also what only the editor checked (#{ in a text, size, children of a button)', () => {
        const L = require('../dashuiLinks.js');
        const d = M.newDocument();
        d.windows[0].size = [50];
        d.windows[0].root.children = [{ type: 'label', text: 'Hola #{x}' }, { type: 'button', label: 'a', children: [{ type: 'text' }] }];
        const p = L.problems(M.serialize(d)).map((x) => x.message).join('; ');
        for (const k of ['#{', 'size es', 'no es un grupo']) assert.ok(p.includes(k), k + ' in ' + p);
    });
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
        // a bare number only against the variable of mui_wait_event (dashweb: "elif k == 1" is not event 1)
        assert.deepStrictEqual(L.handlers(dash.replace('Print "a == 2"', 'k = 7\n            if k == 7\n            end'), 7)
            .map((h) => h.line), [10]);
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
        assert.match(code, /mui_on_press\(_ui_o_button, 5\)/);   // D72: the .dashui objects go as _ui_<name>
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
    await check('new project: its files, and its program compiles', async () => {
        const N = require('../newProject.js');
        assert.strictEqual(N.cleanName('mi programa!'), 'mi_programa');
        assert.strictEqual(N.cleanName('3d'), 'Programa_3d');
        assert.strictEqual(N.cleanName('Mi Juego Ñandú'), 'Mi_Juego_Nandu');   // accents off, not the letter
        assert.strictEqual(N.cleanName('Árbol'), 'Arbol');
        const { name, files } = N.projectFiles('hola', '/x/dash');
        assert.strictEqual(name, 'hola');
        assert.deepStrictEqual(Object.keys(files).sort(),
            ['.gitignore', '.vscode/launch.json', '.vscode/settings.json', 'hola.dash', 'ventana.dashui']);
        assert.deepStrictEqual(JSON.parse(files['.vscode/settings.json']), { 'dash.path': '/x/dash' });
        assert.deepStrictEqual(require('../dashuiLinks.js').problems(files['ventana.dashui']), []);
        assert.strictEqual(JSON.parse(files['.vscode/launch.json']).configurations[0].program, '${workspaceFolder}/hola.dash');
        const repo = path.resolve(__dirname, '..', '..', '..');
        const dir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'dash_proj_'));
        try {
            const prog = N.writeProject(dir, 'Hola Mundo');
            assert.throws(() => N.writeProject(dir, 'Hola Mundo'), /ya existe/);
            if (fs.existsSync('/opt/amiga/bin/m68k-amigaos-gcc') && fs.existsSync(path.join(require('os').homedir(), '.cache', 'dash-mui', 'x'))) {
                const out = require('child_process').spawnSync(path.join(repo, 'dash'), [prog, '-o', path.join(dir, 'prog')],
                                                               { cwd: repo, encoding: 'utf8' });
                assert.strictEqual(out.status, 0, out.stdout + out.stderr);
            }
        } finally {
            fs.rmSync(dir, { recursive: true, force: true });
        }
    });
    await check('new project: a game (V6): player, tileset, level with collisions and its start, and it compiles', () => {
        const N = require('../newProject.js');
        const I = require('../media/iff.js');
        const { name, files } = N.projectFiles('Salta', null, 'game');
        assert.strictEqual(name, 'Salta');
        assert.deepStrictEqual(Object.keys(files).sort(),
            ['.gitignore', '.vscode/launch.json', 'Salta.dash', 'jugador.iff', 'nivel.fmap', 'tiles.iff']);
        const p = I.readIlbm(files['jugador.iff']), t = I.readIlbm(files['tiles.iff']), m = I.readFmap(files['nivel.fmap']);
        assert.deepStrictEqual([p.hardware, p.width, p.height, p.planes, p.frames.length], [true, 16, 16, 2, 2]);
        assert.deepStrictEqual([t.width, t.height, t.frames.length], [16, 16, 3]);
        assert.deepStrictEqual([m.width, m.height, m.tile, m.tileset, m.layers.length, m.layers[1].type], [20, 16, 16, 'tiles.iff', 2, 1]);
        assert.strictEqual(m.layers[1].cells[14 * 20 + 2], 1);                 // the ground under the start, solid
        assert.deepStrictEqual(m.objects.map((o) => [o.kind, o.x, o.y]), [['jugador', 32, 208]]);
        assert.match(files['Salta.dash'], /tilemap_object_find\(0, "jugador", 0\)/);
        const repo = path.resolve(__dirname, '..', '..', '..');
        if (!fs.existsSync(path.join(repo, 'dashc', 'dashc'))) return;
        const dir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'dash_juego_'));
        try {
            const prog = N.writeProject(dir, 'Salta', null, 'game');
            const out = require('child_process').spawnSync(path.join(repo, 'dash'), [prog, '-o', path.join(dir, 'prog')], { cwd: repo, encoding: 'utf8' });
            assert.strictEqual(out.status, 0, out.stdout + out.stderr);
        } finally {
            fs.rmSync(dir, { recursive: true, force: true });
        }
    });
    await check('video: subtitles and the video of pictures at their times (video/rodaje.js)', () => {
        const V = require('../video/rodaje.js');
        assert.strictEqual(V.srtTime(3723456), '01:02:03,456');
        assert.strictEqual(V.srt([{ start: 0, end: 1500, text: 'Hola' }, { start: 2000, end: 2500, text: 'Dos' }]),
                           '1\n00:00:00,000 --> 00:00:01,500\nHola\n\n2\n00:00:02,000 --> 00:00:02,500\nDos\n');
        if (require('child_process').spawnSync('ffmpeg', ['-version']).status !== 0) return;
        const dir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'dash_video_'));
        try {
            // three pictures of 64 x 36 (two colours), at 0, 1 and 2.5 s; the end at 3 s: a video of 3 s
            const shots = [];
            for (const [i, colour, t] of [[0, 'red', 0], [1, 'blue', 1000], [2, 'red', 2500]]) {
                const file = path.join(dir, `f${i}.png`);
                require('child_process').spawnSync('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'lavfi', '-i',
                    `color=c=${colour}:s=64x36`, '-frames:v', '1', file]);
                shots.push({ file, t });
            }
            const out = V.montar(shots, 3000, [{ start: 500, end: 2000, text: 'Hola' }], path.join(dir, 'toma'), dir);
            const probe = require('child_process').spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration',
                                                                         '-of', 'csv=p=0', out.mp4], { encoding: 'utf8' });
            assert(Math.abs(Number(probe.stdout) - 3) < 0.2, 'duration ' + probe.stdout);
            assert(fs.existsSync(out.sub) && fs.existsSync(out.srt));
        } finally {
            fs.rmSync(dir, { recursive: true, force: true });
        }
    });
    await check('video: cards and chapters joined, each subtitle at its time (video/grabar.js)', () => {
        if (require('child_process').spawnSync('ffmpeg', ['-version']).status !== 0) return;
        const G = require('../video/grabar.js');
        assert.strictEqual(G.dt("a: 50% d'x"), 'a\\: 50\\% d\u2019x');
        const dir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'dash_video_'));
        try {
            const a = G.tarjeta(path.join(dir, 'a.mp4'), 'Uno: título', 'línea', 1);
            const b = Object.assign(G.tarjeta(path.join(dir, 'b.mp4'), 'Dos', null, 2), { subs: [{ start: 500, end: 9000, text: 'Hola' }] });
            const res = G.juntar([a, b], path.join(dir, 'todo'));
            assert.deepStrictEqual(res.subs, [{ start: 1500, end: 3000, text: 'Hola' }]);   // after the first card, cut at the end
            const probe = require('child_process').spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration',
                                                                         '-of', 'csv=p=0', res.sub], { encoding: 'utf8' });
            assert(Math.abs(Number(probe.stdout) - 3) < 0.2, 'duration ' + probe.stdout);
        } finally {
            fs.rmSync(dir, { recursive: true, force: true });
        }
    });
    await check('language: a quote typed over a selection replaces it (the hole of a parameter)', () => {
        // with " in surroundingPairs, mui_set_text(obj, text) with "text" selected and "Otra vez" typed gave
        // "Otra vez"" (the quote around the selection is not overtyped at the end): tutorial, chapter 2
        const conf = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'language-configuration.json'), 'utf8'));
        assert(!conf.surroundingPairs.some((pair) => pair[0] === '"'));
        assert(conf.autoClosingPairs.some((pair) => pair.open === '"'));
    });
    await check('preview: the program that takes its own picture', () => {
        const prog = P.previewProgram('Principal', true);
        assert.match(prog, /mui_window_open\(v.window\)\n        time_delay\(25\).*\n        run_command\("C:dash_shot 1 DH0:shot.dsh"\).*\n        mui_app_end\(\)/);
        assert.doesNotMatch(prog, /@native|@header/);    // (without C: Dash 2.0 compiles it)
        assert.match(prog, /C:dash_shot 1 DH0:shot.dsh/);
        assert.strictEqual(P.previewMachine('a500'), 'a1200');
        assert.strictEqual(P.previewMachine('rtg'), 'rtg');
    });
    await check('preview: the images a window names go with it (PROGDIR: from the folder or the one above)', () => {
        const base = fs.mkdtempSync(path.join(require('os').tmpdir(), 'dash_win_'));
        fs.mkdirSync(path.join(base, 'src')); fs.mkdirSync(path.join(base, 'iconos'));
        fs.writeFileSync(path.join(base, 'iconos', 'a.iff'), 'A');
        fs.writeFileSync(path.join(base, 'src', 'b.iff'), 'B');
        const text = JSON.stringify({ dashui: 1, windows: [{ name: 'W', root: { type: 'vgroup', children: [
            { type: 'image_button', file: 'PROGDIR:iconos/a.iff' }, { type: 'image', file: 'b.iff' },
            { type: 'image', file: 'SYS:Prefs/x.iff' }, { type: 'image', file: 'PROGDIR:no.iff' }] } }] });
        const dir = P.windowFiles(text, path.join(base, 'src'));
        try {
            assert.strictEqual(fs.readFileSync(path.join(dir, 'iconos', 'a.iff'), 'utf8'), 'A');
            assert.strictEqual(fs.readFileSync(path.join(dir, 'b.iff'), 'utf8'), 'B');
            assert.deepStrictEqual(fs.readdirSync(dir).sort(), ['b.iff', 'iconos']);
            assert.strictEqual(P.windowFiles(JSON.stringify({ dashui: 1, windows: [] }), base), null);
        } finally {
            fs.rmSync(dir, { recursive: true, force: true });
            fs.rmSync(base, { recursive: true, force: true });
        }
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
        EventEmitter: class { constructor() { this.l = []; this.event = (f) => this.l.push(f); } fire(m) { for (const f of this.l) f(m); } dispose() {} },
    };
    fakeVscode.window.registerCustomEditorProvider = (viewType) => { registered['editor:' + viewType] = true;
                                                                     return { dispose() {} }; };
    const load = Module._load;
    let fakePreview = null;          // (Ver en Amiga's queue: the emulator's work, by hand)
    Module._load = function (request, parent, isMain) {
        if (request === 'vscode') return fakeVscode;
        if (request === './amigaPreview') {
            const real = load.call(this, request, parent, isMain);
            return Object.assign({}, real, { preview: (o) => (fakePreview ? fakePreview(o) : real.preview(o)) });
        }
        return load.call(this, request, parent, isMain);
    };
    const ext = require('../extension.js');
    Module._load = load;
    const repo = path.resolve(__dirname, '..', '..', '..');
    const file = path.join(repo, 'examples', 'mui_hola.dash');

    await check('extension: registers its commands', () => {
        ext.activate({ subscriptions: [] });
        assert.deepStrictEqual(Object.keys(registered).sort(),
            ['dash.choosePath', 'dash.compile', 'dash.gotoEvent', 'dash.newGraphic', 'dash.newProject', 'dash.newWindowFile', 'dash.newline', 'dash.restartLanguageServer', 'dash.runInEmulator', 'editor:dash.dashuiEditor', 'editor:dash.mapEditor', 'editor:dash.spriteEditor']);
    });
    await check('extension: finds the Dash folder from the file', () => assert.strictEqual(ext.findDash(file), repo));
    await check('extension: a new sprite, BOB or map (Amiga-B in Forja) is written and opened in its editor', async () => {
        const I = require('../media/iff.js');
        const written = {}, opened = [];
        fakeVscode.workspace.fs = { writeFile: async (u, b) => { written[u.fsPath] = b; } };
        fakeVscode.commands.executeCommand = async (...a) => { opened.push([a[0], a[1].fsPath, a[2]]); };
        const u = (p) => ({ fsPath: p });
        await ext.newGraphic(null, 'sprite', u('/p/s.iff'));
        await ext.newGraphic(null, 'attached', u('/p/a.iff'));
        await ext.newGraphic(null, 'bob', u('/p/b.iff'));
        await ext.newGraphic(null, 'map', u('/p/m.fmap'));
        const s = I.readIlbm(written['/p/s.iff']), a = I.readIlbm(written['/p/a.iff']), b = I.readIlbm(written['/p/b.iff']);
        assert.deepStrictEqual([s.width, s.height, s.planes, s.hardware], [16, 16, 2, true]);
        assert.deepStrictEqual([a.width, a.planes, a.hardware], [16, 4, true]);
        assert.deepStrictEqual([b.width, b.height, b.planes, b.hardware], [32, 32, 4, false]);
        const m = I.readFmap(written['/p/m.fmap']);
        assert.deepStrictEqual([m.width, m.height, m.tile, m.layers.length, m.layers[0].name], [64, 32, 16, 1, 'fondo']);
        assert.deepStrictEqual(opened.map((o) => o[2]), ['dash.spriteEditor', 'dash.spriteEditor', 'dash.spriteEditor', 'dash.mapEditor']);
        assert(opened.every((o) => o[0] === 'vscode.openWith'));
    });
    await check('extension: compile command', () => {
        const c = ext.compileCommand(repo, file);
        assert(c.includes(`'${repo}/dash' '${file}' -o '${repo}/examples/bin/mui_hola'`), c);
        const o = ext.compileCommand(repo, file, '/tmp/exes');
        assert(o.startsWith("mkdir -p '/tmp/exes' && ") && o.endsWith(" -o '/tmp/exes/mui_hola'"), o);
    });
    await check('extension: run command with autoclose', () => {
        const c = ext.runCommand(repo, file, 5);
        assert.strictEqual(c, `python3 '${repo}/tools/emu_run.py' --dash2 --autoclose 5 --cd '${path.dirname(file)}' '${file}'`);
    });
    await check('extension: quotes paths with spaces and quotes', () => {
        const c = ext.runCommand('/a b', "/x/it's.dash", 0);
        assert.strictEqual(c, `python3 '/a b/tools/emu_run.py' --dash2 --cd '/x' '/x/it'\\''s.dash'`);
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
    await check('extension: "al cambiar" waits its turn, the newest only, and says nothing in windows', async () => {
        const runs = [];
        fakePreview = (o) => new Promise((resolve, reject) => runs.push({ o, resolve, reject }));
        const doc = { fileName: file, getText: () => '{}' };
        const views = [[], [], []].map((said) => ({ said, postMessage: (m) => said.push(m) }));
        const before = sent.length;
        const first = ext.showOnAmiga(doc, 'A', views[0], true);
        await new Promise((r) => setTimeout(r, 10));
        ext.showOnAmiga(doc, 'B', views[1], true);                // while A runs: it waits
        assert.strictEqual(views[1].said.pop().busy, true);
        ext.showOnAmiga(doc, 'C', views[2], true);                // a newer one: B is let go, C waits
        assert.strictEqual(views[1].said.pop().busy, false);
        assert.strictEqual(views[2].said.pop().status, 'En cola…');
        assert.strictEqual(runs.length, 1);
        runs[0].resolve({ png: Buffer.from('x') });
        await first;
        assert.match(views[0].said.pop().src, /^data:image\/png/);
        await new Promise((r) => setTimeout(r, 20));
        assert.strictEqual(runs.length, 2);
        assert.strictEqual(runs[1].o.windowName, 'C');
        runs[1].reject(new Error('sin emulador'));
        await new Promise((r) => setTimeout(r, 20));
        assert.match(views[2].said.pop().error, /sin emulador/);
        assert.strictEqual(sent.length, before);                  // no error window for the automatic ones
        fakePreview = null;
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
    await check('missing tools: what and how to get it, in words (v12)', () => {
        const { missing } = require('../missing.js');
        const cases = [
            ['Error: m68k-amigaos-gcc not found in /opt/amiga/bin/', /compilador de Amiga/],
            ['fs-uae not found', /emulador FS-UAE/],
            ['amiberry not found', /emulador Amiberry/],
            ['bgdbserver not found: /x (tools/get_bgdbserver.sh, or $DASH_BGDBSERVER)', /get_bgdbserver\.sh/],
            ['Error: MUI SDK not found in /x: run tools/get_mui_sdk.sh', /get_mui_sdk\.sh/],
            ['--machine a1200-32 needs $DASH_EMU_SYS_32_MUI (Workbench files with MUI) or --system', /muiSystem32/],
            ['--machine a1200 needs $DASH_EMU_SYS_MUI (Workbench files with MUI) or --system', /"dash\.emulator\.muiSystem"/],
            ['--machine a500 needs $DASH_KICKSTART_A500 (or --kickstart)', /kickstartA500/],
            ['--machine a1200-32 needs $DASH_KICKSTART_32 (or --kickstart)', /kickstart32/],
            ['dash: falta el compilador; constrúyelo con: make -C dashc', /make -C dashc/],
        ];
        for (const [text, want] of cases) assert(want.test(missing(text) || ''), text + ' -> ' + missing(text));
        assert.strictEqual(missing('=== x: RC=0\nhola'), null);
    });

    const { taskCommand } = require('../tasks.js');
    const repo = path.resolve(__dirname, '..', '..', '..');
    await check('tasks: without a folder, its own terminal stays with the output until a key (v11)', async () => {
        const { shellTerminal } = require('../tasks.js');
        const vscode = { EventEmitter: class { constructor() { this.fs = []; this.event = (f) => this.fs.push(f); }
                                                fire(v) { for (const f of this.fs) f(v); } } };
        for (const keepOpen of [false, true]) {
            let text = '', closed = null, got = null;
            const t = shellTerminal(vscode, 'echo hola', '/', {}, (out, code) => { got = [out, code]; }, 'Compilar: x', keepOpen);
            t.onDidWrite((w) => { text += w; });
            t.onDidClose((c) => { closed = c; });
            t.open();
            for (let i = 0; i < 50 && !got; i++) await new Promise((r) => setTimeout(r, 40));
            await new Promise((r) => setTimeout(r, 50));
            assert.deepStrictEqual(got, ['hola\n', 0]);
            if (!keepOpen) { assert.strictEqual(closed, 0); continue; }
            assert.strictEqual(closed, null, 'closed by itself');
            assert(/hola[\s\S]*Pulsa una tecla para cerrar/.test(text), text);
            t.handleInput('x');
            assert.strictEqual(closed, 0);
        }
    });
    await check('tasks: compile, run with --memcheck and with autoclose', () => {
        assert.strictEqual(taskCommand('compile', '/d', '/p/a b.dash'),
                           "mkdir -p '/p/bin' && DASH_FALLBACK_DASH1=1 '/d/dash' -q '/p/a b.dash' -o '/p/bin/a b'");
        assert.strictEqual(taskCommand('memcheck', '/d', '/p/x.dash', { autoclose: 5 }),
                           "mkdir -p '/p/bin' && DASH_FALLBACK_DASH1=1 DASH_TEST_AUTOCLOSE=5 DASH_PRINT_FLUSH=1 '/d/dash' -q --memcheck '/p/x.dash' " +
                           "-o '/p/bin/x' && python3 '/d/tools/emu_run.py' --follow --cd '/p' --window '/p/bin/x'");
        assert.strictEqual(taskCommand('run', '/d', '/p/x.dash', { machine: 'a500', emulator: 'amiberry', window: false,
                                                                 system: '/s y' }),
                           "mkdir -p '/p/bin' && DASH_FALLBACK_DASH1=1 DASH_PRINT_FLUSH=1 '/d/dash' -q '/p/x.dash' -o '/p/bin/x' && " +
                           "python3 '/d/tools/emu_run.py' --follow --cd '/p' --machine 'a500' --emulator amiberry --system '/s y' '/p/bin/x'");
        assert.throws(() => taskCommand('otra', '/d', '/p/x.dash'));
        // dash.outputFolder: absolute, relative to the .dash or ~/...
        assert.strictEqual(taskCommand('compile', '/d', '/p/x.dash', { outputFolder: '/tmp/exes' }),
                           "mkdir -p '/tmp/exes' && DASH_FALLBACK_DASH1=1 '/d/dash' -q '/p/x.dash' -o '/tmp/exes/x'");
        const { outputFile } = require('../tasks.js');
        assert.strictEqual(outputFile('/p/src/x.dash', '../build'), '/p/build/x');
        assert.strictEqual(outputFile('/p/x.dash', '  '), '/p/bin/x');
        assert.strictEqual(outputFile('/p/x.dash', '~/amiga', '.debug'), require('path').join(require('os').homedir(), 'amiga', 'x.debug'));
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
    await check('debugger: bgdbserver listening, seen with netstat on macOS and Windows (no /proc; 0.3.1)', () => {
        const { netstatListening } = require('../debug.js');
        const mac = 'Active Internet connections (including servers)\n' +
            'Proto Recv-Q Send-Q  Local Address          Foreign Address        (state)\n' +
            'tcp4       0      0  127.0.0.1.52011        127.0.0.1.2345         ESTABLISHED\n' +
            'tcp4       0      0  *.2345                 *.*                    LISTEN\n' +
            'tcp6       0      0  *.12345                *.*                    LISTEN\n';
        const win = '\r\nActive Connections\r\n\r\n  Proto  Local Address          Foreign Address        State\r\n' +
            '  TCP    0.0.0.0:2345           0.0.0.0:0              LISTENING\r\n' +
            '  TCP    127.0.0.1:50000        127.0.0.1:61000        ESTABLISHED\r\n';
        assert.strictEqual(netstatListening(mac, 2345), true);
        assert.strictEqual(netstatListening(mac, 52011), false);      // connected, not listening
        assert.strictEqual(netstatListening(mac, 345), false);        // a port that ends the same
        assert.strictEqual(netstatListening(win, 2345), true);
        assert.strictEqual(netstatListening(win, 61000), false);      // the remote end
        assert.strictEqual(netstatListening(win, 50000), false);
    });
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
    });    const { makeProxy } = require('../debugProxy.js');
    await check('debugger: no Ada/C++ exception filters, start-up noise or registers from gdb', async () => {
        const listeners = [];
        const vscode = { EventEmitter: class { constructor() { this.event = (f) => listeners.push(f); }
                                                fire(m) { for (const f of listeners) f(m); } dispose() {} } };
        const proxy = makeProxy(vscode, process.execPath, [require('path').join(__dirname, 'fake-gdb.js')]);
        const got = [];
        proxy.onDidSendMessage((m) => got.push(m));
        proxy.handleMessage({ seq: 1, type: 'request', command: 'initialize', arguments: {} });
        proxy.handleMessage({ seq: 2, type: 'request', command: 'scopes', arguments: { frameId: 1 } });
        const later = () => got.some((m) => m.event === 'output' && /later/.test(m.body.output));
        for (let i = 0; i < 75 && !(later() && got.some((m) => m.command === 'scopes')); i++) await new Promise((r) => setTimeout(r, 40));
        proxy.dispose();
        const init = got.find((m) => m.command === 'initialize');
        assert(init && init.body.supportsConfigurationDoneRequest && !init.body.exceptionBreakpointFilters, JSON.stringify(init));
        const texts = got.filter((m) => m.event === 'output').map((m) => m.body.output);
        assert.deepStrictEqual(texts, ['No symbol table is loaded.  (later: shown)\n']);
        const scopes = got.find((m) => m.command === 'scopes');
        assert.deepStrictEqual(scopes.body.scopes.map((s) => s.name), ['Locals', 'Globals']);
    });
    await check('debugger: what the program wrote just before its end comes before the session ends (v15)', async () => {
        const listeners = [];
        const vscode = { EventEmitter: class { constructor() { this.event = (f) => listeners.push(f); }
                                                fire(m) { for (const f of listeners) f(m); } dispose() {} } };
        const proxy = makeProxy(vscode, process.execPath, [require('path').join(__dirname, 'fake-gdb.js')]);
        const got = [];
        proxy.onDidSendMessage((m) => got.push(m.event || m.command));
        proxy.handleMessage({ seq: 1, type: 'request', command: 'next', arguments: { threadId: 1 } });
        await new Promise((r) => setTimeout(r, 400));
        proxy.output('adiós\n');                     // the emulator's last output, after gdb said the end
        for (let i = 0; i < 60 && !got.includes('terminated'); i++) await new Promise((r) => setTimeout(r, 50));
        proxy.dispose();
        assert(got.indexOf('output') >= 0 && got.indexOf('output') < got.indexOf('terminated'), JSON.stringify(got));
    });
    await check('debugger: without gdb it says so and ends (before: an uncaught exception)', async () => {
        const listeners = [];
        const vscode = { EventEmitter: class { constructor() { this.event = (f) => listeners.push(f); }
                                                fire(m) { for (const f of listeners) f(m); } dispose() {} } };
        const proxy = makeProxy(vscode, '/no/esta/m68k-amigaos-gdb', ['-i=dap']);
        const got = [];
        proxy.onDidSendMessage((m) => got.push(m));
        for (let i = 0; i < 50 && !got.some((m) => m.event === 'terminated'); i++) await new Promise((r) => setTimeout(r, 20));
        assert(got.some((m) => m.event === 'output' && /No encuentro gdb/.test(m.body.output)), JSON.stringify(got));
        assert(got.some((m) => m.event === 'terminated'));
    });
    await check('debugger: the stop of attaching is not seen; it goes on after the breakpoints, unless stopOnEntry', async () => {
        const wait = (ms) => new Promise((r) => setTimeout(r, ms));
        for (const stopOnEntry of [false, true]) {
            const listeners = [];
            const vscode = { EventEmitter: class { constructor() { this.event = (f) => listeners.push(f); }
                                                    fire(m) { for (const f of listeners) f(m); } dispose() {} } };
            const proxy = makeProxy(vscode, process.execPath, [require('path').join(__dirname, 'fake-gdb.js')]);
            const got = [];
            proxy.onDidSendMessage((m) => got.push(m));
            proxy.handleMessage({ seq: 1, type: 'request', command: 'attach', arguments: { program: 'p', stopOnEntry } });
            await wait(300);
            const continued = () => got.some((m) => m.event === 'output' && m.body.output === 'continue 7\n');
            assert(!continued(), 'continue before configurationDone');
            proxy.handleMessage({ seq: 2, type: 'request', command: 'configurationDone', arguments: {} });
            for (let i = 0; i < 50 && !continued() && !got.some((m) => m.command === 'configurationDone'); i++) await wait(40);
            await wait(300);
            proxy.dispose();
            const stops = got.filter((m) => m.event === 'stopped');
            if (stopOnEntry) {
                assert(!continued() && stops.length === 1 && stops[0].body.reason === 'attach', JSON.stringify(got));
            } else {
                assert(continued() && stops.length === 0, JSON.stringify(got));
            }
        }
    });
}

// --- dashDebug.js: the debugger of Dash 2.0 (dbgserver on the Amiga) ------------------------------------------------
async function dashcDebugTests() {
    const dd = require('../dashDebug.js');
    const { emulatorArgs, engineOf } = require('../debug.js');
    const net = require('net');
    await check('dashc debugger: the lines of dbgserver (tabs, escapes, UTF-8 names and Latin-1 texts)', () => {
        assert.deepStrictEqual(dd.parseLine(Buffer.from('var\tp\tPunto\tPunto(x: 1, s: "a\\\\n\\tb")', 'utf8')),
                               ['var', 'p', 'Punto', 'Punto(x: 1, s: "a\\n\tb")']);
        assert.deepStrictEqual(dd.parseLine(Buffer.from('frame\t3\tMain\t/home/año/x.dash', 'utf8')), ['frame', '3', 'Main', '/home/año/x.dash']);
        assert.deepStrictEqual(dd.parseLine(Buffer.from('*out\tcañón\\n', 'latin1')), ['*out', 'cañón\n']);
        assert.strictEqual(dd.unescapeField(dd.escapeField('a\\b\nc\td')), 'a\\b\nc\td');
    });
    await check('dashc debugger: what opens in the variables view (struct fields, list elements)', () => {
        assert.deepStrictEqual(dd.splitTop('x: 1, s: "a, b", h: [P(x: 1, y: 2), nil], d: {2 claves}'),
                               ['x: 1', 's: "a, b"', 'h: [P(x: 1, y: 2), nil]', 'd: {2 claves}']);
        assert(dd.expandable('Punto', 'Punto(x: 1)') && dd.expandable('[Int]', '[1, 2]'));
        assert(!dd.expandable('Punto', 'nil') && !dd.expandable('[Int]', '[]') && !dd.expandable('Int', '3') &&
               !dd.expandable('Punto', 'Punto(...)') && !dd.expandable('String', '"a(b)"') && !dd.expandable('', '? no existe: x'));
        assert.deepStrictEqual(dd.childrenOf('p', 'Punto', 'Punto(x: 1, nombre: "a: b", hijos: [Punto(...)])').children.map((c) => c.expr),
                               ['p.x', 'p.nombre', 'p.hijos']);
        const l = dd.childrenOf('p.l', '[Int]', '[1, 2, 3]');
        assert.deepStrictEqual(l.children.map((c) => [c.name, c.expr]), [['[0]', 'p.l[0]'], ['[1]', 'p.l[1]'], ['[2]', 'p.l[2]']]);
        const long = dd.childrenOf('l', '[Int]', '[' + Array.from({ length: 20 }, (_, i) => i).join(', ') + ', ...]');
        assert(long.more && long.children.length === 200);
    });
    await check('dashc debugger: expressions in Dash worked out with the values of dbgserver', async () => {
        const vals = { n: ['Int', '7'], f: ['Float', '1.5'], s: ['String', '"hola \\"x\\""'], ok: ['Bool', 'true'], v: ['Punto', 'nil'],
                       p: ['Punto', 'Punto(x: 3)'], 'p.x': ['Int', '3'], l: ['[Int]', '[10, 20, 30]'], 'l[1]': ['Int', '20'],
                       'l[2]': ['Int', '30'] };
        const lookup = async (t) => { if (!vals[t]) throw new Error('no existe: ' + t); return dd.fromServer(...vals[t]); };
        const ev = async (e) => { try { return dd.showValue(await dd.evaluateTree(dd.parseExpression(e), lookup, async () => 3)); }
                                  catch (x) { return '! ' + x.message; } };
        const cases = [['n * 2 + 1', '15'], ['n / 2', '3'], ['-n % 4', '-3'], ['f * 2', '3.0'], ['n + f', '8.5'],
                       ['s.length', '8'], ['s == "hola \\"x\\""', 'true'], ['l[n - 6] + 1', '21'], ['l[1 + 1]', '30'],
                       ['l.length', '3'], ['v == nil and not (n < 3)', 'true'], ['p != nil or nada', 'true'],
                       ['ok and p.x >= 3', 'true'], ['n & 3 | 8', '11'], ['1 << 4', '16'], ['"a" + "b"', '"ab"'],
                       ['nada + 1', '! no existe: nada'], ['n / 0', '! división por cero'], ['n +', '! falta algo al final'],
                       ['n n', '! sobra: n'], ['s + 1', '! + entre String y Int']];
        for (const [e, want] of cases) assert.strictEqual(await ev(e), want, e);
        assert(dd.isPath('p.hijos[0].x') && dd.isPath('l[ 3 ]') && !dd.isPath('l[i]') && !dd.isPath('s.length') && !dd.isPath('nil'));
        assert(dd.hitMet('3', 3) && !dd.hitMet('3', 2) && dd.hitMet('% 2', 4) && !dd.hitMet('% 2', 3) && dd.hitMet('== 1', 1) &&
               !dd.hitMet('> 2', 2) && dd.hitMet('', 1));
    });
    await check('dashc debugger: built by dashc or handed to ./dash1 (C in it); the emulator with dbgserver or bgdbserver', () => {
        assert.strictEqual(engineOf(''), 'dash');
        assert.strictEqual(engineOf('dash: el programa lleva C: con ./dash1\n'), 'gdb');
        assert.strictEqual(engineOf('dash: el programa lleva C: se compila por C con gcc\n'), 'gdb');
        const args = emulatorArgs('/d', '/p/bin/x.debug', 31000, { machine: 'a500' }, 'dash');
        assert.deepStrictEqual(args, ['/d/tools/emu_run.py', '--follow', '--dbgserver', '31000', '--window', '--machine', 'a500', '/p/bin/x.debug']);
        assert(emulatorArgs('/d', 'x', 1, {}, 'gdb').includes('--gdbserver'));
    });

    /** A dbgserver of mentira: a TCP server that answers the orders from a table and can send lines by itself */
    function fakeServer(answers) {
        const got = [];
        let socket = null;
        const server = net.createServer((s) => {
            socket = s;
            s.write('dbgserver\t1\n');
            let buf = '';
            s.on('data', (d) => {
                buf += d.toString('latin1');
                for (let at = buf.indexOf('\n'); at >= 0; at = buf.indexOf('\n')) {
                    const line = buf.slice(0, at);
                    buf = buf.slice(at + 1);
                    got.push(line);
                    const f = line.split('\t');
                    const a = answers[f[0]];
                    const out = typeof a === 'function' ? a(f) : a || 'ok';
                    if (out) s.write(out + '\n');
                    if (f[0] === 'quit') s.end();
                }
            });
        });
        return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve({
            port: server.address().port, got, say: (line) => socket.write(line + '\n'), close: () => server.close() })));
    }
    function dap(adapter) {
        let seq = 0;
        const waiting = new Map(), events = [];
        adapter.onDidSendMessage((m) => {
            if (m.type === 'response' && waiting.has(m.request_seq)) { waiting.get(m.request_seq)(m); waiting.delete(m.request_seq); }
            else if (m.type === 'event') events.push(m);
        });
        const request = (command, args) => new Promise((resolve) => {
            const s = ++seq;
            waiting.set(s, resolve);
            adapter.handleMessage({ seq: s, type: 'request', command, arguments: args || {} });
        });
        const until = async (test) => { for (let i = 0; i < 100 && !test(); i++) await new Promise((r) => setTimeout(r, 20)); return test(); };
        return { request, events, until };
    }
    const emitter = { EventEmitter: class { constructor() { this.l = []; this.event = (f) => this.l.push(f); } fire(m) { for (const f of this.l) f(m); } dispose() {} } };
    const src = path.join(fs.mkdtempSync(path.join(require('os').tmpdir(), 'dash-dbg-')), 'x.dash');   // (the breakpoints' source)
    fs.writeFileSync(src, 'Main\n    Print 1\nend\n');

    await check('dashc debugger: launch, breakpoints (whole name, then the name alone), a stop, a condition and a logpoint', async () => {
        const fake = await fakeServer({
            break: (f) => (f[1] === 'x.dash' || f[2] === '5' ? 'ok\ttrue' : 'ok\tfalse'),
            frames: 'frame\t5\tMain\t/otra/parte/x.dash\nok',
            values: (f) => f.slice(2).map((e) => (e === 'i' ? 'val\tInt\t3' : 'val\t\t? no existe: ' + e)).join('\n') + '\nok',
            quit: 'ok\t0',
        });
        const adapter = new dd.DashDebugAdapter(emitter, { sourceDir: path.dirname(src) });
        const c = dap(adapter);
        await c.request('initialize');
        const launch = await c.request('launch', { port: fake.port, args: 'uno dos' });
        assert(launch.success, launch.message);
        assert(c.events.some((e) => e.event === 'initialized'));
        const bps = await c.request('setBreakpoints', { source: { path: src }, breakpoints: [
            { line: 5 }, { line: 7, condition: 'i == 4' }, { line: 9, logMessage: 'i vale {i + 1}' }, { line: 11 }] });
        // 5 with its whole name; the others with the name alone (the debug information named it otherwise)
        assert.deepStrictEqual(fake.got.slice(0, 1), ['start\t\tuno dos']);
        assert.deepStrictEqual(fake.got.filter((l) => l.startsWith('break')).map((l) => l.replace(src, 'SRC')),
            ['break\tSRC\t5', 'break\tSRC\t7', 'break\tx.dash\t7', 'break\tSRC\t9', 'break\tx.dash\t9', 'break\tSRC\t11', 'break\tx.dash\t11']);
        assert.deepStrictEqual(bps.body.breakpoints.map((b) => b.verified), [true, true, true, true]);
        await c.request('configurationDone');
        assert(await c.until(() => fake.got.includes('continue')));
        fake.say('*out\tcañón\\n');
        fake.say('*stopped\tbreakpoint\t/otra/parte/x.dash\t7\tMain');      // i == 4 does not hold: on it goes
        assert(await c.until(() => fake.got.filter((l) => l === 'continue').length === 2));
        fake.say('*stopped\tbreakpoint\t/otra/parte/x.dash\t9\tMain');      // the logpoint: it writes and goes on
        assert(await c.until(() => fake.got.filter((l) => l === 'continue').length === 3));
        fake.say('*stopped\tbreakpoint\t/otra/parte/x.dash\t5\tMain');
        assert(await c.until(() => c.events.some((e) => e.event === 'stopped')));
        const stops = c.events.filter((e) => e.event === 'stopped');
        assert.deepStrictEqual(stops.map((e) => e.body.reason), ['breakpoint']);
        const trace = await c.request('stackTrace', { threadId: 1 });
        assert.deepStrictEqual(trace.body.stackFrames.map((f) => [f.name, f.line, f.source.path]), [['Main', 5, src]]);
        const outs = c.events.filter((e) => e.event === 'output').map((e) => e.body.output);
        assert.deepStrictEqual(outs, ['cañón\n', 'i vale 4\n']);
        // a breakpoint taken out: unbreak with the name it was set with
        await c.request('setBreakpoints', { source: { path: src }, breakpoints: [{ line: 5 }, { line: 9 }] });
        assert.deepStrictEqual(fake.got.filter((l) => l.startsWith('unbreak')).map((l) => l.replace(src, 'SRC')),
                               ['unbreak\tx.dash\t7', 'unbreak\tx.dash\t11']);
        const r = await c.request('evaluate', { expression: 'nada', frameId: 1, context: 'hover' });
        assert(!r.success && r.message === 'no existe: nada', JSON.stringify(r));
        fake.say('*ended\t5');
        assert(await c.until(() => c.events.some((e) => e.event === 'terminated')));
        assert.strictEqual(c.events.find((e) => e.event === 'exited').body.exitCode, 5);
        const bye = await c.request('disconnect');
        assert(bye.success && fake.got[fake.got.length - 1] === 'quit');
        adapter.dispose();
        fake.close();
    });
    await check('dashc debugger: stopOnEntry (a step, seen as "entry"); a program that does not start; the Amiga gone', async () => {
        let fake = await fakeServer({ quit: 'ok\t0' });
        let adapter = new dd.DashDebugAdapter(emitter, {});
        let c = dap(adapter);
        await c.request('launch', { port: fake.port, stopOnEntry: true });
        await c.request('configurationDone');
        assert(await c.until(() => fake.got.includes('step')) && !fake.got.includes('continue'));
        fake.say('*stopped\tstep\t/a/x.dash\t1\tMain');
        assert(await c.until(() => c.events.some((e) => e.event === 'stopped')));
        assert.strictEqual(c.events.find((e) => e.event === 'stopped').body.reason, 'entry');
        await c.request('pause');                                              // (stopped: nothing to send)
        assert(!fake.got.includes('pause'));
        fake.close();
        adapter.dispose();

        fake = await fakeServer({ start: 'error\tno puedo cargar el programa', quit: 'ok\t0' });
        adapter = new dd.DashDebugAdapter(emitter, {});
        c = dap(adapter);
        const launch = await c.request('launch', { port: fake.port });
        assert(!launch.success && /no puedo cargar el programa/.test(launch.message), JSON.stringify(launch));
        assert(c.events.some((e) => e.event === 'terminated'));
        fake.close();
        adapter.dispose();

        fake = await fakeServer({});
        adapter = new dd.DashDebugAdapter(emitter, {});
        c = dap(adapter);
        await c.request('launch', { port: fake.port });
        await c.request('configurationDone');
        assert(await c.until(() => fake.got.includes('continue')));
        fake.close();
        adapter.server.socket.destroy();                                      // the connection cut
        assert(await c.until(() => c.events.some((e) => e.event === 'terminated')));
        assert(c.events.some((e) => e.event === 'output' && /cortado la conexión/.test(e.body.output)));
        adapter.dispose();
    });
}

// --- the files of Forja's sprite and map editors (media/iff.js, V1) -------------------------
// test/fixtures: written by Forja's own test scripts (tests/iff.py and tests/fmap.py of Forja, which write what Forja
// and Dash's tilemap_save write); esperado.json has their pixels.
async function iffTests() {
    const I = require('../media/iff.js');
    const fx = (n) => new Uint8Array(fs.readFileSync(path.join(__dirname, 'fixtures', n)));
    const want = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'esperado.json'), 'utf8'));
    const strip = (s) => {   // the frames side by side again, as rows
        const rows = [];
        for (let y = 0; y < s.height; y++) {
            const r = [];
            for (const f of s.frames) for (let x = 0; x < s.width; x++) r.push(f[y * s.width + x]);
            rows.push(r);
        }
        return rows;
    };
    await check('iff: an ILBM of Forja, with FRJA (3 frames of 8) and GRAB', () => {
        const s = I.readIlbm(fx('bob_forja.iff'));
        assert.deepStrictEqual([s.width, s.height, s.planes, s.hardware, s.frames.length, s.speed, s.grabX, s.grabY],
            [8, 5, 3, false, 3, 4, 2, 3]);
        assert.deepStrictEqual(strip(s), want.filas);
        assert.deepStrictEqual(s.palette.slice(0, 8), want.paleta);
        assert.strictEqual(s.palette[8], I.initialPalette(false)[8]);   // the rest, Forja's colours
    });
    await check('iff: written again, the same bytes as Forja (sp_escribir)', () => {
        assert.deepStrictEqual(Buffer.from(I.writeIlbm(I.readIlbm(fx('bob_forja.iff')))), Buffer.from(fx('bob_forja.iff')));
        assert.deepStrictEqual(Buffer.from(I.writeIlbm(I.readIlbm(fx('sprite_hw.iff')))), Buffer.from(fx('sprite_hw.iff')));
    });
    await check('iff: ByteRun1 and a mask plane, without FRJA: square frames (bob_load)', () => {
        const s = I.readIlbm(fx('bob_rle_mask.iff'));
        assert.deepStrictEqual([s.width, s.frames.length, s.speed, s.grabX], [24, 1, 6, 0]);   // 24 is not 5 x n: one frame
        assert.deepStrictEqual(strip(s), want.filas);
        const sq = I.newSprite('bob', 4, 4, 2);                     // 3 frames of 4x4 written without FRJA: 3 again
        sq.frames.push(new Uint8Array(16).fill(1), new Uint8Array(16).fill(2));
        const b = I.writeIlbm(sq);
        const frja = Buffer.from(b).indexOf('FRJA');
        b.set([88, 88, 88, 88], frja);                              // (the chunk renamed: skipped as unknown)
        const r = I.readIlbm(b);
        assert.deepStrictEqual([r.width, r.frames.length, r.speed], [4, 3, 6]);
    });
    await check('iff: a hardware sprite (FRJA kind 1, 16 wide)', () => {
        const s = I.readIlbm(fx('sprite_hw.iff'));
        assert.deepStrictEqual([s.width, s.height, s.planes, s.hardware, s.frames.length, I.isAttached(s)], [16, 4, 2, true, 2, false]);
        assert.deepStrictEqual(strip(s), want.sprite_filas);
    });
    await check('iff: new sprites, BOBs and attached ones; what is written is read back', () => {
        for (const [kind, w, h, pl, wantPl] of [['sprite', 99, 12, 0, 2], ['attached', 1, 7, 0, 4], ['bob', 20, 10, 5, 5]]) {
            const s = I.newSprite(kind, w, h, pl);
            s.frames[0][3] = (1 << wantPl) - 1;
            s.frames.push(s.frames[0].map((v, i) => i % (1 << wantPl)));
            s.grabX = -2; s.grabY = 5; s.speed = 9;
            const r = I.readIlbm(I.writeIlbm(s));
            assert.deepStrictEqual([r.width, r.height, r.planes, r.hardware, r.speed, r.grabX, r.grabY],
                [s.width, s.height, wantPl, kind !== 'bob', 9, -2, 5], kind);
            assert.deepStrictEqual(r.frames.map((f) => [...f]), s.frames.map((f) => [...f]), kind);
            assert.deepStrictEqual(r.palette.slice(0, 1 << wantPl), s.palette.slice(0, 1 << wantPl), kind);
        }
    });
    await check('iff: what is not an ILBM, or is cut short, says why', () => {
        assert.throws(() => I.readIlbm(new Uint8Array(20)), /IFF ILBM/);
        const b = fx('bob_forja.iff');
        assert.throws(() => I.readIlbm(b.subarray(0, b.length - 10)), /cortada|falta/);
    });
    await check('fmap: a map as tilemap_save writes it: layers, mirrors, collisions and objects', () => {
        const m = I.readFmap(fx('mapa.fmap'));
        assert.deepStrictEqual([m.width, m.height, m.tile, m.tileset, m.layers.length], [3, 2, 16, 'tiles.iff', 2]);
        assert.deepStrictEqual([...m.layers[0].cells], [1, 2, 16387, 0, 32769, 5]);
        assert.deepStrictEqual([m.layers[0].name, m.layers[0].type, m.layers[0].visible], ['fondo', 0, true]);
        assert.deepStrictEqual([m.layers[1].name, m.layers[1].type, m.layers[1].visible], ['choques', 1, false]);
        assert.deepStrictEqual(m.objects, [{ x: 16, y: 160, kind: 'jugador', name: '', sprite: '' },
            { x: 40, y: -3, kind: 'moneda', name: 'oro', sprite: 'moneda.iff' }]);
        assert.strictEqual(m.layers[0].cells[2] & I.TILE_MASK, 3);
        assert(m.layers[0].cells[2] & I.MIRROR_H && m.layers[0].cells[4] & I.MIRROR_V);
    });
    await check('fmap: written again, the same bytes; a new map is read back', () => {
        assert.deepStrictEqual(Buffer.from(I.writeFmap(I.readFmap(fx('mapa.fmap')))), Buffer.from(fx('mapa.fmap')));
        const m = I.newMap(5, 4, 8, 't.iff');
        m.layers[0].cells[7] = 9 | I.MIRROR_V;
        m.layers.push({ name: 'impar', type: 1, visible: true, cells: new Uint16Array(20).fill(2) });
        m.objects.push({ x: -1, y: 2, kind: 'puerta', name: 'a', sprite: '' });
        const r = I.readFmap(I.writeFmap(m));
        assert.deepStrictEqual([r.width, r.height, r.tile, r.tileset], [5, 4, 8, 't.iff']);
        assert.deepStrictEqual(r.layers.map((l) => [l.name, l.type, [...l.cells]]), m.layers.map((l) => [l.name, l.type, [...l.cells]]));
        assert.deepStrictEqual(r.objects, m.objects);
        assert.throws(() => I.readFmap(fx('bob_forja.iff')), /FMAP/);
    });
}

// --- new versions of Dash (updates.js) ---------------------------------------------
async function updateTests() {
    const { checkUpdates, latestRelease, isNewer, localVersion } = require('../updates');
    await check('updates: versions compared by number; only v1.2.3 tags, not drafts, pre-releases or vscode-x', () => {
        assert(isNewer('1.10.0', '1.9.3') && isNewer('2.0.0', '1.99.99') && !isNewer('1.0.0', '1.0.0') && !isNewer('x', '1.0.0'));
        const r = latestRelease([
            { tag_name: 'vscode-0.9.0', html_url: 'e' },
            { tag_name: 'v1.2.0', html_url: 'a' },
            { tag_name: 'v1.3.0', html_url: 'b', prerelease: true },
            { tag_name: 'v1.10.0', html_url: 'c' },
            { tag_name: 'v2.0.0', html_url: 'd', draft: true },
        ]);
        assert.deepStrictEqual(r, { version: '1.10.0', url: 'c' });
        assert.strictEqual(latestRelease([{ tag_name: 'vscode-0.2.4' }]), null);
        assert.strictEqual(localVersion(path.join(__dirname, '..', '..', '..')), require('fs').readFileSync(
            path.join(__dirname, '..', '..', '..', 'compiler', '__init__.py'), 'utf8').match(/__version__ = "([^"]+)"/)[1]);
    });
    const dir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'dash-upd-'));
    fs.mkdirSync(path.join(dir, 'compiler'));
    fs.writeFileSync(path.join(dir, 'compiler', '__init__.py'), '__version__ = "1.0.0"\n');
    function fake(setting = true) {
        const store = {}, shown = [], opened = [];
        const vscode = {
            workspace: { getConfiguration: () => ({ get: (k, d) => (k === 'updates.check' ? setting : d) }) },
            window: { showInformationMessage: (m, ...b) => { shown.push(m); return Promise.resolve(fake.choice); } },
            env: { openExternal: (u) => opened.push(String(u)) },
            Uri: { parse: (u) => u },
        };
        const context = { globalState: { get: (k) => store[k], update: (k, v) => { store[k] = v; return Promise.resolve(); } } };
        return { vscode, context, store, shown, opened };
    }
    const releases = () => Promise.resolve([{ tag_name: 'v1.1.0', html_url: 'https://x/v1.1.0' }]);
    await check('updates: a newer Dash is told once a day; "No avisar de esta" passes over that version', async () => {
        let f = fake(), asked = 0;
        const fetch = () => { asked++; return releases(); };
        fake.choice = undefined;
        const got = await checkUpdates(f.vscode, f.context, () => dir, { fetch, now: () => 1e12 });
        assert(got && got.version === '1.1.0' && f.shown.length === 1 && /1\.1\.0.*1\.0\.0.*git pull y make -C dashc/.test(f.shown[0]), f.shown.join());
        assert.strictEqual(await checkUpdates(f.vscode, f.context, () => dir, { fetch, now: () => 1e12 + 3600e3 }), null);
        assert.strictEqual(asked, 1);                       // (no request again the same day)
        fake.choice = 'No avisar de esta';
        await checkUpdates(f.vscode, f.context, () => dir, { fetch, now: () => 1e12 + 86400e3 });
        await new Promise((r) => setTimeout(r, 0));
        assert.strictEqual(f.store['dash.updates.skipped'], '1.1.0');
        assert.strictEqual(await checkUpdates(f.vscode, f.context, () => dir, { fetch, now: () => 1e12 + 2 * 86400e3 }), null);
        fake.choice = 'Ver novedades';
        f = fake();
        await checkUpdates(f.vscode, f.context, () => dir, { fetch, now: () => 1e12 });
        await new Promise((r) => setTimeout(r, 0));
        assert.deepStrictEqual(f.opened, ['https://x/v1.1.0']);
    });
    await check('updates: nothing with the setting off, without a compiler, without network or when up to date', async () => {
        let asked = 0;
        const fetch = () => { asked++; return releases(); };
        let f = fake(false);
        assert.strictEqual(await checkUpdates(f.vscode, f.context, () => dir, { fetch }), null);
        f = fake();
        assert.strictEqual(await checkUpdates(f.vscode, f.context, () => null, { fetch }), null);
        assert.strictEqual(asked, 0);
        f = fake();
        assert.strictEqual(await checkUpdates(f.vscode, f.context, () => dir, { fetch: () => Promise.reject(new Error('red')) }), null);
        assert.strictEqual(f.store['dash.updates.last'], undefined);   // (tried again next time)
        fs.writeFileSync(path.join(dir, 'compiler', '__init__.py'), '__version__ = "1.1.0"\n');
        f = fake();
        assert.strictEqual(await checkUpdates(f.vscode, f.context, () => dir, { fetch }), null);
        assert.strictEqual(f.shown.length, 0);
    });
}

(async () => {
    await grammarTests();
    await debugTests();
    await dashcDebugTests();
    await taskTests();
    await editingTests();
    await modelTests();
    await require("./webview.js").webviewTests(check, assert);
    await previewTests();
    await extensionTests();
    await updateTests();
    await iffTests();
    await require('./sprite.js').spriteTests(check, assert);
    await require('./map.js').mapTests(check, assert);
    await require('./amigaView.js').amigaViewTests(check, assert);
    console.log(failures ? `${failures} test(s) failed` : 'all tests passed');
    process.exit(failures ? 1 : 0);
})();
