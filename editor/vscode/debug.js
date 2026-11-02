// @ts-check
// Debugging Dash programs on the Amiga (docs/IDE_LOOP.md, tasks 12-14): F5 on a .dash builds it with
// ./dash --debug and starts the emulator with it. Two ways:
// - Dash 2.0 (dashc, the usual one): the program under tools/amiga/dbgserver.dash (tools/emu_run.py --dbgserver
//   PORT), which debugs it with the dbg_* builtins; dashDebug.js is the debug adapter, connected to localhost:PORT.
// - Dash 1.x (./dash1, through C: a program with C in it, "debugger": "gdb", or a Dash without dashc): the program
//   under bgdbserver (tools/emu_run.py --gdbserver PORT) and m68k-amigaos-gdb -i=dap is the debug adapter,
//   attached to localhost:PORT (#line to the .dash).
// Either way breakpoints, steps, the stack and the variables are in Dash lines.
const path = require('path');
const fs = require('fs');
const net = require('net');
const { spawn, execFile, execFileSync } = require('child_process');
const { makeProxy } = require('./debugProxy');
const { DashDebugAdapter } = require('./dashDebug');
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

/** Is something listening on this port? Without connecting (a connection would take bgdbserver's only one):
 *  /proc on Linux; netstat on macOS and Windows, which have no /proc (before 0.3.1 the debugger never saw
 *  bgdbserver there and gave up when the emulator closed) */
function listening(port) {
    const hex = port.toString(16).toUpperCase().padStart(4, '0');
    let proc = false;
    for (const file of ['/proc/net/tcp', '/proc/net/tcp6']) {
        let text = '';
        try { text = fs.readFileSync(file, 'utf8'); } catch (e) { continue; }
        proc = true;
        for (const line of text.split('\n').slice(1)) {
            const cols = line.trim().split(/\s+/);
            if (cols.length > 3 && cols[1].endsWith(':' + hex) && cols[3] === '0A') return true;   // 0A: LISTEN
        }
    }
    if (proc) return false;
    let text = '';
    try {
        text = execFileSync('netstat', process.platform === 'win32' ? ['-an', '-p', 'TCP'] : ['-an', '-p', 'tcp'],
                            { encoding: 'utf8', timeout: 5000, windowsHide: true, stdio: ['ignore', 'pipe', 'ignore'] });
    } catch (e) { return false; }
    return netstatListening(text, port);
}

/** In the output of netstat -an: a socket in LISTEN on that port. macOS: "tcp4 0 0 127.0.0.1.2345 *.* LISTEN"
 *  (the port after a dot); Windows: "TCP 0.0.0.0:2345 0.0.0.0:0 LISTENING" (after a colon) */
function netstatListening(text, port) {
    for (const line of text.split(/\r?\n/)) {
        const cols = line.trim().split(/\s+/);
        if (cols[cols.length - 1] !== 'LISTEN' && cols[cols.length - 1] !== 'LISTENING') continue;
        const local = cols[0] === 'TCP' ? cols[1] : cols[3];   // the local address: Windows "TCP", macOS "tcp4"...
        if (local && (local.endsWith('.' + port) || local.endsWith(':' + port))) return true;
    }
    return false;
}

/** Can this Dash debug with its own compiler (Dash 2.0: the C path beside ./dash, and tools/amiga/dbgserver.dash)? */
function hasDbgserver(dashDir) {
    return fs.existsSync(path.join(dashDir, 'dash1')) && fs.existsSync(path.join(dashDir, 'tools', 'amiga', 'dbgserver.dash'));
}

/** How it was built, from what ./dash said: 'gdb' if it went through C ("se compila por C con gcc"; 2.0.0 said
 *  ": con ./dash1"), else 'dash' */
function engineOf(text) {
    return /(se compila por C con gcc|: con \.\/dash1)/.test(text) ? 'gdb' : 'dash';
}

/** Does this ./dash take --gcc (2.0.1 on; before, the C path was the command ./dash1)? */
function hasGccOption(dashDir) {
    try { return fs.readFileSync(path.join(dashDir, 'dash'), 'utf8').includes('"--gcc"'); } catch (e) { return false; }
}

/** The command line of the emulator for a debug session (engine 'dash': dbgserver; else bgdbserver) */
function emulatorArgs(dashDir, exe, port, options, engine) {
    const args = [path.join(dashDir, 'tools', 'emu_run.py'), '--follow',
                  engine === 'dash' ? '--dbgserver' : '--gdbserver', String(port)];
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

    /* the program with --debug: with ./dash, which takes what its own compiler cannot do (C in it) through C, the
       build for gdb; engine 'gdb' (a real Amiga with bgdbserver, "debugger": "gdb") through C (./dash --gcc).
       engine of the answer: the debugger that goes with what was built */
    const build = (dashDir, file, exe, engine) => new Promise((resolve) => {
        const env = Object.assign({}, process.env, helpers.env(), { DASH_PRINT_FLUSH: '1', DASH_FALLBACK_DASH1: '1' });
        fs.mkdirSync(path.dirname(exe), { recursive: true });
        const dashc = engine !== 'gdb' && hasDbgserver(dashDir);
        const viaC = !dashc && fs.existsSync(path.join(dashDir, 'dash1'));
        const gcc = viaC && hasGccOption(dashDir);
        const dash = viaC && !gcc ? 'dash1' : 'dash';
        execFile(path.join(dashDir, dash), [...(gcc ? ['--gcc'] : []), '--debug', file, '-o', exe], { cwd: dashDir, env, maxBuffer: 1 << 24 },
                 (error, stdout, stderr) => {
                     const text = String(stdout) + String(stderr);
                     resolve({ ok: !error, text, engine: dashc ? engineOf(text) : 'gdb' });
                 });
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
                const built = await build(dashDir, file, exe, config.debugger === 'gdb' ? 'gdb' : 'auto');
                const engine = built.engine;
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
                const child = spawn('python3', emulatorArgs(dashDir, exe, port, options, engine),
                                    { cwd: dashDir, env: Object.assign({}, process.env, helpers.env()), detached: true });
                const target = `localhost:${port}`;
                let said = '';             // what it says: if it does not start, what is missing
                child.stdout.on('data', (d) => {
                    said += d;
                    output.append(d.toString('utf8'));
                    // (with dbgserver the program's output comes through it: what emu_run says is dbgserver's)
                    if (engine !== 'dash') toConsole(target, d.toString('utf8'));
                });
                child.stderr.on('data', (d) => { said += d; output.append(d.toString('utf8')); });
                emulators.set(target, child);
                for (let i = 0; i < 1200 && !listening(port); i++) {        // up to 2 minutes (a 68000 boots slowly)
                    if (child.exitCode !== null) break;
                    await new Promise((r) => setTimeout(r, 100));
                }
                if (!listening(port)) {
                    stopEmulator(target);
                    output.show(true);
                    vscode.window.showErrorMessage(missing(said) || (engine === 'dash'
                        ? 'El emulador no arrancó dbgserver: mira "Dash: Amiga" (¿falta la ROM o el sistema?).'
                        : 'El emulador no arrancó bgdbserver: mira "Dash: Amiga" ' +
                          '(¿falta tools/get_bgdbserver.sh, la ROM o el sistema?).'));
                    return undefined;
                }
                if (engine === 'dash')
                    return Object.assign({}, config, { engine, program: exe, source: file, host: '127.0.0.1', port, target });
                return Object.assign({}, config, { request: 'attach', program: exe, target });
            });
        },
    }));

    // Dash 2.0: dashDebug.js, connected to dbgserver. Dash 1.x: gdb itself is the adapter (DAP); a different gdb
    // with dash.debug.gdb. With tools/gdb/dash.py of the Dash compiler: values as Dash shows them (texts, lists,
    // dictionaries, structs) and the stack without the runtime
    context.subscriptions.push(vscode.debug.registerDebugAdapterDescriptorFactory('dash', {
        createDebugAdapterDescriptor: (session) => {
            const c = session.configuration;
            if (c.engine === 'dash') {
                return new vscode.DebugAdapterInlineImplementation(/** @type {any} */ (new DashDebugAdapter(vscode,
                    { sourceDir: path.dirname(c.source || c.program), name: path.basename(c.source || c.program, '.dash') })));
            }
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
        const built = await build(dashDir, file, exe, 'gdb');
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

module.exports = { setupDebugger, emulatorArgs, freePort, listening, netstatListening, engineOf, hasDbgserver };
