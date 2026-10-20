// The video tutorial (docs/IDE_VIDEO_LOOP.md): each chapter of video/capitulos/ shot with video/rodaje.js, a
// cover, a title before each chapter, and all of it joined with its subtitles.
//
//     node video/grabar.js --out ~/.cache/dash-video/tutorial            # all the chapters
//     node video/grabar.js --out /tmp/t --solo 3,5                       # some (by the number of their file)
//     node video/grabar.js --out /tmp/t --dev                            # the extension from its folder, not packaged
//
// A chapter: video/capitulos/NN_nombre.js with { titulo, resumen, preparar(dir) (the files of its folder),
// open: [files to open], settings: {}, sinCarpeta (VS Code without a folder open), async guion(r, dir) }. Out: <out>/NN.mp4 (and .srt, .json, -sub.mp4) per
// chapter, and <out>/tutorial.mp4, tutorial.srt and tutorial-sub.mp4 (the subtitles on the picture).
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const { Rodaje, srt, SUB_STYLE } = require('./rodaje');

const HERE = __dirname;
const EXTENSION = path.resolve(HERE, '..');
const DASH = path.resolve(EXTENSION, '..', '..');
const FONT = '/usr/share/fonts/TTF/DejaVuSans.ttf';
const FONT_BOLD = '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf';

function ff(args) {
    const r = spawnSync('ffmpeg', ['-loglevel', 'error', '-y', ...args], { encoding: 'utf8' });
    if (r.status !== 0) throw new Error('ffmpeg: ' + (r.stderr || '').slice(-600));
}

/** A text for drawtext (its special characters escaped) */
function dt(text) {
    return String(text).replace(/\\/g, '\\\\\\\\').replace(/'/g, '\u2019').replace(/:/g, '\\:').replace(/%/g, '\\%');
}

/** A card: a title (and a line under it) on the Dash blue, seconds long, the same format as the chapters */
function tarjeta(out, titulo, linea, seconds = 3) {
    const font = fs.existsSync(FONT_BOLD) ? `fontfile=${FONT_BOLD}:` : '';
    const font2 = fs.existsSync(FONT) ? `fontfile=${FONT}:` : '';
    const filters = [`drawtext=${font}text='${dt(titulo)}':fontcolor=white:fontsize=52:x=(w-text_w)/2:y=(h-text_h)/2-30`];
    if (linea) filters.push(`drawtext=${font2}text='${dt(linea)}':fontcolor=0xc8d0e8:fontsize=26:x=(w-text_w)/2:y=(h)/2+40`);
    ff(['-f', 'lavfi', '-i', `color=c=0x1f2d5c:s=1280x720:r=30:d=${seconds}`, '-vf', filters.join(',') + ',format=yuv420p',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', out]);
    return { mp4: out, duration: seconds * 1000, subs: [] };
}

/** Pieces [{mp4, duration (ms), subs}] one after another: out.mp4, out.srt (each subtitle at its piece's time),
    out-sub.mp4 */
function juntar(pieces, out) {
    const list = out + '.txt';
    fs.writeFileSync(list, pieces.map((p) => `file '${p.mp4}'`).join('\n') + '\n');
    ff(['-f', 'concat', '-safe', '0', '-i', list, '-vf', 'fps=30,format=yuv420p', '-c:v', 'libx264', '-preset', 'medium',
        '-crf', '20', '-movflags', '+faststart', out + '.mp4']);
    const subs = [];
    let at = 0;
    for (const p of pieces) {
        for (const s of p.subs || []) subs.push({ start: at + s.start, end: at + Math.min(s.end, p.duration), text: s.text });
        at += p.duration;
    }
    fs.writeFileSync(out + '.srt', srt(subs));
    const srtPath = (out + '.srt').replace(/:/g, '\\:').replace(/'/g, "\\'");
    ff(['-i', out + '.mp4', '-vf', `subtitles='${srtPath}':force_style='${SUB_STYLE}'`, '-c:v', 'libx264', '-preset', 'medium',
        '-crf', '20', '-movflags', '+faststart', out + '-sub.mp4']);
    fs.rmSync(list, { force: true });
    return { mp4: out + '.mp4', srt: out + '.srt', sub: out + '-sub.mp4', duration: at, subs };
}

/** The chapters of video/capitulos (all, or those whose number is in solo) */
function capitulos(solo) {
    const dir = path.join(HERE, 'capitulos');
    return fs.readdirSync(dir).filter((f) => /^\d+_.*\.js$/.test(f)).sort()
        .filter((f) => !solo || solo.includes(Number(f.split('_')[0])))
        .map((f) => Object.assign({ numero: Number(f.split('_')[0]), fichero: f }, require(path.join(dir, f))));
}

/** The extension packaged (npm run package): its .vsix */
function empaquetar() {
    const r = spawnSync('npm', ['run', 'package'], { cwd: EXTENSION, encoding: 'utf8' });
    const m = /Packaged: (\S+\.vsix)/.exec(r.stdout || '');
    if (r.status !== 0 || !m) throw new Error('npm run package: ' + (r.stdout + r.stderr).slice(-400));
    return m[1];
}

/** One chapter shot in a folder of its own: its pieces (its title card and its video) */
async function grabarCapitulo(cap, out, vsix) {
    const ws = fs.mkdtempSync(path.join(os.tmpdir(), `dash-cap${cap.numero}-`));
    const folder = path.join(ws, cap.carpeta || 'proyecto');
    fs.mkdirSync(folder, { recursive: true });
    if (cap.preparar) await cap.preparar(folder);
    const settings = Object.assign({ 'dash.path': DASH }, cap.settings || {});
    // sinCarpeta: VS Code empty (the chapter makes its folder in `folder`, as a person would)
    const r = await Rodaje.start({ workspace: cap.sinCarpeta ? null : folder, open: cap.open || [], settings, vsix });
    try {
        await cap.guion(r, folder);
    } catch (e) {
        await r.page.screenshot({ path: path.join(out, `${String(cap.numero).padStart(2, '0')}-fallo.png`) }).catch(() => {});
        await r.fin(path.join(out, String(cap.numero).padStart(2, '0') + '-fallo')).catch(() => {});
        throw new Error(`capítulo ${cap.numero} (${cap.titulo}): ${e.message}`);
    }
    const res = await r.fin(path.join(out, String(cap.numero).padStart(2, '0')));
    fs.rmSync(ws, { recursive: true, force: true });
    const card = tarjeta(path.join(out, String(cap.numero).padStart(2, '0') + '-titulo.mp4'), cap.titulo, cap.resumen, 3);
    return [card, { mp4: res.mp4, duration: res.duration, subs: JSON.parse(fs.readFileSync(res.json, 'utf8')).subs }];
}

async function main() {
    const args = process.argv.slice(2);
    const opt = (name) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : null; };
    const out = path.resolve(opt('--out') || path.join(os.homedir(), '.cache', 'dash-video', 'tutorial'));
    const solo = opt('--solo') ? opt('--solo').split(',').map(Number) : null;
    fs.mkdirSync(out, { recursive: true });
    const vsix = args.includes('--dev') ? null : empaquetar();
    const pieces = [tarjeta(path.join(out, '00-portada.mp4'), 'Dash para Amiga en VS Code',
                            'Un tutorial de la extensión', 4)];
    for (const cap of capitulos(solo)) {
        process.stdout.write(`capítulo ${cap.numero}: ${cap.titulo}... `);
        const t = Date.now();
        pieces.push(...await grabarCapitulo(cap, out, vsix));
        console.log(`${Math.round((Date.now() - t) / 1000)} s`);
    }
    const res = juntar(pieces, path.join(out, 'tutorial'));
    console.log(`tutorial: ${res.mp4} (${Math.round(res.duration / 1000)} s, ${res.subs.length} subtítulos), ${res.sub}`);
}

if (require.main === module) main().catch((e) => { console.error(e.message); process.exit(1); });

module.exports = { tarjeta, juntar, capitulos, grabarCapitulo, dt };
