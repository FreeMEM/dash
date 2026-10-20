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
 * The debug adapter that VS Code talks to: gdb -i=dap behind, with the expressions turned into C.
 * @param {typeof import('vscode')} vscode
 */
function makeProxy(vscode, command, args, options = {}) {
    const emitter = new vscode.EventEmitter();
    const gdb = spawn(command, args, { stdio: ['pipe', 'pipe', 'pipe'] });
    let buffer = Buffer.alloc(0);
    const send = (message) => emitter.fire(message);
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
            send(options.fromGdb ? options.fromGdb(message) || message : message);
        }
    });
    gdb.stderr.on('data', (data) => send({ type: 'event', event: 'output', seq: 0,
                                          body: { category: 'console', output: data.toString('utf8') } }));
    gdb.on('exit', () => send({ type: 'event', event: 'terminated', seq: 0, body: {} }));
    const write = (message) => {
        const body = Buffer.from(JSON.stringify(message), 'utf8');
        gdb.stdin.write(`Content-Length: ${body.length}\r\n\r\n`);
        gdb.stdin.write(body);
    };
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
            }
            if (options.toGdb) message = options.toGdb(message) || message;
            write(message);
        },
        write,
        dispose() {
            try { gdb.kill(); } catch (e) { /* gone */ }
            emitter.dispose();
        },
    };
}

module.exports = { dashToC, logMessageToC, makeProxy };
