// @ts-check
// Custom editors for binary files: the sprite and BOB editor (IFF ILBM, media/sprite.js) and, with the same
// document, the tile map editor (FMAP). The webview holds the picture; each change it makes comes here as the whole
// file (they are small), so VS Code's undo, redo, save, revert and hot exit work as with any file.
const vscode = require('vscode');
const path = require('path');
const fs = require('fs');

class BinaryDocument {
    /** @param {vscode.Uri} uri @param {Uint8Array} bytes */
    constructor(uri, bytes) {
        this.uri = uri;
        this.bytes = bytes;
        this._onDispose = new vscode.EventEmitter();
        this.onDidDispose = this._onDispose.event;
    }
    dispose() { this._onDispose.fire(); this._onDispose.dispose(); }
}

class BinaryEditorProvider {
    /**
     * @param {vscode.ExtensionContext} context
     * @param {{page: string, scripts: string[], empty?: (uri: vscode.Uri) => Uint8Array | null}} kind
     *   page: the HTML in media/; scripts: the files it loads ({{name}} in the page); empty: the bytes of a new
     *   file (an empty file opened)
     */
    constructor(context, kind) {
        this.context = context;
        this.kind = kind;
        this._onDidChange = new vscode.EventEmitter();
        this.onDidChangeCustomDocument = this._onDidChange.event;
        /** @type {Map<string, Set<vscode.Webview>>} */
        this.webviews = new Map();
    }

    async openCustomDocument(uri, openContext) {
        const from = openContext && openContext.backupId ? vscode.Uri.parse(openContext.backupId) : uri;
        let bytes = new Uint8Array(0);
        try { bytes = await vscode.workspace.fs.readFile(from); } catch (e) { /* a new file: empty */ }
        if (!bytes.length && this.kind.empty) bytes = this.kind.empty(uri) || bytes;
        const doc = new BinaryDocument(uri, bytes);
        doc.onDidDispose(() => this.webviews.delete(uri.toString()));
        return doc;
    }

    html(webview) {
        const media = vscode.Uri.joinPath(this.context.extensionUri, 'media');
        const uri = (f) => webview.asWebviewUri(vscode.Uri.joinPath(media, f)).toString();
        let html = fs.readFileSync(path.join(this.context.extensionPath, 'media', this.kind.page), 'utf8')
            .replace(/\{\{cspSource\}\}/g, webview.cspSource);
        for (const f of this.kind.scripts) html = html.replace(`{{${f}}}`, uri(f));
        return html;
    }

    post(doc, message) {
        for (const w of this.webviews.get(doc.uri.toString()) || []) w.postMessage(message);
    }

    /** @param {BinaryDocument} doc @param {vscode.WebviewPanel} panel */
    resolveCustomEditor(doc, panel) {
        const key = doc.uri.toString();
        if (!this.webviews.has(key)) this.webviews.set(key, new Set());
        this.webviews.get(key).add(panel.webview);
        panel.onDidDispose(() => { const s = this.webviews.get(key); if (s) s.delete(panel.webview); });
        panel.webview.options = {
            enableScripts: true,
            localResourceRoots: [vscode.Uri.joinPath(this.context.extensionUri, 'media'),
                ...(vscode.workspace.workspaceFolders || []).map((f) => f.uri)],
        };
        panel.webview.html = this.html(panel.webview);
        const send = () => panel.webview.postMessage({ type: 'load', bytes: Array.from(doc.bytes),
            name: path.basename(doc.uri.fsPath || doc.uri.path) });
        panel.webview.onDidReceiveMessage(async (m) => {
            if (m.type === 'ready') send();
            else if (m.type === 'edit') this.edit(doc, new Uint8Array(m.bytes), m.label || 'Cambio', panel.webview);
            else if (m.type === 'clipboard') {
                await vscode.env.clipboard.writeText(m.text);
                if (m.say) vscode.window.setStatusBarMessage(m.say, 4000);
            } else if (m.type === 'undo' || m.type === 'redo') {
                await vscode.commands.executeCommand(m.type);
            } else if (m.type === 'readFile' && typeof m.path === 'string') {
                // another file next to this one (the tileset of a map, the sprite of an object)
                const base = vscode.Uri.joinPath(doc.uri, '..');
                let bytes = null;
                try { bytes = Array.from(await vscode.workspace.fs.readFile(vscode.Uri.joinPath(base, m.path))); } catch (e) { /* missing */ }
                panel.webview.postMessage({ type: 'file', id: m.id, path: m.path, bytes });
            } else if (m.type === 'pickFile') {
                const base = vscode.Uri.joinPath(doc.uri, '..');
                const got = await vscode.window.showOpenDialog({ defaultUri: base, canSelectMany: false,
                    filters: { 'Imágenes IFF': ['iff', 'ilbm', 'lbm', 'brush', 'bob', 'spr'] }, title: m.title });
                const rel = got && got[0] ? path.relative(base.fsPath, got[0].fsPath).split(path.sep).join('/') : null;
                panel.webview.postMessage({ type: 'picked', id: m.id, path: rel });
            } else if (m.type === 'error') {
                vscode.window.showErrorMessage(m.text);
            }
        });
    }

    /** A change from the webview: the new bytes, with undo and redo for VS Code */
    edit(doc, bytes, label, from) {
        const before = doc.bytes;
        doc.bytes = bytes;
        const set = (b) => { doc.bytes = b; this.post(doc, { type: 'load', bytes: Array.from(b), keep: true }); };
        // the other editors of the same file see it too
        for (const w of this.webviews.get(doc.uri.toString()) || [])
            if (w !== from) w.postMessage({ type: 'load', bytes: Array.from(bytes), keep: true });
        this._onDidChange.fire({ document: doc, label, undo: () => set(before), redo: () => set(bytes) });
    }

    async saveCustomDocument(doc) { await vscode.workspace.fs.writeFile(doc.uri, doc.bytes); }
    async saveCustomDocumentAs(doc, dest) { await vscode.workspace.fs.writeFile(dest, doc.bytes); }
    async revertCustomDocument(doc) {
        doc.bytes = await vscode.workspace.fs.readFile(doc.uri);
        this.post(doc, { type: 'load', bytes: Array.from(doc.bytes), keep: true });
    }
    async backupCustomDocument(doc, context) {
        await vscode.workspace.fs.writeFile(context.destination, doc.bytes);
        return { id: context.destination.toString(), delete: async () => {
            try { await vscode.workspace.fs.delete(context.destination); } catch (e) { /* gone */ }
        } };
    }
}

/** The sprite and BOB editor, for .iff, .ilbm, .lbm, .brush, .bob and .spr */
function registerSpriteEditor(context) {
    const IFF = require('./media/iff.js');
    const provider = new BinaryEditorProvider(context, {
        page: 'sprite.html', scripts: ['sprite.css', 'iff.js', 'spriteModel.js', 'sprite.js'],
        // an empty file: a BOB of 32 x 32 and 16 colours, as Forja's Amiga-B
        empty: () => IFF.writeIlbm(IFF.newSprite('bob', 32, 32, 4)),
    });
    context.subscriptions.push(vscode.window.registerCustomEditorProvider('dash.spriteEditor', provider,
        { webviewOptions: { retainContextWhenHidden: true }, supportsMultipleEditorsPerDocument: true }));
    return provider;
}

module.exports = { BinaryEditorProvider, BinaryDocument, registerSpriteEditor };
