// Capítulo 6 del tutorial: depurar en un Amiga de verdad, con el emulador haciendo de Amiga
// (docs/IDE_VIDEO_LOOP.md, v8): bgdbserver en él, esperando a gdb por la red
const fs = require('fs');
const net = require('net');
const path = require('path');
const { spawn } = require('child_process');

const DASH = path.resolve(__dirname, '..', '..', '..', '..');

const PROGRAMA = `# Suma de 1 a 5, avisando de cada paso
func avisar(total: Int)
    Print "Llevamos #{total}"
end

Main
    total = 0
    for n in (1..5)
        total = total + n
        avisar(total)
    end
    Print "Fin"
end
`;

// as "Dash: Nuevo proyecto" leaves it: the emulator, and a real Amiga by its name
const LAUNCH = {
    version: '0.2.0',
    configurations: [
        { type: 'dash', request: 'launch', name: 'Depurar en el Amiga', program: '${workspaceFolder}/suma.dash' },
        { type: 'dash', request: 'attach', name: 'Amiga real', target: 'amiga.local:2345', program: '${workspaceFolder}/suma.dash' },
    ],
};

function puertoLibre() {
    return new Promise((resolve) => {
        const s = net.createServer();
        s.listen(0, '127.0.0.1', () => { const { port } = s.address(); s.close(() => resolve(port)); });
    });
}

function escuchando(port) {
    const hex = ':' + port.toString(16).toUpperCase().padStart(4, '0');
    return ['/proc/net/tcp', '/proc/net/tcp6'].some((f) => {
        try { return fs.readFileSync(f, 'utf8').split('\n').some((l) => { const c = l.trim().split(/\s+/); return c[1] && c[1].endsWith(hex) && c[3] === '0A'; }); }
        catch (e) { return false; }
    });
}

async function parado(r, ms = 120000) {
    await r.page.waitForSelector('.monaco-editor .debug-top-stack-frame-line', { timeout: ms }).catch(() => {});
    await r.esperar(800);
}

module.exports = {
    titulo: '6. Un Amiga de verdad',
    resumen: 'El programa en tu Amiga, y VS Code depurándolo por la red',
    carpeta: 'suma',
    preparar(dir) {
        fs.writeFileSync(path.join(dir, 'suma.dash'), PROGRAMA);
        fs.mkdirSync(path.join(dir, '.vscode'), { recursive: true });
        fs.writeFileSync(path.join(dir, '.vscode', 'launch.json'), JSON.stringify(LAUNCH, null, 2) + '\n');
    },
    open: ['suma.dash'],
    async guion(r, dir) {
        let amiga = null;
        try {
            await r.decir('También se depura un programa que corre en un Amiga de verdad, por la red', 4500);
            r.subtitulo('"Dash: Preparar para un Amiga real" lo compila con lo que necesita el depurador', 6500);
            await r.orden('Dash: Preparar para un Amiga real', 600);
            await r.saltar(() => r.page.waitForSelector('.notification-toast:has-text("Listo")', { timeout: 120000 }).catch(() => {}));
            await r.esperar(5500);
            await r.decir('En el Amiga hacen falta una pila TCP/IP y bgdbserver, de Aminet', 5000);
            r.subtitulo('Se copia bin/suma.debug al Amiga y en su Shell: bgdbserver :2345 suma.debug', 6000);
            // the emulator plays the Amiga: bgdbserver waiting on the network (no window)
            const port = await puertoLibre();
            amiga = spawn('python3', [path.join(DASH, 'tools', 'emu_run.py'), '--gdbserver', String(port), '--no-relay',
                                      path.join(dir, 'bin', 'suma.debug')], { cwd: DASH, detached: true, stdio: 'ignore' });
            await r.esperar(6000);
            await r.saltar(async () => { for (let i = 0; i < 240 && !escuchando(port); i++) await r.esperar(500); });
            await r.decir('Aquí el emulador hace de Amiga, con bgdbserver esperando', 4000);
            // the configuration: its address
            r.subtitulo('En launch.json, "Amiga real" dice dónde está: su nombre o su IP, y el puerto', 7000);
            await r.clic('.explorer-folders-view .monaco-list-row:has-text(".vscode")');
            await r.esperar(700);
            await r.clic('.explorer-folders-view .monaco-list-row:has-text("launch.json")');
            await r.esperar(2500);
            await r.clic(r.linea('amiga.local'));
            await r.esperar(500);
            await r.tecla('End', 200);
            await r.tecla('Shift+Home', 300);
            await r.tecla('Backspace', 300);      // (typing a quote over a selection would put it between quotes)
            await r.escribir(`"target": "localhost:${port}",`, 45);
            await r.tecla('Control+s', 1500);
            // a breakpoint, and F5 with that configuration
            r.subtitulo('Un punto de parada, y se arranca con la configuración "Amiga real"', 6000);
            await r.clic('.tab:has-text("suma.dash")');
            await r.esperar(800);
            await r.clic(await r.margen('avisar(total)'));
            await r.esperar(1200);
            await r.orden('Debug: Select and Start Debugging', 900);
            await r.clic(r.page.locator('.quick-input-list .monaco-list-row', { hasText: 'Amiga real' }).first());
            await r.saltar(() => parado(r));
            await r.esperar(1500);
            await r.clic('.debug-view-content .monaco-list-row:has-text("Locals")');
            await r.decir('Para en el Amiga: las variables, la pila y los pasos, igual que en el emulador', 6000);
            r.subtitulo('Lo que escribe el programa sale en el Shell del Amiga', 5000);
            await r.tecla('F5', 500);
            await r.saltar(() => parado(r, 30000));
            await r.esperar(4500);
            await r.tecla('Shift+F5', 1500);
            await r.decir('Eso es todo: a programar el Amiga con Dash', 3500);
        } finally {
            if (amiga) try { process.kill(-amiga.pid, 'SIGTERM'); } catch (e) { /* gone */ }
        }
    },
};
