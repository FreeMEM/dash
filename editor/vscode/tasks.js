// @ts-check
// Tasks of type "dash" (Terminal > Run Task, tasks.json, Ctrl+Shift+B): compile, run in the emulator, run
// with --memcheck or --profile. Their output goes through the "$dash" problem matcher (package.json:
// file:line:column: Error: message, as compiler/main.py prints them) and "$gcc" for the C, so the errors
// land in Problems and on the code. Also the CodeLens over Main and the status bar button.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { missing } = require('./missing');

/**
 * Where the executable of a .dash goes: bin/ next to it (the default) or the folder of dash.outputFolder (absolute,
 * ~/..., or relative to the .dash's folder), like Forja's "Ejecutables en:".
 * @param {string} file the .dash
 * @param {string} [folder] dash.outputFolder
 * @param {string} [suffix] '.debug' for the debugger's build
 */
function outputFile(file, folder, suffix = '') {
    const name = path.basename(file, '.dash') + suffix;
    let dir = String(folder || '').trim();
    if (!dir) return path.join(path.dirname(file), 'bin', name);
    if (dir === '~' || dir.startsWith('~/')) dir = path.join(os.homedir(), dir.slice(1));
    return path.join(path.resolve(path.dirname(file), dir), name);
}

/** dash.outputFolder ('' without it) */
function outputFolder(vscode) {
    try { return vscode.workspace.getConfiguration('dash').get('outputFolder') || ''; } catch (e) { return ''; }
}

// ./dash: Dash 2.0 (dashc), which has what these tasks use (--fpu, --cpu, DASH_TEST_AUTOCLOSE, DASH_PRINT_FLUSH); a
// program with C in it ./dash compiles it through C with gcc (DASH_FALLBACK_DASH1 for Dash 2.0.0)
function dashExe(dashDir) {
    return 'dash';
}

/** @param {string} arg */
function quote(arg) {
    return "'" + String(arg).replace(/'/g, "'\\''") + "'";
}

const KINDS = {
    compile: { label: 'Compilar', run: false, flag: '' },
    run: { label: 'Ejecutar en el emulador', run: true, flag: '' },
    memcheck: { label: 'Ejecutar con comprobación de memoria', run: true, flag: '--memcheck' },
    profile: { label: 'Ejecutar con perfil', run: true, flag: '--profile' },
    // DashOS (AArch64): ./dash --dashos makes its ELF; tools/dashos_run.py runs it on the PC in qemu-aarch64 (the
    // platform of Linux: no compositor, the windows of mui_* are not seen)
    dashos: { label: 'Compilar para DashOS', run: false, flag: '', dashos: true },
    'dashos-run': { label: 'Ejecutar en DashOS (QEMU)', run: true, flag: '', dashos: true },
};

/** C in the program (@native, @c, @header): DashOS goes through C with clang, not straight (dashc-a64) */
function hasC(text) {
    return /^\s*@(native|c|header)\b/m.test(String(text || ''));
}

/** Where the DashOS executable of a .dash goes: dashos/ inside the folder of the Amiga's */
function dashosOutputFile(file, folder) {
    const out = outputFile(file, folder);
    return path.join(path.dirname(out), 'dashos', path.basename(out));
}

/** The command of the DashOS tasks */
function dashosCommand(kind, dashDir, file, options) {
    if (kind === 'dashos') {
        const out = dashosOutputFile(file, options.outputFolder);
        return `mkdir -p ${quote(path.dirname(out))} && ${quote(path.join(dashDir, 'dash'))} --dashos` +
            (options.withC ? ' --gcc' : '') + ` ${quote(file)} -o ${quote(out)}`;
    }
    return `python3 ${quote(path.join(dashDir, 'tools', 'dashos_run.py'))}` + (options.withC ? '' : ' --directo') + ` ${quote(file)}`;
}

/**
 * Programs on PATH (null: not there)
 * @param {string} name
 * @param {Record<string, string>} [env]
 */
function which(name, env) {
    const dirs = String((env && env.PATH) || process.env.PATH || '').split(path.delimiter);
    for (const d of dirs) {
        if (!d) continue;
        const p = path.join(d, name);
        try { fs.accessSync(p, fs.constants.X_OK); return p; } catch (e) { /* not here */ }
    }
    return null;
}

/** libkit_c.a of DashOS as tools/dashos_run.py looks for it (DASH_KIT_C, DASHOS_DIR, ~/Projects/dashos) */
function kitC(env) {
    const e = Object.assign({}, process.env, env || {});
    const dashos = e.DASHOS_DIR || path.join(os.homedir(), 'Projects', 'dashos');
    const cands = (e.DASH_KIT_C ? [e.DASH_KIT_C] : []).concat([path.join(dashos, 'build', 'libkit_c.a'),
        path.join(dashos, 'kit-c', 'target', 'aarch64-unknown-none', 'release', 'libkit_c.a')]);
    return { found: cands.find((c) => fs.existsSync(c)) || null, cands };
}

/**
 * What is missing to compile (kind 'dashos') or run ('dashos-run') a program for DashOS, in words, or null.
 * @param {string} kind
 * @param {string} dashDir
 * @param {string} text the program
 * @param {Record<string, string>} [env]
 */
function dashosMissing(kind, dashDir, text, env) {
    const withC = hasC(text);
    if (!fs.existsSync(path.join(dashDir, 'tools', 'dashos_run.py')))
        return `El Dash de ${dashDir} aún no compila para DashOS (falta tools/dashos_run.py): ponlo al día (git pull).`;
    if (kind === 'dashos-run' && !which('qemu-aarch64', env))
        return 'Falta QEMU para ARM (qemu-aarch64), que ejecuta el programa en el PC: instala el paquete qemu-user ' +
               '(Arch: qemu-user; Debian y Ubuntu: qemu-user).';
    const llvm = ['clang', 'ld.lld', 'llvm-ar', 'llvm-nm', 'llvm-objcopy'].filter((t) => !which(t, env));
    if (llvm.length) return `Falta ${llvm.join(', ')} (LLVM), que enlaza los programas de DashOS: instala clang, lld y llvm.`;
    if (!withC && !fs.existsSync(path.join(dashDir, 'dashc', 'dashc-a64')))
        return 'Falta construir el compilador para DashOS: en la carpeta de Dash, ejecuta make -C dashc dashc-a64.';
    if (/\bmui_[a-z_]+\s*\(|\.dashui"/.test(String(text || '')) && !kitC(env).found)
        return 'Este programa tiene ventanas (mui_*): falta libkit_c.a de DashOS. Hazla con make -C kernel kit-c en la ' +
               'carpeta de DashOS y pon esa carpeta en el ajuste "dash.dashos.folder" (DASHOS_DIR), o el fichero en ' +
               '"dash.dashos.kitC" (DASH_KIT_C). Buscada en: ' + kitC(env).cands.join(', ');
    return null;
}

const MACHINES = {
    a1200: 'A1200 (3.1)', a500: 'A500 (68000, 3.1)', 'a1200-32': 'A1200 (AmigaOS 3.2)', rtg: '68040 con RTG (3.2)',
};

/**
 * The shell command of a task (run in the Dash compiler's folder).
 * @param {string} kind compile, run, memcheck or profile
 * @param {string} dashDir
 * @param {string} file the .dash
 * @param {{autoclose?: number, machine?: string, emulator?: string, window?: boolean, system?: string,
 *          outputFolder?: string, withC?: boolean}} [options]
 */
function taskCommand(kind, dashDir, file, options = {}) {
    const k = KINDS[kind];
    if (!k) throw new Error('tarea desconocida: ' + kind);
    if (k.dashos) return dashosCommand(kind, dashDir, file, options);
    const out = outputFile(file, options.outputFolder);
    // a program that waits for its window to be closed ends by itself in the emulator after autoclose s
    // (test mode, DASH_TEST_AUTOCLOSE, read when it is compiled)
    const seconds = k.run && options.autoclose && options.autoclose > 0 ? Math.floor(options.autoclose) : 0;
    // to run it: each Print goes out at once (DASH_PRINT_FLUSH), so the output shows while it runs
    const compile = `mkdir -p ${quote(path.dirname(out))} && DASH_FALLBACK_DASH1=1 ` + (seconds ? `DASH_TEST_AUTOCLOSE=${seconds} ` : '') +
        (k.run ? 'DASH_PRINT_FLUSH=1 ' : '') +
        `${quote(path.join(dashDir, dashExe(dashDir)))} -q` + (k.flag ? ' ' + k.flag : '') + ` ${quote(file)} -o ${quote(out)}`;
    if (!k.run) return compile;
    // the program is built here (with its option) and the emulator runs the binary as it is
    // run in the folder of the .dash (Proyecto: in the emulator): it finds its files with a relative path, as Forja
    // runs it in the drawer of its .dash, wherever the executable goes (dash.outputFolder)
    const emu = [' --follow', ` --cd ${quote(path.dirname(file))}`];
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
 * keepOpen (a terminal of its own, not a task's): at the end it stays, with its output, until a key.
 * @param {typeof import('vscode')} vscode
 */
function shellTerminal(vscode, command, cwd, env, done, title, keepOpen) {
    const { spawn } = require('child_process');
    const write = new vscode.EventEmitter();
    const close = new vscode.EventEmitter();
    let child = null;
    let all = '';
    let ended = false;          // keepOpen: the command ended, the terminal waits for a key
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
                if (!keepOpen) { close.fire(code === null ? 1 : code); return; }
                ended = true;           // (else the output, with its errors, went with the terminal)
                write.fire(`\r\n\x1b[2m${code === 0 ? 'Terminado' : 'Terminado con error ' + code}. ` +
                           'Pulsa una tecla para cerrar.\x1b[0m\r\n');
            });
            child.on('error', (e) => { write.fire(String(e) + '\r\n'); close.fire(1); });
        },
        close: stop,
        handleInput(data) {
            if (ended) close.fire(0);
            else if (data === '\x03') stop();                  // Ctrl+C
        },
    };
}

/**
 * The document saved, its file; an untitled one asks for a name first (VS Code's Save As), and its file is then
 * the new one. null if it was not saved (the dialog cancelled).
 * @param {typeof import('vscode')} vscode
 * @param {import('vscode').TextDocument} doc
 */
async function savedFile(vscode, doc) {
    if (!doc) return null;
    if (doc.isUntitled) {
        const uri = await vscode.workspace.save(doc.uri);      // its Save As: the new file's uri (or nothing)
        return uri && uri.scheme === 'file' ? uri.fsPath : null;
    }
    if (doc.isDirty) await doc.save();
    return doc.fileName;
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
    const afterRun = (kind, file, output, code) => {
        const lack = code !== 0 && missing(output);       // a tool that is not there: what, and how to get it
        if (lack) vscode.window.showErrorMessage(lack);
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

    /** Runs a task on the active .dash (saved first); the commands of the palette, CodeLens and status bar.
        (A failure says so: a command's rejected promise is not seen anywhere.) */
    async function runTask(kind, file) {
        try {
            return await startTask(kind, file);
        } catch (e) {
            vscode.window.showErrorMessage(`Dash (${kind}): ${e && e.message ? e.message : e}`);
            return undefined;
        }
    }

    async function startTask(kind, file) {
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
        if (doc) file = await savedFile(vscode, doc);
        if (!file) return;
        if (KINDS[kind] && KINDS[kind].dashos && helpers.findDash(file)) {     // DashOS: QEMU, LLVM, kit-c...
            let text = '';
            try { text = fs.readFileSync(file, 'utf8'); } catch (e) { /* gone */ }
            const lack = dashosMissing(kind, helpers.findDash(file), text, helpers.env());
            if (lack) { vscode.window.showErrorMessage(lack); return; }
        }
        const task = forFile(kind, file);
        if (!task) {
            vscode.window.showErrorMessage(helpers.noDash ? helpers.noDash() : 'No encuentro el compilador Dash: pon su carpeta en el ajuste "dash.path".');
            return;
        }
        // VS Code runs tasks only with a folder open (with a file alone it did nothing): the same command in a
        // terminal of ours (without the problem matchers: the language server's errors are there)
        if (!(vscode.workspace.workspaceFolders || []).length) {
            const dashDir = helpers.findDash(file);
            const title = `${KINDS[kind].label}: ${path.basename(file)}`;
            for (const t of vscode.window.terminals) if (t.name === title) t.dispose();   // the last one's, as tasks do
            const terminal = vscode.window.createTerminal({ name: title, pty: shellTerminal(vscode,
                taskCommand(kind, dashDir, file, emulatorOptions(vscode, file)), dashDir, helpers.env(),
                (out, code) => afterRun(kind, file, out, code), title + '…', true) });
            terminal.show(true);
            return terminal;
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
                    lenses.push(new vscode.CodeLens(range, { title: 'DashOS', command: 'dash.runInDashOS',
                                                             tooltip: 'Compilar para DashOS y ejecutar en QEMU (qemu-aarch64; sin ventanas)' }));
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
        vscode.commands.registerCommand('dash.compileDashOS', () => runTask('dashos')),
        vscode.commands.registerCommand('dash.runInDashOS', () => runTask('dashos-run')),
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
                      window: config.get('window') !== false, outputFolder: outputFolder(vscode) };
    let text = '';
    try { text = require('fs').readFileSync(file, 'utf8'); } catch (e) { /* not saved yet */ }
    if (machine === 'a1200' && config.get('muiSystem') && /\bmui_|\.dashui"/.test(text)) options.system = config.get('muiSystem');
    options.withC = hasC(text);
    return options;
}

module.exports = { outputFile, outputFolder, dashosOutputFile, dashosMissing, hasC, which, kitC, taskCommand, makeTask, setupTasks, KINDS, MACHINES, emulatorOptions, parseProfile, shellTerminal, savedFile };
