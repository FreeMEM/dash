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

/**
 * The shell command of a task (run in the Dash compiler's folder).
 * @param {string} kind compile, run, memcheck or profile
 * @param {string} dashDir
 * @param {string} file the .dash
 * @param {{autoclose?: number}} [options]
 */
function taskCommand(kind, dashDir, file, options = {}) {
    const k = KINDS[kind];
    if (!k) throw new Error('tarea desconocida: ' + kind);
    const out = path.join(path.dirname(file), 'bin', path.basename(file, '.dash'));
    // a program that waits for its window to be closed ends by itself in the emulator after autoclose s
    // (test mode, DASH_TEST_AUTOCLOSE, read when it is compiled)
    const seconds = k.run && options.autoclose && options.autoclose > 0 ? Math.floor(options.autoclose) : 0;
    const compile = `mkdir -p ${quote(path.dirname(out))} && ` + (seconds ? `DASH_TEST_AUTOCLOSE=${seconds} ` : '') +
        `${quote(path.join(dashDir, 'dash'))}` + (k.flag ? ' ' + k.flag : '') + ` ${quote(file)} -o ${quote(out)}`;
    if (!k.run) return compile;
    // the program is built here (with its option) and the emulator runs the binary as it is
    return `${compile} && python3 ${quote(path.join(dashDir, 'tools', 'emu_run.py'))} ${quote(out)}`;
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
function makeTask(vscode, kind, file, dashDir, env, options, definition) {
    const def = definition || { type: 'dash', task: kind, file };
    const execution = new vscode.ShellExecution(taskCommand(kind, dashDir, file, options), { cwd: dashDir, env });
    const task = new vscode.Task(def, vscode.TaskScope.Workspace, `${KINDS[kind].label}: ${path.basename(file)}`,
                                 'dash', execution, ['$dash', '$gcc']);
    if (kind === 'compile') task.group = vscode.TaskGroup.Build;
    task.presentationOptions = { reveal: vscode.TaskRevealKind.Always, clear: true };
    return task;
}

/**
 * @param {typeof import('vscode')} vscode
 * @param {import('vscode').ExtensionContext} context
 * @param {{findDash: (f: string) => string | null, env: () => Record<string, string>, trusted: () => boolean}} helpers
 */
function setupTasks(vscode, context, helpers) {
    const autoclose = () => Number(vscode.workspace.getConfiguration('dash.emulator').get('autoclose')) || 0;
    const forFile = (kind, file, definition) => {
        const dashDir = helpers.findDash(file);
        return dashDir ? makeTask(vscode, kind, file, dashDir, helpers.env(), { autoclose: autoclose() }, definition) : null;
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
                    lenses.push(new vscode.CodeLens(range, { title: 'Compilar', command: 'dash.compile' }));
                    lenses.push(new vscode.CodeLens(range, { title: 'Memoria', command: 'dash.runMemcheck', tooltip: 'Ejecutar con --memcheck' }));
                    lenses.push(new vscode.CodeLens(range, { title: 'Perfil', command: 'dash.runProfile', tooltip: 'Ejecutar con --profile' }));
                    break;
                }
            }
            return lenses;
        },
    }));

    // the status bar: Run, while a .dash is in front
    const item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 50);
    item.text = '$(play) Dash';
    item.tooltip = 'Ejecutar en el emulador (Dash)';
    item.command = 'dash.runInEmulator';
    const update = () => (activeFile() ? item.show() : item.hide());
    update();
    context.subscriptions.push(item, vscode.window.onDidChangeActiveTextEditor(update));

    context.subscriptions.push(
        vscode.commands.registerCommand('dash.runMemcheck', () => runTask('memcheck')),
        vscode.commands.registerCommand('dash.runProfile', () => runTask('profile')),
    );
    return runTask;
}

module.exports = { taskCommand, makeTask, setupTasks, KINDS };
