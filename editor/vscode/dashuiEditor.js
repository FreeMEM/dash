// Custom editor for .dashui files: the JSON stays in VS Code's document (undo, save
// and dirty state as with any text file) and a webview shows it as palette, tree,
// properties and preview (media/editor.js).
const vscode = require('vscode');
const path = require('path');
const fs = require('fs');

class DashUIEditorProvider {
    constructor(context, onAmiga) {
        this.context = context;
        this.onAmiga = onAmiga;   // "Ver en Amiga": (document, windowName, webview, auto) => void
    }

    static register(context, onAmiga) {
        return vscode.window.registerCustomEditorProvider('dash.dashuiEditor', new DashUIEditorProvider(context, onAmiga),
            { webviewOptions: { retainContextWhenHidden: true }, supportsMultipleEditorsPerDocument: false });
    }

    html(webview) {
        const media = vscode.Uri.joinPath(this.context.extensionUri, 'media');
        const uri = (f) => webview.asWebviewUri(vscode.Uri.joinPath(media, f)).toString();
        return fs.readFileSync(path.join(this.context.extensionPath, 'media', 'editor.html'), 'utf8')
            .replace(/\{\{cspSource\}\}/g, webview.cspSource)
            .replace('{{css}}', uri('editor.css'))
            .replace('{{model}}', uri('model.js'))
            .replace('{{editor}}', uri('editor.js'));
    }

    resolveCustomTextEditor(document, panel) {
        panel.webview.options = {
            enableScripts: true,
            localResourceRoots: [vscode.Uri.joinPath(this.context.extensionUri, 'media'),
                                 ...(vscode.workspace.workspaceFolders || []).map((f) => f.uri)],
        };
        panel.webview.html = this.html(panel.webview);
        const send = () => panel.webview.postMessage({ type: 'update', text: document.getText(),
            amigaAuto: !!vscode.workspace.getConfiguration('dash.emulator').get('previewOnChange') });
        const changes = vscode.workspace.onDidChangeTextDocument((e) => {
            if (e.document.uri.toString() === document.uri.toString() && e.contentChanges.length) send();
        });
        panel.onDidDispose(() => changes.dispose());
        panel.webview.onDidReceiveMessage(async (m) => {
            if (m.type === 'ready') send();
            // (the editor's text has \n; a file with Windows line ends keeps them: VS Code puts its own)
            else if (m.type === 'edit' && m.text !== document.getText().replace(/\r\n/g, '\n')) {
                const edit = new vscode.WorkspaceEdit();
                edit.replace(document.uri, new vscode.Range(0, 0, document.lineCount, 0), m.text);
                await vscode.workspace.applyEdit(edit);
            } else if (m.type === 'gotoEvent') {
                await vscode.commands.executeCommand('dash.gotoEvent', document.uri, m.event, m.name);
            } else if (m.type === 'undo' || m.type === 'redo') {
                await vscode.commands.executeCommand(m.type);   // the document's (the editor is the active one)
            } else if (m.type === 'amiga' && this.onAmiga) {
                this.onAmiga(document, m.window, panel.webview, !!m.auto);
            } else if (m.type === 'amigaAuto') {   // "al cambiar": remembered for every .dashui
                await vscode.workspace.getConfiguration('dash.emulator').update('previewOnChange', !!m.on, true);
            }
        });
    }
}

module.exports = { DashUIEditorProvider };
