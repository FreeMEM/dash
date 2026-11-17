// @ts-check
// Dash's help in VS Code, as Forja has it on the Amiga (FORJA_LOOP 3.4): a view with the whole ficha (signature,
// parameters, text, example, see also, DashOS), the index, search, links, back and forward, and "Probar" (the
// example, in a file of its own, run in the emulator or in DashOS). Shift+F1 on a name opens its ficha; the hover
// of a builtin gets its parameters, DashOS and links. The fichas come from tools/gen_ayuda.py of the Dash
// repository (help.js), the same file as the Amiga's DASH:Ayuda/Dash.ayuda.
const fs = require('fs');
const path = require('path');
const H = require('./help');

/**
 * @param {typeof import('vscode')} vscode
 * @param {import('vscode').ExtensionContext} context
 * @param {{findDash: (f: string) => string | null, noDash: () => string, trusted: () => boolean,
 *          runTask?: (kind: string, file: string) => any, lspRunning?: () => boolean}} helpers
 */
function setupHelp(vscode, context, helpers) {
    const storage = (context.globalStorageUri && context.globalStorageUri.fsPath) ||
        path.join(require('os').tmpdir(), 'dash-vscode');
    /** @type {H.Help | null} */
    let help = null;
    let helpDir = null;                 // the Dash folder the help is of
    let loading = null;

    const language = () => {
        const l = vscode.workspace.getConfiguration('dash').get('help.language', 'auto');
        if (l === 'es' || l === 'en') return l;
        return String((vscode.env && vscode.env.language) || 'es').startsWith('es') ? 'es' : 'en';
    };
    const dashDirNow = () => {
        const e = vscode.window.activeTextEditor;
        const f = e && e.document.uri.scheme === 'file' ? e.document.fileName : null;
        const ws = (vscode.workspace.workspaceFolders || [])[0];
        return (f && helpers.findDash(f)) || (ws && helpers.findDash(path.join(ws.uri.fsPath, 'x'))) ||
            helpers.findDash(path.join(storage, 'x'));
    };

    /** The help (made the first time, with a notice), or null with a message said; quiet: nothing said */
    async function getHelp(quiet) {
        const dashDir = dashDirNow();
        if (!dashDir) { if (!quiet) vscode.window.showErrorMessage(helpers.noDash()); return null; }
        if (!helpers.trusted()) {
            if (!quiet) vscode.window.showWarningMessage('La ayuda de Dash se hace con tools/gen_ayuda.py: confía en la carpeta (modo restringido).');
            return null;
        }
        if (help && helpDir === dashDir && help.language === language()) {
            // made again if Dash's documentation changed (a git pull)
            if (!loading) loading = refresh(dashDir, true).finally(() => { loading = null; });
            return help;
        }
        const work = () => refresh(dashDir, quiet);
        loading = loading || (quiet || !vscode.window.withProgress ? work()
            : vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Preparando la ayuda de Dash…' }, work));
        try { await loading; } finally { loading = null; }
        return help && helpDir === dashDir ? help : null;
    }

    async function refresh(dashDir, quiet) {
        try {
            const file = await H.helpFile(dashDir, storage, language(), vscode.workspace.getConfiguration('dash').get('python') || 'python3');
            help = H.openHelp(file);
            helpDir = dashDir;
        } catch (e) {
            if (!quiet) vscode.window.showErrorMessage('Ayuda de Dash: ' + e.message);
        }
    }

    // --- the view ---
    /** @type {import('vscode').WebviewPanel | null} */
    let panel = null;
    const history = [];
    let at = -1;
    let current = -1;
    let listOf = null;                  // what the list shows: null the index, or a search

    function html(webview) {
        const nonce = String(Math.random()).slice(2);
        return `<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';">
<style>
body{font-family:var(--vscode-font-family);font-size:var(--vscode-font-size);color:var(--vscode-foreground);margin:0;padding:0}
.bar{display:flex;gap:6px;align-items:center;padding:6px 10px;border-bottom:1px solid var(--vscode-panel-border);position:sticky;top:0;background:var(--vscode-editor-background);z-index:1}
.bar input{flex:1;min-width:6em;background:var(--vscode-input-background);color:var(--vscode-input-foreground);border:1px solid var(--vscode-input-border,transparent);padding:3px 6px}
button{background:var(--vscode-button-secondaryBackground);color:var(--vscode-button-secondaryForeground);border:0;padding:3px 9px;cursor:pointer}
button.p{background:var(--vscode-button-background);color:var(--vscode-button-foreground)}
button:disabled{opacity:.45;cursor:default}
.main{display:flex;height:calc(100vh - 40px)}
#list{width:15em;min-width:10em;overflow:auto;border-right:1px solid var(--vscode-panel-border);margin:0;padding:4px 0;list-style:none}
#list li{padding:2px 10px;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#list li:hover{background:var(--vscode-list-hoverBackground)}
#list li.sel{background:var(--vscode-list-activeSelectionBackground);color:var(--vscode-list-activeSelectionForeground)}
#list li.h{font-weight:bold;cursor:default;opacity:.8;margin-top:6px}
#list li.h:hover{background:none}
#ficha{flex:1;overflow:auto;padding:4px 18px 30px}
h1{font-size:1.4em;margin:10px 0 6px}h2{font-size:1.1em;margin:16px 0 4px}
a{color:var(--vscode-textLink-foreground);text-decoration:none}a:hover{text-decoration:underline}
pre{background:var(--vscode-textCodeBlock-background);padding:6px 9px;overflow:auto;font-family:var(--vscode-editor-font-family);font-size:var(--vscode-editor-font-size)}
pre.sig{font-weight:bold}.c{color:var(--vscode-descriptionForeground)}
.b{padding:1px 6px;border-radius:3px;font-size:.9em;background:var(--vscode-badge-background);color:var(--vscode-badge-foreground)}
.b.no{opacity:.7}
#empty{opacity:.7;padding:10px}
@media (max-width:520px){.main{flex-direction:column;height:auto}#list{width:auto;max-height:30vh;border-right:0;border-bottom:1px solid var(--vscode-panel-border)}}
</style></head><body>
<div class="bar">
<button id="back" title="Atrás (Alt+Izquierda)">&larr;</button><button id="fwd" title="Adelante (Alt+Derecha)">&rarr;</button>
<button id="idx">Índice</button>
<input id="q" type="search" placeholder="Buscar en la ayuda (palabras, sin acentos)" aria-label="Buscar en la ayuda">
<button id="try" class="p" title="Abre el ejemplo en un fichero y lo ejecuta en el emulador">Probar</button>
<button id="tryos" title="Abre el ejemplo y lo ejecuta en DashOS (QEMU)">Probar en DashOS</button>
</div>
<div class="main"><ul id="list" role="listbox" aria-label="Fichas"></ul><div id="ficha" role="document"><p id="empty">Cargando la ayuda…</p></div></div>
<script nonce="${nonce}">
const vscode = acquireVsCodeApi();
const $ = (id) => document.getElementById(id);
let timer = null;
$('back').onclick = () => vscode.postMessage({ back: 1 });
$('fwd').onclick = () => vscode.postMessage({ forward: 1 });
$('idx').onclick = () => { $('q').value = ''; vscode.postMessage({ index: 1 }); };
$('try').onclick = () => vscode.postMessage({ try: 'amiga' });
$('tryos').onclick = () => vscode.postMessage({ try: 'dashos' });
$('q').oninput = () => { clearTimeout(timer); timer = setTimeout(() => vscode.postMessage({ search: $('q').value }), 200); };
$('q').onkeydown = (e) => { if (e.key === 'Enter') { clearTimeout(timer); vscode.postMessage({ search: $('q').value, first: true }); } };
document.addEventListener('click', (e) => {
  const a = e.target.closest('[data-id]');
  if (a && !a.classList.contains('h')) { e.preventDefault(); vscode.postMessage({ go: Number(a.dataset.id) }); }
});
document.addEventListener('keydown', (e) => {
  if (e.altKey && e.key === 'ArrowLeft') vscode.postMessage({ back: 1 });
  if (e.altKey && e.key === 'ArrowRight') vscode.postMessage({ forward: 1 });
  if (e.key === 'Backspace' && e.target === document.body) vscode.postMessage({ back: 1 });
});
window.addEventListener('message', (ev) => {
  const m = ev.data;
  if (m.list) {
    $('list').innerHTML = m.list;
  }
  if (m.ficha !== undefined) { $('ficha').innerHTML = m.ficha; $('ficha').scrollTop = 0; }
  if (m.sel !== undefined) document.querySelectorAll('#list li').forEach((li) => li.classList.toggle('sel', Number(li.dataset.id) === m.sel));
  if (m.state) {
    $('back').disabled = !m.state.back; $('fwd').disabled = !m.state.forward;
    $('try').disabled = !m.state.try; $('tryos').disabled = !m.state.tryos;
    $('try').style.display = m.state.solo ? 'none' : '';
  }
  if (m.query !== undefined) $('q').value = m.query;
  if (m.focus) $('q').focus();
});
vscode.postMessage({ ready: 1 });
</script></body></html>`;
    }

    const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

    function listHtml(h, ids) {
        if (ids) {
            if (!ids.length) return '<li class="h">(nada)</li>';
            return ids.map((id) => {
                const f = h.ficha(id);
                return `<li data-id="${id}" title="${esc(f.title)}">${esc(f.type === 'F' ? f.key : f.title)}</li>`;
            }).join('');
        }
        let kind = '', out = '';
        const heads = { inicio: '', grupo: 'Funciones por grupo', manual: 'Manual de referencia' };
        for (const e of h.contents()) {
            if (e.kind !== kind && heads[e.kind]) out += `<li class="h">${heads[e.kind]}</li>`;
            kind = e.kind;
            out += `<li data-id="${e.id}" title="${esc(e.title)}">${esc(e.title)}</li>`;
        }
        return out;
    }

    function exampleOf(id) {
        return help ? help.example(id) : null;
    }

    function state() {
        const f = help && current >= 0 ? help.ficha(current) : null;
        const ex = f ? exampleOf(current) : null;
        const os = f && f.fields.dashos;
        return { back: at > 0, forward: at < history.length - 1, try: !!ex && os !== 'solo', tryos: !!ex && os !== 'no', solo: os === 'solo' };
    }

    function show(id, remember = true) {
        if (!help || !panel || id < 0 || id >= help.fichas.length) return false;
        if (remember) { history.splice(at + 1); history.push(id); at = history.length - 1; }
        current = id;
        const f = help.ficha(id);
        panel.title = 'Ayuda: ' + (f.type === 'F' ? f.key : f.title);
        panel.webview.postMessage({ ficha: H.fichaHtml(help, f), sel: id, state: state() });
        return true;
    }

    function setList(query) {
        listOf = query || null;
        const ids = listOf ? help.search(listOf) : null;
        panel.webview.postMessage({ list: listHtml(help, ids), sel: current });
        return ids;
    }

    async function openPanel() {
        if (panel) { panel.reveal(undefined, true); return panel; }
        panel = vscode.window.createWebviewPanel('dash.help', 'Ayuda de Dash',
            { viewColumn: vscode.ViewColumn.Beside, preserveFocus: true }, { enableScripts: true, retainContextWhenHidden: true });
        if (context.extensionPath) panel.iconPath = vscode.Uri.file(path.join(context.extensionPath, 'media', 'dash-file.svg'));
        let ready;
        const isReady = new Promise((r) => { ready = r; });
        panel.webview.onDidReceiveMessage((m) => {
            if (m.ready) { ready(); return; }
            if (!help) return;
            if (m.go !== undefined) show(m.go);
            else if (m.back && at > 0) show(history[--at], false);
            else if (m.forward && at < history.length - 1) show(history[++at], false);
            else if (m.index) { setList(''); show(help.idOf('inicio')); }
            else if (m.search !== undefined) {
                const ids = setList(String(m.search).trim());
                if (m.first && ids && ids.length) show(ids[0]);
            } else if (m.try) tryExample(current, m.try);
        });
        panel.onDidDispose(() => { panel = null; history.length = 0; at = -1; current = -1; });
        panel.webview.html = html(panel.webview);
        await Promise.race([isReady, new Promise((r) => setTimeout(r, 3000))]);
        return panel;
    }

    /** Dash: Ayuda (Shift+F1): the ficha of name, or of the word at the cursor; with no ficha, a search for it;
        with no word, the index */
    async function showHelp(name) {
        const h = await getHelp(false);
        if (!h) return null;
        if (typeof name !== 'string' || !name) name = wordAtCursor() || '';
        await openPanel();
        let id = name ? h.lookup(name) : -1;
        if (id < 0 && name && h.idOf(name) >= 0) id = h.idOf(name);
        if (id >= 0) { if (listOf === null || current < 0) setList(''); show(id); return id; }
        if (name) {
            const ids = setList(name);
            panel.webview.postMessage({ query: name });
            if (ids && ids.length) show(ids[0]);
            else panel.webview.postMessage({ ficha: `<p id="empty">Nada en la ayuda sobre "${esc(name)}".</p>`, state: state() });
            return ids && ids.length ? ids[0] : -1;
        }
        setList('');
        show(h.idOf('inicio'));
        return h.idOf('inicio');
    }

    /** Dash: Buscar en la ayuda */
    async function searchHelp(query) {
        if (typeof query !== 'string') {
            query = await vscode.window.showInputBox({ title: 'Buscar en la ayuda de Dash', prompt: 'Palabras (sin acentos, todas a la vez)',
                                                       value: wordAtCursor() || '' });
            if (query === undefined) return null;
        }
        const h = await getHelp(false);
        if (!h) return null;
        await openPanel();
        const ids = setList(query.trim());
        panel.webview.postMessage({ query, focus: true });
        if (ids && ids.length) show(ids[0]);
        return ids;
    }

    function wordAtCursor() {
        const e = vscode.window.activeTextEditor;
        if (!e || e.document.languageId !== 'dash') return null;
        const r = e.document.getWordRangeAtPosition(e.selection.active, /@?[A-Za-z_][A-Za-z0-9_]*/);
        return r ? e.document.getText(r).replace(/^@/, '') : null;
    }

    /**
     * "Probar": the ficha's example in ejemplo_<key>.dash (the extension's storage), opened and run: in the
     * emulator, or in DashOS (QEMU) with where 'dashos' or for a ficha only of DashOS. Returns the file.
     */
    async function tryExample(key, where) {
        const h = help || await getHelp(false);
        if (!h) return null;
        const id = typeof key === 'number' ? key : h.lookup(key) >= 0 ? h.lookup(key) : h.idOf(key);
        const f = h.ficha(id);
        const ex = f && exampleOf(id);
        if (!ex) { vscode.window.showWarningMessage(`La ficha ${f ? f.key : key} no tiene un ejemplo que se pueda ejecutar.`); return null; }
        const dir = path.join(storage, 'ejemplos');
        fs.mkdirSync(dir, { recursive: true });
        const file = path.join(dir, `ejemplo_${ex.from.replace(/^tests\/|\.dash$/g, '').replace(/[^A-Za-z0-9_]/g, '_')}.dash`);
        // (an example being changed by hand is not overwritten while it has unsaved changes)
        const open = vscode.workspace.textDocuments.find((d) => d.uri.scheme === 'file' && d.fileName === file);
        if (!open || !open.isDirty) fs.writeFileSync(file, `# Ejemplo de la ayuda de Dash (${f.key}). Se puede cambiar y volver a ejecutar.\n` + ex.code);
        const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(file));
        await vscode.window.showTextDocument(doc, { viewColumn: vscode.ViewColumn.One, preview: false });
        const kind = where === 'dashos' || (f.fields.dashos === 'solo' && where !== 'amiga') ? 'dashos-run' : 'run';
        if (helpers.runTask) await helpers.runTask(kind, file);
        return file;
    }

    /** What the help adds to a hover (the language server's, or none) of the name at position */
    function hover(h, document, position) {
        if (!help) { getHelp(true).catch(() => {}); return h; }      // (made now, ready for the next one)
        const r = document.getWordRangeAtPosition(position, /[A-Za-z_][A-Za-z0-9_]*/);
        if (!r) return h;
        const word = document.getText(r);
        // a word after "." is a field or a method (l.has): not a builtin
        if (r.start.character > 0 && document.lineAt(r.start.line).text[r.start.character - 1] === '.') return h;
        const id = help.lookup(word);
        if (id < 0) return h;
        const f = help.ficha(id);
        let md;
        if (f.type === 'F') md = H.hoverMarkdown(help, f, { full: !h, canTry: !!exampleOf(id) });
        else if (!h) md = `**${f.title}**\n\n[Ayuda de Dash: ${word}](command:dash.help.show?${encodeURIComponent(JSON.stringify([word]))})`;
        else return h;
        const ms = new vscode.MarkdownString(md);
        ms.isTrusted = { enabledCommands: ['dash.help.show', 'dash.help.try'] };
        if (!h) return new vscode.Hover(ms, r);
        h.contents.push(ms);
        return h;
    }

    context.subscriptions.push(
        vscode.commands.registerCommand('dash.help.show', (name) => showHelp(name)),
        vscode.commands.registerCommand('dash.help.search', (q) => searchHelp(q)),
        vscode.commands.registerCommand('dash.help.try', (key, where) => tryExample(key, where)),
        // without the language server (off, or not started), the hover is the help's alone
        vscode.languages.registerHoverProvider({ language: 'dash' }, {
            provideHover: (document, position) => (helpers.lspRunning && helpers.lspRunning() ? null : hover(null, document, position)),
        }),
        { dispose: () => { if (panel) panel.dispose(); } },
    );
    return { hover, getHelp, showHelp, searchHelp, tryExample, get panel() { return panel; }, get current() { return current; } };
}

module.exports = { setupHelp };
