// Dash for VS Code: commands that compile a Dash program and run it in FS-UAE.
// Plain JavaScript (no build step); the visual MUI editor comes in later tasks
// (docs/MUI_EDITOR.md).
const vscode = require('vscode');
const path = require('path');
const fs = require('fs');
const { DashUIEditorProvider } = require('./dashuiEditor');
const DashUI = require('./media/model');
const { runPreview } = require('./amigaPreview');
const { newline, onTyped } = require('./endwise');
const { setupLanguageServer, stopLanguageServer } = require('./lspClient');
const { setupTasks, emulatorOptions } = require('./tasks');
const { setupDebugger } = require('./debug');

/** The Dash compiler folder: the setting, or the first folder up from the file with ./dash and compiler/. */
function findDash(fromFile) {
    const configured = vscode.workspace.getConfiguration('dash').get('path');
    if (configured) return configured;
    let dir = path.dirname(fromFile);
    for (let i = 0; i < 12; i++) {
        if (fs.existsSync(path.join(dir, 'dash')) && fs.existsSync(path.join(dir, 'compiler'))) return dir;
        const parent = path.dirname(dir);
        if (parent === dir) break;
        dir = parent;
    }
    return null;
}

function quote(arg) {
    return "'" + String(arg).replace(/'/g, "'\\''") + "'";
}

/** The terminal where Dash commands run (one, reused). */
let terminal = null;
function dashTerminal(env) {
    if (terminal && terminal.exitStatus === undefined) return terminal;
    terminal = vscode.window.createTerminal({ name: 'Dash', env });
    return terminal;
}

/** The active .dash file, saved; null (with a message) if there is none. */
async function activeDashFile() {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.languageId !== 'dash') {
        vscode.window.showWarningMessage('Abre un fichero .dash');
        return null;
    }
    if (editor.document.isDirty) await editor.document.save();
    return editor.document.fileName;
}

/** Commands that the terminal will run (exported for the tests). */
function compileCommand(dashDir, file) {
    const out = path.join(path.dirname(file), 'bin', path.basename(file, '.dash'));
    return `mkdir -p ${quote(path.dirname(out))} && ${quote(path.join(dashDir, 'dash'))} ${quote(file)} -o ${quote(out)}`;
}

function runCommand(dashDir, file, autoclose) {
    const tool = path.join(dashDir, 'tools', 'emu_run.py');
    const close = autoclose > 0 ? ` --autoclose ${Math.floor(autoclose)}` : '';
    return `python3 ${quote(tool)}${close} ${quote(file)}`;
}

function emulatorEnv() {
    const config = vscode.workspace.getConfiguration('dash.emulator');
    const env = {};
    // the ROM and Workbench files of each machine (tools/emu_run.py --machine reads these variables)
    for (const [setting, variable] of [['kickstart', 'DASH_KICKSTART'], ['system', 'DASH_EMU_SYS'],
                                        ['kickstartA500', 'DASH_KICKSTART_A500'], ['kickstart32', 'DASH_KICKSTART_32'],
                                        ['system32', 'DASH_EMU_SYS_32'], ['systemRtg', 'DASH_EMU_SYS_32_RTG']])
        if (config.get(setting)) env[variable] = config.get(setting);
    return env;
}

// In Restricted Mode (a folder not trusted) nothing is compiled or run: only colours and the editor
const UNTRUSTED = 'Carpeta sin confianza (modo restringido): para compilar o usar el emulador, confía en ella ' +
                  '("Manage" en la barra de arriba).';
const trusted = () => vscode.workspace.isTrusted !== false;

/** Compile or run the active program: a task of type "dash" (tasks.js), so its errors go to Problems */
let runTask = null;
async function run(kind) {
    if (!trusted()) { vscode.window.showWarningMessage(UNTRUSTED); return; }
    if (runTask) return runTask(kind === 'compile' ? 'compile' : 'run');
    const file = await activeDashFile();
    if (!file) return;
    const dashDir = findDash(file);
    if (!dashDir) {
        vscode.window.showErrorMessage('No encuentro el compilador Dash: pon su carpeta en el ajuste "dash.path".');
        return;
    }
    const t = dashTerminal(emulatorEnv());
    t.show(true);
    if (kind === 'compile') t.sendText(`cd ${quote(dashDir)} && ${compileCommand(dashDir, file)}`);
    else t.sendText(`cd ${quote(dashDir)} && ${runCommand(dashDir, file,
        vscode.workspace.getConfiguration('dash.emulator').get('autoclose'))}`);
}

/** "Ver en Amiga": the window in FS-UAE with MUI, its picture shown in the editor */
let previewRunning = false;
async function showOnAmiga(document, windowName, webview) {
    // busy: the webview's button is off and says so while the emulator works (about 30 s)
    const say = (m) => webview.postMessage(Object.assign({ type: 'screenshot', busy: false }, m));
    const fail = (error) => { say({ error }); vscode.window.showErrorMessage('Ver en Amiga: ' + error); };
    if (previewRunning) { say({ status: 'Ya hay una vista en marcha…', busy: true }); return; }
    if (!trusted()) { fail(UNTRUSTED); return; }
    const dashDir = findDash(document.fileName);
    if (!dashDir) { fail('No encuentro el compilador Dash: pon su carpeta en el ajuste "dash.path".'); return; }
    const config = vscode.workspace.getConfiguration('dash.emulator');
    const status = `Compilando "${windowName}" y arrancando el emulador (unos 30 s)…`;
    const work = () => runPreview({
        dashDir, dashuiText: document.getText(), windowName,
        kickstart: config.get('kickstart') || process.env.DASH_KICKSTART,
        system: config.get('muiSystem') || process.env.DASH_EMU_SYS_MUI,
    });
    previewRunning = true;
    say({ status, busy: true });
    try {
        const { png } = vscode.window.withProgress
            ? await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification,
                                                 title: 'Ver en Amiga: ' + status }, work)
            : await work();
        say({ src: 'data:image/png;base64,' + png.toString('base64'), status: `"${windowName}" en el Amiga emulado` });
    } catch (e) {
        fail('No se pudo: ' + e.message);
    } finally {
        previewRunning = false;
    }
}

/** New .dashui file with one empty window, opened in the visual editor */
async function newWindowFile() {
    const uri = await vscode.window.showSaveDialog({ filters: { 'Ventanas MUI': ['dashui'] } });
    if (!uri) return;
    await vscode.workspace.fs.writeFile(uri, Buffer.from(DashUI.serialize(DashUI.newDocument()), 'utf8'));
    await vscode.commands.executeCommand('vscode.openWith', uri, 'dash.dashuiEditor');
}

function activate(context) {
    context.subscriptions.push(
        vscode.commands.registerCommand('dash.compile', () => run('compile')),
        vscode.commands.registerCommand('dash.runInEmulator', () => run('emulator')),
        vscode.commands.registerCommand('dash.newWindowFile', newWindowFile),
        vscode.commands.registerCommand('dash.newline', () => newline(vscode)),   // Enter: the "end" by itself
        vscode.workspace.onDidChangeTextDocument((e) => onTyped(vscode, e)),     // else/elif/end to their level
        DashUIEditorProvider.register(context, showOnAmiga),
    );
    setupLanguageServer(vscode, context, findDash);   // errors while typing (compiler/lsp.py)
    if (vscode.tasks && vscode.tasks.registerTaskProvider)   // (not in the tests' fake vscode)
        runTask = setupTasks(vscode, context, { findDash, env: emulatorEnv, trusted });
    if (vscode.debug && vscode.debug.registerDebugConfigurationProvider)   // F5: debug on the Amiga (gdb + bgdbserver)
        setupDebugger(vscode, context, { findDash, env: emulatorEnv, trusted, emulatorOptions });
}

function deactivate() {
    return stopLanguageServer();
}

module.exports = { activate, deactivate, compileCommand, runCommand, findDash, showOnAmiga };
