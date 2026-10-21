// @ts-check
// A .dashui and its code (docs/IDE_LOOP.md, task 19): its problems in the Problems panel while it is
// edited (as text or in the visual editor), and "Dash: Ir al código del evento": from an event number of
// the .dashui to where a .dash that imports it handles it, or the code for it created there.
const path = require('path');
const fs = require('fs');
const L = require('./dashuiLinks');

/** @param {typeof import('vscode')} vscode */
function setupDashuiCode(vscode, context) {
    const isDashui = (doc) => doc.uri.scheme === 'file' && doc.fileName.endsWith('.dashui');
    if (vscode.languages && vscode.languages.createDiagnosticCollection) {
        const diagnostics = vscode.languages.createDiagnosticCollection('dashui');
        const check = (doc) => {
            if (!isDashui(doc)) return;
            diagnostics.set(doc.uri, L.problems(doc.getText()).map((p) => {
                const d = new vscode.Diagnostic(new vscode.Range(p.start.line, p.start.character, p.end.line, p.end.character),
                    p.message, p.severity === 'warning' ? vscode.DiagnosticSeverity.Warning : vscode.DiagnosticSeverity.Error);
                d.source = 'dashui';
                return d;
            }));
        };
        context.subscriptions.push(diagnostics,
            vscode.workspace.onDidOpenTextDocument(check),
            vscode.workspace.onDidChangeTextDocument((e) => check(e.document)),
            vscode.workspace.onDidCloseTextDocument((doc) => diagnostics.delete(doc.uri)));
        vscode.workspace.textDocuments.forEach(check);
    }

    /** The .dash files that import this .dashui: of the workspace, else of its folder; [{uri, text}] */
    async function users(dashuiUri) {
        const base = path.basename(dashuiUri.fsPath);
        const folder = vscode.workspace.getWorkspaceFolder(dashuiUri);
        let uris = folder ? await vscode.workspace.findFiles(new vscode.RelativePattern(folder, '**/*.dash'), '**/node_modules/**', 500)
            : [];
        if (!uris.length) {
            const dir = path.dirname(dashuiUri.fsPath);
            uris = fs.readdirSync(dir).filter((f) => f.endsWith('.dash')).map((f) => vscode.Uri.file(path.join(dir, f)));
        }
        const out = [];
        for (const uri of uris) {
            const open = vscode.workspace.textDocuments.find((d) => d.uri.toString() === uri.toString());
            const text = open ? open.getText() : fs.readFileSync(uri.fsPath, 'utf8');
            if (L.importsDashui(text, base)) out.push({ uri, text });
        }
        // the one in the same folder first
        out.sort((a, b) => (path.dirname(b.uri.fsPath) === path.dirname(dashuiUri.fsPath) ? 1 : 0) -
                           (path.dirname(a.uri.fsPath) === path.dirname(dashuiUri.fsPath) ? 1 : 0));
        return out;
    }

    async function show(uri, line, character) {
        const editor = await vscode.window.showTextDocument(uri, { viewColumn: vscode.ViewColumn.Beside, preview: false });
        const pos = new vscode.Position(line, character);
        editor.selection = new vscode.Selection(pos, pos);
        editor.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);
        return editor;
    }

    /**
     * Event n of the .dashui at dashuiUri, of the object called name: to its code. create: true (tests), make
     * it without asking when there is none; else a question. Returns {uri, line, created} or null.
     */
    async function gotoEvent(dashuiUri, n, name, create) {
        if (!dashuiUri || !Number.isInteger(n) || n <= 0) {
            vscode.window.showWarningMessage('Ese objeto no tiene número de evento: pon uno en sus propiedades.');
            return null;
        }
        const files = await users(dashuiUri);
        if (!files.length) {
            vscode.window.showWarningMessage(`Ningún .dash importa ${path.basename(dashuiUri.fsPath)} (import "${path.basename(dashuiUri.fsPath)}").`);
            return null;
        }
        for (const f of files) {
            const found = L.handlers(f.text, n).filter((h) => !h.constant);
            if (found.length) {
                await show(f.uri, found[0].line, found[0].character);
                return { uri: f.uri, line: found[0].line, created: false };
            }
        }
        const f = files[0];
        if (!create) {
            const answer = await vscode.window.showInformationMessage(
                `${path.basename(f.uri.fsPath)} no trata el evento ${n}${name ? ' (' + name + ')' : ''}. ¿Crear su código?`, 'Crear');
            if (answer !== 'Crear') return null;
        }
        const plan = L.addHandler(f.text, n, name);
        const edit = new vscode.WorkspaceEdit();
        for (const e of plan.edits) edit.insert(f.uri, new vscode.Position(e.line, 0), e.text + '\n');
        await vscode.workspace.applyEdit(edit);
        const at = plan.handler || { line: plan.edits[0].line, character: 0 };
        await show(f.uri, at.line, at.character);
        if (!plan.handler) {
            vscode.window.showInformationMessage(`Añadida la constante ${plan.name}: no hay un bucle de mui_wait_event donde poner su código.`);
        }
        return { uri: f.uri, line: at.line, created: true, name: plan.name };
    }

    context.subscriptions.push(vscode.commands.registerCommand('dash.gotoEvent', gotoEvent));
    return { gotoEvent };
}

module.exports = { setupDashuiCode };
