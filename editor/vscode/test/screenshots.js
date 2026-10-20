// The pictures of the README and the walkthrough (images/): the visual editor (its webview in a headless
// Chromium, with the window of "Dash: Nuevo proyecto"). The Amiga's (images/amiga.png) comes from the
// emulator: tools/emu_run.py --autoclose 8 --screenshot 6 images/amiga.png <the new project's program>.
//     node test/screenshots.js
const path = require('path');
const fs = require('fs');
const { findChromium, openPage } = require('./webview.js');
const { projectFiles } = require('../newProject.js');

(async () => {
    const chromium = findChromium();
    if (!chromium) { console.error('no Chromium'); process.exit(1); }
    const page = await openPage(chromium, 'file://' + path.join(__dirname, 'webview.html'));
    try {
        await page.send('Emulation.setDeviceMetricsOverride', { width: 1000, height: 560, deviceScaleFactor: 1, mobile: false });
        await page.eval('new Promise((r) => { const t = () => DashUIEditor.doc ? r() : setTimeout(t, 20); t(); })');
        const text = projectFiles('hola').files['ventana.dashui'];
        await page.eval(`DashUIEditor.load(${JSON.stringify(text)})`);
        await page.eval('DashUIEditor.select([1, 0])');
        const shot = await page.send('Page.captureScreenshot', { format: 'png' });
        const out = path.join(__dirname, '..', 'images', 'editor.png');
        fs.mkdirSync(path.dirname(out), { recursive: true });
        fs.writeFileSync(out, Buffer.from(shot.data, 'base64'));
        console.log('saved ' + out);
    } finally {
        page.close();
    }
})();
