// @ts-check
// Between VS Code and gdb (-i=dap): the expressions the user writes are Dash (debug console, watch, hover,
// breakpoint conditions, logpoints) and gdb parses C, so they are turned into C on the way: p.x -> p->x,
// l[i] -> $at(l, i), s.length -> $len(s) (gdb functions of tools/gdb/dash.py), and/or/not, true/false/nil,
// Color.ROJO -> Color_ROJO. Everything else goes through as it is.
const { spawn } = require('child_process');

const IDENT = '[A-Za-z_][A-Za-z0-9_]*';

/**
 * A Dash expression in C for gdb (texts in quotes are left alone).
 * @param {string} expr
 */
function dashToC(expr) {
    // the texts out of the way (their dots and words are not code), back after the change
    const texts = [];
    let code = '';
    let i = 0;
    while (i < expr.length) {
        if (expr[i] === '"') {
            let j = i + 1;
            while (j < expr.length && expr[j] !== '"') j += expr[j] === '\\' ? 2 : 1;
            texts.push(expr.slice(i, j + 1));
            code += `\u0001${texts.length - 1}\u0001`;
            i = j + 1;
        } else {
            code += expr[i++];
        }
    }
    return codeToC(code).replace(/\u0001(\d+)\u0001/g, (_, n) => texts[Number(n)]);
}

/** @param {string} code an expression with its texts taken out */
function codeToC(code) {
    let c = code
        .replace(/\band\b/g, '&&').replace(/\bor\b/g, '||').replace(/\bnot\b\s*/g, '!')
        .replace(/\btrue\b/g, '1').replace(/\bfalse\b/g, '0').replace(/\bnil\b/g, '0');
    // an enum's value: Color.ROJO is the C constant Color_ROJO
    c = c.replace(new RegExp(`\\b([A-Z][A-Za-z0-9_]*)\\.([A-Z][A-Z0-9_]*)\\b`, 'g'), '$1_$2');
    // x.length (also a.b.length) is $len(x)
    c = c.replace(new RegExp(`\\b(${IDENT}(?:\\.${IDENT})*)\\.length\\b`, 'g'),
                  (_, chain) => `$len(${chain.replace(/\./g, '->')})`);
    // the other dots go into a struct: p.x is p->x (structs are pointers in C); not in numbers (1.5)
    c = c.replace(new RegExp(`(?<=[A-Za-z_0-9\\])])\\.(?=[A-Za-z_])`, 'g'), (m, offset) => {
        const before = c.slice(0, offset);
        return /(^|[^A-Za-z_0-9])[0-9]+$/.test(before) ? m : '->';
    });
    // x[i] is $at(x, i): an element of a list, a value of a dictionary, a character of a text (inner ones first)
    const index = new RegExp(`((?:\\$at\\([^()]*\\)|${IDENT})(?:->${IDENT})*)\\[([^\\[\\]]*)\\]`);
    for (let n = 0; n < 20 && index.test(c); n++) c = c.replace(index, (_, left, inside) => `$at(${left}, ${inside})`);
    return c;
}

/** A logpoint's message: the {expressions} in it, in C */
function logMessageToC(message) {
    return message.replace(/\{([^{}]+)\}/g, (_, e) => '{' + dashToC(e) + '}');
}

/**
 * The debug adapter that VS Code talks to: gdb -i=dap behind, with the expressions turned into C. Also:
 * a function breakpoint of its own on _dash_debug_trap (./dash --debug: the runtime calls it on an error, an
 * index out of a list...), hidden from VS Code, whose stop becomes an "exception" with the error's text;
 * and output(text), the program's output, to the debug console.
 * @param {typeof import('vscode')} vscode
 */
function makeProxy(vscode, command, args) {
    const emitter = new vscode.EventEmitter();
    const gdb = spawn(command, args, { stdio: ['pipe', 'pipe', 'pipe'] });
    let buffer = Buffer.alloc(0);
    let seq = 900000;                        // requests of ours (VS Code's are far below)
    const waiting = new Map();               // seq of ours -> what to do with gdb's answer
    let userFunctionSeq = null;              // VS Code's setFunctionBreakpoints in flight (it gets one more)
    let sawFunctionBreakpoints = false;
    let trapId = null;
    const send = (message) => emitter.fire(Object.assign({ seq: 0 }, message));
    const write = (message) => {
        const body = Buffer.from(JSON.stringify(message), 'utf8');
        gdb.stdin.write(`Content-Length: ${body.length}\r\n\r\n`);
        gdb.stdin.write(body);
    };
    const ask = (command, args) => new Promise((resolve) => {
        const s = ++seq;
        waiting.set(s, resolve);
        write({ seq: s, type: 'request', command, arguments: args });
    });
    const trapRequest = (user) => ({ breakpoints: [...user, { name: '_dash_debug_stop' }] });

    async function fromGdb(message) {
        if (message.type === 'response' && waiting.has(message.request_seq)) {
            const done = waiting.get(message.request_seq);
            waiting.delete(message.request_seq);
            done(message);
            return;
        }
        if (message.type === 'response' && message.request_seq === userFunctionSeq && message.body) {
            const list = message.body.breakpoints || [];
            const trap = list.pop();                 // ours: VS Code did not ask for it
            trapId = trap ? trap.id : trapId;
            userFunctionSeq = null;
        }
        if (message.type === 'event' && message.event === 'stopped' && trapId !== null &&
            (message.body.hitBreakpointIds || []).includes(trapId)) {
            const answer = await ask('evaluate', { expression: '(STRPTR)_dash_debug_what', context: 'watch' });
            const text = answer.success ? String(answer.body.result).replace(/^"|"$/g, '') : 'error del programa';
            send({ type: 'event', event: 'output', body: { category: 'stderr', output: `Error del programa: ${text}\n` } });
            message.body = Object.assign({}, message.body, { reason: 'exception', description: text, text,
                                                              hitBreakpointIds: undefined });
        }
        send(message);
    }

    gdb.stdout.on('data', (data) => {
        buffer = Buffer.concat([buffer, data]);
        for (;;) {
            const head = buffer.indexOf('\r\n\r\n');
            if (head < 0) return;
            const m = /Content-Length:\s*(\d+)/i.exec(buffer.slice(0, head).toString('ascii'));
            const length = m ? Number(m[1]) : 0;
            if (buffer.length < head + 4 + length) return;
            const body = buffer.slice(head + 4, head + 4 + length).toString('utf8');
            buffer = buffer.slice(head + 4 + length);
            let message;
            try { message = JSON.parse(body); } catch (e) { continue; }
            fromGdb(message);
        }
    });
    gdb.stderr.on('data', (data) => send({ type: 'event', event: 'output',
                                          body: { category: 'console', output: data.toString('utf8') } }));
    gdb.on('exit', () => send({ type: 'event', event: 'terminated', body: {} }));
    return {
        onDidSendMessage: emitter.event,
        handleMessage(message) {
            const a = message.arguments;
            if (message.type === 'request' && a) {
                if (message.command === 'evaluate' && a.expression && a.context === 'repl') {
                    // the debug console: an expression of Dash; "-exec <command>" is a gdb command, as it is
                    if (/^\s*-exec\s+/.test(a.expression)) a.expression = a.expression.replace(/^\s*-exec\s+/, '');
                    else { a.expression = dashToC(a.expression); a.context = 'watch'; }
                } else if ((message.command === 'evaluate' || message.command === 'setExpression') && a.expression) {
                    a.expression = dashToC(a.expression);
                }
                if (message.command === 'setBreakpoints' && Array.isArray(a.breakpoints)) {
                    for (const b of a.breakpoints) {
                        if (b.condition) b.condition = dashToC(b.condition);
                        if (b.logMessage) b.logMessage = logMessageToC(b.logMessage);
                    }
                }
                if (message.command === 'setFunctionBreakpoints') {
                    sawFunctionBreakpoints = true;
                    userFunctionSeq = message.seq;
                    message.arguments = trapRequest(a.breakpoints || []);
                }
            }
            if (message.type === 'request' && message.command === 'configurationDone' && !sawFunctionBreakpoints) {
                sawFunctionBreakpoints = true;           // VS Code had none to set: ours alone, before going on
                ask('setFunctionBreakpoints', trapRequest([])).then((r) => {
                    const list = (r.body && r.body.breakpoints) || [];
                    if (list.length) trapId = list[list.length - 1].id;
                });
            }
            write(message);
        },
        /** the program's output (the emulator's), to the debug console */
        output(text) {
            send({ type: 'event', event: 'output', body: { category: 'stdout', output: text } });
        },
        dispose() {
            try { gdb.kill(); } catch (e) { /* gone */ }
            emitter.dispose();
        },
    };
}

module.exports = { dashToC, logMessageToC, makeProxy };
