// Dash for VS Code: commands that compile a Dash program and run it in FS-UAE.
// Plain JavaScript (no build step); the visual MUI editor comes in later tasks
// (docs/MUI_EDITOR.md).
const vscode = require('vscode');
const path = require('path');
const fs = require('fs');
const { DashUIEditorProvider } = require('./dashuiEditor');
const DashUI = require('./media/model');
const { preview, previewMachine, stopServers } = require('./amigaPreview');
const { newline, onTyped } = require('./endwise');
const { setupLanguageServer, stopLanguageServer } = require('./lspClient');
const { setupTasks, emulatorOptions } = require('./tasks');
const { setupDebugger } = require('./debug');
const { setupDashuiCode } = require('./dashuiCode');
const { writeProject, cleanName } = require('./newProject');

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
                                        ['system32', 'DASH_EMU_SYS_32'], ['systemRtg', 'DASH_EMU_SYS_32_RTG'],
                                        ['muiSystem', 'DASH_EMU_SYS_MUI'], ['muiSystem32', 'DASH_EMU_SYS_32_MUI']])
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

/** "Ver en Amiga": the window in FS-UAE with MUI, its picture shown in the editor. The emulated Amiga stays
    on between previews (tools/emu_preview.py, one per machine): the first one boots it; the next ones take
    a couple of seconds, and the same window again is not compiled again. The machine: dash.emulator.machine
    (an A500 has no 68020 for MUI: the A1200). */
let previewRunning = false;
const machineNames = { a1200: 'A1200 (3.1)', 'a1200-32': 'A1200 (3.2)', rtg: '68040 con tarjeta gráfica' };
async function showOnAmiga(document, windowName, webview) {
    // busy: the webview's button is off and says so while the emulator works
    const say = (m) => webview.postMessage(Object.assign({ type: 'screenshot', busy: false }, m));
    const fail = (error) => { say({ error }); vscode.window.showErrorMessage('Ver en Amiga: ' + error); };
    if (previewRunning) { say({ status: 'Ya hay una vista en marcha…', busy: true }); return; }
    if (!trusted()) { fail(UNTRUSTED); return; }
    const dashDir = findDash(document.fileName);
    if (!dashDir) { fail('No encuentro el compilador Dash: pon su carpeta en el ajuste "dash.path".'); return; }
    const config = vscode.workspace.getConfiguration('dash.emulator');
    const machine = previewMachine(config.get('machine') || 'a1200');
    const status = `"${windowName}" en el ${machineNames[machine]}…`;
    const work = () => preview({ dashDir, dashuiText: document.getText(), windowName, machine, env: emulatorEnv(),
                                 baseDir: path.dirname(document.fileName) });
    previewRunning = true;
    say({ status, busy: true });
    try {
        const { png } = vscode.window.withProgress
            ? await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification,
                                                 title: 'Ver en Amiga: ' + status }, work)
            : await work();
        say({ src: 'data:image/png;base64,' + png.toString('base64'), status: `"${windowName}" en el ${machineNames[machine]}` });
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

/**
 * "Dash: Nuevo proyecto": a folder with a program and its window (newProject.js), opened. parent and name
 * (tests): without questions; open false: not opened. Returns the program's path.
 */
async function newProject(parent, name, open) {
    if (!name) {
        name = await vscode.window.showInputBox({ title: 'Nuevo proyecto de Dash', prompt: 'Nombre del programa',
                                                  value: 'hola', validateInput: (v) => (v.trim() ? null : 'Pon un nombre') });
        if (!name) return null;
    }
    if (!parent) {
        const picked = await vscode.window.showOpenDialog({ canSelectFolders: true, canSelectFiles: false,
                                                            openLabel: 'Crear el proyecto aquí', title: 'Dónde crear la carpeta del proyecto' });
        if (!picked || !picked.length) return null;
        parent = picked[0].fsPath;
    }
    const folder = path.join(parent, cleanName(name));
    let program;
    try {
        // the compiler: the setting (nothing to write), or the Dash repository the folder is in
        const configured = vscode.workspace.getConfiguration('dash').get('path');
        program = writeProject(folder, name, configured ? null : findDash(path.join(folder, 'x')));
    } catch (e) {
        vscode.window.showErrorMessage('No se pudo crear el proyecto: ' + e.message);
        return null;
    }
    if (open !== false) {
        const uri = vscode.Uri.file(folder);
        if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length) {
            await vscode.commands.executeCommand('vscode.openFolder', uri, { forceNewWindow: true });
        } else {
            await extContext.globalState.update('dash.openAfter', program);   // after the window reloads with the folder
            await vscode.commands.executeCommand('vscode.openFolder', uri);
        }
    }
    return program;
}

/** "Dash: Elegir la carpeta del compilador" (the walkthrough): the setting dash.path */
async function choosePath() {
    const picked = await vscode.window.showOpenDialog({ canSelectFolders: true, canSelectFiles: false,
                                                        openLabel: 'Esta es la carpeta de Dash', title: 'La carpeta del compilador Dash (la del repositorio)' });
    if (!picked || !picked.length) return;
    const dir = picked[0].fsPath;
    if (!fs.existsSync(path.join(dir, 'dash')) || !fs.existsSync(path.join(dir, 'compiler'))) {
        vscode.window.showWarningMessage(`En ${dir} no están ./dash ni compiler/: elige la carpeta del repositorio de Dash.`);
        return;
    }
    await vscode.workspace.getConfiguration('dash').update('path', dir, vscode.ConfigurationTarget.Global);
    vscode.window.showInformationMessage('Compilador Dash: ' + dir);
}

let extContext = null;

function activate(context) {
    extContext = context;
    context.subscriptions.push(
        vscode.commands.registerCommand('dash.compile', () => run('compile')),
        vscode.commands.registerCommand('dash.runInEmulator', () => run('emulator')),
        vscode.commands.registerCommand('dash.newWindowFile', newWindowFile),
        vscode.commands.registerCommand('dash.newProject', newProject),
        vscode.commands.registerCommand('dash.choosePath', choosePath),
        vscode.commands.registerCommand('dash.newline', () => newline(vscode)),   // Enter: the "end" by itself
        vscode.workspace.onDidChangeTextDocument((e) => onTyped(vscode, e)),     // else/elif/end to their level
        DashUIEditorProvider.register(context, showOnAmiga),
    );
    setupDashuiCode(vscode, context);                 // .dashui problems, and from an event to its code
    // a project just made in this window: its program open, beside the walkthrough
    const after = context.globalState && context.globalState.get('dash.openAfter');
    if (after) {
        context.globalState.update('dash.openAfter', undefined);
        if (fs.existsSync(after)) vscode.window.showTextDocument(vscode.Uri.file(after)).then(undefined, () => {});
    }
    setupLanguageServer(vscode, context, findDash);   // errors while typing (compiler/lsp.py)
    if (vscode.tasks && vscode.tasks.registerTaskProvider)   // (not in the tests' fake vscode)
        runTask = setupTasks(vscode, context, { findDash, env: emulatorEnv, trusted });
    if (vscode.debug && vscode.debug.registerDebugConfigurationProvider)   // F5: debug on the Amiga (gdb + bgdbserver)
        setupDebugger(vscode, context, { findDash, env: emulatorEnv, trusted, emulatorOptions });
}

function deactivate() {
    stopServers();                        // the Amigas of "Ver en Amiga"
    return stopLanguageServer();
}

module.exports = { activate, deactivate, compileCommand, runCommand, findDash, showOnAmiga, newProject };
