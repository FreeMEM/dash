// @ts-check
// The debugger of Dash 2.0 (docs/DEPURADOR_LOOP.md): a program built with ./dash --debug (dashc) runs on the Amiga
// under tools/amiga/dbgserver.dash, which drives it with the dbg_* builtins and talks lines of text over TCP (its
// protocol is at the top of that file). This is the debug adapter VS Code talks to (DAP, inline): its requests
// become those lines, and the lines that come by themselves (*out, *stopped, *ended) become its events.
// Breakpoint conditions, hit counts, logpoints and the expressions of the debug console are worked out here, with
// the values dbgserver gives (a variable with .field and [n] after it).
const net = require('net');
const path = require('path');
const fs = require('fs');

/** A field of a line of dbgserver: \\ \n \t \r come escaped */
function unescapeField(s) {
    return s.replace(/\\(.)/g, (_, c) => (c === 'n' ? '\n' : c === 't' ? '\t' : c === 'r' ? '\r' : c));
}

function escapeField(s) {
    return String(s).replace(/\\/g, '\\\\').replace(/\n/g, '\\n').replace(/\t/g, '\\t').replace(/\r/g, '\\r');
}

const utf8 = new TextDecoder('utf-8', { fatal: true });

/** A line of dbgserver in its fields: UTF-8 if it is (file names, as dashc wrote them), else Latin-1 (the texts
    of the program, in the Amiga's characters) */
function parseLine(buf) {
    let text;
    try { text = utf8.decode(buf); } catch (e) { text = buf.toString('latin1'); }
    return text.replace(/\r$/, '').split('\t').map(unescapeField);
}

/** The pieces of a list of values separated by commas, not those inside texts, (), [] or {} */
function splitTop(text) {
    const out = [];
    let depth = 0, start = 0, quoted = false;
    for (let i = 0; i < text.length; i++) {
        const c = text[i];
        if (quoted) {
            if (c === '\\') i++;
            else if (c === '"') quoted = false;
        } else if (c === '"') quoted = true;
        else if ('([{'.includes(c)) depth++;
        else if (')]}'.includes(c)) depth--;
        else if (c === ',' && depth === 0) {
            out.push(text.slice(start, i).trim());
            start = i + 1;
        }
    }
    if (text.slice(start).trim()) out.push(text.slice(start).trim());
    return out;
}

const STRUCT_VALUE = /^([A-Za-z_][A-Za-z0-9_.]*)\((.*)\)$/s;

/** Does this value open in the variables view? A struct with its fields, a list with something in it */
function expandable(type, value) {
    if (!value || value === 'nil' || value.startsWith('?')) return false;
    if (type.startsWith('[')) return value.startsWith('[') && value !== '[]';
    const m = STRUCT_VALUE.exec(value);
    return !!m && m[2] !== '...' && m[2].trim() !== '';
}

/**
 * What is inside a value: the fields of a struct (Punto(x: 3, y: 4)) or the elements of a list ([1, 2, ...]),
 * as {name, expr}. A list of more than 20 comes with "..." at its end: then up to 200 are asked for.
 */
function childrenOf(expr, type, value) {
    if (type.startsWith('[')) {
        const items = splitTop(value.slice(1, -1));
        const more = items.length && items[items.length - 1] === '...';
        const n = more ? 200 : items.length;
        return { list: true, more, children: Array.from({ length: n }, (_, i) => ({ name: `[${i}]`, expr: `${expr}[${i}]` })) };
    }
    const m = STRUCT_VALUE.exec(value);
    if (!m) return { list: false, more: false, children: [] };
    const children = splitTop(m[2]).map((f) => f.slice(0, f.indexOf(':')).trim()).filter((f) => /^[A-Za-z_]\w*$/.test(f))
        .map((f) => ({ name: f, expr: `${expr}.${f}` }));
    return { list: false, more: false, children };
}

/** A text as dbgserver shows it ("a \"b\"") back to the text */
function unquote(value) {
    const inner = value.replace(/^"/, '').replace(/(\.\.\.)?"$/, '');
    return inner.replace(/\\(.)/g, (_, c) => (c === 'n' ? '\n' : c));
}

/** A value of dbgserver (its type and its text) as a value for the expressions: {t, v} */
function fromServer(type, value) {
    if (value === 'nil') return { t: 'nil', v: null };
    if (type === 'Int' || type === 'Char') return { t: 'Int', v: parseInt(value, 10) };
    if (type === 'Float' || type === 'Fixed' || type === 'Double') return { t: 'Float', v: parseFloat(value) };
    if (type === 'Bool') return { t: 'Bool', v: value === 'true' };
    if (type === 'String') return { t: 'String', v: unquote(value) };
    return { t: type || 'other', v: value, text: value };
}

/** How a value of the expressions is shown (as dbgserver shows them; in a logpoint, texts without quotes) */
function showValue(x, bare) {
    if (x.t === 'nil') return 'nil';
    if (x.t === 'Bool') return x.v ? 'true' : 'false';
    if (x.t === 'Int') return String(x.v);
    if (x.t === 'Float') return Number.isInteger(x.v) ? x.v.toFixed(1) : String(x.v);
    if (x.t === 'String') return bare ? x.v : '"' + x.v.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n') + '"';
    return x.text;
}

// --- the expressions of the debug console, conditions and logpoints: Dash, worked out here ---------------------------

const TOKEN = /\s*(?:(0x[0-9A-Fa-f]+|\d+\.\d+|\d+)|("(?:[^"\\]|\\.)*")|([A-Za-z_][A-Za-z0-9_]*)|(==|!=|<=|>=|<<|>>|[-+*\/%<>()\[\].,&|^~]))/y;

function tokenize(text) {
    const out = [];
    TOKEN.lastIndex = 0;
    let at = 0;
    while (at < text.length) {
        if (/^\s*$/.test(text.slice(at))) break;
        TOKEN.lastIndex = at;
        const m = TOKEN.exec(text);
        if (!m) throw new Error(`no lo entiendo: ${text.slice(at).trim()}`);
        at = TOKEN.lastIndex;
        if (m[1] !== undefined) out.push({ k: 'num', v: m[1] });
        else if (m[2] !== undefined) out.push({ k: 'str', v: unquote(m[2]) });
        else if (m[3] !== undefined) out.push({ k: 'id', v: m[3] });
        else out.push({ k: 'op', v: m[4] });
    }
    return out;
}

/** The tree of an expression of Dash (the operators of the language, with its precedence) */
function parseExpression(text) {
    const toks = tokenize(text);
    let i = 0;
    const peek = () => toks[i];
    const isOp = (v) => toks[i] && toks[i].k === 'op' && toks[i].v === v;
    const isWord = (v) => toks[i] && toks[i].k === 'id' && toks[i].v === v;
    const expect = (v) => { if (!isOp(v)) throw new Error(`falta ${v}`); i++; };
    const binary = (next, ops) => () => {
        let a = next();
        while (toks[i] && toks[i].k === 'op' && ops.includes(toks[i].v)) {
            const op = toks[i++].v;
            a = { k: 'bin', op, a, b: next() };
        }
        return a;
    };
    function primary() {
        const t = peek();
        if (!t) throw new Error('falta algo al final');
        i++;
        if (t.k === 'num') return { k: 'lit', x: t.v.includes('.') ? { t: 'Float', v: parseFloat(t.v) } : { t: 'Int', v: Number(t.v) } };
        if (t.k === 'str') return { k: 'lit', x: { t: 'String', v: t.v } };
        if (t.k === 'op' && t.v === '(') {
            const e = orExpr();
            expect(')');
            return e;
        }
        if (t.k === 'id') {
            if (t.v === 'true' || t.v === 'false') return { k: 'lit', x: { t: 'Bool', v: t.v === 'true' } };
            if (t.v === 'nil') return { k: 'lit', x: { t: 'nil', v: null } };
            const parts = [];
            for (;;) {
                if (isOp('.') && toks[i + 1] && toks[i + 1].k === 'id') {
                    parts.push({ field: toks[i + 1].v });
                    i += 2;
                } else if (isOp('[')) {
                    i++;
                    parts.push({ index: orExpr() });
                    expect(']');
                } else break;
            }
            return { k: 'path', name: t.v, parts };
        }
        throw new Error(`no lo entiendo: ${t.v}`);
    }
    function unary() {
        if (isOp('-')) { i++; return { k: 'neg', a: unary() }; }
        if (isOp('~')) { i++; return { k: 'inv', a: unary() }; }
        return primary();
    }
    const mul = binary(unary, ['*', '/', '%']);
    const add = binary(mul, ['+', '-']);
    const shift = binary(add, ['<<', '>>']);
    const band = binary(shift, ['&']);
    const bxor = binary(band, ['^']);
    const bor = binary(bxor, ['|']);
    const cmp = binary(bor, ['==', '!=', '<', '>', '<=', '>=']);
    function notExpr() {
        if (isWord('not')) { i++; return { k: 'not', a: notExpr() }; }
        return cmp();
    }
    function andExpr() {
        let a = notExpr();
        while (isWord('and')) { i++; a = { k: 'and', a, b: notExpr() }; }
        return a;
    }
    function orExpr() {
        let a = andExpr();
        while (isWord('or')) { i++; a = { k: 'or', a, b: andExpr() }; }
        return a;
    }
    const tree = orExpr();
    if (i < toks.length) throw new Error(`sobra: ${toks.slice(i).map((t) => t.k === 'str' ? JSON.stringify(t.v) : t.v).join(' ')}`);
    return tree;
}

const truthy = (x) => (x.t === 'Bool' ? x.v : x.t === 'nil' ? false : x.t === 'Int' || x.t === 'Float' ? x.v !== 0 : true);

/**
 * The value of an expression tree. lookup(text) gives the value of a variable path ("p.hijos[0].x") as {t, v};
 * listLength(text) how many elements a list has.
 */
async function evaluateTree(node, lookup, listLength) {
    const ev = (n) => evaluateTree(n, lookup, listLength);
    switch (node.k) {
    case 'lit': return node.x;
    case 'path': {
        let text = node.name;
        const parts = node.parts.slice();
        const last = parts[parts.length - 1];
        let length = false;
        if (last && last.field === 'length') { parts.pop(); length = true; }
        for (const p of parts) {
            if (p.field) text += '.' + p.field;
            else {
                const k = await ev(p.index);
                if (k.t !== 'Int') throw new Error('el índice no es un Int');
                text += `[${k.v}]`;
            }
        }
        if (!length) return lookup(text);
        const base = await lookup(text);
        if (base.t === 'String') return { t: 'Int', v: base.v.length };
        if (base.t.startsWith('[')) return { t: 'Int', v: await listLength(text, base) };
        if (base.t.startsWith('{')) return { t: 'Int', v: parseInt(String(base.text).slice(1), 10) };
        return lookup(text + '.length');
    }
    case 'neg': {
        const a = await ev(node.a);
        if (a.t !== 'Int' && a.t !== 'Float') throw new Error('- con algo que no es un número');
        return { t: a.t, v: -a.v };
    }
    case 'inv': {
        const a = await ev(node.a);
        if (a.t !== 'Int') throw new Error('~ con algo que no es un Int');
        return { t: 'Int', v: ~a.v };
    }
    case 'not': return { t: 'Bool', v: !truthy(await ev(node.a)) };
    case 'and': {
        const a = await ev(node.a);
        return truthy(a) ? { t: 'Bool', v: truthy(await ev(node.b)) } : { t: 'Bool', v: false };
    }
    case 'or': {
        const a = await ev(node.a);
        return truthy(a) ? { t: 'Bool', v: true } : { t: 'Bool', v: truthy(await ev(node.b)) };
    }
    case 'bin': return binaryOp(node.op, await ev(node.a), await ev(node.b));
    }
    throw new Error('no lo entiendo');
}

function binaryOp(op, a, b) {
    const num = (x) => x.t === 'Int' || x.t === 'Float';
    if (op === '==' || op === '!=') {
        let same;
        if (num(a) && num(b)) same = a.v === b.v;
        else if (a.t === 'nil' || b.t === 'nil') same = a.t === b.t;
        else if (a.t === 'String' && b.t === 'String') same = a.v === b.v;
        else if (a.t === 'Bool' && b.t === 'Bool') same = a.v === b.v;
        else same = a.t === b.t && showValue(a) === showValue(b);
        return { t: 'Bool', v: op === '==' ? same : !same };
    }
    if (['<', '>', '<=', '>='].includes(op)) {
        if (!((num(a) && num(b)) || (a.t === 'String' && b.t === 'String'))) throw new Error(`${op} entre ${a.t} y ${b.t}`);
        const r = op === '<' ? a.v < b.v : op === '>' ? a.v > b.v : op === '<=' ? a.v <= b.v : a.v >= b.v;
        return { t: 'Bool', v: r };
    }
    if (op === '+' && a.t === 'String' && b.t === 'String') return { t: 'String', v: a.v + b.v };
    if (!num(a) || !num(b)) throw new Error(`${op} entre ${a.t} y ${b.t}`);
    const ints = a.t === 'Int' && b.t === 'Int';
    if (['&', '|', '^', '<<', '>>'].includes(op)) {
        if (!ints) throw new Error(`${op} con algo que no es un Int`);
        const v = op === '&' ? a.v & b.v : op === '|' ? a.v | b.v : op === '^' ? a.v ^ b.v : op === '<<' ? a.v << b.v : a.v >> b.v;
        return { t: 'Int', v };
    }
    if ((op === '/' || op === '%') && b.v === 0) throw new Error('división por cero');
    let v;
    if (op === '+') v = a.v + b.v;
    else if (op === '-') v = a.v - b.v;
    else if (op === '*') v = ints ? Math.imul(a.v, b.v) : a.v * b.v;
    else if (op === '/') v = ints ? Math.trunc(a.v / b.v) : a.v / b.v;
    else v = ints ? a.v % b.v : a.v % b.v;
    return { t: ints ? 'Int' : 'Float', v: ints ? v | 0 : v };
}

/** A variable with .field and [number] after it: dbgserver gives its value as it is (and its type) */
const PATH = /^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*|\[\s*\d+\s*\])*$/;
const isPath = (e) => PATH.test(e) && !/^(true|false|nil|not)$/.test(e) && !/\.length$/.test(e);

/** A hit condition of a breakpoint ("3", ">= 3", "% 2") met on hit number n? A bare number: from that hit on */
function hitMet(condition, n) {
    const m = /^\s*(==|=|>=|>|<=|<|%)?\s*(\d+)\s*$/.exec(condition || '');
    if (!m) return true;
    const k = Number(m[2]);
    switch (m[1]) {
    case '==': case '=': return n === k;
    case '>': return n > k;
    case '<=': return n <= k;
    case '<': return n < k;
    case '%': return k > 0 && n % k === 0;
    default: return n >= k;
    }
}

// --- the connection to dbgserver ----------------------------------------------------------------------------------

class DbgServer {
    /**
     * @param {net.Socket} socket
     * @param {(fields: string[]) => void} onEvent the lines that start with *, and ['*closed'] at the end
     */
    constructor(socket, onEvent) {
        this.socket = socket;
        this.onEvent = onEvent;
        this.buffer = Buffer.alloc(0);
        this.queue = [];                     // the orders sent, waiting for their answer: {resolve, reject, data}
        this.closed = false;
        this.hello = new Promise((resolve) => { this.greet = resolve; });
        socket.on('data', (d) => this.data(d));
        socket.on('error', () => {});
        socket.on('close', () => {
            this.closed = true;
            for (const q of this.queue.splice(0)) q.reject(new Error('dbgserver cerró la conexión'));
            if (this.greet) { this.greet(null); this.greet = null; }
            this.onEvent(['*closed']);
        });
    }

    data(d) {
        this.buffer = Buffer.concat([this.buffer, d]);
        for (let at = this.buffer.indexOf(10); at >= 0; at = this.buffer.indexOf(10)) {
            const fields = parseLine(this.buffer.slice(0, at));
            this.buffer = this.buffer.slice(at + 1);
            this.line(fields);
        }
    }

    line(fields) {
        if (this.greet) { this.greet(fields); this.greet = null; return; }
        if (fields[0].startsWith('*')) { this.onEvent(fields); return; }
        const q = this.queue[0];
        if (!q) return;
        if (fields[0] === 'ok' || fields[0] === 'error') {
            this.queue.shift();
            q.resolve({ ok: fields[0] === 'ok', value: fields[1], error: fields[0] === 'error' ? fields[1] || 'error' : undefined,
                        data: q.data });
        } else q.data.push(fields);
    }

    /** An order: its answer, {ok, value, error, data: the lines before it} (orders have no escapes: a tab or a
        line break inside a field becomes a space) */
    send(fields, encoding = 'utf8') {
        return new Promise((resolve, reject) => {
            if (this.closed) { reject(new Error('dbgserver cerró la conexión')); return; }
            this.queue.push({ resolve, reject, data: [] });
            this.socket.write(Buffer.from(fields.map((f) => String(f).replace(/[\t\r\n]/g, ' ')).join('\t') + '\n', /** @type {BufferEncoding} */ (encoding)));
        });
    }

    close() { try { this.socket.end(); this.socket.destroy(); } catch (e) { /* gone */ } }
}

/** A connection to host:port, tried again for a while (the emulator may still be starting it) */
function connectTo(host, port, seconds = 20) {
    const until = Date.now() + seconds * 1000;
    return new Promise((resolve, reject) => {
        const attempt = () => {
            const socket = net.connect(port, host);
            socket.once('connect', () => { socket.removeAllListeners('error'); resolve(socket); });
            socket.once('error', (e) => {
                socket.destroy();
                if (Date.now() < until) setTimeout(attempt, 250);
                else reject(e);
            });
        };
        attempt();
    });
}

// --- the debug adapter ------------------------------------------------------------------------------------------

const REASONS = { breakpoint: 'breakpoint', step: 'step', pause: 'pause' };

/**
 * The debug adapter of Dash 2.0 for VS Code (vscode.DebugAdapterInlineImplementation). The launch (or attach)
 * request carries host and port of a dbgserver already listening, args (the program's) and stopOnEntry;
 * sourceDir is where the sources are looked for when the debug information names them otherwise.
 * @param {typeof import('vscode') | {EventEmitter: any}} vscode
 */
class DashDebugAdapter {
    constructor(vscode, options = {}) {
        this.emitter = new vscode.EventEmitter();
        this.onDidSendMessage = this.emitter.event;
        this.options = options;
        this.server = null;
        this.chain = Promise.resolve();      // the requests and the stops one after another (their orders in order)
        this.breakpoints = new Map();        // source path -> Map line -> {id, line, name, verified, condition, ...}
        this.nextId = 1;
        this.handles = [];                   // variablesReference - 1 -> what it opens (while stopped)
        this.stopped = false;
        this.ended = false;
        this.terminated = false;
        this.quitting = false;               // the end asked for (quit): the connection's end is no surprise
        this.entry = false;
        this.timeout = options.timeout || 30000;
    }

    handleMessage(message) {
        if (message.type !== 'request') return;
        this.serial(() => this.request(message).catch((e) => this.respond(message, undefined, e.message || String(e))));
    }

    serial(job) {
        this.chain = this.chain.then(job, job);
        return this.chain;
    }

    send(message) { this.emitter.fire(Object.assign({ seq: 0 }, message)); }

    respond(request, body, error) {
        this.send({ type: 'response', request_seq: request.seq, command: request.command, success: !error,
                    message: error, body: body || {} });
    }

    event(event, body) { this.send({ type: 'event', event, body: body || {} }); }

    output(text, category = 'console') { this.event('output', { category, output: text }); }

    terminate() {
        if (this.terminated) return;
        this.terminated = true;
        this.event('terminated');
    }

    /** An order to dbgserver, with a time limit (if the Amiga hangs, the session ends instead of waiting) */
    async order(fields, encoding) {
        if (!this.server) throw new Error('sin conexión con el Amiga');
        let timer;
        const late = new Promise((_, reject) => {
            timer = setTimeout(() => reject(new Error(`dbgserver no contesta (${fields[0]})`)), this.timeout);
        });
        try {
            return await Promise.race([this.server.send(fields, encoding), late]);
        } catch (e) {
            if (/no contesta/.test(e.message)) {
                this.output(e.message + '\n', 'stderr');
                this.server.close();
                this.terminate();
            }
            throw e;
        } finally {
            clearTimeout(timer);
        }
    }

    /** A source as the debug information names it, as a path here */
    sourcePath(file) {
        if (!file) return file;
        if (path.isAbsolute(file) && fs.existsSync(file)) return file;
        const dir = this.options.sourceDir || '';
        for (const f of [path.resolve(dir, file), path.join(dir, path.basename(file))])
            if (dir && fs.existsSync(f)) return f;
        return file;
    }

    handle(what) {
        this.handles.push(what);
        return this.handles.length;
    }

    async request(r) {
        const a = r.arguments || {};
        switch (r.command) {
        case 'initialize':
            this.respond(r, {
                supportsConfigurationDoneRequest: true, supportsConditionalBreakpoints: true,
                supportsHitConditionalBreakpoints: true, supportsLogPoints: true, supportsEvaluateForHovers: true,
                supportsTerminateRequest: true,
            });
            return;
        case 'launch':
        case 'attach':
            return this.launch(r, a);
        case 'setBreakpoints':
            return this.setBreakpoints(r, a);
        case 'setExceptionBreakpoints':
        case 'setFunctionBreakpoints':
            this.respond(r, { breakpoints: [] });
            return;
        case 'configurationDone':
            this.respond(r);
            await this.go(this.entry ? 'step' : 'continue');
            return;
        case 'threads':
            this.respond(r, { threads: [{ id: 1, name: this.options.name || 'Main' }] });
            return;
        case 'stackTrace':
            return this.stackTrace(r, a);
        case 'scopes': {
            const frame = (a.frameId || 1) - 1;
            this.respond(r, { scopes: [
                { name: 'Locales', presentationHint: 'locals', variablesReference: this.handle({ kind: 'vars', frame }), expensive: false },
                { name: 'Globales', variablesReference: this.handle({ kind: 'globals' }), expensive: false },
            ] });
            return;
        }
        case 'variables':
            return this.variables(r, a);
        case 'evaluate':
            return this.evaluate(r, a);
        case 'continue':
            await this.go('continue');
            this.respond(r, { allThreadsContinued: true });
            return;
        case 'next':
        case 'stepIn':
        case 'stepOut':
            await this.go(r.command === 'next' ? 'next' : r.command === 'stepIn' ? 'step' : 'out');
            this.respond(r);
            return;
        case 'pause':
            if (this.server && !this.stopped && !this.ended) await this.order(['pause']);
            this.respond(r);
            return;
        case 'terminate':
            if (this.server && !this.ended) await this.order(['end']).catch(() => {});
            this.respond(r);
            this.terminate();
            return;
        case 'disconnect':
            if (this.server && !this.server.closed) {
                this.quitting = true;
                await this.order(['quit']).catch(() => {});
                this.server.close();
            }
            this.respond(r);
            return;
        default:
            this.respond(r, undefined, `no sé hacer ${r.command}`);
        }
    }

    async launch(r, a) {
        this.entry = !!a.stopOnEntry;
        const host = a.host || '127.0.0.1';
        let socket;
        try {
            socket = this.options.connect ? await this.options.connect(a) : await connectTo(host, Number(a.port));
        } catch (e) {
            this.respond(r, undefined, `No me puedo conectar con dbgserver en ${host}:${a.port}: ${e.message}`);
            this.terminate();
            return;
        }
        this.server = new DbgServer(socket, (fields) => this.serial(() => this.serverEvent(fields)));
        const hello = await Promise.race([this.server.hello, new Promise((res) => setTimeout(() => res(null), this.timeout))]);
        if (!hello || hello[0] !== 'dbgserver') {
            this.respond(r, undefined, `En ${host}:${a.port} no contesta dbgserver.`);
            this.server.close();
            this.terminate();
            return;
        }
        // (its arguments, in the Amiga's characters)
        const started = await this.order(['start', a.amigaProgram || '', a.args || ''], 'latin1');
        if (!started.ok) {
            this.quitting = true;
            await this.order(['quit']).catch(() => {});
            this.server.close();
            this.respond(r, undefined, `No arranca el programa: ${started.error}`);
            this.terminate();
            return;
        }
        this.respond(r);
        this.event('initialized');
    }

    async setBreakpoints(r, a) {
        const file = a.source && a.source.path ? a.source.path : '';
        const wanted = a.breakpoints || (a.lines || []).map((line) => ({ line }));
        const old = this.breakpoints.get(file) || new Map();
        const now = new Map();
        const lines = new Set(wanted.map((b) => b.line));
        for (const [line, b] of old) {
            if (!lines.has(line) && b.verified && this.server) await this.order(['unbreak', b.name, line]);
        }
        const out = [];
        for (const w of wanted) {
            let b = old.get(w.line);
            if (!b) {
                b = { id: this.nextId++, line: w.line, hits: 0, verified: false, name: null };
                // its whole name first (two files may be called the same), then the name alone (a path written otherwise)
                for (const name of [file, path.basename(file)]) {
                    if (!name || !this.server) continue;
                    const got = await this.order(['break', name, w.line]);
                    if (got.ok && got.value === 'true') { b.verified = true; b.name = name; break; }
                }
            }
            Object.assign(b, { condition: w.condition, logMessage: w.logMessage, hitCondition: w.hitCondition });
            now.set(w.line, b);
            out.push({ id: b.id, verified: b.verified, line: w.line,
                       message: b.verified ? undefined : 'Esa línea no tiene código (o no es de este programa)' });
        }
        this.breakpoints.set(file, now);
        this.respond(r, { breakpoints: out });
    }

    /** continue, step, next or out */
    async go(how) {
        if (!this.server || this.ended) return;
        this.stopped = false;
        this.handles = [];
        const got = await this.order([how]);
        if (!got.ok) throw new Error(got.error);
    }

    breakpointAt(file, line) {
        const local = this.sourcePath(file);
        for (const [f, lines] of this.breakpoints) {
            if (f === local || (!fs.existsSync(local) && path.basename(f) === path.basename(local))) {
                const b = lines.get(line);
                if (b) return b;
            }
        }
        return null;
    }

    async serverEvent(fields) {
        const [kind] = fields;
        if (kind === '*out') {
            this.output(fields[1] || '', 'stdout');
        } else if (kind === '*stopped') {
            const [, reason, file, line] = fields;
            this.stopped = true;
            this.handles = [];
            if (reason === 'breakpoint' && !(await this.stopsHere(file, Number(line)))) {
                await this.go('continue');
                return;
            }
            const why = this.entry ? 'entry' : REASONS[reason] || 'step';
            this.entry = false;
            this.event('stopped', { reason: why, threadId: 1, allThreadsStopped: true });
        } else if (kind === '*ended') {
            this.ended = true;
            this.stopped = false;
            const rc = Number(fields[1]);
            this.output(`El programa ha acabado (código ${rc}).\n`);
            this.event('exited', { exitCode: rc });
            this.terminate();
        } else if (kind === '*closed') {
            if (!this.quitting && !this.ended) this.output('Se ha cortado la conexión con el Amiga.\n', 'stderr');
            this.terminate();
        }
    }

    /** At a breakpoint: does it stop? Its condition, its hits; a logpoint writes its message and goes on */
    async stopsHere(file, line) {
        const b = this.breakpointAt(file, line);
        if (!b) return true;
        if (b.condition) {
            try {
                if (!truthy(await this.evaluateText(b.condition, 0))) return false;
            } catch (e) {
                this.output(`La condición del punto de parada de la línea ${line} (${b.condition}): ${e.message}\n`, 'stderr');
                return true;
            }
        }
        b.hits++;
        if (b.hitCondition && !hitMet(b.hitCondition, b.hits)) return false;
        if (b.logMessage) {
            let text = '';
            const parts = b.logMessage.split(/(\{[^{}]+\})/);
            for (const p of parts) {
                if (!/^\{.*\}$/.test(p)) { text += p; continue; }
                try { text += showValue(await this.evaluateText(p.slice(1, -1), 0), true); }
                catch (e) { text += `{${e.message}}`; }
            }
            this.output(text + '\n');
            return false;
        }
        return true;
    }

    async stackTrace(r, a) {
        if (!this.stopped) { this.respond(r, { stackFrames: [], totalFrames: 0 }); return; }
        const got = await this.order(['frames']);
        const frames = got.data.filter((f) => f[0] === 'frame').map((f, i) => {
            const file = this.sourcePath(f[3]);
            const here = file && fs.existsSync(file);
            return { id: i + 1, name: f[2] || '?', line: Number(f[1]) || 0, column: 1,
                     source: here ? { name: path.basename(file), path: file } : { name: path.basename(f[3] || '?'), presentationHint: 'deemphasize' } };
        });
        const start = a.startFrame || 0;
        const levels = a.levels || frames.length;
        this.respond(r, { stackFrames: frames.slice(start, start + levels), totalFrames: frames.length });
    }

    variable(frame, name, type, value, expr) {
        return { name, value, type: type || undefined, evaluateName: expr,
                 variablesReference: expandable(type || '', value) ? this.handle({ kind: 'children', frame, expr, type, value }) : 0 };
    }

    async variables(r, a) {
        const h = this.handles[(a.variablesReference || 0) - 1];
        if (!h || !this.stopped) { this.respond(r, { variables: [] }); return; }
        let list = [];
        if (h.kind === 'vars' || h.kind === 'globals') {
            const frame = h.kind === 'vars' ? h.frame : -1;
            const got = await this.order(h.kind === 'vars' ? ['vars', frame] : ['globals']);
            list = got.data.filter((f) => f[0] === 'var').map(([, name, type, value]) => this.variable(frame, name, type, value, name));
        } else if (h.kind === 'children') {
            const inside = childrenOf(h.expr, h.type, h.value);
            if (inside.children.length) {
                const got = await this.order(['values', h.frame, ...inside.children.map((c) => c.expr)]);
                const rows = got.data.filter((f) => f[0] === 'val');
                inside.children.forEach((c, i) => {
                    const row = rows[i];
                    if (!row || (inside.list && row[2].startsWith('?'))) return;
                    list.push(this.variable(h.frame, c.name, row[1], row[2], c.expr));
                });
            }
        }
        this.respond(r, { variables: list });
    }

    /** The value of a variable path in a frame, as {t, v} (an error with why, if there is none) */
    async lookup(frame, text) {
        const got = await this.order(['values', frame, text]);
        const row = got.data.find((f) => f[0] === 'val');
        if (!row) throw new Error('sin valor');
        if (row[2].startsWith('?')) throw new Error(row[2].replace(/^\?\s*/, ''));
        return fromServer(row[1], row[2]);
    }

    async listLength(frame, text, base) {
        const items = splitTop(String(base.text).slice(1, -1));
        if (!items.length || items[items.length - 1] !== '...') return items.length;
        const got = await this.order(['values', frame, ...Array.from({ length: 1000 }, (_, i) => `${text}[${i}]`)]);
        return got.data.filter((f) => f[0] === 'val' && !f[2].startsWith('?')).length;
    }

    evaluateText(text, frame) {
        return evaluateTree(parseExpression(text), (t) => this.lookup(frame, t), (t, base) => this.listLength(frame, t, base));
    }

    async evaluate(r, a) {
        const text = String(a.expression || '').trim();
        if (!this.stopped) { this.respond(r, undefined, 'El programa no está parado.'); return; }
        const frame = a.frameId ? a.frameId - 1 : 0;
        if (isPath(text)) {
            const got = await this.order(['values', frame, text.replace(/\s+/g, '')]);
            const row = got.data.find((f) => f[0] === 'val');
            if (!row || row[2].startsWith('?')) {
                this.respond(r, undefined, row ? row[2].replace(/^\?\s*/, '') : 'sin valor');
                return;
            }
            const v = this.variable(frame, text, row[1], row[2], text);
            this.respond(r, { result: v.value, type: v.type, variablesReference: v.variablesReference });
            return;
        }
        let x;
        try { x = await this.evaluateText(text, frame); } catch (e) { this.respond(r, undefined, e.message); return; }
        this.respond(r, { result: showValue(x), type: x.t, variablesReference: 0 });
    }

    dispose() {
        if (this.server) this.server.close();
        this.emitter.dispose();
    }
}

module.exports = { DashDebugAdapter, DbgServer, parseLine, escapeField, unescapeField, splitTop, childrenOf, expandable,
                   parseExpression, evaluateTree, fromServer, showValue, hitMet, isPath, connectTo };
