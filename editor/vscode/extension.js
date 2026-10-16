// Dash for VS Code: commands that compile a Dash program and run it in FS-UAE.
// Plain JavaScript (no build step); the visual MUI editor comes in later tasks
// (docs/MUI_EDITOR.md).
const vscode = require('vscode');
const path = require('path');
const fs = require('fs');
const { DashUIEditorProvider } = require('./dashuiEditor');
const DashUI = require('./media/model');

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
    if (config.get('kickstart')) env.DASH_KICKSTART = config.get('kickstart');
    if (config.get('system')) env.DASH_EMU_SYS = config.get('system');
    return env;
}

async function run(kind) {
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
        DashUIEditorProvider.register(context, (document, windowName) =>
            vscode.window.showInformationMessage(`Ver en Amiga: ${windowName} (pendiente, tarea 23)`)),
    );
}

function deactivate() {}

module.exports = { activate, deactivate, compileCommand, runCommand, findDash };
