// Test page for the editor's webview in a plain browser: loads a sample .dashui as VS
// Code would ({type:'update'}); edits sent back are in window.__posted.
window.postMessage({ type: 'update', text: JSON.stringify({
    dashui: 1,
    windows: [{ name: 'Principal', title: 'Navegador', id: 1, menus: [{ title: 'Proyecto', items: [{ label: 'Salir', key: 'Q', event: 9 }] }],
        root: { type: 'vgroup', children: [
            { type: 'hgroup', children: [
                { type: 'button', name: 'atras', label: '<', event: 1 },
                { type: 'string', name: 'url', text: 'http://aminet.net/', max: 1024, ack: 2 } ] },
            { type: 'canvas', name: 'pagina', min_width: 320, min_height: 120 },
            { type: 'text', name: 'estado', text: 'Listo' } ] } }],
}, null, 2) }, '*');
