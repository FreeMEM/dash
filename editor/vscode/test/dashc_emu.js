// The debug adapter of Dash 2.0 (dashDebug.js) against the real thing, without VS Code: the emulator with
// tools/amiga/dbgserver.dash and dashc/tests/depurar/depurado_datos.dash built with ./dash --debug, and a DAP client
// here: launch, breakpoints (one with a condition that does not hold, one that does, a logpoint), the stop, the
// stack, the variables (a struct opened, a list inside it, the globals), expressions, a step, the output and the
// end with its code. Needs FS-UAE, $DASH_KICKSTART and $DASH_EMU_SYS; the emulator uses the PC's network, so:
//     flock /run/user/1000/dash-emu-red.lock node test/dashc_emu.js [--a500]
// (dashc/tests/depurar_vscode.py runs it after its own tests.)
const path = require('path');
const fs = require('fs');
const os = require('os');
const assert = require('assert');
const { spawn, execFileSync } = require('child_process');
const { DashDebugAdapter } = require('../dashDebug');
const { freePort, listening } = require('../debug');

const DASH = path.resolve(__dirname, '..', '..', '..');
const SOURCE = path.join(DASH, 'dashc', 'tests', 'depurar', 'depurado_datos.dash');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

let failures = 0;
function check(name, fn) {
    try {
        fn();
        console.log('ok   ' + name);
    } catch (e) {
        failures++;
        console.log('FAIL ' + name + ': ' + e.message);
    }
}

class EventEmitter {
    constructor() { this.listeners = []; this.event = (f) => this.listeners.push(f); }
    fire(m) { for (const f of this.listeners) f(m); }
    dispose() {}
}

/** A DAP client of the adapter: requests with their responses, and the events in order */
function client(adapter) {
    let seq = 0;
    const waiting = new Map();
    const events = [];
    adapter.onDidSendMessage((m) => {
        if (m.type === 'response' && waiting.has(m.request_seq)) {
            waiting.get(m.request_seq)(m);
            waiting.delete(m.request_seq);
        } else if (m.type === 'event') events.push(m);
    });
    const request = (command, args) => new Promise((resolve) => {
        const s = ++seq;
        waiting.set(s, resolve);
        adapter.handleMessage({ seq: s, type: 'request', command, arguments: args || {} });
    });
    const event = async (name, seconds = 60) => {
        for (let i = 0; i < seconds * 20; i++) {
            const k = events.findIndex((e) => e.event === name);
            if (k >= 0) return events.splice(k, 1)[0];
            await wait(50);
        }
        throw new Error(`no llegó ${name}; llegaron: ${events.map((e) => e.event).join(' ')}`);
    };
    return { request, event, events };
}

(async () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_dap_'));
    const exe = path.join(tmp, 'depurado_datos');
    execFileSync(path.join(DASH, 'dash'), ['--debug', SOURCE, '-o', exe], { env: Object.assign({}, process.env, { DASH_PRINT_FLUSH: '1' }) });
    const port = await freePort();
    const emu = spawn('python3', [path.join(DASH, 'tools', 'emu_run.py'), '--dbgserver', String(port), '--timeout', '600',
                                  ...(process.argv.includes('--a500') ? ['--machine', 'a500'] : []), exe],
                      { cwd: DASH, stdio: ['ignore', 'pipe', 'pipe'], detached: true });
    let said = '';
    emu.stdout.on('data', (d) => { said += d; });
    emu.stderr.on('data', (d) => { said += d; });
    const ended = new Promise((resolve) => emu.on('exit', (code) => resolve(code)));
    try {
        for (let i = 0; i < 3000 && !listening(port) && emu.exitCode === null; i++) await wait(100);
        assert(listening(port), 'dbgserver did not start: ' + said);
        const adapter = new DashDebugAdapter({ EventEmitter }, { sourceDir: path.dirname(SOURCE), name: 'depurado_datos' });
        const dap = client(adapter);
        const init = await dap.request('initialize', { adapterID: 'dash' });
        check('initialize', () => assert(init.success && init.body.supportsConditionalBreakpoints && init.body.supportsLogPoints));
        const launch = await dap.request('launch', { host: '127.0.0.1', port, args: '' });
        check('launch', () => assert(launch.success, launch.message));
        await dap.event('initialized');
        const bps = await dap.request('setBreakpoints', { source: { path: SOURCE }, breakpoints: [
            { line: 2 },                                                    // a comment: no code
            { line: 20, condition: 'lista[1] == 20 and p.x == 3' },
            { line: 21, condition: 'lista[1] == 99' },                      // does not hold: it goes on
            { line: 22, logMessage: 'f vale {f * 2}, saludo {saludo}' },
            { line: 12 },
        ] });
        check('setBreakpoints', () => assert.deepStrictEqual(bps.body.breakpoints.map((b) => b.verified), [false, true, true, true, true]));
        await dap.request('configurationDone');

        let stop = await dap.event('stopped');
        let trace = (await dap.request('stackTrace', { threadId: 1 })).body.stackFrames;
        check('the condition that holds stops, the other does not', () => {
            assert.strictEqual(stop.body.reason, 'breakpoint');
            assert.deepStrictEqual(trace.map((f) => [f.name, f.line]), [['Main', 20]]);
        });
        await dap.request('continue', { threadId: 1 });
        stop = await dap.event('stopped');
        trace = (await dap.request('stackTrace', { threadId: 1 })).body.stackFrames;
        check('stopped at line 12, in mira, called from line 23 of Main', () => {
            assert.strictEqual(stop.body.reason, 'breakpoint');
            assert.deepStrictEqual(trace.map((f) => [f.name, f.line, f.source.path]), [['mira', 12, SOURCE], ['Main', 23, SOURCE]]);
        });
        const threads = await dap.request('threads');
        check('threads', () => assert.deepStrictEqual(threads.body.threads, [{ id: 1, name: 'depurado_datos' }]));
        const scopes = (await dap.request('scopes', { frameId: trace[0].id })).body.scopes;
        const locals = (await dap.request('variables', { variablesReference: scopes[0].variablesReference })).body.variables;
        const byName = Object.fromEntries(locals.map((v) => [v.name, v]));
        check('locals of mira', () => {
            assert.deepStrictEqual(locals.map((v) => [v.name, v.type]), [['p', 'Punto'], ['n', 'Int']]);
            assert.strictEqual(byName.n.value, '2');
            assert(byName.p.variablesReference > 0 && byName.n.variablesReference === 0);
        });
        const fields = (await dap.request('variables', { variablesReference: byName.p.variablesReference })).body.variables;
        check('the fields of a struct', () => assert.deepStrictEqual(fields.map((v) => [v.name, v.value]),
            [['x', '4'], ['nombre', '"dos \\"x\\""'], ['hijos', '[Punto(x: 3, nombre: "uno", hijos: nil)]']]));
        const items = (await dap.request('variables', { variablesReference: fields[2].variablesReference })).body.variables;
        check('a list inside it', () => assert.deepStrictEqual(items.map((v) => [v.name, v.value, v.evaluateName]),
            [['[0]', 'Punto(x: 3, nombre: "uno", hijos: nil)', 'p.hijos[0]']]));
        const globals = (await dap.request('variables', { variablesReference: scopes[1].variablesReference })).body.variables;
        check('globals', () => assert.deepStrictEqual(globals.map((v) => [v.name, v.value]), [['cuenta', '7'], ['saludo', '"hola"']]));
        const main = (await dap.request('scopes', { frameId: trace[1].id })).body.scopes;
        const mainVars = (await dap.request('variables', { variablesReference: main[0].variablesReference })).body.variables;
        check('locals of Main (the frame that called)', () => assert.deepStrictEqual(mainVars.map((v) => [v.name, v.value]).slice(0, 2),
            [['lista', '[10, 20, 30]'], ['p', 'Punto(x: 3, nombre: "uno", hijos: nil)']]));
        const ev = async (expression, frameId, context) => {
            const r = await dap.request('evaluate', { expression, frameId: frameId || trace[0].id, context: context || 'repl' });
            return r.success ? r.body.result : '! ' + r.message;
        };
        const got = [await ev('p.hijos[0].nombre'), await ev('n * 10 + p.x'), await ev('p.nombre.length', null, 'watch'),
                     await ev('n', null, 'hover'), await ev('lista[2] / 7', trace[1].id), await ev('f * 2', trace[1].id),
                     await ev('nada'), await ev('vacio == nil and ok', trace[1].id), await ev('cuenta + 1')];
        check('expressions: paths, arithmetic, .length, another frame, errors', () => assert.deepStrictEqual(got,
            ['"uno"', '24', '7', '2', '4', '3.0', '! no existe: nada', 'true', '8']));
        await dap.request('next', { threadId: 1 });
        stop = await dap.event('stopped');
        trace = (await dap.request('stackTrace', { threadId: 1 })).body.stackFrames;
        const t = await ev('t', trace[0].id);
        check('a step (next) to line 13, t = 6', () => {
            assert.strictEqual(stop.body.reason, 'step');
            assert.strictEqual(trace[0].line, 13);
            assert.strictEqual(t, '6');
        });
        await dap.request('stepOut', { threadId: 1 });
        stop = await dap.event('stopped');
        trace = (await dap.request('stackTrace', { threadId: 1 })).body.stackFrames;
        check('out of the function, back in Main', () => assert.deepStrictEqual(trace.map((f) => [f.name, f.line]), [['Main', 24]]));
        await dap.request('continue', { threadId: 1 });
        const exited = await dap.event('exited');
        await dap.event('terminated');
        const out = dap.events.filter((e) => e.event === 'output').map((e) => e.body.output).join('');
        check('the end: its code, the logpoint and the program\'s output', () => {
            assert.strictEqual(exited.body.exitCode, 0);
            assert(/f vale 3\.0, saludo hola\n/.test(out), JSON.stringify(out));
            assert(/r: 6\n/.test(out), JSON.stringify(out));
            assert(out.indexOf('f vale') < out.indexOf('r: 6'), JSON.stringify(out));
        });
        const bye = await dap.request('disconnect', {});
        check('disconnect', () => assert(bye.success));
        const code = await Promise.race([ended, wait(60000).then(() => 'timeout')]);
        check('the emulator ends (dbgserver too)', () => assert.strictEqual(code, 0, said));
        adapter.dispose();
    } catch (e) {
        failures++;
        console.log('FAIL ' + e.message);
    } finally {
        if (emu.exitCode === null) { try { process.kill(-emu.pid, 'SIGTERM'); } catch (e) { /* gone */ } }
        fs.rmSync(tmp, { recursive: true, force: true });
    }
    console.log(failures ? `${failures} test(s) failed` : 'all tests passed');
    process.exit(failures ? 1 : 0);
})();
