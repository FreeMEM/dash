// @ts-check
// Debugging Dash programs on the Amiga (docs/IDE_LOOP.md, tasks 12-14): F5 on a .dash builds it with
// ./dash --debug (#line to the .dash), starts the emulator with the program under bgdbserver
// (tools/emu_run.py --gdbserver PORT) and m68k-amigaos-gdb -i=dap is the debug adapter, attached to
// localhost:PORT. Breakpoints, steps, the stack and the variables come from gdb, in Dash lines.
const path = require('path');
const fs = require('fs');
const net = require('net');
const { spawn, execFile } = require('child_process');
const { makeProxy } = require('./debugProxy');

/** A TCP port free on this machine (the emulator's bsdsocket listens on the PC's sockets) */
function freePort() {
    return new Promise((resolve, reject) => {
        const server = net.createServer();
        server.unref();
        server.on('error', reject);
        server.listen(0, '127.0.0.1', () => {
            const { port } = /** @type {net.AddressInfo} */ (server.address());
            server.close(() => resolve(port));
        });
    });
}

/** Is something listening on this port? Read from /proc (a connection would take bgdbserver's only one) */
function listening(port) {
    const hex = port.toString(16).toUpperCase().padStart(4, '0');
    for (const file of ['/proc/net/tcp', '/proc/net/tcp6']) {
        let text = '';
        try { text = fs.readFileSync(file, 'utf8'); } catch (e) { continue; }
        for (const line of text.split('\n').slice(1)) {
            const cols = line.trim().split(/\s+/);
            if (cols.length > 3 && cols[1].endsWith(':' + hex) && cols[3] === '0A') return true;   // 0A: LISTEN
        }
    }
    return false;
}

/** The command line of the emulator for a debug session */
function emulatorArgs(dashDir, exe, port, options) {
    const args = [path.join(dashDir, 'tools', 'emu_run.py'), '--follow', '--gdbserver', String(port)];
    if (options.window !== false) args.push('--window');
    if (options.machine && options.machine !== 'a1200') args.push('--machine', options.machine);
    if (options.emulator === 'amiberry') args.push('--emulator', 'amiberry');
    if (options.system) args.push('--system', options.system);
    args.push(exe);
    return args;
}

/**
 * @param {typeof import('vscode')} vscode
 * @param {import('vscode').ExtensionContext} context
 * @param {{findDash: (f: string) => string | null, env: () => Record<string, string>, trusted: () => boolean,
 *          emulatorOptions: (vscode: any, file: string) => any}} helpers
 */
function setupDebugger(vscode, context, helpers) {
    const output = vscode.window.createOutputChannel('Dash: Amiga');
    const emulators = new Map();            // target "localhost:PORT" -> the emulator's process
    const consoles = new Map();             // target -> {proxy, pending}: the program's output to the debug console
    const toConsole = (target, text) => {
        const lines = text.split(/(?<=\n)/).filter((l) => !l.startsWith('=== '));   // emu_run's summary: not the program's
        if (!lines.length) return;
        const c = consoles.get(target) || { proxy: null, pending: [] };
        consoles.set(target, c);
        if (c.proxy) c.proxy.output(lines.join(''));
        else c.pending.push(lines.join(''));
    };
    const stopEmulator = (target) => {
        const child = emulators.get(target);
        emulators.delete(target);
        consoles.delete(target);
        if (child && child.exitCode === null) {
            try { process.kill(-child.pid, 'SIGTERM'); } catch (e) { /* gone */ }
        }
    };

    const build = (dashDir, file, exe) => new Promise((resolve) => {
        const env = Object.assign({}, process.env, helpers.env(), { DASH_PRINT_FLUSH: '1' });
        fs.mkdirSync(path.dirname(exe), { recursive: true });
        execFile(path.join(dashDir, 'dash'), ['--debug', file, '-o', exe], { cwd: dashDir, env, maxBuffer: 1 << 24 },
                 (error, stdout, stderr) => resolve({ ok: !error, text: String(stdout) + String(stderr) }));
    });

    context.subscriptions.push(output, vscode.debug.registerDebugConfigurationProvider('dash', {
        provideDebugConfigurations: () => [{ type: 'dash', request: 'launch', name: 'Depurar en el Amiga', program: '${file}' }],
        resolveDebugConfiguration: (folder, config) => {
            if (!config.type && !config.request && !config.name) {      // F5 with no launch.json
                const editor = vscode.window.activeTextEditor;
                if (!editor || editor.document.languageId !== 'dash') return null;
                Object.assign(config, { type: 'dash', request: 'launch', name: 'Depurar en el Amiga' });
            }
            if (config.request === 'launch' && !config.program) config.program = '${file}';
            return config;
        },
        resolveDebugConfigurationWithSubstitutedVariables: async (folder, config) => {
            if (config.request !== 'launch') return config;                // attach: as it is (an Amiga of yours)
            if (!helpers.trusted()) {
                vscode.window.showWarningMessage('Carpeta sin confianza (modo restringido): para depurar, confía en ella.');
                return undefined;
            }
            const file = config.program;
            const dashDir = helpers.findDash(file);
            if (!dashDir) {
                vscode.window.showErrorMessage('No encuentro el compilador Dash: pon su carpeta en el ajuste "dash.path".');
                return undefined;
            }
            const doc = vscode.workspace.textDocuments.find((d) => d.fileName === file);
            if (doc && doc.isDirty) await doc.save();
            const exe = path.join(path.dirname(file), 'bin', path.basename(file, '.dash') + '.debug');
            return vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Depurar en el Amiga' },
                                              async (progress) => {
                progress.report({ message: 'compilando con --debug…' });
                const built = await build(dashDir, file, exe);
                output.clear();
                output.append(built.text);
                if (!built.ok) {
                    output.show(true);
                    vscode.window.showErrorMessage('No compila: mira "Dash: Amiga" (o Problemas, con Dash: Compilar).');
                    return undefined;
                }
                const port = await freePort();
                const options = Object.assign(helpers.emulatorOptions(vscode, file),
                                              config.machine ? { machine: config.machine } : {},
                                              config.emulator ? { emulator: config.emulator } : {},
                                              config.window !== undefined ? { window: config.window } : {});
                progress.report({ message: 'arrancando el emulador…' });
                const child = spawn('python3', emulatorArgs(dashDir, exe, port, options),
                                    { cwd: dashDir, env: Object.assign({}, process.env, helpers.env()), detached: true });
                const target = `localhost:${port}`;
                child.stdout.on('data', (d) => { output.append(d.toString('utf8')); toConsole(target, d.toString('utf8')); });
                child.stderr.on('data', (d) => output.append(d.toString('utf8')));
                emulators.set(target, child);
                for (let i = 0; i < 1200 && !listening(port); i++) {        // up to 2 minutes (a 68000 boots slowly)
                    if (child.exitCode !== null) break;
                    await new Promise((r) => setTimeout(r, 100));
                }
                if (!listening(port)) {
                    stopEmulator(target);
                    output.show(true);
                    vscode.window.showErrorMessage('El emulador no arrancó bgdbserver: mira "Dash: Amiga" ' +
                                                   '(¿falta tools/get_bgdbserver.sh, la ROM o el sistema?).');
                    return undefined;
                }
                return Object.assign({}, config, { request: 'attach', program: exe, target });
            });
        },
    }));

    // gdb itself is the adapter (DAP); a different gdb with dash.debug.gdb. With tools/gdb/dash.py of the Dash
    // compiler: values as Dash shows them (texts, lists, dictionaries, structs) and the stack without the runtime
    context.subscriptions.push(vscode.debug.registerDebugAdapterDescriptorFactory('dash', {
        createDebugAdapterDescriptor: (session) => {
            const args = ['-i=dap', '-q'];
            const dashDir = session.configuration.program ? helpers.findDash(session.configuration.program) : null;
            const script = dashDir ? path.join(dashDir, 'tools', 'gdb', 'dash.py') : null;
            if (script && fs.existsSync(script)) args.push('-x', script);
            // in between: the expressions of the user (console, watch, hover, conditions, logpoints) from Dash to C,
            // the runtime's errors as exceptions, and the program's output in the debug console
            const proxy = makeProxy(vscode,
                vscode.workspace.getConfiguration('dash.debug').get('gdb') || '/opt/amiga/bin/m68k-amigaos-gdb', args);
            const target = session.configuration.target;
            if (target) {
                const c = consoles.get(target) || { proxy: null, pending: [] };
                c.proxy = proxy;
                consoles.set(target, c);
                setTimeout(() => { for (const t of c.pending.splice(0)) proxy.output(t); }, 0);
            }
            return new vscode.DebugAdapterInlineImplementation(proxy);
        },
    }));

    // after attaching gdb leaves the program stopped at its start: it goes on, unless stopOnEntry
    context.subscriptions.push(vscode.debug.registerDebugAdapterTrackerFactory('dash', {
        createDebugAdapterTracker: (session) => ({
            onDidSendMessage: (m) => {
                if (m.type === 'event' && m.event === 'stopped' && m.body && m.body.reason === 'attach' &&
                    !session.configuration.stopOnEntry) {
                    session.customRequest('continue', { threadId: m.body.threadId || 1 }).then(undefined, () => {});
                }
            },
        }),
    }));

    context.subscriptions.push(vscode.commands.registerCommand('dash.debug', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'dash') { vscode.window.showWarningMessage('Abre un fichero .dash'); return; }
        return vscode.debug.startDebugging(vscode.workspace.getWorkspaceFolder(editor.document.uri),
            { type: 'dash', request: 'launch', name: 'Depurar en el Amiga', program: editor.document.fileName });
    }));

    context.subscriptions.push(vscode.debug.onDidTerminateDebugSession((session) => {
        if (session.type === 'dash' && session.configuration.target) stopEmulator(session.configuration.target);
    }), { dispose: () => { for (const t of [...emulators.keys()]) stopEmulator(t); } });
}

module.exports = { setupDebugger, emulatorArgs, freePort, listening };
