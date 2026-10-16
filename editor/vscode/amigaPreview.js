// "Ver en Amiga": the window of a .dashui opened by a tiny Dash program in FS-UAE,
// and a picture of the screen (tools/emu_run.py --screenshot). No VS Code here, so it
// can be tested from node: node amigaPreview.js <dash dir> <file.dashui> <Window> <out.png>
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFile } = require('child_process');

/** The Dash program that shows one window of the .dashui until it closes itself (autoclose). */
function previewProgram(windowName) {
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(windowName)) throw new Error('bad window name: ' + windowName);
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

module.exports = { previewProgram, emuArgs, runPreview };

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
