// @ts-check
// Tasks of type "dash" (Terminal > Run Task, tasks.json, Ctrl+Shift+B): compile, run in the emulator, run
// with --memcheck or --profile. Their output goes through the "$dash" problem matcher (package.json:
// file:line:column: Error: message, as compiler/main.py prints them) and "$gcc" for the C, so the errors
// land in Problems and on the code. Also the CodeLens over Main and the status bar button.
const path = require('path');

/** @param {string} arg */
function quote(arg) {
    return "'" + String(arg).replace(/'/g, "'\\''") + "'";
}

const KINDS = {
    compile: { label: 'Compilar', run: false, flag: '' },
    run: { label: 'Ejecutar en el emulador', run: true, flag: '' },
    memcheck: { label: 'Ejecutar con comprobación de memoria', run: true, flag: '--memcheck' },
    profile: { label: 'Ejecutar con perfil', run: true, flag: '--profile' },
};

const MACHINES = {
    a1200: 'A1200 (3.1)', a500: 'A500 (68000, 3.1)', 'a1200-32': 'A1200 (AmigaOS 3.2)', rtg: '68040 con RTG (3.2)',
};

/**
 * The shell command of a task (run in the Dash compiler's folder).
 * @param {string} kind compile, run, memcheck or profile
 * @param {string} dashDir
 * @param {string} file the .dash
 * @param {{autoclose?: number, machine?: string, emulator?: string, window?: boolean, system?: string}} [options]
 */
function taskCommand(kind, dashDir, file, options = {}) {
    const k = KINDS[kind];
    if (!k) throw new Error('tarea desconocida: ' + kind);
    const out = path.join(path.dirname(file), 'bin', path.basename(file, '.dash'));
    // a program that waits for its window to be closed ends by itself in the emulator after autoclose s
    // (test mode, DASH_TEST_AUTOCLOSE, read when it is compiled)
    const seconds = k.run && options.autoclose && options.autoclose > 0 ? Math.floor(options.autoclose) : 0;
    // to run it: each Print goes out at once (DASH_PRINT_FLUSH), so the output shows while it runs
    const compile = `mkdir -p ${quote(path.dirname(out))} && ` + (seconds ? `DASH_TEST_AUTOCLOSE=${seconds} ` : '') +
        (k.run ? 'DASH_PRINT_FLUSH=1 ' : '') +
        `${quote(path.join(dashDir, 'dash'))} -q` + (k.flag ? ' ' + k.flag : '') + ` ${quote(file)} -o ${quote(out)}`;
    if (!k.run) return compile;
    // the program is built here (with its option) and the emulator runs the binary as it is
    const emu = [' --follow'];
    if (options.window !== false) emu.push(' --window');
    if (options.machine && options.machine !== 'a1200') emu.push(` --machine ${quote(options.machine)}`);
    if (options.emulator === 'amiberry') emu.push(' --emulator amiberry');
    if (options.system) emu.push(` --system ${quote(options.system)}`);
    return `${compile} && python3 ${quote(path.join(dashDir, 'tools', 'emu_run.py'))}${emu.join('')} ${quote(out)}`;
}

/**
 * A vscode.Task for a .dash file.
 * @param {typeof import('vscode')} vscode
 * @param {string} kind
 * @param {string} file
 * @param {string} dashDir
 * @param {Record<string, string>} env
 * @param {{autoclose?: number}} options
 * @param {any} [definition] the one of tasks.json, when it comes from there
 */
function makeTask(vscode, kind, file, dashDir, env, options, definition, onOutput) {
    const def = definition || { type: 'dash', task: kind, file };
    const command = taskCommand(kind, dashDir, file, options);
    // running ones go through a terminal of ours, to read what the program said (the profile's table...)
    const execution = KINDS[kind].run && onOutput
        ? new vscode.CustomExecution(async () => shellTerminal(vscode, command, dashDir, env, (out, code) => onOutput(kind, file, out, code),
                                                             `${KINDS[kind].label}: ${path.basename(file)}…`))
        : new vscode.ShellExecution(command, { cwd: dashDir, env });
    // with the language server on, its diagnostics are the same as $dash's: the errors came out twice in Problems
    const lsp = !vscode.workspace || !vscode.workspace.getConfiguration ||
        vscode.workspace.getConfiguration('dash.languageServer').get('enabled', true) !== false;
    const task = new vscode.Task(def, vscode.TaskScope.Workspace, `${KINDS[kind].label}: ${path.basename(file)}`,
                                 'dash', execution, lsp ? ['$dash-memcheck', '$gcc'] : ['$dash', '$dash-memcheck', '$gcc']);
    if (kind === 'compile') task.group = vscode.TaskGroup.Build;
    // (echo off: not the whole command line before the output)
    task.presentationOptions = { reveal: vscode.TaskRevealKind.Always, clear: true, echo: false };
    return task;
}

/**
 * A pseudoterminal that runs a shell command (as ShellExecution would), shows its output and gives it
 * all to done(output, exit code) at the end. Closing it (stopping the task) ends the command's group.
 * @param {typeof import('vscode')} vscode
 */
function shellTerminal(vscode, command, cwd, env, done, title) {
    const { spawn } = require('child_process');
    const write = new vscode.EventEmitter();
    const close = new vscode.EventEmitter();
    let child = null;
    let all = '';
    const stop = () => { try { if (child && child.exitCode === null) process.kill(-child.pid, 'SIGTERM'); } catch (e) { /* gone */ } };
    return {
        onDidWrite: write.event,
        onDidClose: close.event,
        open() {
            // what it does, in words (the whole command line was noise: "mkdir -p ... && ... emu_run.py ...")
            write.fire(`\x1b[2m${title || '$ ' + command}\x1b[0m\r\n`);
            child = spawn('/bin/sh', ['-c', command], { cwd, env: Object.assign({}, process.env, env), detached: true });
            const out = (data) => {
                const text = data.toString('utf8');
                all += text;
                write.fire(text.replace(/\r?\n/g, '\r\n'));
            };
            child.stdout.on('data', out);
            child.stderr.on('data', out);
            child.on('close', (code) => {
                try { done(all, code); } catch (e) { write.fire(String(e) + '\r\n'); }
                close.fire(code === null ? 1 : code);
            });
            child.on('error', (e) => { write.fire(String(e) + '\r\n'); close.fire(1); });
        },
        close: stop,
        handleInput(data) { if (data === '\x03') stop(); },      // Ctrl+C
    };
}

/** The table of --profile in the output: [{own, total, calls, name}] (lines "perfil: 12.3% 45.6% 789 nombre") */
function parseProfile(output) {
    const rows = [];
    for (const line of output.split(/\r?\n/)) {
        const m = /^perfil:\s+([\d.]+)%\s+([\d.]+)%\s+(\d+)\s+(\S.*)$/.exec(line);
        if (m) rows.push({ own: Number(m[1]), total: Number(m[2]), calls: Number(m[3]), name: m[4].trim() });
    }
    const samples = /^perfil: (\d+) muestras/m.exec(output);
    return { rows, samples: samples ? Number(samples[1]) : 0 };
}

/** The profile in a webview: a table sorted by own time; a click on a function goes to it */
function showProfile(vscode, file, profile) {
    const panel = vscode.window.createWebviewPanel('dash.profile', 'Perfil: ' + path.basename(file),
                                                   vscode.ViewColumn.Beside, { enableScripts: true });
    const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
    const rows = profile.rows.map((r) => `<tr><td class="n">${r.own.toFixed(1)} %</td><td class="n">${r.total.toFixed(1)} %</td>` +
        `<td class="n">${r.calls}</td><td><a href="#" data-name="${esc(r.name)}">${esc(r.name)}</a>` +
        `<div class="bar" style="width:${Math.min(100, r.own)}%"></div></td></tr>`).join('');
    panel.webview.html = `<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';">
<style>body{font-family:var(--vscode-font-family);color:var(--vscode-foreground)}table{border-collapse:collapse;width:100%}
td,th{padding:3px 8px;border-bottom:1px solid var(--vscode-panel-border)}th{text-align:left}.n{text-align:right;font-variant-numeric:tabular-nums}
a{color:var(--vscode-textLink-foreground)}.bar{height:3px;background:var(--vscode-charts-orange)}</style></head><body>
<p>${profile.samples} muestras (50 por segundo). <b>Propio</b>: tiempo en la función; <b>total</b>: con lo que llama.</p>
<table><tr><th>Propio</th><th>Total</th><th>Llamadas</th><th>Función</th></tr>${rows}</table>
<script>const vscode = acquireVsCodeApi();
document.querySelectorAll('a[data-name]').forEach((a) => a.addEventListener('click', (e) => {
  e.preventDefault(); vscode.postMessage({ goTo: a.dataset.name }); }));</script></body></html>`;
    panel.webview.onDidReceiveMessage((m) => m.goTo && goToFunction(vscode, m.goTo));
    return panel;
}

/** Opens the definition of a function ("f" or "Struct.metodo") through the language server's symbols */
async function goToFunction(vscode, name) {
    const [container, method] = name.includes('.') ? name.split('.', 2) : [null, name];
    const found = (await vscode.commands.executeCommand('vscode.executeWorkspaceSymbolProvider', method)) || [];
    const hit = found.find((s) => s.name === method && (!container || s.containerName === container)) ||
                found.find((s) => s.name === method);
    if (!hit) { vscode.window.showWarningMessage(`No encuentro ${name}`); return; }
    const doc = await vscode.workspace.openTextDocument(hit.location.uri);
    await vscode.window.showTextDocument(doc, { selection: hit.location.range, viewColumn: vscode.ViewColumn.One });
}

/**
 * @param {typeof import('vscode')} vscode
 * @param {import('vscode').ExtensionContext} context
 * @param {{findDash: (f: string) => string | null, env: () => Record<string, string>, trusted: () => boolean}} helpers
 */
function setupTasks(vscode, context, helpers) {
    // what a run left: the profile's table in a panel
    const afterRun = (kind, file, output) => {
        const profile = parseProfile(output);
        if (profile.rows.length) showProfile(vscode, file, profile);
    };
    const forFile = (kind, file, definition) => {
        const dashDir = helpers.findDash(file);
        return dashDir ? makeTask(vscode, kind, file, dashDir, helpers.env(), emulatorOptions(vscode, file), definition, afterRun) : null;
    };
    const activeFile = () => {
        const e = vscode.window.activeTextEditor;
        return e && e.document.languageId === 'dash' && e.document.uri.scheme === 'file' ? e.document.fileName : null;
    };
    context.subscriptions.push(vscode.tasks.registerTaskProvider('dash', {
        provideTasks: () => {
            const file = activeFile();
            if (!file || !helpers.trusted()) return [];
            return Object.keys(KINDS).map((k) => forFile(k, file)).filter(Boolean);
        },
        resolveTask: (task) => {
            const def = task.definition;
            let file = def.file;
            if (!file || file === '${file}') file = activeFile();
            if (!file || !KINDS[def.task] || !helpers.trusted()) return undefined;
            return forFile(def.task, file, def);
        },
    }));

    /** Runs a task on the active .dash (saved first); the commands of the palette, CodeLens and status bar. */
    async function runTask(kind, file) {
        if (!helpers.trusted()) {
            vscode.window.showWarningMessage('Carpeta sin confianza (modo restringido): para compilar o usar el ' +
                                             'emulador, confía en ella ("Manage" en la barra de arriba).');
            return;
        }
        const editor = vscode.window.activeTextEditor;
        if (!file) {
            if (!editor || editor.document.languageId !== 'dash') {
                vscode.window.showWarningMessage('Abre un fichero .dash');
                return;
            }
            file = editor.document.fileName;
        }
        const doc = vscode.workspace.textDocuments.find((d) => d.fileName === file);
        if (doc && doc.isDirty) await doc.save();
        const task = forFile(kind, file);
        if (!task) {
            vscode.window.showErrorMessage('No encuentro el compilador Dash: pon su carpeta en el ajuste "dash.path".');
            return;
        }
        return vscode.tasks.executeTask(task);
    }

    // over Main: run, compile
    context.subscriptions.push(vscode.languages.registerCodeLensProvider({ language: 'dash' }, {
        provideCodeLenses: (document) => {
            const lenses = [];
            for (let i = 0; i < document.lineCount; i++) {
                if (/^Main\b/.test(document.lineAt(i).text)) {
                    const range = new vscode.Range(i, 0, i, 4);
                    lenses.push(new vscode.CodeLens(range, { title: '▶ Ejecutar', command: 'dash.runInEmulator', tooltip: 'En el emulador' }));
                    lenses.push(new vscode.CodeLens(range, { title: 'Depurar', command: 'dash.debug', tooltip: 'F5: breakpoints, pasos y variables en el Amiga' }));
                    lenses.push(new vscode.CodeLens(range, { title: 'Compilar', command: 'dash.compile' }));
                    lenses.push(new vscode.CodeLens(range, { title: 'Memoria', command: 'dash.runMemcheck', tooltip: 'Ejecutar con --memcheck' }));
                    lenses.push(new vscode.CodeLens(range, { title: 'Perfil', command: 'dash.runProfile', tooltip: 'Ejecutar con --profile' }));
                    break;
                }
            }
            return lenses;
        },
    }));

    // the status bar: Run, and the machine it runs on (a click changes it), while a .dash is in front
    const item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 50);
    item.text = '$(play) Dash';
    item.tooltip = 'Ejecutar en el emulador (Dash)';
    item.command = 'dash.runInEmulator';
    const machineItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 49);
    machineItem.command = 'dash.chooseMachine';
    const update = () => {
        const config = vscode.workspace.getConfiguration('dash.emulator');
        const machine = config.get('machine') || 'a1200';
        machineItem.text = '$(device-desktop) ' + (MACHINES[machine] || machine).split(' (')[0] +
            (config.get('program') === 'amiberry' ? ' · Amiberry' : '');
        machineItem.tooltip = 'Máquina del emulador: ' + (MACHINES[machine] || machine) + ' (clic para cambiarla)';
        if (activeFile()) { item.show(); machineItem.show(); } else { item.hide(); machineItem.hide(); }
    };
    update();
    context.subscriptions.push(item, machineItem, vscode.window.onDidChangeActiveTextEditor(update),
                               vscode.workspace.onDidChangeConfiguration((e) => e.affectsConfiguration('dash.emulator') && update()));
    context.subscriptions.push(vscode.commands.registerCommand('dash.chooseMachine', async () => {
        const config = vscode.workspace.getConfiguration('dash.emulator');
        const items = Object.entries(MACHINES).map(([id, label]) => ({ label, id, emulator: 'fs-uae',
                                                                       description: 'FS-UAE' }))
            .concat([['a1200', 'A1200 (3.1)'], ['a500', 'A500 (68000, 3.1)'], ['a1200-32', 'A1200 (AmigaOS 3.2)']]
                .map(([id, label]) => ({ label, id, emulator: 'amiberry', description: 'Amiberry (con sucesos de sockets)' })));
        const pick = await vscode.window.showQuickPick(items, { placeHolder: 'Máquina en la que ejecutar los programas' });
        if (!pick) return;
        const target = vscode.workspace.workspaceFolders ? vscode.ConfigurationTarget.Workspace : vscode.ConfigurationTarget.Global;
        await config.update('machine', pick.id, target);
        await config.update('program', pick.emulator, target);
    }));

    context.subscriptions.push(
        vscode.commands.registerCommand('dash.runMemcheck', () => runTask('memcheck')),
        vscode.commands.registerCommand('dash.runProfile', () => runTask('profile')),
    );
    return runTask;
}

/**
 * How the emulator runs a file: its machine, emulator, window; the Workbench files with MUI when the
 * program uses MUI (on the A1200 with 3.1, dash.emulator.muiSystem).
 * @param {typeof import('vscode')} vscode
 * @param {string} file
 */
function emulatorOptions(vscode, file) {
    const config = vscode.workspace.getConfiguration('dash.emulator');
    const machine = config.get('machine') || 'a1200';
    const options = { autoclose: Number(config.get('autoclose')) || 0, machine, emulator: config.get('program') || 'fs-uae',
                      window: config.get('window') !== false };
    let text = '';
    try { text = require('fs').readFileSync(file, 'utf8'); } catch (e) { /* not saved yet */ }
    if (machine === 'a1200' && config.get('muiSystem') && /\bmui_|\.dashui"/.test(text)) options.system = config.get('muiSystem');
    return options;
}

module.exports = { taskCommand, makeTask, setupTasks, KINDS, MACHINES, emulatorOptions, parseProfile, shellTerminal };
