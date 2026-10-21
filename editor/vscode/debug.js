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
const { savedFile } = require('./tasks');
const { missing } = require('./missing');

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
    const emulators = new Map();            // target "localhost:PORT" -> the emulator's process (or the relay's)
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

    /** The executable for the debugger of a .dash (what F5 and "Preparar para un Amiga real" build) */
    const debugExe = (file) => path.join(path.dirname(file), 'bin', path.basename(file, '.dash') + '.debug');

    /* attach: a bgdbserver already running (an Amiga of yours: bgdbserver :2345 prog.debug). gdb goes
       through tools/gdb_relay.py, so it finds the globals (relay: false, straight to target) */
    async function attach(config) {
        if (!config.target || !config.program) {
            vscode.window.showErrorMessage('Para conectar hacen falta "target" (host:puerto de bgdbserver) y "program".');
            return undefined;
        }
        const exe = config.program.endsWith('.dash') ? debugExe(config.program) : config.program;
        if (!fs.existsSync(exe)) {
            vscode.window.showErrorMessage(`No está ${exe}: compílalo con "Dash: Preparar para un Amiga real".`);
            return undefined;
        }
        const dashDir = helpers.findDash(config.program);
        const relay = dashDir ? path.join(dashDir, 'tools', 'gdb_relay.py') : null;
        if (config.relay === false || !relay || !fs.existsSync(relay) || !helpers.trusted())
            return Object.assign({}, config, { program: exe });
        const port = await freePort();
        const child = spawn('python3', [relay, '--listen', String(port), '--to', config.target, exe],
                            { cwd: dashDir, detached: true });
        child.stderr.on('data', (d) => output.append(d.toString('utf8')));
        const target = `localhost:${port}`;
        emulators.set(target, child);
        for (let i = 0; i < 50 && !listening(port) && child.exitCode === null; i++) await new Promise((r) => setTimeout(r, 100));
        if (!listening(port)) {
            stopEmulator(target);
            output.show(true);
            vscode.window.showErrorMessage('No arrancó tools/gdb_relay.py: mira "Dash: Amiga".');
            return undefined;
        }
        return Object.assign({}, config, { program: exe, target, amiga: config.target });
    }

    context.subscriptions.push(output, vscode.debug.registerDebugConfigurationProvider('dash', {
        provideDebugConfigurations: () => [{ type: 'dash', request: 'launch', name: 'Depurar en el Amiga', program: '${file}' }],
        resolveDebugConfiguration: async (folder, config) => {
            const editor = vscode.window.activeTextEditor;
            if (!config.type && !config.request && !config.name) {      // F5 with no launch.json
                if (!editor || editor.document.languageId !== 'dash') return null;
                Object.assign(config, { type: 'dash', request: 'launch', name: 'Depurar en el Amiga' });
            }
            if (config.request === 'launch' && (!config.program || config.program === '${file}') && editor &&
                editor.document.isUntitled && editor.document.languageId === 'dash') {
                config.program = await savedFile(vscode, editor.document);   // a name first
                if (!config.program) return undefined;
            }
            if (config.request === 'launch' && !config.program) config.program = '${file}';
            return config;
        },
        resolveDebugConfigurationWithSubstitutedVariables: async (folder, config) => {
            if (config.request === 'attach') return attach(config);
            if (config.request !== 'launch') return config;
            if (!helpers.trusted()) {
                vscode.window.showWarningMessage('Carpeta sin confianza (modo restringido): para depurar, confía en ella.');
                return undefined;
            }
            const file = config.program;
            const dashDir = helpers.findDash(file);
            if (!dashDir) {
                vscode.window.showErrorMessage(helpers.noDash());
                return undefined;
            }
            const doc = vscode.workspace.textDocuments.find((d) => d.fileName === file);
            if (doc && doc.isDirty) await doc.save();
            const exe = debugExe(file);
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
                let said = '';             // what it says: if it does not start, what is missing
                child.stdout.on('data', (d) => { said += d; output.append(d.toString('utf8')); toConsole(target, d.toString('utf8')); });
                child.stderr.on('data', (d) => { said += d; output.append(d.toString('utf8')); });
                emulators.set(target, child);
                for (let i = 0; i < 1200 && !listening(port); i++) {        // up to 2 minutes (a 68000 boots slowly)
                    if (child.exitCode !== null) break;
                    await new Promise((r) => setTimeout(r, 100));
                }
                if (!listening(port)) {
                    stopEmulator(target);
                    output.show(true);
                    vscode.window.showErrorMessage(missing(said) || ('El emulador no arrancó bgdbserver: mira "Dash: Amiga" ' +
                                                   '(¿falta tools/get_bgdbserver.sh, la ROM o el sistema?).'));
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

    context.subscriptions.push(vscode.commands.registerCommand('dash.debug', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'dash') { vscode.window.showWarningMessage('Abre un fichero .dash'); return; }
        const program = await savedFile(vscode, editor.document);
        if (!program) return;
        return vscode.debug.startDebugging(vscode.workspace.getWorkspaceFolder(vscode.Uri.file(program)),
            { type: 'dash', request: 'launch', name: 'Depurar en el Amiga', program });
    }));

    // A real Amiga: the program built for the debugger, to copy there and start under bgdbserver
    context.subscriptions.push(vscode.commands.registerCommand('dash.prepareAmiga', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'dash') { vscode.window.showWarningMessage('Abre un fichero .dash'); return; }
        if (!helpers.trusted()) { vscode.window.showWarningMessage('Carpeta sin confianza (modo restringido): para compilar, confía en ella.'); return; }
        const file = await savedFile(vscode, editor.document);
        if (!file) return;
        const dashDir = helpers.findDash(file);
        if (!dashDir) { vscode.window.showErrorMessage(helpers.noDash()); return; }
        const exe = debugExe(file);
        const built = await build(dashDir, file, exe);
        output.clear();
        output.append(built.text);
        if (!built.ok) { output.show(true); vscode.window.showErrorMessage('No compila: mira "Dash: Amiga".'); return; }
        output.append(`\nPara depurarlo en un Amiga:\n  1. Copia ${exe} y bgdbserver (tools/get_bgdbserver.sh) al Amiga.\n` +
                      `  2. En su Shell: bgdbserver :2345 ${path.basename(exe)}\n` +
                      `  3. En launch.json, "Amiga real": target con su nombre o IP y el puerto.\n` +
                      `  4. Elígela en Ejecutar y depurar (o "Debug: Select and Start Debugging") y F5.\n`);
        output.show(true);
        vscode.window.showInformationMessage(`Listo: ${path.basename(exe)}. En el Amiga: bgdbserver :2345 ${path.basename(exe)}`);
    }));

    context.subscriptions.push(vscode.debug.onDidTerminateDebugSession((session) => {
        if (session.type === 'dash' && session.configuration.target) stopEmulator(session.configuration.target);
    }), { dispose: () => { for (const t of [...emulators.keys()]) stopEmulator(t); } });
}

module.exports = { setupDebugger, emulatorArgs, freePort, listening };
