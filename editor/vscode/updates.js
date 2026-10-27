// New versions of Dash: at most once a day, the latest release of Dash on GitHub (tags v1.2.3; the
// extension's own are vscode-x.y.z) against the version of the compiler in use (__version__ in its
// compiler/__init__.py). A notice with what is new; "dash.updates.check" off: no request at all.
const fs = require('fs');
const path = require('path');

const RELEASES = 'https://api.github.com/repos/FreeMEM/dash/releases?per_page=30';
const DAY = 24 * 3600 * 1000;

/** The version of the compiler in that folder, or null */
function localVersion(dashDir) {
    try {
        const m = /__version__\s*=\s*["']([^"']+)["']/.exec(
            fs.readFileSync(path.join(dashDir, 'compiler', '__init__.py'), 'utf8'));
        return m ? m[1] : null;
    } catch (e) {
        return null;
    }
}

/** [major, minor, patch] of "1.2.3" (or "v1.2.3"), or null */
function parseVersion(text) {
    const m = /^v?(\d+)\.(\d+)\.(\d+)$/.exec(String(text || '').trim());
    return m ? [+m[1], +m[2], +m[3]] : null;
}

/** Is version a newer than b? (false if either is not a version) */
function isNewer(a, b) {
    const x = parseVersion(a), y = parseVersion(b);
    if (!x || !y) return false;
    for (let i = 0; i < 3; i++) if (x[i] !== y[i]) return x[i] > y[i];
    return false;
}

/** The newest published release of Dash in GitHub's list: {version, url}, or null */
function latestRelease(list) {
    let best = null;
    for (const r of Array.isArray(list) ? list : []) {
        if (!r || r.draft || r.prerelease || !/^v\d+\.\d+\.\d+$/.test(r.tag_name || '')) continue;
        const version = r.tag_name.slice(1);
        if (!best || isNewer(version, best.version)) best = { version, url: r.html_url };
    }
    return best;
}

/** GitHub's list of releases (rejects on a network error or an answer that is not 200) */
function fetchReleases() {
    const https = require('https');
    return new Promise((resolve, reject) => {
        const req = https.get(RELEASES, { headers: { 'User-Agent': 'dash-vscode', Accept: 'application/vnd.github+json' },
                                          timeout: 10000 }, (res) => {
            let body = '';
            res.setEncoding('utf8');
            res.on('data', (c) => { body += c; });
            res.on('end', () => {
                if (res.statusCode !== 200) return reject(new Error('HTTP ' + res.statusCode));
                try { resolve(JSON.parse(body)); } catch (e) { reject(e); }
            });
        });
        req.on('timeout', () => req.destroy(new Error('timeout')));
        req.on('error', reject);
    });
}

/**
 * Looks for a newer Dash, if it is time to (once a day) and the setting allows it.
 * @param {*} vscode
 * @param {*} context the extension's (its globalState keeps the time of the last look and the version passed over)
 * @param {() => string | null} dashDir the compiler folder in use, or null
 * @param {{fetch?: () => Promise<any>, now?: () => number}} [opts] for the tests
 * @returns {Promise<{version: string, url: string} | null>} the newer release told about, if any
 */
async function checkUpdates(vscode, context, dashDir, opts = {}) {
    if (!vscode.workspace.getConfiguration('dash').get('updates.check', true)) return null;
    const state = context.globalState;
    const now = (opts.now || Date.now)();
    if (now - (state.get('dash.updates.last') || 0) < DAY) return null;
    const dir = dashDir();
    const mine = dir && localVersion(dir);
    if (!mine) return null;                   // (no compiler yet: the walkthrough says how to get one)
    let latest;
    try {
        latest = latestRelease(await (opts.fetch || fetchReleases)());
    } catch (e) {
        return null;                          // (no network: tomorrow again)
    }
    await state.update('dash.updates.last', now);
    if (!latest || !isNewer(latest.version, mine) || state.get('dash.updates.skipped') === latest.version) return null;
    const see = 'Ver novedades', skip = 'No avisar de esta';
    vscode.window.showInformationMessage(`Hay una versión nueva de Dash: ${latest.version} (tienes la ${mine}).`, see, skip)
        .then((choice) => {
            if (choice === see) vscode.env.openExternal(vscode.Uri.parse(latest.url));
            else if (choice === skip) state.update('dash.updates.skipped', latest.version);
        }, () => {});
    return latest;
}

module.exports = { checkUpdates, latestRelease, isNewer, parseVersion, localVersion };
