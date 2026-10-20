// @ts-check
// The client of Dash's language server (compiler/lsp.py of the Dash compiler, started with
// `python3 -m compiler.lsp` in the compiler's folder). Only in a trusted folder: the server runs code
// of that folder. It starts with the first .dash document, and again with "Dash: Reiniciar el servidor
// de lenguaje" (after changing dash.path, say).

/** @type {import('vscode-languageclient/node').LanguageClient | null} */
let client = null;
let starting = null;
let warnedOld = false;      // said once that dash.path has no compiler/lsp.py

/**
 * Starts the server if it is not running and there is a Dash compiler to start it from.
 * @param {typeof import('vscode')} vscode
 * @param {(fromFile: string) => string | null} findDash
 * @param {string} [fromFile] a .dash file, to look for the compiler up from it
 */
let warnedNoDash = false;
async function startLanguageServer(vscode, findDash, fromFile, noDash) {
    if (client || starting) return starting;
    const config = vscode.workspace.getConfiguration('dash');
    if (config.get('languageServer.enabled') === false || vscode.workspace.isTrusted === false) return null;
    const folder = (vscode.workspace.workspaceFolders || [])[0];
    const dashDir = (fromFile && findDash(fromFile)) || (folder && findDash(folder.uri.fsPath + '/x')) || null;
    if (!dashDir) {
        // once, with a .dash open: without it there are no errors while typing, and nothing said why
        if (noDash && !warnedNoDash) {
            warnedNoDash = true;
            vscode.window.showWarningMessage(noDash(), 'Abrir el ajuste').then((choice) => {
                if (choice) vscode.commands.executeCommand('workbench.action.openSettings', 'dash.path');
            });
        }
        return null;
    }
    if (!require('fs').existsSync(require('path').join(dashDir, 'compiler', 'lsp.py'))) {
        if (!warnedOld) {
            warnedOld = true;
            vscode.window.showInformationMessage(`El compilador Dash de ${dashDir} aún no trae servidor de lenguaje ` +
                '(compiler/lsp.py): sin errores mientras se escribe. Actualiza Dash o cambia el ajuste "dash.path".');
        }
        return null;
    }
    const { LanguageClient } = require('vscode-languageclient/node');
    const python = config.get('python') || 'python3';
    const serverOptions = { command: python, args: ['-m', 'compiler.lsp'], options: { cwd: dashDir } };
    const clientOptions = {
        documentSelector: [{ scheme: 'file', language: 'dash' }, { scheme: 'untitled', language: 'dash' }],
        outputChannelName: 'Dash (servidor de lenguaje)',
    };
    const c = new LanguageClient('dash', 'Dash', serverOptions, clientOptions);
    starting = c.start().then(() => { client = c; return c; }, (e) => {
        vscode.window.showErrorMessage(`No arranca el servidor de lenguaje de Dash (${python} -m compiler.lsp en ${dashDir}): ${e.message}`);
        return null;
    }).finally(() => { starting = null; });
    return starting;
}

async function stopLanguageServer() {
    const c = client;
    client = null;
    if (c) await c.stop();
}

/**
 * Starts it now if a .dash is open, or with the first one; and on trust being given.
 * @param {typeof import('vscode')} vscode
 * @param {import('vscode').ExtensionContext} context
 * @param {(fromFile: string) => string | null} findDash
 * @param {() => string} [noDash] why there is no compiler (said once)
 */
function setupLanguageServer(vscode, context, findDash, noDash) {
    const tryDoc = (doc) => {
        if (doc && doc.languageId === 'dash') startLanguageServer(vscode, findDash, doc.uri.scheme === 'file' ? doc.uri.fsPath : undefined, noDash);
    };
    (vscode.workspace.textDocuments || []).forEach(tryDoc);
    context.subscriptions.push(
        vscode.workspace.onDidOpenTextDocument(tryDoc),
        vscode.workspace.onDidGrantWorkspaceTrust(() => (vscode.workspace.textDocuments || []).forEach(tryDoc)),
        vscode.commands.registerCommand('dash.restartLanguageServer', async () => {
            await stopLanguageServer();
            const doc = vscode.window.activeTextEditor && vscode.window.activeTextEditor.document;
            const c = await startLanguageServer(vscode, findDash, doc && doc.uri.scheme === 'file' ? doc.uri.fsPath : undefined);
            if (!c) vscode.window.showWarningMessage('Servidor de lenguaje de Dash: no arranca (¿carpeta sin confianza, sin compilador Dash o apagado en dash.languageServer.enabled?)');
        }),
        { dispose: () => { stopLanguageServer(); } },
    );
}

module.exports = { setupLanguageServer, stopLanguageServer };
