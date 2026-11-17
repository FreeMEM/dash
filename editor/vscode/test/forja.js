// Tests of what makes the extension "the Forja" of Linux and DashOS (FORJA_LOOP 6.1): Dash's help (help.js,
// helpView.js), errors with ./dash --check (check.js), DashOS (tasks.js), the project templates (newProject.js) and
// what the language server knows of the new builtins. Without VS Code: a fake vscode where one is needed.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

const repo = path.resolve(__dirname, '..', '..', '..');
const built = fs.existsSync(path.join(repo, 'dashc', 'dashc'));
const tmp = (p) => fs.mkdtempSync(path.join(os.tmpdir(), p));

/** A small fake vscode: what help, check and tasks use */
function fakeVscode(extra = {}) {
    const posted = [], shown = [], errors = [], warnings = [], commands = {}, collections = [];
    class Range { constructor(a, b, c, d) { this.start = { line: a, character: b }; this.end = { line: c, character: d }; } }
    class Diagnostic { constructor(range, message, severity) { Object.assign(this, { range, message, severity }); } }
    class MarkdownString { constructor(v) { this.value = v; } }
    class Hover { constructor(c, r) { this.contents = [c]; this.range = r; } }
    const listeners = {};
    const on = (name) => (f) => { (listeners[name] = listeners[name] || []).push(f); return { dispose() {} }; };
    const vscode = {
        Range, Diagnostic, MarkdownString, Hover,
        DiagnosticSeverity: { Error: 0, Warning: 1 },
        ViewColumn: { One: 1, Beside: -2 },
        ProgressLocation: { Notification: 15 },
        Uri: { file: (p) => ({ scheme: 'file', fsPath: p, path: p, toString: () => 'file://' + p }),
               parse: (s) => ({ scheme: 'file', fsPath: s.replace(/^file:\/\//, ''), toString: () => s }) },
        env: { language: 'es' },
        workspace: {
            textDocuments: [], workspaceFolders: undefined, isTrusted: true,
            getConfiguration: () => ({ get: (k, d) => (extra.settings && k in extra.settings ? extra.settings[k] : d) }),
            onDidOpenTextDocument: on('open'), onDidSaveTextDocument: on('save'), onDidChangeTextDocument: on('change'),
            onDidCloseTextDocument: on('close'), onDidChangeConfiguration: on('config'), onDidGrantWorkspaceTrust: on('trust'),
            openTextDocument: async (uri) => ({ uri, fileName: uri.fsPath }),
        },
        window: {
            activeTextEditor: null,
            showErrorMessage: (m) => errors.push(m), showWarningMessage: (m) => warnings.push(m),
            showInformationMessage: () => {},
            showTextDocument: async (d) => { shown.push(d.fileName); },
            createOutputChannel: () => ({ appendLine() {}, dispose() {} }),
            createWebviewPanel: (id, title) => {
                const handlers = [];
                const panel = {
                    title, reveal() {}, dispose() {}, onDidDispose: () => ({ dispose() {} }),
                    webview: { html: '', postMessage: (m) => { posted.push(m); return Promise.resolve(true); },
                               onDidReceiveMessage: (f) => { handlers.push(f); return { dispose() {} }; } },
                    send: (m) => handlers.forEach((f) => f(m)),
                };
                vscode.lastPanel = panel;
                setTimeout(() => panel.send({ ready: 1 }), 0);
                return panel;
            },
        },
        languages: {
            createDiagnosticCollection: () => {
                const c = { map: new Map(), set(u, d) { this.map.set(u.toString(), d); }, clear() { this.map.clear(); }, dispose() {} };
                collections.push(c);
                return c;
            },
            registerHoverProvider: () => ({ dispose() {} }),
        },
        commands: { registerCommand: (n, f) => { commands[n] = f; return { dispose() {} }; } },
    };
    return { vscode, posted, shown, errors, warnings, commands, collections, listeners };
}

/** A text document of the fake */
function doc(file, text, dirty = false) {
    const lines = text.split('\n');
    return { uri: { scheme: 'file', fsPath: file, toString: () => 'file://' + file }, fileName: file, languageId: 'dash',
             isDirty: dirty, isClosed: false, version: 1,
             getText: (r) => (r ? lines[r.start.line].slice(r.start.character, r.end.character) : text),
             lineAt: (i) => ({ text: lines[i] }),
             getWordRangeAtPosition: (pos, re) => {
                 const l = lines[pos.line];
                 const g = new RegExp(re.source, 'g');
                 let m;
                 while ((m = g.exec(l))) if (m.index <= pos.character && pos.character <= m.index + m[0].length)
                     return { start: { line: pos.line, character: m.index }, end: { line: pos.line, character: m.index + m[0].length } };
                 return undefined;
             } };
}

async function forjaTests(check, assert) {
    const H = require('../help.js');
    const cache = tmp('dash_ayuda_');
    let help = null;

    await check('help: tools/gen_ayuda.py makes the .ayuda once, read as Forja reads it', async () => {
        const file = await H.helpFile(repo, cache, 'es');
        const t = fs.statSync(file).mtimeMs;
        assert.strictEqual(await H.helpFile(repo, cache, 'es'), file);        // not made again
        assert.strictEqual(fs.statSync(file).mtimeMs, t);
        help = H.openHelp(file);
        assert.strictEqual(help.language, 'es');
        assert(help.fichas.length > 1000 && help.groups.length > 30, `${help.fichas.length} fichas`);
        assert.strictEqual(H.openHelp(file), help);                            // read once
        await assert.rejects(H.helpFile('/nada', cache, 'es'), /no trae la ayuda/);
    });
    if (!help) return;
    await check('help: a function ficha: signature, group, DashOS, example; links in the HTML', () => {
        const f = help.ficha(help.lookup('File_Seek'));
        assert.strictEqual(f.key, 'file_seek');
        assert.strictEqual(f.fields.firma, 'file_seek(handle, position, mode) -> Int');
        assert.strictEqual(f.fields.dashos, 'si');
        assert.strictEqual(help.ficha(help.idOf(f.fields.grupo)).type, 'G');
        const html = H.fichaHtml(help, f);
        assert.match(html, /<h1>file_seek<\/h1>/);
        assert.match(html, /<li>handle: el fichero\.<\/li>/);               // the parameters, a list
        assert.match(html, new RegExp(`<a href="#" data-id="${help.lookup('file_pos')}">file_pos\\(handle\\) -&gt; Int</a>: `));
        assert.match(html, new RegExp(`data-id="${help.lookup('file_close')}">file_close</a>\\(f\\)`));   // names in the code
        assert.match(html, /DashOS: sí/);
    });
    await check('help: the words of the language and the new builtins have their ficha', () => {
        assert.strictEqual(help.ficha(help.lookup('if')).type, 'M');
        assert(help.lookup('EventLoop') >= 0 && help.lookup('struct') >= 0);
        for (const n of ['gl_open', 'gl_vertex', 'rexx_send_wait', 'str_join', 'mui_list_add_lines', 'mui_request_text',
                         'mui_menu_add', 'mui_menu_extend', 'mui_menu_remove', 'mui_on_activate'])
            assert.strictEqual((help.ficha(help.lookup(n)) || {}).type, 'F', n);
        assert.strictEqual(help.ficha(help.lookup('mui_menu_add')).fields.dashos, 'no');
    });
    await check('help: search (folded words, all of them, prefixes; the ficha with that name first)', () => {
        assert.strictEqual(H.fold('Música Ñandú x-y'), 'musica nandu x y');
        assert.strictEqual(help.ficha(help.search('str_join')[0]).key, 'str_join');
        const found = help.search('música').map((i) => help.ficha(i).key);
        assert(found.includes('audio_functions'), found.join());
        const both = help.search('abrir fichero');
        assert(both.length > 0 && both.length <= 80);
        assert(help.search('fich').length > 0);                               // a prefix
        assert.deepStrictEqual(help.search('zzzzqq'), []);
    });
    await check('help: "Probar": the whole example of a ficha, or for a function, its group\'s', () => {
        const g = help.example(help.lookup('gl_vertex'));
        assert.strictEqual(g.from, 'gl_functions');
        assert.match(g.code, /^import "lib\/amiga\/gl.dash"/m);
        assert.match(g.code, /^Main$/m);
        assert.strictEqual(help.example(help.lookup('if')), null);            // a piece of code, not a program
        assert.strictEqual(H.wholeProgram(['|x = 1', ' texto', '|Main', '|    Print 1', '|end']), 'Main\n    Print 1\nend\n');
    });
    await check('help: the hover: parameters, DashOS and the links (whole without the language server)', () => {
        const f = help.ficha(help.lookup('str_join'));
        const short = H.hoverMarkdown(help, f, { canTry: false });
        assert.match(short, /- `list`: una lista \[String\]\./);
        assert.match(short, /En DashOS: sí · \[Ayuda de str_join\]\(command:dash\.help\.show\?/);
        assert.doesNotMatch(short, /```dash/);
        const full = H.hoverMarkdown(help, f, { full: true, canTry: true });
        assert.match(full, /^```dash\nstr_join\(list, sep\) -> String\n```/);
        assert.match(full, /\[Probar el ejemplo\]\(command:dash\.help\.try\?/);
    });

    await check('help view: Shift+F1 on a name, links, back and forward, search, "Probar" in the emulator and DashOS', async () => {
        const { setupHelp } = require('../helpView.js');
        const f = fakeVscode();
        const runs = [];
        const storage = tmp('dash_store_');
        const prog = path.join(repo, 'examples', 'hola.dash');
        f.vscode.window.activeTextEditor = { document: doc(prog, 'Main\n    file_seek(f, 0, -1)\nend'),
                                             selection: { active: { line: 1, character: 7 } } };
        const v = setupHelp(f.vscode, { subscriptions: [], globalStorageUri: { fsPath: storage } },
            { findDash: () => repo, noDash: () => 'sin dash', trusted: () => true, runTask: async (k, file) => runs.push([k, file]) });
        // the help of the extension's storage: made there (tools/gen_ayuda.py), so here, taken from the cache above
        const id = await f.commands['dash.help.show']();
        assert.strictEqual(v.current, id);
        const fichas = f.posted.filter((m) => m.ficha);
        assert.match(fichas[fichas.length - 1].ficha, /<h1>file_seek<\/h1>/);
        assert.strictEqual(f.vscode.lastPanel.title, 'Ayuda: file_seek');
        assert(f.posted.some((m) => m.list && /Funciones por grupo/.test(m.list)));   // the index on the left
        const pos = help.lookup('file_pos');
        f.vscode.lastPanel.send({ go: pos });
        assert.strictEqual(v.current, pos);
        f.vscode.lastPanel.send({ back: 1 });
        assert.strictEqual(v.current, id);
        f.vscode.lastPanel.send({ forward: 1 });
        assert.strictEqual(v.current, pos);
        f.vscode.lastPanel.send({ search: 'abrir fichero', first: true });
        const lists = f.posted.filter((m) => m.list);
        assert.match(lists[lists.length - 1].list, /data-id/);
        assert.notStrictEqual(v.current, pos);                       // the first found, shown
        // Probar: the group's example in a file of its own, opened and run
        const file = await f.commands['dash.help.try']('gl_vertex');
        assert.strictEqual(path.basename(file), 'ejemplo_gl_functions.dash');
        assert.match(fs.readFileSync(file, 'utf8'), /^# Ejemplo de la ayuda de Dash \(gl_vertex\)/);
        assert.deepStrictEqual(runs.pop(), ['run', file]);
        assert.deepStrictEqual(f.shown, [file]);
        await f.commands['dash.help.try']('file_seek', 'dashos');
        assert.strictEqual(runs.pop()[0], 'dashos-run');
        await f.commands['dash.help.try']('if');
        assert.match(f.warnings.pop(), /no tiene un ejemplo/);
        // a name without a ficha: a search for it
        assert.strictEqual(await f.commands['dash.help.show']('zzzzqq'), -1);
        assert.match(f.posted[f.posted.length - 1].ficha, /Nada en la ayuda/);
        // the hover: what the help adds to the language server's, or the whole of it without one
        const d = doc(prog, 'Main\n    s = str_join(l, ", ")\n    x.has(1)\nend');
        const lsp = new f.vscode.Hover(new f.vscode.MarkdownString('```dash\nstr_join(list, sep)\n```'));
        const h = v.hover(lsp, d, { line: 1, character: 9 });
        assert.strictEqual(h.contents.length, 2);
        assert.match(h.contents[1].value, /En DashOS: sí/);
        assert.deepStrictEqual(h.contents[1].isTrusted, { enabledCommands: ['dash.help.show', 'dash.help.try'] });
        assert.match(v.hover(null, d, { line: 1, character: 9 }).contents[0].value, /^```dash\nstr_join\(list, sep\) -> String/);
        assert.strictEqual(v.hover(null, d, { line: 2, character: 7 }), null);       // l.has: a method, not a builtin
        assert.match(v.hover(null, doc(prog, 'Main\nend'), { line: 0, character: 1 }).contents[0].value, /Ayuda de Dash: Main/);
        fs.rmSync(storage, { recursive: true, force: true });
    });

    // --- ./dash --check ---
    const C = require('../check.js');
    await check('check: what ./dash --check prints, and the word it marks', () => {
        const p = C.parseCheck('Warning: el programa no tiene Main\n/a/b.dash:4:9: Error: la función foo no existe\nx\n' +
                               'c.dash:1:1: Warning: algo\n');
        assert.deepStrictEqual(p, [{ file: '/a/b.dash', line: 4, column: 9, severity: 'Error', message: 'la función foo no existe' },
                                   { file: 'c.dash', line: 1, column: 1, severity: 'Warning', message: 'algo' }]);
        assert.deepStrictEqual(C.wordRange('Main\n    y = foo(2)\nend', 2, 9), [1, 8, 11]);
        assert.deepStrictEqual(C.wordRange('Main\n    x = (1\nend', 2, 11), [1, 9, 10]);   // at the end: the last character
        assert.deepStrictEqual(C.wordRange('a', 9, 1), [0, 0, 1]);
    });
    if (built) {
        await check('check: all the errors, also of a module, and the unsaved text of a module (--texto)', async () => {
            const dir = tmp('dash_check_t_');
            const a = path.join(dir, 'a.dash'), b = path.join(dir, 'b.dash');
            fs.writeFileSync(a, 'import "b.dash"\nMain\n    y = foo(2)\n    Print z\n    Print ayuda(1)\nend\n');
            fs.writeFileSync(b, 'func ayuda(n: Int) -> Int\n    return n + q\nend\n');
            const t0 = Date.now();
            const r = await C.runCheck(repo, a, {});
            const ms = Date.now() - t0;
            assert(r.ok);
            assert.deepStrictEqual(r.problems.map((p) => [path.basename(p.file), p.line, p.message]),
                [['a.dash', 3, 'la función foo no existe'], ['a.dash', 4, 'la variable z no existe'], ['b.dash', 2, 'la variable q no existe']]);
            const fixed = await C.runCheck(repo, a, { [b]: 'func ayuda(n: Int) -> Int\n    return n\nend\n' });
            assert.deepStrictEqual(fixed.problems.map((p) => path.basename(p.file)), ['a.dash', 'a.dash']);
            const mod = await C.runCheck(repo, b, {});                       // a module alone: no "falta Main"
            assert.deepStrictEqual(mod.problems.map((p) => p.message), ['la variable q no existe']);
            assert(ms < 5000, ms + ' ms');
            // an error without a place (a .dashui that is wrong): on the first line, and it is still a check
            const c = path.join(dir, 'c.dash');
            fs.writeFileSync(c, 'import "v.dashui"\nMain\nend\n');
            fs.writeFileSync(path.join(dir, 'v.dashui'), '{"dashui":1,"windows":[{"name":"W","root":{"type":"nada"}}]}');
            const ui = await C.runCheck(repo, c, {});
            assert(ui.ok);
            assert.strictEqual(ui.problems.length, 1);
            assert.match(ui.problems[0].message, /v\.dashui: ventana 1: tipo de objeto desconocido: nada$/);
            assert.deepStrictEqual([ui.problems[0].file, ui.problems[0].line], [c, 1]);
            // a Dash that cannot check: not ok, said
            const old = tmp('dash_viejo_');
            fs.writeFileSync(path.join(old, 'dash'), '#!/usr/bin/env python3\nimport sys\nprint("dash: falta el compilador; constrúyelo con: make -C dashc", file=sys.stderr)\nsys.exit(1)\n');
            const r2 = await C.runCheck(old, a, {});
            assert.strictEqual(r2.ok, false);
            assert.match(r2.output, /make -C dashc/);
            fs.rmSync(old, { recursive: true, force: true });
            fs.rmSync(dir, { recursive: true, force: true });
        });
        await check('check: the errors of the open documents land in their files; fixed, they go', async () => {
            const dir = tmp('dash_check_v_');
            const a = path.join(dir, 'a.dash');
            fs.writeFileSync(a, 'Main\n    Print z\nend\n');
            const f = fakeVscode();
            const d = doc(a, 'Main\n    Print z\nend\n');
            let fellBack = 0;
            const c = C.setupCheck(f.vscode, { subscriptions: [] }, { findDash: () => repo, trusted: () => true, onFallback: () => fellBack++ });
            f.vscode.workspace.textDocuments.push(d);
            assert.strictEqual(c.usesCheck(), true);
            await c.check(d);
            const diags = f.collections[0].map.get('file://' + a);
            assert.strictEqual(diags.length, 1);
            assert.strictEqual(diags[0].message, 'la variable z no existe');
            assert.deepStrictEqual([diags[0].range.start, diags[0].range.end], [{ line: 1, character: 10 }, { line: 1, character: 11 }]);
            // typed and not saved: the text in the editor is what is checked
            const d2 = Object.assign(doc(a, 'Main\n    z = 1\n    Print z\nend\n', true), { version: 2 });
            f.vscode.workspace.textDocuments[0] = d2;
            await c.check(d2);
            assert.deepStrictEqual(f.collections[0].map.get('file://' + a), []);
            assert.strictEqual(fellBack, 0);
            // with "dash.errors.source": "languageServer", nothing from here
            const g = fakeVscode({ settings: { 'errors.source': 'languageServer' } });
            assert.strictEqual(C.setupCheck(g.vscode, { subscriptions: [] }, { findDash: () => repo, trusted: () => true }).usesCheck(), false);
            fs.rmSync(dir, { recursive: true, force: true });
        });
    }

    // --- DashOS ---
    const T = require('../tasks.js');
    await check('dashos: the commands (straight, or through C with clang when the program has C)', () => {
        assert.strictEqual(T.taskCommand('dashos', '/d', '/p/x.dash'), "mkdir -p '/p/bin/dashos' && '/d/dash' --dashos '/p/x.dash' -o '/p/bin/dashos/x'");
        assert.strictEqual(T.taskCommand('dashos', '/d', '/p/x.dash', { withC: true, outputFolder: '/o' }),
                           "mkdir -p '/o/dashos' && '/d/dash' --dashos --gcc '/p/x.dash' -o '/o/dashos/x'");
        assert.strictEqual(T.taskCommand('dashos-run', '/d', '/p/x.dash'), "python3 '/d/tools/dashos_run.py' --directo '/p/x.dash'");
        assert.strictEqual(T.taskCommand('dashos-run', '/d', '/p/x.dash', { withC: true }), "python3 '/d/tools/dashos_run.py' '/p/x.dash'");
        assert(T.hasC('Main\nend\n@native func f()\n"""\n"""\nend') && !T.hasC('Main\n    Print "@native"\nend'));
        const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'));
        assert.deepStrictEqual(pkg.contributes.taskDefinitions[0].properties.task.enum.slice(-2), ['dashos', 'dashos-run']);
        assert(pkg.contributes.debuggers[0].configurationAttributes.launch.properties.target.enum.includes('dashos'));
    });
    await check('dashos: what is missing, in words (QEMU, LLVM, dashc-a64, kit-c)', () => {
        const fake = tmp('dash_falta_');
        fs.mkdirSync(path.join(fake, 'tools'));
        fs.writeFileSync(path.join(fake, 'tools', 'dashos_run.py'), '');
        assert.match(T.dashosMissing('dashos-run', fake, 'Main\nend', { PATH: '/nada' }), /qemu-user/);
        assert.match(T.dashosMissing('dashos', fake, 'Main\nend', { PATH: '/nada' }), /Falta clang, ld\.lld.*instala clang, lld y llvm/);
        assert.match(T.dashosMissing('dashos', '/nada', 'Main\nend', {}), /git pull/);
        const bin = tmp('dash_bin_');
        for (const t of ['qemu-aarch64', 'clang', 'ld.lld', 'llvm-ar', 'llvm-nm', 'llvm-objcopy']) {
            fs.writeFileSync(path.join(bin, t), '#!/bin/sh\n');
            fs.chmodSync(path.join(bin, t), 0o755);
        }
        assert.match(T.dashosMissing('dashos-run', fake, 'Main\nend', { PATH: bin }), /make -C dashc dashc-a64/);
        assert.strictEqual(T.dashosMissing('dashos-run', fake, '@native func f()\nend\nMain\nend', { PATH: bin }), null);   // (by C)
        fs.mkdirSync(path.join(fake, 'dashc'));
        fs.writeFileSync(path.join(fake, 'dashc', 'dashc-a64'), '');
        assert.strictEqual(T.dashosMissing('dashos-run', fake, 'Main\nend', { PATH: bin }), null);
        const nokit = { PATH: bin, DASHOS_DIR: '/nada', DASH_KIT_C: '' };
        assert.match(T.dashosMissing('dashos', fake, 'Main\n    w = mui_window_begin("x", 0)\nend', nokit), /libkit_c\.a.*dash\.dashos\.folder/);
        fs.writeFileSync(path.join(bin, 'libkit_c.a'), '');
        assert.strictEqual(T.dashosMissing('dashos', fake, 'Main\n    w = mui_window_begin("x", 0)\nend',
                                           { PATH: bin, DASH_KIT_C: path.join(bin, 'libkit_c.a') }), null);
        const { missing } = require('../missing.js');
        assert.match(missing("FileNotFoundError: [Errno 2] No such file or directory: 'qemu-aarch64'"), /qemu-user/);
        assert.match(missing('falta libkit_c.a de DashOS para las ventanas (mui_*): make -C kernel kit-c'), /dash\.dashos\.folder/);
        assert.match(missing('dash: falta el compilador para DashOS; constrúyelo con: make -C dashc dashc-a64'), /dashc-a64/);
        fs.rmSync(fake, { recursive: true, force: true });
        fs.rmSync(bin, { recursive: true, force: true });
    });

    // --- the project templates ---
    const N = require('../newProject.js');
    await check('templates: command, demo, 3D and DashOS (one program each; DashOS runs first in QEMU)', () => {
        assert.deepStrictEqual(N.KINDS.map((k) => k.id), ['mui', 'cli', 'game', 'demo', '3d', 'dashos']);
        for (const k of ['cli', 'demo', '3d', 'dashos']) {
            const { files } = N.projectFiles('prueba', null, k);
            assert.deepStrictEqual(Object.keys(files).sort(), ['.gitignore', '.vscode/launch.json', 'prueba.dash'], k);
        }
        assert.match(N.projectFiles('x', null, 'demo').files['x.dash'], /^\s+asm in d5 = centro out salir = d0/m);
        assert.match(N.projectFiles('x', null, '3d').files['x.dash'], /^import "lib\/amiga\/gl.dash"/m);
        const launch = JSON.parse(N.projectFiles('x', null, 'dashos').files['.vscode/launch.json']);
        assert.deepStrictEqual([launch.configurations[0].target, launch.configurations[0].program], ['dashos', '${workspaceFolder}/x.dash']);
    });
    if (built) {
        await check('templates: each one compiles with ./dash; the DashOS one also with --dashos', () => {
            const dir = tmp('dash_plantillas_');
            try {
                for (const k of ['cli', 'demo', '3d', 'dashos']) {
                    const prog = N.writeProject(path.join(dir, k), 'p_' + k, null, k);
                    const out = spawnSync(path.join(repo, 'dash'), [prog, '-o', path.join(dir, k, 'prog')], { cwd: repo, encoding: 'utf8' });
                    assert.strictEqual(out.status, 0, k + ': ' + out.stdout + out.stderr);
                }
                if (fs.existsSync(path.join(repo, 'dashc', 'dashc-a64')) && T.which('ld.lld')) {
                    const prog = path.join(dir, 'dashos', 'p_dashos.dash');
                    const out = spawnSync(path.join(repo, 'dash'), ['--dashos', prog, '-o', path.join(dir, 'elf')], { cwd: repo, encoding: 'utf8' });
                    assert.strictEqual(out.status, 0, out.stdout + out.stderr);
                    assert.strictEqual(fs.readFileSync(path.join(dir, 'elf')).slice(1, 4).toString(), 'ELF');
                    if (T.which('qemu-aarch64')) {
                        const run = spawnSync('python3', [path.join(repo, 'tools', 'dashos_run.py'), '--directo', prog], { cwd: repo, encoding: 'utf8', timeout: 300000 });
                        assert.strictEqual(run.status, 0, run.stdout + run.stderr);
                        assert.match(run.stdout, /^8 palabras distintas\nRepetidas: el \(3\), y \(2\), lenguaje \(2\)\n$/);
                    }
                }
            } finally {
                fs.rmSync(dir, { recursive: true, force: true });
            }
        });
    }

    // --- the language server knows the new builtins: completion and signature ---
    await check('language server: completion and signature of the new builtins (gl_*, rexx_send_wait, str_join, l.has...)', async () => {
        const server = spawn('python3', ['-m', 'compiler.lsp'], { cwd: repo });
        let buf = Buffer.alloc(0);
        const waiting = new Map();
        server.stdout.on('data', (d) => {
            buf = Buffer.concat([buf, d]);
            for (;;) {
                const h = buf.indexOf('\r\n\r\n');
                if (h < 0) return;
                const len = Number(/Content-Length: (\d+)/.exec(buf.slice(0, h).toString())[1]);
                if (buf.length < h + 4 + len) return;
                const msg = JSON.parse(buf.slice(h + 4, h + 4 + len).toString());
                buf = buf.slice(h + 4 + len);
                if (msg.id !== undefined && waiting.has(msg.id)) { waiting.get(msg.id)(msg.result); waiting.delete(msg.id); }
            }
        });
        let next = 1;
        const send = (o) => { const s = JSON.stringify(Object.assign({ jsonrpc: '2.0' }, o)); server.stdin.write(`Content-Length: ${Buffer.byteLength(s)}\r\n\r\n${s}`); };
        const request = (method, params) => new Promise((resolve) => { const id = next++; waiting.set(id, resolve); send({ id, method, params }); });
        try {
            await request('initialize', { processId: null, rootUri: null, capabilities: {} });
            send({ method: 'initialized', params: {} });
            const uri = 'file://' + path.join(os.tmpdir(), 'dash_lsp_nuevo.dash');
            // first a program that compiles (members come from the last good analysis), then what is being typed
            const good = 'import "lib/amiga/gl.dash"\nMain\n    l = ["a"]\n    s = str_join(l, ", ")\nend\n';
            const text = 'import "lib/amiga/gl.dash"\nMain\n    l = ["a"]\n    s = str_join(l, ", ")\n    r = rexx_send_w\n    gl_\n    l.\n    mui_menu_ex\nend\n';
            send({ method: 'textDocument/didOpen', params: { textDocument: { uri, languageId: 'dash', version: 1, text: good } } });
            await request('textDocument/completion', { textDocument: { uri }, position: { line: 3, character: 4 } });
            send({ method: 'textDocument/didChange', params: { textDocument: { uri, version: 2 }, contentChanges: [{ text }] } });
            const labels = (r) => (Array.isArray(r) ? r : (r && r.items) || []).map((i) => i.label);
            assert(labels(await request('textDocument/completion', { textDocument: { uri }, position: { line: 4, character: 19 } })).includes('rexx_send_wait'));
            const gl = labels(await request('textDocument/completion', { textDocument: { uri }, position: { line: 5, character: 7 } }));
            assert(gl.includes('gl_open') && gl.includes('gl_vertex'), gl.slice(0, 10).join());
            assert(labels(await request('textDocument/completion', { textDocument: { uri }, position: { line: 6, character: 6 } })).includes('has'));
            assert(labels(await request('textDocument/completion', { textDocument: { uri }, position: { line: 7, character: 15 } })).includes('mui_menu_extend'));
            const sig = await request('textDocument/signatureHelp', { textDocument: { uri }, position: { line: 3, character: 20 } });
            assert.match(sig.signatures[0].label, /^str_join\(list, sep\)/);
            assert.strictEqual(sig.activeParameter, 1);
        } finally {
            server.kill();
        }
    });
    fs.rmSync(cache, { recursive: true, force: true });
}

module.exports = { forjaTests, fakeVscode, doc };
