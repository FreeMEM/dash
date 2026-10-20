// @ts-check
// Between a .dashui and the Dash code that uses it (docs/IDE_LOOP.md, task 19), without VS Code (tests):
// - problems(text): what is wrong in a .dashui (not JSON, names, types, event numbers), with its place;
// - handlers(dash, n): where a .dash handles event number n: its constants with that value
//   (const ID_ATRAS = 1) and the comparisons with them or with the number (ev == ID_ATRAS);
// - addHandler(dash, n, name): the edits that add the constant and an "if ev == ..." in the loop of
//   mui_wait_event (the program's own variable), or only the constant if there is no loop.
const M = require('./media/model.js');

const IDENT = '[A-Za-z_][A-Za-z0-9_]*';

/** line and column (from 0) of an offset in a text */
function position(text, offset) {
    const before = text.slice(0, offset);
    const line = before.split('\n').length - 1;
    return { line, character: offset - (before.lastIndexOf('\n') + 1) };
}

/** where "key": value (a string) is in the JSON text, or the start */
function placeOf(text, key, value, from) {
    const re = new RegExp(`"${key}"\\s*:\\s*${JSON.stringify(String(value)).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`, 'g');
    re.lastIndex = from || 0;
    const m = re.exec(text);
    return m ? { start: position(text, m.index), end: position(text, m.index + m[0].length), offset: m.index } : null;
}

/**
 * Problems of a .dashui text: [{message, start: {line, character}, end, severity: 'error'|'warning'}]
 * @param {string} text
 */
function problems(text) {
    const out = [];
    const zero = { line: 0, character: 0 };
    let doc;
    try {
        doc = M.parse(text);
    } catch (e) {
        // where: "at position N", or the piece of text the message quotes ("Unexpected token '}', ...[}" ...")
        const m = /position (\d+)/.exec(e.message);
        const q = /Unexpected token '(.)', (?:\.\.\.)?"(.*?)"(?:\.\.\.)? is not valid/.exec(e.message);
        let offset = m ? Number(m[1]) : /end of JSON/.test(e.message) ? text.length : -1;
        if (offset < 0 && q && text.indexOf(q[2]) >= 0) offset = text.indexOf(q[2]) + Math.max(0, q[2].indexOf(q[1]));
        const at = offset >= 0 ? position(text, offset) : zero;
        out.push({ message: 'No es un .dashui válido: ' + e.message, start: at, end: at, severity: 'error' });
        return out;
    }
    const seenWindows = {};
    let from = 0;
    for (const win of doc.windows) {
        const wp = placeOf(text, 'name', win.name || '', from) || { start: zero, end: zero, offset: from };
        from = wp.offset;
        const add = (message, place, severity) => out.push({ message, start: (place || wp).start, end: (place || wp).end,
                                                          severity: severity || 'error' });
        if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(win.name || '')) add(`nombre de ventana no válido: "${win.name || ''}"`);
        if (seenWindows[win.name]) add(`ventana repetida: ${win.name}`);
        seenWindows[win.name] = true;
        const names = {};
        const events = {};
        let cursor = wp.offset + 1;          // the objects come in the text in the order of the walk
        (function walk(n) {
            if (!n || typeof n !== 'object') return;
            const tp = placeOf(text, 'type', n.type || '', cursor);
            if (tp) cursor = tp.offset + 1;
            const np = (n.name !== undefined && placeOf(text, 'name', n.name, tp ? tp.offset : cursor)) || tp;
            if (!M.TYPES[n.type]) add(`tipo desconocido: ${n.type}`, tp);
            if (n.name !== undefined) {
                if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(String(n.name)) || n.name === 'window') add(`nombre no válido: ${n.name}`, np);
                else if (names[n.name]) add(`nombre repetido en ${win.name}: ${n.name}`, np);
                names[n.name] = true;
            }
            for (const key of ['event', 'change', 'ack', 'double']) {
                if (n[key] === undefined) continue;
                if (!Number.isInteger(n[key]) || n[key] <= 0) add(`${key}: un número de evento entero mayor que 0`, np);
                else (events[n[key]] = events[n[key]] || []).push(n.name || n.type);
            }
            (n.children || []).forEach(walk);
        })(win.root);
        from = cursor;                       // the next window's name is after this one's objects
        for (const m of win.menus || []) for (const it of m.items || []) {
            if (it.separator || it.event === undefined) continue;
            if (!Number.isInteger(it.event) || it.event <= 0) add(`menú "${it.label || ''}": un número de evento entero mayor que 0`);
        }
        // the same number on two objects of a window is allowed (a button and a menu item, say), but an
        // object without a name cannot be told apart in the code
        for (const [ev, who] of Object.entries(events)) {
            if (who.length > 1 && who.some((w) => !w || M.TYPES[w])) {
                add(`evento ${ev} en ${who.length} objetos de ${win.name} (${who.join(', ')})`, null, 'warning');
            }
        }
    }
    return out;
}

/** const NAME = n in a .dash: [{name, line}] */
function constantsFor(dash, n) {
    const out = [];
    const re = new RegExp(`^[ \\t]*const[ \\t]+(${IDENT})[ \\t]*=[ \\t]*(-?\\d+)[ \\t]*(#.*)?$`, 'gm');
    let m;
    while ((m = re.exec(dash))) if (Number(m[2]) === n) out.push({ name: m[1], line: position(dash, m.index).line });
    return out;
}

/**
 * Where a .dash handles event n: [{line, character, text}] (comparisons with its constants or the number,
 * outside comments and texts), the constants themselves last
 * @param {string} dash
 * @param {number} n
 */
function handlers(dash, n) {
    const consts = constantsFor(dash, n);
    const words = consts.map((c) => c.name).concat([String(n)]);
    const out = [];
    const lines = dash.split('\n');
    lines.forEach((raw, line) => {
        const code = raw.replace(/"(?:[^"\\]|\\.)*"/g, (s) => ' '.repeat(s.length)).replace(/#.*$/, '');
        if (/^\s*const\s/.test(code)) return;
        for (const w of words) {
            const re = new RegExp(`(==|!=)\\s*${w}\\b|\\b${w}\\s*(==|!=)`, 'g');
            const m = re.exec(code);
            if (m) { out.push({ line, character: m.index, text: raw.trim() }); return; }
        }
    });
    return out.concat(consts.map((c) => ({ line: c.line, character: 0, text: lines[c.line].trim(), constant: true })));
}

/** A constant name for an event of an object: ID_ + its name in capitals (or EVENTO_n) */
function constantName(dash, n, objectName) {
    let base = objectName ? 'ID_' + String(objectName).replace(/[^A-Za-z0-9_]/g, '_').toUpperCase() : 'EVENTO_' + n;
    let name = base, k = 2;
    while (new RegExp(`\\b${name}\\b`).test(dash)) name = base + '_' + k++;
    return name;
}

/**
 * Edits that add the code for event n: [{line, text}] insertions (before that line), and where the new
 * handler is ({line, character}); handler null if there is no loop of mui_wait_event
 * @param {string} dash
 * @param {number} n
 * @param {string} [objectName]
 */
function addHandler(dash, n, objectName) {
    const lines = dash.split('\n');
    const existing = constantsFor(dash, n)[0];
    const name = existing ? existing.name : constantName(dash, n, objectName);
    const edits = [];
    if (!existing) {
        // after the last const or import before the code (functions, structs, Main...), else at the start
        let at = 0;
        for (let i = 0; i < lines.length && !/^(func|struct|Main|enum|var|Window|@)/.test(lines[i]); i++)
            if (/^(const|import)\s/.test(lines[i])) at = i + 1;
        edits.push({ line: at, text: `const ${name} = ${n}` + (at > 0 && /^import\s/.test(lines[at - 1]) ? '\n' : '') });
    }
    // the loop: "x = mui_wait_event(...)": the handler goes right after it, at its indentation
    let handler = null;
    for (let i = 0; i < lines.length; i++) {
        const m = new RegExp(`^(\\s*)(${IDENT})\\s*=\\s*mui_wait_event(?:_signals)?\\s*\\(`).exec(lines[i]);
        if (!m) continue;
        const indent = m[1];
        edits.push({ line: i + 1, text: `${indent}if ${m[2]} == ${name}\n${indent}    # ${objectName || 'evento ' + n}\n${indent}end` });
        // the line of the comment, once the insertions above it are made
        const shift = edits.filter((e) => e.line <= i + 1 && e !== edits[edits.length - 1])
            .reduce((s, e) => s + e.text.split('\n').length, 0);
        handler = { line: i + 1 + shift + 1, character: indent.length + 4 };
        break;
    }
    return { name, edits, handler };
}

/** The text with the insertions made (for tests; VS Code applies them as a WorkspaceEdit) */
function applyEdits(dash, edits) {
    const lines = dash.split('\n');
    for (const e of edits.slice().sort((a, b) => b.line - a.line)) lines.splice(e.line, 0, ...e.text.split('\n'));
    return lines.join('\n');
}

/** Does a .dash import this .dashui (by its file name)? */
function importsDashui(dash, dashuiBase) {
    const re = /^\s*import\s+"([^"]+)"/gm;
    let m;
    while ((m = re.exec(dash))) if (m[1].split('/').pop() === dashuiBase) return true;
    return false;
}

module.exports = { problems, handlers, addHandler, applyEdits, importsDashui, constantName };
