// @ts-check
// Errors while typing with `./dash --check` (Forja's way, FORJA_LOOP 3.5): the compiler that makes the executable
// (./dash, straight to 68000 code) says what is wrong, up to 20 errors, in a few tens of milliseconds, with its own
// words. The unsaved text of the open .dash files goes with --texto ruta=fichero, so a module being typed counts
// in the program that imports it. The language server (compiler/lsp.py) still does completion, hover, definition,
// rename...; its own errors are shown instead only with "dash.errors.source": "languageServer", or when this Dash
// has no --check (then once said in the output).
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFile } = require('child_process');

const LINE = /^(.*?):(\d+):(\d+):\s+(Error|Warning):\s+(.*)$/;
const MAX_TEXTS = 16;           // dashc takes 16 --texto at most

/**
 * What ./dash --check printed: [{file, line, column, severity, message}] (lines without a place are left out: "el
 * programa no tiene Main" of a module)
 * @param {string} output
 */
function parseCheck(output) {
    const out = [];
    for (const l of String(output).split(/\r?\n/)) {
        const m = LINE.exec(l);
        if (m) out.push({ file: m[1], line: Number(m[2]), column: Number(m[3]), severity: m[4], message: m[5].trim() });
    }
    return out;
}

/**
 * The columns of the word at line:column (1-based) of a text: [row, start, end], 0-based (as the language server
 * marks them: the name, or the last character at the end of a line)
 * @param {string} text
 */
function wordRange(text, line, column) {
    const lines = text.split('\n');
    const row = Math.max(0, Math.min(line - 1, lines.length - 1));
    const src = (lines[row] || '').replace(/\r$/, '');
    let start = Math.max(0, Math.min(column - 1, src.length));
    const w = /^([A-Za-z_][A-Za-z0-9_]*|\S)/.exec(src.slice(start));
    let end = start + (w ? w[0].length : 0);
    if (end === start) { start = Math.max(0, start - 1); end = src.length; }
    return [row, start, end];
}

/**
 * The arguments of ./dash for checking file, with the unsaved texts ({path: text}) written to tmpDir
 * @param {string} file
 * @param {Record<string, string>} unsaved
 * @param {string} tmpDir
 */
function checkArgs(file, unsaved, tmpDir) {
    const args = ['--check', file];
    let n = 0;
    for (const [p, text] of Object.entries(unsaved)) {
        if (n === MAX_TEXTS) break;
        const copy = path.join(tmpDir, `texto${n++}.dash`);
        fs.writeFileSync(copy, text);
        args.push('--texto', `${p}=${copy}`);
    }
    return args;
}

/**
 * Runs ./dash --check: resolves {ok, problems, output}; ok false if this Dash cannot check (no --check, compiler not
 * built): then output says why.
 * @param {string} dashDir
 * @param {string} file
 * @param {Record<string, string>} unsaved
 * @param {{python?: string, onChild?: (c: import('child_process').ChildProcess) => void}} [o]
 */
function runCheck(dashDir, file, unsaved, o = {}) {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_check_'));
    let args;
    try { args = checkArgs(file, unsaved, tmp); } catch (e) { fs.rmSync(tmp, { recursive: true, force: true }); return Promise.reject(e); }
    return new Promise((resolve) => {
        const child = execFile(o.python || 'python3', [path.join(dashDir, 'dash'), ...args],
                               { cwd: fs.existsSync(path.dirname(file)) ? path.dirname(file) : dashDir, timeout: 30000, maxBuffer: 4 << 20 },
                               (err, stdout, stderr) => {
            fs.rmSync(tmp, { recursive: true, force: true });
            const output = String(stdout) + String(stderr);
            const problems = parseCheck(output);
            const killed = err && (/** @type {any} */ (err).killed || /** @type {any} */ (err).signal);
            // this Dash cannot check: no --check or --texto (its usage), not built, no Python
            const cannot = !killed && err && !problems.length &&
                (/^uso: dash|^dash: falta el compilador/m.test(output) || /** @type {any} */ (err).code === 'ENOENT');
            // an error without a place ("dash: Error: ventana.dashui: ...", of an import): on the first line
            if (err && !killed && !cannot && !problems.length) {
                const said = output.split('\n').map((l) => l.trim()).filter(Boolean);
                const line = said.find((l) => /Error/.test(l)) || said[0] || 'error al comprobar';
                problems.push({ file, line: 1, column: 1, severity: 'Error', message: line.replace(/^dash: (Error: )?/, '') });
            }
            resolve({ ok: !cannot, problems, output, killed: !!killed });
        });
        if (o.onChild) o.onChild(child);
    });
}

/**
 * Errors while typing with ./dash --check. Returns {usesCheck}: true while these errors are the ones shown (the
 * language server's are then left out by lspClient.js).
 * @param {typeof import('vscode')} vscode
 * @param {import('vscode').ExtensionContext} context
 * @param {{findDash: (f: string) => string | null, trusted: () => boolean, onFallback?: () => void}} helpers
 */
function setupCheck(vscode, context, helpers) {
    const collection = vscode.languages.createDiagnosticCollection('dash');
    const output = vscode.window.createOutputChannel('Dash (errores)');
    /** @type {Map<string, Map<string, any[]>>} key of the checked document -> file uri -> its problems */
    const results = new Map();
    const timers = new Map();
    const running = new Map();
    let fallback = false;              // this Dash has no --check: the language server's errors
    const config = () => vscode.workspace.getConfiguration('dash');
    const wanted = () => config().get('errors.source', 'check') !== 'languageServer';
    const usesCheck = () => wanted() && !fallback && helpers.trusted();
    const isDash = (d) => d && d.languageId === 'dash' && (d.uri.scheme === 'file' || d.uri.scheme === 'untitled');

    /** the problems of every check, together, in their files (each once) */
    const publish = () => {
        /** @type {Map<string, Map<string, any>>} */
        const byFile = new Map();
        for (const files of results.values()) {
            for (const [uri, diags] of files) {
                const m = byFile.get(uri) || new Map();
                for (const d of diags) m.set(`${d.range.start.line}:${d.range.start.character}:${d.message}`, d);
                byFile.set(uri, m);
            }
        }
        collection.clear();
        for (const [uri, m] of byFile) collection.set(vscode.Uri.parse(uri), [...m.values()]);
    };

    async function check(doc) {
        if (!usesCheck() || !isDash(doc)) return;
        const key = doc.uri.toString();
        let file = doc.uri.scheme === 'file' ? doc.uri.fsPath : null;
        if (file && !fs.existsSync(file)) {               // deleted (still open): nothing to check
            if (results.delete(key)) publish();
            return;
        }
        const dashDir = helpers.findDash(file || ((vscode.workspace.workspaceFolders || [])[0] || { uri: { fsPath: '' } }).uri.fsPath + '/x');
        if (!dashDir) return;
        const unsaved = {};
        let untitled = null;
        if (!file) {                                     // untitled: its text in a file of its own
            untitled = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_sin_nombre_'));
            file = path.join(untitled, 'sin_nombre.dash');
            fs.writeFileSync(file, doc.getText());
        }
        for (const d of vscode.workspace.textDocuments) {
            if (d.languageId === 'dash' && d.uri.scheme === 'file' && d.isDirty && fs.existsSync(d.uri.fsPath)) unsaved[d.uri.fsPath] = d.getText();
        }
        const prev = running.get(key);
        if (prev) try { prev.kill(); } catch (e) { /* gone */ }
        const version = doc.version;
        let r;
        try {
            r = await runCheck(dashDir, file, unsaved, { python: config().get('python') || 'python3',
                                                          onChild: (c) => running.set(key, c) });
        } finally {
            if (untitled) fs.rmSync(untitled, { recursive: true, force: true });
        }
        if (r.killed) return;                            // a newer one took its place
        running.delete(key);
        if (!r.ok) {
            if (!fallback) {
                fallback = true;
                output.appendLine(`./dash --check no va en ${dashDir}: se usan los errores del servidor de lenguaje.`);
                output.appendLine(r.output.trim());
                results.clear();
                publish();
                if (helpers.onFallback) helpers.onFallback();
            }
            return;
        }
        if (doc.isClosed) return;
        const files = new Map([[key, []]]);
        for (const p of r.problems) {
            const same = untitled ? p.file === file : path.resolve(path.dirname(file), p.file) === path.resolve(file);
            const uri = same ? doc.uri : vscode.Uri.file(path.resolve(path.dirname(file), p.file));
            let text = '';
            const open = vscode.workspace.textDocuments.find((d) => d.uri.toString() === uri.toString());
            if (same) text = doc.getText();
            else if (open) text = open.getText();
            else try { text = fs.readFileSync(uri.fsPath, 'latin1'); } catch (e) { /* gone */ }
            const [row, start, end] = wordRange(text, p.line, p.column);
            const d = new vscode.Diagnostic(new vscode.Range(row, start, row, end), p.message,
                p.severity === 'Warning' ? vscode.DiagnosticSeverity.Warning : vscode.DiagnosticSeverity.Error);
            d.source = 'dash';
            const k = uri.toString();
            files.set(k, (files.get(k) || []).concat([d]));
        }
        if (doc.version !== version && doc.isDirty) return;    // typed meanwhile: the next check says it
        results.set(key, files);
        publish();
    }

    const later = (doc, ms) => {
        if (!usesCheck() || !isDash(doc)) return;
        const key = doc.uri.toString();
        clearTimeout(timers.get(key));
        timers.set(key, setTimeout(() => { timers.delete(key); check(doc).catch((e) => output.appendLine(String(e))); }, ms));
    };
    const checkAll = () => (vscode.workspace.textDocuments || []).forEach((d) => later(d, 0));

    context.subscriptions.push(collection, output,
        vscode.workspace.onDidOpenTextDocument((d) => later(d, 0)),
        vscode.workspace.onDidSaveTextDocument((d) => {
            later(d, 0);
            // the others that are open may import it: they are checked again too (as the language server does)
            for (const o of vscode.workspace.textDocuments) if (o !== d) later(o, 50);
        }),
        vscode.workspace.onDidChangeTextDocument((e) => e.contentChanges.length && later(e.document, 600)),
        vscode.workspace.onDidCloseTextDocument((d) => {
            const key = d.uri.toString();
            clearTimeout(timers.get(key));
            if (results.delete(key)) publish();
        }),
        vscode.workspace.onDidChangeConfiguration((e) => {
            if (!e.affectsConfiguration('dash.errors.source') && !e.affectsConfiguration('dash.path')) return;
            fallback = false;
            results.clear();
            publish();
            if (helpers.onFallback) helpers.onFallback();    // (the language server's errors back, or away)
            checkAll();
        }),
        { dispose: () => { for (const t of timers.values()) clearTimeout(t); for (const c of running.values()) try { c.kill(); } catch (e) { /* gone */ } } },
    );
    if (vscode.workspace.onDidGrantWorkspaceTrust) context.subscriptions.push(vscode.workspace.onDidGrantWorkspaceTrust(checkAll));
    checkAll();
    return { usesCheck, check };
}

module.exports = { parseCheck, wordRange, checkArgs, runCheck, setupCheck };
