// Dash for VS Code: commands that compile a Dash program and run it in FS-UAE.
// Plain JavaScript (no build step); the visual MUI editor comes in later tasks
// (docs/MUI_EDITOR.md).
const vscode = require('vscode');
const path = require('path');
const fs = require('fs');
const { DashUIEditorProvider } = require('./dashuiEditor');
const { registerSpriteEditor, registerMapEditor } = require('./spriteEditor');
const DashUI = require('./media/model');
const { preview, previewMachine, stopServers } = require('./amigaPreview');
const { newline, onTyped } = require('./endwise');
const { setupLanguageServer, stopLanguageServer } = require('./lspClient');
const { setupTasks, emulatorOptions, savedFile, outputFile, outputFolder } = require('./tasks');
const { missing } = require('./missing');
const { setupDebugger } = require('./debug');
const { setupDashuiCode } = require('./dashuiCode');
const { writeProject, cleanName } = require('./newProject');
const { checkUpdates } = require('./updates');

/** A .dashui given to VS Code when it starts ("code carpeta ventana.dashui") opens as JSON text: its editor
    is not there yet. Then, just after starting (not later: whoever opens one as text on purpose keeps it), the
    ones as text without changes go to the visual editor. */
function reopenStartupDashui() {
    if (!vscode.window.tabGroups || process.uptime() > 30) return;
    for (const group of vscode.window.tabGroups.all) {
        for (const tab of group.tabs) {
            const input = tab.input;
            if (!(input instanceof vscode.TabInputText) || !input.uri.path.endsWith('.dashui') || tab.isDirty) continue;
            vscode.commands.executeCommand('vscode.openWith', input.uri, 'dash.dashuiEditor',
                                           { viewColumn: group.viewColumn, preserveFocus: !tab.isActive })
                .then(() => vscode.window.tabGroups.close(tab)).then(undefined, () => {});
        }
    }
}

/** The dash.path setting, with ~ for the home folder */
function dashSetting() {
    const configured = vscode.workspace.getConfiguration('dash').get('path') || '';
    return configured.replace(/^~(?=$|\/)/, require('os').homedir());
}

/** The Dash compiler folder: the setting (if it is one), or the first folder up from the file with ./dash and
    compiler/. */
function findDash(fromFile) {
    const configured = dashSetting();
    if (configured) return fs.existsSync(path.join(configured, 'dash')) && fs.existsSync(path.join(configured, 'compiler'))
        ? configured : null;      // (a wrong one ran /x/dash: "not found" from the shell, and nothing more)
    let dir = path.dirname(fromFile);
    for (let i = 0; i < 12; i++) {
        if (fs.existsSync(path.join(dir, 'dash')) && fs.existsSync(path.join(dir, 'compiler'))) return dir;
        const parent = path.dirname(dir);
        if (parent === dir) break;
        dir = parent;
    }
    return null;
}

/** Why findDash gave nothing, and what to do */
function noDash() {
    const configured = dashSetting();
    return configured
        ? `El ajuste "dash.path" (${configured}) no es la carpeta del compilador Dash: tiene que tener ./dash y compiler/.`
        : 'No encuentro el compilador Dash: pon su carpeta en el ajuste "dash.path".';
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
    return savedFile(vscode, editor.document);         // (an untitled one: its name first)
}

/** Commands that the terminal will run (exported for the tests). */
function compileCommand(dashDir, file, folder = '') {
    const out = outputFile(file, folder);
    return `mkdir -p ${quote(path.dirname(out))} && ${quote(path.join(dashDir, 'dash'))} ${quote(file)} -o ${quote(out)}`;
}

function runCommand(dashDir, file, autoclose) {
    const tool = path.join(dashDir, 'tools', 'emu_run.py');
    const close = autoclose > 0 ? ` --autoclose ${Math.floor(autoclose)}` : '';
    // (--dash2: compiled with ./dash, Dash 2.0; a program with C goes through C with gcc)
    return `python3 ${quote(tool)} --dash2${close} ${quote(file)}`;
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
        vscode.window.showErrorMessage(noDash());
        return;
    }
    const t = dashTerminal(emulatorEnv());
    t.show(true);
    if (kind === 'compile') t.sendText(`cd ${quote(dashDir)} && ${compileCommand(dashDir, file, outputFolder(vscode))}`);
    else t.sendText(`cd ${quote(dashDir)} && ${runCommand(dashDir, file,
        vscode.workspace.getConfiguration('dash.emulator').get('autoclose'))}`);
}

/** "Ver en Amiga": the window in FS-UAE with MUI, its picture shown in the editor. The emulated Amiga stays
    on between previews (tools/emu_preview.py, one per machine): the first one boots it; the next ones take
    a couple of seconds, and the same window again is not compiled again. The machine: dash.emulator.machine
    (an A500 has no 68020 for MUI: the A1200). */
let previewRunning = false;
let previewNext = null;        // an automatic one ("al cambiar") that came while another ran: done after it
const machineNames = { a1200: 'A1200 (3.1)', 'a1200-32': 'A1200 (3.2)', rtg: '68040 con tarjeta gráfica' };
async function showOnAmiga(document, windowName, webview, auto) {
    // busy: the webview's button is off and says so while the emulator works. auto ("al cambiar", after
    // each change): no notification and no error window, only what the editor shows
    const say = (m) => webview.postMessage(Object.assign({ type: 'screenshot', busy: false }, m));
    const fail = (error) => { say({ error }); if (!auto) vscode.window.showErrorMessage('Ver en Amiga: ' + error); };
    if (previewRunning) {
        if (auto) {
            if (previewNext && previewNext[2] !== webview) previewNext[2].postMessage({ type: 'screenshot', busy: false });
            previewNext = [document, windowName, webview, auto];
            say({ status: 'En cola…', busy: true });
        } else say({ status: 'Ya hay una vista en marcha…', busy: true });
        return;
    }
    if (!trusted()) { fail(UNTRUSTED); return; }
    const dashDir = findDash(document.fileName);
    if (!dashDir) { fail(noDash()); return; }
    const config = vscode.workspace.getConfiguration('dash.emulator');
    const machine = previewMachine(config.get('machine') || 'a1200');
    const status = `"${windowName}" en el ${machineNames[machine]}…`;
    const work = () => preview({ dashDir, dashuiText: document.getText(), windowName, machine, env: emulatorEnv(),
                                 baseDir: path.dirname(document.fileName) });
    previewRunning = true;
    say({ status, busy: true });
    try {
        const { png } = vscode.window.withProgress && !auto
            ? await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification,
                                                 title: 'Ver en Amiga: ' + status }, work)
            : await work();
        say({ src: 'data:image/png;base64,' + png.toString('base64'), status: `"${windowName}" en el ${machineNames[machine]}` });
    } catch (e) {
        fail(missing(e.message) || 'No se pudo: ' + e.message);
    } finally {
        previewRunning = false;
        if (previewNext) {
            const next = previewNext;
            previewNext = null;
            setTimeout(() => showOnAmiga(...next), 0);
        }
    }
}

/**
 * "Dash: Nuevo sprite, BOB o mapa" (Amiga-B in Forja): which, where (from the explorer, the folder clicked), and it
 * opens in its editor. kind and target (tests): without questions.
 */
async function newGraphic(folder, kind, target) {
    const { KINDS, newGraphicBytes } = require('./newGraphic');
    let k = KINDS.find((x) => x.id === kind);
    if (!k) {
        k = await vscode.window.showQuickPick(KINDS.map((x) => Object.assign({ description: x.file }, x)),
            { title: 'Nuevo sprite, BOB o mapa', placeHolder: 'Qué quieres crear' });
        if (!k) return null;
    }
    let uri = target;
    if (!uri) {
        const base = folder && folder.fsPath ? folder
            : vscode.window.activeTextEditor ? vscode.Uri.file(path.dirname(vscode.window.activeTextEditor.document.fileName))
                : (vscode.workspace.workspaceFolders || [])[0] && vscode.workspace.workspaceFolders[0].uri;
        uri = await vscode.window.showSaveDialog({ defaultUri: base ? vscode.Uri.joinPath(base, k.file) : undefined,
            filters: k.id === 'map' ? { 'Mapas de tiles': ['fmap'] } : { 'Imágenes IFF': ['iff', 'bob', 'spr'] }, title: k.label });
        if (!uri) return null;
    }
    await vscode.workspace.fs.writeFile(uri, newGraphicBytes(k.id));
    await vscode.commands.executeCommand('vscode.openWith', uri, k.view);
    return uri;
}

/**
 * "Ver en Amiga" of the sprite and map editors (amigaView.js): the file as the editor has it, loaded by a small
 * program as a game would, pictured in the emulator. message: {tx, ty} (a map: the top left cell of the view)
 */
let graphicRunning = false;
async function graphicOnAmiga(kind, doc, webview, message) {
    const say = (m) => webview.postMessage(Object.assign({ type: 'amiga', busy: false }, m));
    const fail = (error) => { say({ error }); vscode.window.showErrorMessage('Ver en Amiga: ' + error); };
    if (graphicRunning) { say({ status: 'Ya hay una vista en marcha…', busy: true }); return; }
    if (!trusted()) { fail(UNTRUSTED); return; }
    const file = doc.uri.fsPath, dashDir = findDash(file);
    if (!dashDir) { fail(noDash()); return; }
    const IFF = require('./media/iff.js'), AV = require('./amigaView');
    const name = path.basename(file);
    const files = [{ name, bytes: doc.bytes }];
    let program;
    try {
        if (kind === 'sprite') program = AV.spriteProgram(IFF.readIlbm(doc.bytes), name);
        else {
            const m = IFF.readFmap(doc.bytes);
            let tileset = '', depth = 4;
            if (m.tileset) {
                const p = path.resolve(path.dirname(file), m.tileset);
                if (!fs.existsSync(p)) throw new Error(`no encuentro el tileset ${m.tileset}`);
                const bytes = fs.readFileSync(p);
                depth = IFF.readIlbm(new Uint8Array(bytes)).planes;
                tileset = path.basename(p) === name ? 'tileset_' + path.basename(p) : path.basename(p);
                files.push({ name: tileset, bytes });
            }
            program = AV.mapProgram(m, name, tileset, message && message.tx, message && message.ty, depth);
        }
    } catch (e) { fail(e.message); return; }
    const machine = vscode.workspace.getConfiguration('dash.emulator').get('machine') || undefined;
    graphicRunning = true;
    say({ status: `${name} en el Amiga emulado…`, busy: true });
    try {
        const work = () => AV.runView({ dashDir, program, files, env: emulatorEnv(), machine });
        const { png } = vscode.window.withProgress
            ? await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: `Ver en Amiga: ${name}` }, work)
            : await work();
        say({ src: 'data:image/png;base64,' + png.toString('base64'), status: `${name} en el Amiga emulado` });
    } catch (e) {
        fail(missing(e.message) || 'No se pudo: ' + e.message);
    } finally {
        graphicRunning = false;
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
async function newProject(parent, name, open, kind) {
    if (!kind && name) kind = 'mui';                 // (the tests, and the walkthrough's: the MUI program)
    if (!kind) {
        const picked = await vscode.window.showQuickPick([
            { id: 'mui', label: 'Aplicación con ventana MUI', detail: 'Un programa con su ventana del editor visual (MUI y un 68020)' },
            { id: 'game', label: 'Juego', detail: 'Un jugador (sprite de hardware), un nivel (mapa de tiles con choques) y el programa que lo mueve con el joystick' },
        ], { title: 'Nuevo proyecto de Dash', placeHolder: 'Qué clase de programa' });
        if (!picked) return null;
        kind = picked.id;
    }
    if (!name) {
        name = await vscode.window.showInputBox({ title: 'Nuevo proyecto de Dash', prompt: 'Nombre del programa',
                                                  value: kind === 'game' ? 'juego' : 'hola', validateInput: (v) => (v.trim() ? null : 'Pon un nombre') });
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
        program = writeProject(folder, name, configured ? null : findDash(path.join(folder, 'x')), kind);
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

/** The context key dash.compilerFound (the walkthrough's first step is done when the compiler is found: by the
    setting, or in a folder of the workspace inside the Dash repository) */
function updateCompilerContext() {
    const configured = vscode.workspace.getConfiguration('dash').get('path');
    const ok = configured ? fs.existsSync(path.join(configured, 'dash')) && fs.existsSync(path.join(configured, 'compiler'))
        : (vscode.workspace.workspaceFolders || []).some((f) => !!findDash(path.join(f.uri.fsPath, 'x')));
    if (vscode.commands.executeCommand) vscode.commands.executeCommand('setContext', 'dash.compilerFound', ok).then(undefined, () => {});
}

function activate(context) {
    extContext = context;
    updateCompilerContext();
    if (vscode.workspace.onDidChangeConfiguration)
        context.subscriptions.push(vscode.workspace.onDidChangeConfiguration((e) => {
            if (e.affectsConfiguration('dash.path')) updateCompilerContext();
        }));
    context.subscriptions.push(
        vscode.commands.registerCommand('dash.compile', () => run('compile')),
        vscode.commands.registerCommand('dash.runInEmulator', () => run('emulator')),
        vscode.commands.registerCommand('dash.newWindowFile', newWindowFile),
        vscode.commands.registerCommand('dash.newGraphic', (folder) => newGraphic(folder)),
        vscode.commands.registerCommand('dash.newProject', newProject),
        vscode.commands.registerCommand('dash.choosePath', choosePath),
        vscode.commands.registerCommand('dash.newline', () => newline(vscode)),   // Enter: the "end" by itself
        vscode.workspace.onDidChangeTextDocument((e) => onTyped(vscode, e)),     // else/elif/end to their level
        DashUIEditorProvider.register(context, showOnAmiga),
    );
    registerSpriteEditor(context, (doc, webview, m) => graphicOnAmiga('sprite', doc, webview, m));   // .iff (as Forja's)
    registerMapEditor(context, (doc, webview, m) => graphicOnAmiga('map', doc, webview, m));         // .fmap (as Forja's)
    setupDashuiCode(vscode, context);                 // .dashui problems, and from an event to its code
    reopenStartupDashui();
    // a project just made in this window: its program open, beside the walkthrough
    const after = context.globalState && context.globalState.get('dash.openAfter');
    if (after) {
        context.globalState.update('dash.openAfter', undefined);
        if (fs.existsSync(after)) vscode.window.showTextDocument(vscode.Uri.file(after)).then(undefined, () => {});
    }
    setupLanguageServer(vscode, context, findDash, noDash);   // errors while typing (compiler/lsp.py)
    if (vscode.tasks && vscode.tasks.registerTaskProvider)   // (not in the tests' fake vscode)
        runTask = setupTasks(vscode, context, { findDash, noDash, env: emulatorEnv, trusted });
    if (vscode.debug && vscode.debug.registerDebugConfigurationProvider)   // F5: debug on the Amiga (gdb + bgdbserver)
        setupDebugger(vscode, context, { findDash, noDash, env: emulatorEnv, trusted, emulatorOptions });
    if (vscode.env && vscode.env.openExternal)       // a newer Dash on GitHub (once a day)
        checkUpdates(vscode, context, compilerInUse).catch(() => {});
}

/** The compiler folder for the open file or the first folder of the workspace (or the setting), or null */
function compilerInUse() {
    const editor = vscode.window.activeTextEditor;
    if (editor && editor.document.uri.scheme === 'file') return findDash(editor.document.fileName);
    const folder = vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders[0];
    if (folder) return findDash(path.join(folder.uri.fsPath, 'x'));
    return dashSetting() ? findDash(path.join(dashSetting(), 'x')) : null;
}

function deactivate() {
    stopServers();                        // the Amigas of "Ver en Amiga"
    return stopLanguageServer();
}

module.exports = { activate, deactivate, compileCommand, runCommand, findDash, showOnAmiga, newProject, newGraphic, graphicOnAmiga };
