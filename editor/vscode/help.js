// @ts-check
// The help of Dash (the same as Forja's on the Amiga): the .ayuda file that tools/gen_ayuda.py makes from Dash's
// documentation (docs/AYUDA_FORMATO.md of the Dash repository), read here and turned into the help view, the hover
// and "Probar". No vscode here: the tests use it as it is.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execFile } = require('child_process');

// Latin-1 0xE0-0xFF folded as the generator folds them (docs/AYUDA_FORMATO.md): a space is a separator
const FOLD = 'aaaaaa ceeeeiiii nooooo  uuuuy y';

/** A text as the index has its words: lower case, without accents, a-z 0-9 _ (the rest, separators) */
function fold(text) {
    let out = '';
    for (const ch of String(text).toLowerCase()) {
        const c = ch.charCodeAt(0);
        if ((c >= 97 && c <= 122) || (c >= 48 && c <= 57) || c === 95) out += ch;
        else if (c >= 0xE0 && c <= 0xFF) out += FOLD[c - 0xE0];
        else out += ' ';
    }
    return out.replace(/\s+/g, ' ').trim();
}

class Help {
    /** @param {Buffer} bytes the whole .ayuda */
    constructor(bytes) {
        this.text = bytes.toString('latin1');
        const end = this.text.indexOf('\n.\n');
        if (!this.text.startsWith('DASHAYUDA 1\n') || end < 0) throw new Error('no es un fichero de ayuda de Dash (formato 1)');
        /** @type {Record<string, number[]>} */
        const head = {};
        for (const line of this.text.slice(0, end).split('\n').slice(1)) {
            const [k, ...v] = line.split(' ');
            head[k] = v.map((x) => (/^\d+$/.test(x) ? Number(x) : NaN));
            if (k === 'idioma' || k === 'version') head[k] = /** @type {any} */ (v.join(' '));
        }
        this.language = /** @type {any} */ (head.idioma);
        this.version = /** @type {any} */ (head.version);
        const table = (k) => { const [at, n, len] = head[k]; return { at, n, len }; };
        // the fichas: position, length, type, key
        const f = table('fichas');
        /** @type {{pos: number, len: number, type: string, key: string}[]} */
        this.fichas = [];
        /** @type {Map<string, number>} */
        this.byKey = new Map();
        for (let i = 0; i < f.n; i++) {
            const r = this.text.substr(f.at + i * f.len, f.len - 1);
            const key = r.slice(18).trimEnd();
            this.fichas.push({ pos: Number(r.slice(0, 8)), len: Number(r.slice(9, 15)), type: r[16], key });
            this.byKey.set(key, i);
        }
        // the names (functions, groups, words of the language) -> id
        const n = table('nombres');
        /** @type {Map<string, number>} */
        this.names = new Map();
        for (let i = 0; i < n.n; i++) {
            const r = this.text.substr(n.at + i * n.len, n.len - 1);
            this.names.set(r.slice(0, n.len - 7).trimEnd(), Number(r.slice(n.len - 6)));
        }
        // the words of the search: sorted, each with where its ids are and how many
        const w = table('palabras');
        /** @type {{word: string, at: number, n: number}[]} */
        this.words = [];
        for (let i = 0; i < w.n; i++) {
            const r = this.text.substr(w.at + i * w.len, w.len - 1);
            this.words.push({ word: r.slice(0, w.len - 15).trimEnd(), at: Number(r.slice(w.len - 14, w.len - 6)), n: Number(r.slice(w.len - 5)) });
        }
        const g = head.grupos, s = head.secciones;
        /** @type {{id: number, title: string}[]} */
        this.groups = this._lines(g[0], g[1]).map((l) => ({ id: Number(l.slice(0, 5)), title: l.slice(6) }));
        /** @type {{id: number, level: number, title: string}[]} */
        this.sections = this._lines(s[0], s[1]).map((l) => ({ id: Number(l.slice(0, 5)), level: Number(l[6]), title: l.slice(8) }));
        /** @type {Map<number, any>} */
        this.cache = new Map();
    }

    _lines(at, count) {
        const out = [];
        let p = at;
        for (let i = 0; i < count; i++) {
            const e = this.text.indexOf('\n', p);
            out.push(this.text.slice(p, e));
            p = e + 1;
        }
        return out;
    }

    /** The id of the ficha of a name (a function, a group, "if", "struct"...), -1 if there is none */
    lookup(name) {
        const id = this.names.get(String(name || '').toLowerCase());
        return id === undefined ? -1 : id;
    }

    /** The id of a key, -1 if there is none */
    idOf(key) {
        const id = this.byKey.get(key);
        return id === undefined ? -1 : id;
    }

    /**
     * A ficha: its key, type, title, fields (%x), and its lines (without the first one, the fields kept)
     * @param {number} id
     */
    ficha(id) {
        if (this.cache.has(id)) return this.cache.get(id);
        const f = this.fichas[id];
        if (!f) return null;
        const lines = this.text.substr(f.pos, f.len).replace(/\n$/, '').split('\n');
        const first = /^@(\S+) (\S) ?(.*)$/.exec(lines[0]) || [];
        /** @type {Record<string, string>} */
        const fields = {};
        for (const l of lines.slice(1)) {
            if (!l.startsWith('%')) break;
            const sp = l.indexOf(' ');
            fields[l.slice(1, sp < 0 ? undefined : sp)] = sp < 0 ? '' : l.slice(sp + 1);
        }
        const out = { id, key: f.key, type: f.type, title: first[3] || f.key, fields, lines: lines.slice(1) };
        if (this.cache.size > 200) this.cache.clear();
        this.cache.set(id, out);
        return out;
    }

    /** The ids of a word of the index (folded), the best first; [] if it is not there */
    _word(word) {
        let lo = 0, hi = this.words.length - 1;
        while (lo <= hi) {
            const mid = (lo + hi) >> 1, w = this.words[mid].word;
            if (w === word) {
                const e = this.words[mid];
                return this.text.substr(e.at, e.n * 6 - 1).split(' ').map(Number);
            }
            if (w < word) lo = mid + 1; else hi = mid - 1;
        }
        return [];
    }

    /** The words of the index that start with p (folded), max of them */
    prefix(p, max = 8) {
        let lo = 0, hi = this.words.length;
        while (lo < hi) { const mid = (lo + hi) >> 1; if (this.words[mid].word < p) lo = mid + 1; else hi = mid; }
        const out = [];
        for (let i = lo; i < this.words.length && out.length < max && this.words[i].word.startsWith(p); i++) out.push(this.words[i].word);
        return out;
    }

    /**
     * Search as Forja does: the fichas with every word of q (a word not in the index counts as those that start
     * like it), the best first; the ficha called q, the first of all. 80 at most.
     * @param {string} q
     */
    search(q, max = 80) {
        /** @type {Map<number, number> | null} */
        let total = null;
        for (const w of fold(q).split(' ')) {
            if (w.length < 3) continue;
            let ids = this._word(w);
            if (!ids.length) {
                const seen = new Set();
                for (const p of this.prefix(w)) for (const id of this._word(p)) if (!seen.has(id)) { seen.add(id); ids.push(id); }
            }
            const here = new Map(ids.map((id, k) => [id, ids.length - k + 10]));
            if (!total) total = here;
            else {
                const both = new Map();
                for (const [id, points] of here) if (total.has(id)) both.set(id, total.get(id) + points);
                total = both;
            }
        }
        const order = [...(total || new Map())].sort((a, b) => b[1] - a[1] || a[0] - b[0]).map(([id]) => id);
        const exact = this.lookup(String(q).trim());
        const out = exact >= 0 ? [exact] : [];
        for (const id of order) if (id !== exact && out.length < max) out.push(id);
        return out;
    }

    /** The index for the list: home, syntax, alphabetical index, the groups and the chapters of the manual */
    contents() {
        const out = [];
        for (const k of ['inicio', 'sintaxis', 'indice', 'grupos', 'manual']) {
            const id = this.idOf(k);
            if (id >= 0) out.push({ id, title: this.ficha(id).title, kind: 'inicio' });
        }
        for (const g of this.groups) out.push({ id: g.id, title: g.title, kind: 'grupo' });
        for (const s of this.sections) if (s.level === 1) out.push({ id: s.id, title: s.title, kind: 'manual' });
        return out;
    }

    /**
     * The program of "Probar", as Forja finds it: the first piece of code of the ficha that is a whole program (it has
     * Main); for a function, whose example is a piece of its group's (the same tests/test_doc_*.dash), the group's.
     * { code, from } or null.
     * @param {number} id
     */
    example(id) {
        const f = this.ficha(id);
        if (!f) return null;
        const own = wholeProgram(f.lines);
        if (own) return { code: own, from: f.key };
        if (f.type !== 'F' || !f.fields.ejemplo || !f.fields.grupo) return null;
        const g = this.ficha(this.idOf(f.fields.grupo));
        const code = g && g.fields.ejemplo === f.fields.ejemplo ? wholeProgram(g.lines) : '';
        return code ? { code, from: g.key } : null;
    }
}

/** The first run of code lines ("|") that has a line starting with Main; '' if none */
function wholeProgram(lines) {
    let code = '', main = false;
    for (const l of lines) {
        if (l.startsWith('|')) {
            const c = l.slice(1);
            code += c + '\n';
            if (/^Main(\s|#|$)/.test(c)) main = true;
        } else {
            if (main) return code;
            code = '';
        }
    }
    return main ? code : '';
}

// --- the ficha in HTML (the help view) and in Markdown (the hover) ------------------------------------------------

const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

/** The text lines of a ficha in blocks: paragraphs (wrapped lines joined), list items and tables (as they are) */
function textBlocks(lines) {
    const blocks = [];
    let cur = null;
    const flush = () => { if (cur) blocks.push(cur); cur = null; };
    for (const raw of lines) {
        const l = raw.slice(1);
        if (!l.trim()) { flush(); continue; }
        if (/^\s*[-*] /.test(l)) {                       // a list item; its next lines are indented
            flush();
            cur = { kind: 'item', text: l.replace(/^\s*[-*] /, ''), indent: /^\s*/.exec(l)[0].length };
            continue;
        }
        if (cur && cur.kind === 'item' && /^\s{2,}\S/.test(l)) { cur.text += ' ' + l.trim(); continue; }
        if (/\S {3,}\S/.test(l.trim()) || /^\s*\|/.test(l)) {    // columns: a table, as it is
            if (!cur || cur.kind !== 'table') { flush(); cur = { kind: 'table', text: '' }; }
            cur.text += (cur.text ? '\n' : '') + l;
            continue;
        }
        if (!cur || cur.kind !== 'para') { flush(); cur = { kind: 'para', text: l.trim() }; }
        else cur.text += ' ' + l.trim();
    }
    flush();
    return blocks;
}

/**
 * The ficha as HTML: names with a ficha are links (in code, every one; in text, those with "_", as Forja does).
 * @param {Help} help
 * @param {any} f a ficha
 */
function fichaHtml(help, f) {
    const linkName = (name, always) => {
        const id = help.lookup(name);
        return id >= 0 && id !== f.id && (always || name.includes('_'))
            ? `<a href="#" data-id="${id}">${esc(name)}</a>` : esc(name);
    };
    const linkText = (t, always) => esc(t).replace(/[A-Za-z_][A-Za-z0-9_]*/g, (w) => {
        const html = linkName(w, always);
        return html === w ? w : html;
    });
    const code = (c) => {
        // a comment (# outside a string) is not looked into
        let inStr = false, cut = c.length;
        for (let i = 0; i < c.length; i++) {
            if (c[i] === '"') inStr = !inStr;
            else if (c[i] === '#' && !inStr && c[i + 1] !== '{') { cut = i; break; }
        }
        return linkText(c.slice(0, cut), true) + (cut < c.length ? `<span class="c">${esc(c.slice(cut))}</span>` : '');
    };
    const out = [`<h1>${esc(f.title)}</h1>`];
    if (f.fields.firma) out.push(`<pre class="sig"><code>${esc(f.fields.firma)}</code></pre>`);
    const os = f.fields.dashos;
    if (os) out.push(`<p class="badges"><span class="b ${os}">DashOS: ${{ si: 'sí', no: 'no', solo: 'solo DashOS' }[os] || os}</span>` +
                     (f.fields.grupo ? ` <a href="#" data-id="${help.idOf(f.fields.grupo)}">${esc((help.ficha(help.idOf(f.fields.grupo)) || {}).title || f.fields.grupo)}</a>` : '') + '</p>');
    let i = 0;
    const lines = f.lines.filter((l) => !l.startsWith('%'));
    // the signature is the first subtitle of a function: already shown
    if (f.fields.firma && lines[0] === '#' + f.fields.firma) lines.shift();
    while (i < lines.length) {
        const l = lines[i];
        if (l.startsWith('#')) { out.push(`<h2>${esc(l.slice(1))}</h2>`); i++; continue; }
        if (l.startsWith('|')) {
            const run = [];
            while (i < lines.length && lines[i].startsWith('|')) run.push(lines[i++].slice(1));
            out.push(`<pre class="code"><code>${run.map(code).join('\n')}</code></pre>`);
            continue;
        }
        if (l.startsWith('*')) {
            const run = [];
            while (i < lines.length && lines[i].startsWith('*')) {
                const m = /^\*(\S+) ?(.*)$/.exec(lines[i++]) || [];
                const id = help.idOf(m[1]);
                const text = m[2] || m[1];
                // "file_pos(handle) -> Int: what it does": the signature is the link; any other, the whole text
                const cut = text.startsWith(m[1]) ? text.indexOf(': ') : -1;
                const [name, rest] = cut > 0 ? [text.slice(0, cut), text.slice(cut + 2)] : [text, ''];
                run.push(id >= 0 ? `<li><a href="#" data-id="${id}">${esc(name)}</a>${rest ? ': ' + esc(rest) : ''}</li>`
                    : `<li>${esc(text)}</li>`);
            }
            out.push(`<ul class="links">${run.join('')}</ul>`);
            continue;
        }
        if (l.startsWith(' ')) {
            const run = [];
            while (i < lines.length && lines[i].startsWith(' ')) run.push(lines[i++]);
            let list = [];
            const flushList = () => { if (list.length) out.push(`<ul>${list.join('')}</ul>`); list = []; };
            for (const b of textBlocks(run)) {
                if (b.kind === 'item') { list.push(`<li>${linkText(b.text, false)}</li>`); continue; }
                flushList();
                out.push(b.kind === 'table' ? `<pre class="table">${esc(b.text)}</pre>` : `<p>${linkText(b.text, false)}</p>`);
            }
            flushList();
            continue;
        }
        i++;                                             // a blank line
    }
    return out.join('\n');
}

/**
 * The ficha of a function for the hover, in Markdown: without the language server, its signature and its text;
 * with it (which already gives the signature and the short text), the parameters, DashOS and the links only.
 * @param {Help} help
 * @param {any} f
 * @param {{full?: boolean, canTry?: boolean}} [o]
 */
function hoverMarkdown(help, f, o = {}) {
    const md = [];
    const lines = f.lines.filter((l) => !l.startsWith('%'));
    if (o.full && f.fields.firma) md.push('```dash\n' + f.fields.firma + '\n```');
    // the first paragraph and the parameters ("- x: ..."), until the first subtitle after the signature
    const start = lines.findIndex((l) => l.startsWith(' '));
    const body = [];
    for (let i = Math.max(0, start); i < lines.length && start >= 0; i++) {
        if (lines[i].startsWith('#') || lines[i].startsWith('|') || lines[i].startsWith('*')) break;
        body.push(lines[i].startsWith(' ') ? lines[i] : ' ');
    }
    const blocks = textBlocks(body);
    const items = blocks.filter((b) => b.kind === 'item').map((b) => '- ' + b.text.replace(/^(\w+):/, '`$1`:'));
    if (o.full) {
        const first = blocks.find((b) => b.kind === 'para' && b.text);
        if (first) md.push(first.text);
    }
    if (items.length) md.push(items.join('\n'));
    const os = { si: 'sí', no: 'no (solo en el Amiga)', solo: 'solo allí' }[f.fields.dashos];
    const links = [`[Ayuda de ${f.key}](command:dash.help.show?${encodeURIComponent(JSON.stringify([f.key]))})`];
    if (o.canTry) links.push(`[Probar el ejemplo](command:dash.help.try?${encodeURIComponent(JSON.stringify([f.key]))})`);
    md.push((os ? `En DashOS: ${os} · ` : '') + links.join(' · '));
    return md.join('\n\n');
}

// --- making the .ayuda with tools/gen_ayuda.py ---------------------------------------------------------------------

/** What tools/gen_ayuda.py reads: when one is newer than the .ayuda, it is made again */
function helpSources(dashDir) {
    const out = [];
    const add = (rel) => { const p = path.join(dashDir, rel); if (fs.existsSync(p)) out.push(p); };
    ['tools/gen_ayuda.py', 'tools/gen_builtins_doc.py', 'compiler/amiga_builtins.py', 'compiler/builtins_es.py',
     'docs/SINTAXIS.md', 'docs/SINTAXIS.en.md', 'docs/MANUAL_REFERENCIA.md', 'docs/MANUAL_REFERENCIA.en.md'].forEach(add);
    for (const [dir, re] of [['compiler/builtins_doc', /\.py$/], ['tests', /^test_doc_.*\.dash$/]]) {
        try { for (const n of fs.readdirSync(path.join(dashDir, dir))) if (re.test(n)) out.push(path.join(dashDir, dir, n)); } catch (e) { /* none */ }
    }
    return out;
}

const making = new Map();       // folder -> the promise of tools/gen_ayuda.py running there

/**
 * The .ayuda of a Dash repository in the language asked ('es' or 'en'), made (again) in cacheDir if it is not there
 * or Dash's documentation changed. Rejects with a message in words.
 * @param {string} dashDir
 * @param {string} cacheDir the extension's storage
 * @param {'es' | 'en'} language
 * @param {string} [python]
 */
async function helpFile(dashDir, cacheDir, language, python = 'python3') {
    const tool = path.join(dashDir, 'tools', 'gen_ayuda.py');
    if (!fs.existsSync(tool))
        throw new Error(`el Dash de ${dashDir} no trae la ayuda (tools/gen_ayuda.py): ponlo al día (git pull).`);
    const dir = path.join(cacheDir, 'ayuda', crypto.createHash('sha1').update(path.resolve(dashDir)).digest('hex').slice(0, 12));
    const file = path.join(dir, language === 'en' ? 'Dash_en.ayuda' : 'Dash.ayuda');
    const newest = Math.max(0, ...helpSources(dashDir).map((p) => fs.statSync(p).mtimeMs));
    if (fs.existsSync(file) && fs.statSync(file).mtimeMs >= newest) return file;
    if (!making.has(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        making.set(dir, new Promise((resolve, reject) => {
            execFile(python, [tool, '--salida', dir], { cwd: dashDir, timeout: 120000, maxBuffer: 4 << 20 }, (err, stdout, stderr) => {
                making.delete(dir);
                if (err) reject(new Error(`no se pudo hacer la ayuda (${python} tools/gen_ayuda.py): ` +
                                          ((stderr || '').trim().split('\n').pop() || err.message)));
                else resolve(undefined);
            });
        }));
    }
    await making.get(dir);
    if (!fs.existsSync(file)) throw new Error('tools/gen_ayuda.py no dejó ' + path.basename(file));
    return file;
}

const loaded = new Map();        // file -> {mtime, help}

/** The Help of a .ayuda, read once (again if it changed) */
function openHelp(file) {
    const mtime = fs.statSync(file).mtimeMs;
    const had = loaded.get(file);
    if (had && had.mtime === mtime) return had.help;
    const help = new Help(fs.readFileSync(file));
    loaded.set(file, { mtime, help });
    return help;
}

module.exports = { Help, fold, wholeProgram, textBlocks, fichaHtml, hoverMarkdown, helpFile, helpSources, openHelp };
