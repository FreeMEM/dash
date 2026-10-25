// "Ver en Amiga": the window of a .dashui opened by a tiny Dash program in FS-UAE,
// and a picture of the screen (tools/emu_run.py --screenshot). No VS Code here, so it
// can be tested from node: node amigaPreview.js <dash dir> <file.dashui> <Window> <out.png>
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFile } = require('child_process');

/** The Dash program that shows one window of the .dashui until it closes itself (autoclose); selfShot: it
    takes the picture itself as soon as the window is open (C:dash_shot to DH0:shot.ppm) and ends, for the
    Amiga that stays on (tools/emu_preview.py) */
function previewProgram(windowName, selfShot) {
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(windowName)) throw new Error('bad window name: ' + windowName);
    if (selfShot) {
        return [
            'import "preview.dashui"',
            '@header "#include <dos/dostags.h>"',
            '',
            '@native func capturar() -> Int',
            '"""',
            '    Delay(25);    /* MUI has drawn the window by now */',
            '    return SystemTags((CONST_STRPTR)"C:dash_shot 1 DH0:shot.dsh", TAG_DONE);   /* (a PPM on RTG) */',
            '"""',
            'end',
            '',
            'Main',
            '    if mui_app_begin("Vista previa", "DASHPREVIEW") == 0',
            '        Print "MUI no está disponible"',
            '    else',
            `        v = ${windowName}_create()`,
            '        mui_window_open(v.window)',
            '        capturar()',
            '        mui_app_end()',
            '    end',
            'end',
            '',
        ].join('\n');
    }
    return [
        'import "preview.dashui"',
        '',
        'Main',
        '    if mui_app_begin("Vista previa", "DASHPREVIEW") == 0',
        '        Print "MUI no está disponible"',
        '    else',
        `        v = ${windowName}_create()`,
        '        mui_window_open(v.window)',
        '        while true',
        '            ev = mui_wait_event()',
        '            if ev == -1',
        '                break',
        '            end',
        '        end',
        '        mui_app_end()',
        '    end',
        'end',
        '',
    ].join('\n');
}

/** Arguments for tools/emu_run.py: the window is captured `shotAt` seconds after boot. */
function emuArgs(dashDir, program, png, opts = {}) {
    const shotAt = opts.shotAt || 15;
    const args = [path.join(dashDir, 'tools', 'emu_run.py'),
        '--autoclose', String(shotAt + 10), '--timeout', String(opts.timeout || 180),
        '--screenshot', String(shotAt), png];
    if (opts.kickstart) args.push('--kickstart', opts.kickstart);
    if (opts.system) args.push('--system', opts.system);
    if (opts.workbench) args.push('--workbench');
    args.push(program);
    return args;
}

/**
 * Run the preview. dashuiText: the editor's text (saved or not). Resolves with
 * { png: Buffer, output } or rejects with an Error whose message says what failed.
 */
function runPreview({ dashDir, dashuiText, windowName, kickstart, system, workbench, shotAt, env }) {
    return new Promise((resolve, reject) => {
        let dir;
        try {
            dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash-preview-'));
            fs.writeFileSync(path.join(dir, 'preview.dashui'), dashuiText);
            fs.writeFileSync(path.join(dir, 'preview.dash'), previewProgram(windowName));
        } catch (e) {
            reject(e);
            return;
        }
        const png = path.join(dir, 'shot.png');
        const program = path.join(dir, 'preview.dash');
        const args = emuArgs(dashDir, program, png, { kickstart, system, workbench, shotAt });
        execFile('python3', args, { cwd: dashDir, env: Object.assign({}, process.env, env || {}),
                                    timeout: 300000, maxBuffer: 4 * 1024 * 1024 }, (err, stdout, stderr) => {
            const output = (stdout || '') + (stderr || '');
            try {
                if (fs.existsSync(png)) {
                    resolve({ png: fs.readFileSync(png), output });
                } else {
                    const why = /Error|error|not found|cannot/.test(output) ? output.trim().split('\n').slice(-3).join(' ')
                        : (err ? err.message : 'no screenshot');
                    reject(new Error(why));
                }
            } finally {
                fs.rmSync(dir, { recursive: true, force: true });
            }
        });
    });
}

/* The Amiga that stays on (tools/emu_preview.py): one per machine, kept between previews (it goes off
   after IDLE_MS without use). Each preview: the program compiled (cached by the .dashui's text and the
   window: the same window again is not compiled again), then shown and pictured there. */
const crypto = require('crypto');
const { spawn } = require('child_process');
const IDLE_MS = 10 * 60 * 1000;

class PreviewServer {
    /** command: [program, ...args] of the server (python3 tools/emu_preview.py --machine ...) */
    constructor(command, options) {
        this.proc = spawn(command[0], command.slice(1), Object.assign({ stdio: ['pipe', 'pipe', 'pipe'] }, options || {}));
        this.waiting = [];                  // resolvers of the answers to come, in order
        this.stderr = '';
        this.dead = null;
        let buffer = '';
        this.proc.stdout.on('data', (d) => {
            buffer += d.toString('utf8');
            let i;
            while ((i = buffer.indexOf('\n')) >= 0) {
                const line = buffer.slice(0, i).trim();
                buffer = buffer.slice(i + 1);
                const next = this.waiting.shift();
                if (next) next(line);
            }
        });
        this.proc.stderr.on('data', (d) => { this.stderr = (this.stderr + d.toString('utf8')).slice(-2000); });
        const gone = (why) => {
            this.dead = this.dead || why;
            for (const next of this.waiting.splice(0)) next('error ' + this.dead);
        };
        this.proc.on('exit', () => gone('the emulator ended' + (this.stderr ? ': ' + this.stderr.trim().split('\n').pop() : '')));
        this.proc.on('error', (e) => gone(e.message));
        this.ready = this.answer().then((line) => {
            if (line !== 'ready') throw new Error(line.replace(/^error /, ''));
        });
        this.queue = this.ready.catch(() => {});
    }

    answer() {
        if (this.dead) return Promise.resolve('error ' + this.dead);
        return new Promise((resolve) => this.waiting.push(resolve));
    }

    /** The picture of a program (it takes it itself), as a PNG file; one at a time. files: a folder whose
        files go to DH0: first (the images the window names), or nothing */
    show(program, png, files) {
        const run = this.queue.then(async () => {
            await this.ready;
            const reply = this.answer();
            this.proc.stdin.write(`show ${program} ${png}${files ? ' ' + files : ''}\n`);
            const line = await reply;
            if (!line.startsWith('ok ')) throw new Error(line.replace(/^error /, ''));
            return png;
        });
        this.queue = run.catch(() => {});
        return run;
    }

    stop() {
        if (this.dead) return;
        try { this.proc.stdin.write('quit\n'); } catch (e) { /* gone */ }
        setTimeout(() => { if (!this.dead) this.proc.kill(); }, 15000).unref();
    }
}

const servers = new Map();                  // key -> {server, timer}

/** The machines with MUI: an A500 has no 68020, so its previews go to the A1200 */
function previewMachine(machine) {
    return ['a1200', 'a1200-32', 'rtg'].includes(machine) ? machine : 'a1200';
}

function serverFor(dashDir, machine, env) {
    const key = JSON.stringify([dashDir, machine, env || {}]);
    let entry = servers.get(key);
    if (!entry || entry.server.dead) {
        const server = new PreviewServer(['python3', path.join(dashDir, 'tools', 'emu_preview.py'), '--machine', machine],
                                         { cwd: dashDir, env: Object.assign({}, process.env, env || {}) });
        entry = { server, timer: null };
        servers.set(key, entry);
    }
    clearTimeout(entry.timer);
    entry.timer = setTimeout(() => { entry.server.stop(); servers.delete(key); }, IDLE_MS);
    entry.timer.unref();
    return entry.server;
}

function stopServers() {
    for (const { server, timer } of servers.values()) { clearTimeout(timer); server.stop(); }
    servers.clear();
}

const compileCache = path.join(os.tmpdir(), 'dash-preview-cache');

/** The compiled preview of a window: by its .dashui and by the Dash that compiles it (the dates of its
    compiler: after a git pull with a fix in the window code, the old program is not shown again) */
function cacheKey(dashDir, dashuiText, windowName) {
    let stamp = '';
    for (const f of ['dashui.py', 'codegen.py', 'amiga_builtins.py']) {
        try { stamp += fs.statSync(path.join(dashDir, 'compiler', f)).mtimeMs + '/'; } catch (e) { /* not there */ }
    }
    return crypto.createHash('sha1').update(dashuiText + '\0' + windowName + '\0' + stamp).digest('hex').slice(0, 16);
}

/** The preview program of a window, compiled (or from the cache); rejects with the compiler's message */
function compilePreview(dashDir, dashuiText, windowName, env) {
    const dir = path.join(compileCache, cacheKey(dashDir, dashuiText, windowName));
    const exe = path.join(dir, 'vista');
    if (fs.existsSync(exe)) return Promise.resolve(exe);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, 'preview.dashui'), dashuiText);
    fs.writeFileSync(path.join(dir, 'preview.dash'), previewProgram(windowName, true));
    return new Promise((resolve, reject) => {
        execFile(path.join(dashDir, 'dash'), [path.join(dir, 'preview.dash'), '-o', exe + '.tmp'],
                 { cwd: dashDir, env: Object.assign({}, process.env, env || {}), maxBuffer: 4 * 1024 * 1024 },
                 (err, stdout, stderr) => {
                     if (err || !fs.existsSync(exe + '.tmp')) {
                         // the compiler's own message (file:line:col: Error: ...), without the path of the temporary file
                         const text = (stdout || '') + (stderr || '');
                         const own = text.split('\n').filter((l) => /:\d+:\d+: (Error|Warning):/.test(l))
                             .map((l) => l.replace(/^.*?:(\d+):(\d+): /, 'línea $1: '));
                         const any = text.split('\n').filter((l) => /rror/.test(l));
                         reject(new Error((own.length ? own : any.slice(-2)).join(' · ') || (err ? err.message : 'no compila')));
                         return;
                     }
                     fs.renameSync(exe + '.tmp', exe);
                     resolve(exe);
                 });
    });
}

/**
 * A window of a .dashui on the Amiga that stays on: { png: Buffer, compiled: Boolean }. machine: a1200,
 * a1200-32 or rtg (else a1200); env: the ROM and Workbench variables (with MUI) for tools/emu_preview.py;
 * baseDir: the .dashui's folder (its images are looked for from there).
 */
/**
 * The files a .dashui names (images: "file"), from the folder of the .dashui or the one above it (where the
 * program usually is: PROGDIR:), copied to a folder with the same relative paths; that folder, or null
 */
function windowFiles(dashuiText, baseDir) {
    if (!baseDir) return null;
    const names = new Set();
    (function walk(x) {
        if (Array.isArray(x)) x.forEach(walk);
        else if (x && typeof x === 'object') {
            if (typeof x.file === 'string' && x.file) names.add(x.file);
            Object.values(x).forEach(walk);
        }
    })(JSON.parse(dashuiText));
    let dir = null;
    for (const name of names) {
        const rel = name.replace(/^PROGDIR:/i, '');
        if (/:/.test(rel) || path.isAbsolute(rel) || rel.split('/').includes('..')) continue;   // another volume
        const from = [path.join(baseDir, rel), path.join(baseDir, '..', rel)].find((f) => fs.existsSync(f));
        if (!from) continue;
        dir = dir || fs.mkdtempSync(path.join(os.tmpdir(), 'dash-preview-files-'));
        fs.mkdirSync(path.dirname(path.join(dir, rel)), { recursive: true });
        fs.copyFileSync(from, path.join(dir, rel));
    }
    return dir;
}

async function preview({ dashDir, dashuiText, windowName, machine, env, baseDir }) {
    let names = [];
    dashuiText = dashuiText.replace(/^\uFEFF/, '');          // a BOM (Windows editors)
    try { names = JSON.parse(dashuiText).windows.map((w) => w.name); } catch (e) { throw new Error('el .dashui no es JSON válido'); }
    if (!names.includes(windowName)) throw new Error(`no hay una ventana "${windowName}" (hay: ${names.join(', ')})`);
    const exe = fs.existsSync(path.join(compileCache, cacheKey(dashDir, dashuiText, windowName), 'vista'));
    const server = serverFor(dashDir, previewMachine(machine), env);   // it boots meanwhile
    const program = await compilePreview(dashDir, dashuiText, windowName, env);
    const png = path.join(path.dirname(program), `shot-${Date.now()}.png`);
    const files = windowFiles(dashuiText, baseDir);
    try {
        await server.show(program, png, files);
        return { png: fs.readFileSync(png), compiled: !exe };
    } finally {
        fs.rmSync(png, { force: true });
        if (files) fs.rmSync(files, { recursive: true, force: true });
    }
}

module.exports = { previewProgram, emuArgs, runPreview, PreviewServer, preview, previewMachine, stopServers, windowFiles };

if (require.main === module) {
    const [dashDir, file, windowName, out] = process.argv.slice(2);
    if (!out) {
        console.error('usage: node amigaPreview.js <dash dir> <file.dashui> <Window> <out.png>');
        process.exit(2);
    }
    runPreview({ dashDir, dashuiText: fs.readFileSync(file, 'utf8'), windowName,
                 kickstart: process.env.DASH_KICKSTART, system: process.env.DASH_EMU_SYS_MUI })
        .then(({ png }) => { fs.writeFileSync(out, png); console.log('saved ' + out); })
        .catch((e) => { console.error(e.message); process.exit(1); });
}
