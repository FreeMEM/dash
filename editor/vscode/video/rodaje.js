// Shooting the video tutorial of the extension (docs/IDE_VIDEO_LOOP.md): VS Code without a window (the Electron of
// Code - OSS with --ozone-platform=headless), driven by Playwright, with a cursor drawn inside the page that goes
// to every click, the window's pictures taken at a steady pace and, at the end, an MP4 (ffmpeg) and its subtitles
// (SRT, from the times the script says them). Nothing appears on the user's screen.
//
//     const { Rodaje } = require('./rodaje');
//     const r = await Rodaje.start({ workspace: dir, open: ['hola.dash'] });
//     await r.subtitulo('Esto es Dash', 3000);
//     await r.clic('text=hola.dash');
//     await r.escribir('Print "hola"');
//     await r.fin('/tmp/toma');      // /tmp/toma.mp4, /tmp/toma.srt and /tmp/toma-sub.mp4 (subtitles on the picture)
//
// playwright-core: $DASH_PLAYWRIGHT, else ~/.cache/dash-video/node_modules/playwright-core (outside git).
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const PLAYWRIGHT = process.env.DASH_PLAYWRIGHT || path.join(os.homedir(), '.cache', 'dash-video', 'node_modules', 'playwright-core');
const ELECTRON = process.env.DASH_ELECTRON || '/usr/lib/electron42/electron';
const CODE = process.env.DASH_CODE_MAIN || '/usr/lib/code/code.mjs';
const EXTENSION = path.resolve(__dirname, '..');

// The shooting profile: big letters, nothing but the editor (no chat, no welcome, no tips, no updates)
const SETTINGS = {
    'workbench.startupEditor': 'none',
    'workbench.secondarySideBar.defaultVisibility': 'hidden',
    'workbench.tips.enabled': false,
    'workbench.enableExperiments': false,
    'chat.disableAIFeatures': true,
    'chat.commandCenter.enabled': false,
    'update.mode': 'none',
    'extensions.ignoreRecommendations': true,
    'telemetry.telemetryLevel': 'off',
    'security.workspace.trust.enabled': false,
    'editor.fontSize': 17,
    'editor.minimap.enabled': false,
    'window.commandCenter': false,
    'workbench.layoutControl.enabled': false,
    'editor.accessibilitySupport': 'off',
    'git.enabled': false,
    'window.title': '${activeEditorShort}${separator}${rootName}',   // (not "[Extension Development Host]")
    'files.simpleDialog.enable': true,         // VS Code's own file dialogs: the system's are not seen without a window
};

// An arrow of 22 x 32, with a white edge (it is seen on dark and light)
const CURSOR_PATH = 'M1 1 L1 25 L7 19 L11 30 L15 28 L11 18 L20 18 Z';

class Rodaje {
    /**
     * VS Code with the workspace folder open (and files of it in editors), the cursor and the pictures running.
     * settings: more settings of the profile (dash.path, dash.emulator...); fps: pictures a second (about);
     * vsix: the extension installed from this package (as a user has it), else loaded from its folder (then
     * the window's title says "[Extension Development Host]").
     */
    static async start({ workspace, open = [], settings = {}, width = 1280, height = 720, fps = 12, env = {}, vsix = null }) {
        const { _electron } = require(PLAYWRIGHT);
        const r = new Rodaje();
        r.tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'dash-rodaje-'));
        r.frames = path.join(r.tmp, 'frames');
        fs.mkdirSync(r.frames);
        fs.mkdirSync(path.join(r.tmp, 'user', 'User'), { recursive: true });
        fs.writeFileSync(path.join(r.tmp, 'user', 'User', 'settings.json'),
                         JSON.stringify(Object.assign({}, SETTINGS, settings), null, 2));
        if (vsix) {
            // VS Code's command line (cli.js): the package into the shooting profile's extensions
            const inst = spawnSync(ELECTRON, [path.join(path.dirname(CODE), 'out', 'cli.js'), CODE, '--user-data-dir',
                                              path.join(r.tmp, 'user'), '--extensions-dir', path.join(r.tmp, 'ext'),
                                              '--install-extension', vsix],
                                   { env: Object.assign({}, process.env, { ELECTRON_RUN_AS_NODE: '1' }), encoding: 'utf8', timeout: 120000 });
            if (!/successfully installed/.test(inst.stdout || '')) throw new Error('cannot install ' + vsix + ': ' + (inst.stdout + inst.stderr).slice(-300));
        }
        r.app = await _electron.launch({
            executablePath: ELECTRON,
            args: [CODE, '--ozone-platform=headless', '--user-data-dir', path.join(r.tmp, 'user'),
                   '--extensions-dir', path.join(r.tmp, 'ext'), '--disable-workspace-trust', '--skip-welcome',
                   '--skip-release-notes', '--disable-telemetry', '--new-window',
                   ...(vsix ? [] : [`--extensionDevelopmentPath=${EXTENSION}`]),
                   ...(workspace ? [workspace, ...open.map((f) => path.join(workspace, f))] : [])],   // (no folder: an empty window)
            env: Object.assign({}, process.env, env),
            timeout: 90000,
        });
        r.page = await r.app.firstWindow();
        await r.app.evaluate(({ BrowserWindow }, [w, h]) => {
            for (const win of BrowserWindow.getAllWindows()) win.setContentSize(w, h);
        }, [width, height]);
        await r.page.setViewportSize({ width, height }).catch(() => {});
        await r.page.waitForSelector('.monaco-workbench', { timeout: 60000 });
        r.size = { width, height };
        r.pos = { x: width / 2, y: height / 2 };
        r.subs = [];
        r.shots = [];
        await r.page.waitForTimeout(2500);         // the extension and its language server start
        await r.ponerCursor();
        r.t0 = Date.now();                         // the video's time 0: the first picture
        r.capturando = true;
        r.loop = r.capturar(1000 / fps);
        return r;
    }

    /** The cursor: an element over everything, without events (it is put again if VS Code redraws the body) */
    async ponerCursor() {
        await this.page.evaluate(([d, x, y]) => {
            let c = document.getElementById('rodaje-cursor');
            if (!c) {
                // (built element by element: the workbench takes no innerHTML, it wants Trusted Types)
                const ns = 'http://www.w3.org/2000/svg';
                const svg = document.createElementNS(ns, 'svg');
                svg.setAttribute('width', '22');
                svg.setAttribute('height', '32');
                svg.setAttribute('viewBox', '0 0 22 32');
                const arrow = document.createElementNS(ns, 'path');
                for (const [k, v] of [['d', d], ['fill', '#111'], ['stroke', '#fff'], ['stroke-width', '2'], ['stroke-linejoin', 'round']])
                    arrow.setAttribute(k, v);
                svg.append(arrow);
                c = document.createElement('div');
                c.id = 'rodaje-cursor';
                c.append(svg);
                c.style.cssText = 'position:fixed;left:0;top:0;z-index:2147483647;pointer-events:none;' +
                                  'width:22px;height:32px;transform-origin:1px 1px;';
                const ring = document.createElement('div');
                ring.id = 'rodaje-anillo';
                ring.style.cssText = 'position:fixed;z-index:2147483646;pointer-events:none;width:28px;height:28px;' +
                                     'margin:-14px 0 0 -14px;border-radius:50%;border:3px solid #ffb000;opacity:0;';
                document.body.append(ring, c);
            }
            c.style.left = x + 'px';
            c.style.top = y + 'px';
        }, [CURSOR_PATH, this.pos.x, this.pos.y]);
    }

    /** The pictures, one each `every` ms (or as fast as a picture can be taken), with their time */
    async capturar(every) {
        let n = 0;
        while (this.capturando) {
            const t = Date.now();
            try {
                const file = path.join(this.frames, String(n).padStart(6, '0') + '.png');
                await this.page.screenshot({ path: file, animations: 'allow', caret: 'initial' });
                this.shots.push({ file, t: t - this.t0 });
                n++;
            } catch (e) {
                if (!this.capturando) break;
            }
            const left = every - (Date.now() - t);
            if (left > 0) await new Promise((r) => setTimeout(r, left));
        }
    }

    now() { return Date.now() - this.t0; }

    esperar(ms) { return new Promise((r) => setTimeout(r, ms)); }

    /** A subtitle from now, for ms (the script goes on meanwhile: wait with esperar) */
    subtitulo(text, ms = 3000) {
        this.subs.push({ start: this.now(), end: this.now() + ms, text });
    }

    /** The subtitle, and waits while it is read */
    async decir(text, ms = 3000) {
        this.subtitulo(text, ms);
        await this.esperar(ms);
    }

    /** Where a target is: {x, y}, a CSS/Playwright selector of the window, or a Locator (also inside a webview) */
    async donde(target) {
        if (target && typeof target.x === 'number') return target;
        const loc = typeof target === 'string' ? this.page.locator(target).first() : target;
        await loc.waitFor({ state: 'visible', timeout: 15000 });
        const box = await loc.boundingBox();
        if (!box) throw new Error('not visible: ' + target);
        return { x: Math.round(box.x + box.width / 2), y: Math.round(box.y + box.height / 2) };
    }

    /** The cursor goes to the target along a soft curve (the real mouse too: hovers work) */
    async mover(target, ms = 700) {
        const to = await this.donde(target);
        const from = Object.assign({}, this.pos);
        const steps = Math.max(8, Math.round(ms / 25));
        const bend = { x: (to.y - from.y) * 0.12, y: (from.x - to.x) * 0.12 };    // a little arc
        for (let i = 1; i <= steps; i++) {
            const s = i / steps, e = s < 0.5 ? 2 * s * s : 1 - Math.pow(-2 * s + 2, 2) / 2;   // ease in and out
            const arc = Math.sin(Math.PI * e);
            this.pos = { x: from.x + (to.x - from.x) * e + bend.x * arc, y: from.y + (to.y - from.y) * e + bend.y * arc };
            await this.ponerCursor();
            await this.page.mouse.move(this.pos.x, this.pos.y);
            await this.esperar(ms / steps);
        }
        return to;
    }

    /** Click on the target (after going there), with a ring that grows where it clicks */
    async clic(target, { button = 'left', double = false, ms = 700, modifiers = [] } = {}) {
        const at = await this.mover(target, ms);
        await this.page.evaluate(([x, y]) => {
            const r = document.getElementById('rodaje-anillo');
            if (!r) return;
            r.style.left = x + 'px';
            r.style.top = y + 'px';
            r.animate([{ opacity: 0.9, transform: 'scale(0.5)' }, { opacity: 0, transform: 'scale(1.6)' }],
                      { duration: 500, easing: 'ease-out' });
        }, [at.x, at.y]);
        for (const m of modifiers) await this.page.keyboard.down(m);       // Control+click...
        await this.page.mouse.click(at.x, at.y, { button, clickCount: double ? 2 : 1 });
        for (const m of modifiers.slice().reverse()) await this.page.keyboard.up(m);
        await this.esperar(350);
    }

    /** A line of the editor that has this text (its end, to click there and type after it) */
    linea(text) {
        return this.page.locator('.monaco-editor .view-line', { hasText: text }).first();
    }

    /** A word of the editor: the token with exactly that text (the n-th) */
    palabra(text, n = 0) {
        return this.page.locator('.monaco-editor .view-line span span', { hasText: new RegExp(`^${text}$`) }).nth(n);
    }

    /** Typing at a person's pace (delay ms a key) */
    async escribir(text, delay = 55) {
        await this.page.keyboard.type(text, { delay });
    }

    /** A key or a combination: 'Enter', 'Control+Shift+P', 'F5'... */
    async tecla(combo, after = 300) {
        await this.page.keyboard.press(combo);
        await this.esperar(after);
    }

    /** After the window reloads (a folder opened in it): the workbench there again, and the cursor */
    async recargada(ms = 30000) {
        await this.esperar(1500);
        await this.page.waitForSelector('.monaco-workbench .explorer-folders-view, .monaco-workbench .part.editor', { timeout: ms });
        await this.esperar(2500);                  // the extension starts again
        await this.ponerCursor();
    }

    /** A command of the palette, as a person would: F1, its name, Enter */
    async orden(name, after = 800) {
        await this.tecla('F1', 400);
        await this.escribir(name, 35);
        await this.esperar(500);
        await this.tecla('Enter', after);
    }

    /** End: the pictures as a video of the times they were taken, and its subtitles; returns the paths */
    async fin(out) {
        this.capturando = false;
        await this.loop;
        const end = this.now();
        await this.app.close().catch(() => {});
        return montar(this.shots, end, this.subs, out, this.tmp);
    }
}

// subtitles on the picture: white on a dark box, at the bottom
const SUB_STYLE = 'FontName=DejaVu Sans,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BorderStyle=4,' +
                  'BackColour=&HA0000000,Outline=1,Shadow=0,MarginV=22';

function srtTime(ms) {
    const h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60, s = Math.floor(ms / 1000) % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(Math.floor(ms % 1000)).padStart(3, '0')}`;
}

function srt(subs) {
    return subs.map((s, i) => `${i + 1}\n${srtTime(s.start)} --> ${srtTime(s.end)}\n${s.text}\n`).join('\n');
}

/** shots [{file, t}] (ms from the start) to out.mp4 at 30 fps (each frame, the picture of its moment), out.srt,
    and out-sub.mp4 with the subtitles on the picture */
function montar(shots, end, subs, out, tmp) {
    if (!shots.length) throw new Error('no pictures');
    // one link a frame, to the last picture taken by its time: exact times (ffmpeg's concat with durations
    // rounded them, a video of 8.9 s came out of 8.2)
    const seq = path.join(tmp, 'seq');
    fs.rmSync(seq, { recursive: true, force: true });
    fs.mkdirSync(seq);
    const frames = Math.max(1, Math.round(end * 30 / 1000));
    let j = 0;
    for (let k = 0; k < frames; k++) {
        while (j + 1 < shots.length && shots[j + 1].t <= k * 1000 / 30) j++;
        fs.symlinkSync(shots[j].file, path.join(seq, String(k).padStart(6, '0') + '.png'));
    }
    fs.mkdirSync(path.dirname(out), { recursive: true });
    const ff = (args) => {
        const r = spawnSync('ffmpeg', ['-loglevel', 'error', '-y', ...args], { encoding: 'utf8' });
        if (r.status !== 0) throw new Error('ffmpeg: ' + r.stderr.slice(-500));
    };
    ff(['-framerate', '30', '-i', path.join(seq, '%06d.png'), '-vf', 'format=yuv420p', '-c:v', 'libx264',
        '-preset', 'medium', '-crf', '20', '-movflags', '+faststart', out + '.mp4']);
    fs.writeFileSync(out + '.srt', srt(subs));
    fs.writeFileSync(out + '.json', JSON.stringify({ duration: end, subs }, null, 1));
    if (subs.length) {
        const style = SUB_STYLE;
        const srtPath = (out + '.srt').replace(/\\/g, '/').replace(/:/g, '\\:').replace(/'/g, "\\'");
        ff(['-i', out + '.mp4', '-vf', `subtitles='${srtPath}':force_style='${style}'`, '-c:v', 'libx264', '-preset', 'medium',
            '-crf', '20', '-movflags', '+faststart', out + '-sub.mp4']);
    }
    return { mp4: out + '.mp4', srt: out + '.srt', json: out + '.json', sub: subs.length ? out + '-sub.mp4' : null,
             frames: shots.length, duration: end };
}

module.exports = { Rodaje, srt, srtTime, montar, SUB_STYLE };
