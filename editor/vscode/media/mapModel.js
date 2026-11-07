// @ts-check
// What the tile map editor does to a map, as Forja's (src/mapas.dash): cells, box, fill, layers, collisions,
// objects, size, and the Dash lines that load and draw it. No DOM: the webview (media/map.js) and the tests use it.
// A map is DashIFF's (media/iff.js): {width, height, tile, tileset, layers: [{name, type, visible, cells}], objects}.
(function (root) {
    'use strict';
    const IFF = typeof module === 'object' && module.exports ? require('./iff.js') : root.DashIFF;

    const TOOLS = ['pencil', 'box', 'fill', 'picker', 'erase'];
    const TOOL_KEYS = 'pbfke';                       // Forja's: lápiz, caja (box), relleno (fill), cuentagotas, borrar
    const TOOL_NAMES = ['Lápiz', 'Caja', 'Relleno', 'Cuentagotas', 'Borrar'];
    const TILES = 0, COLLISIONS = 1;
    const COLLISION_NAMES = ['Sólido', 'Plataforma', 'Escalera', 'Daño'];      // 1 to 4
    const COLLISION_COLOURS = [0xE63C32, 0xF0C828, 0x3CC850, 0xDC3CDC];
    const CLASSES = ['jugador', 'enemigo', 'moneda', 'puerta', 'otro'];
    const MAX_SIDE = 1024;

    function clone(m) {
        return Object.assign({}, m, { layers: m.layers.map((l) => Object.assign({}, l, { cells: l.cells.slice() })),
            objects: m.objects.map((o) => Object.assign({}, o)) });
    }
    const isCollisions = (m, l) => !!m.layers[l] && m.layers[l].type === COLLISIONS;

    function get(m, l, x, y) {
        return x < 0 || y < 0 || x >= m.width || y >= m.height ? 0 : m.layers[l].cells[y * m.width + x];
    }
    /** Sets a cell; true if it changed */
    function set(m, l, x, y, v) {
        if (x < 0 || y < 0 || x >= m.width || y >= m.height) return false;
        const c = m.layers[l].cells, i = y * m.width + x;
        if (c[i] === v) return false;
        c[i] = v;
        return true;
    }

    /** The cells of a line from one cell to another (a drag without gaps) */
    function line(m, l, x0, y0, x1, y1, v) {
        let n = 0;
        let dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);
        const sx = x1 < x0 ? -1 : 1, sy = y1 < y0 ? -1 : 1;
        let err = dx - dy;
        for (;;) {
            if (set(m, l, x0, y0, v)) n++;
            if (x0 === x1 && y0 === y1) break;
            const e2 = err * 2;
            if (e2 > -dy) { err -= dy; x0 += sx; }
            if (e2 < dx) { err += dx; y0 += sy; }
        }
        return n;
    }

    /** The box from x1, y1 to x2, y2 (any order), full of v: how many cells changed */
    function box(m, l, x1, y1, x2, y2, v) {
        let n = 0;
        for (let y = Math.min(y1, y2); y <= Math.max(y1, y2); y++)
            for (let x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) if (set(m, l, x, y, v)) n++;
        return n;
    }

    /** Fills from x, y the equal cells joined by their sides: how many changed */
    function fill(m, l, x, y, v) {
        if (x < 0 || y < 0 || x >= m.width || y >= m.height) return 0;
        const c = m.layers[l].cells, w = m.width, old = c[y * w + x];
        if (old === v) return 0;
        let n = 0;
        const stack = [y * w + x];
        while (stack.length) {
            const i = stack.pop();
            if (c[i] !== old) continue;
            c[i] = v; n++;
            const cx = i % w;
            if (cx > 0) stack.push(i - 1);
            if (cx < w - 1) stack.push(i + 1);
            if (i >= w) stack.push(i - w);
            if (i + w < c.length) stack.push(i + w);
        }
        return n;
    }

    // --- layers: {ok, layer} (the layer chosen after it) or {message}
    function addLayer(m, cur) {
        if (m.layers.length >= IFF.MAX_LAYERS) return { message: 'Un mapa tiene como mucho 8 capas.' };
        m.layers.splice(cur + 1, 0, { name: `capa ${m.layers.length + 1}`, type: TILES, visible: true,
            cells: new Uint16Array(m.width * m.height) });
        return { ok: true, layer: cur + 1 };
    }
    function removeLayer(m, cur) {
        if (m.layers.length < 2) return { message: 'Es la única capa.' };
        m.layers.splice(cur, 1);
        return { ok: true, layer: Math.min(cur, m.layers.length - 1) };
    }
    /** d -1: back (drawn before); 1: to the front */
    function moveLayer(m, cur, d) {
        const a = cur + d;
        if (a < 0 || a >= m.layers.length) return {};
        const [l] = m.layers.splice(cur, 1);
        m.layers.splice(a, 0, l);
        return { ok: true, layer: a };
    }
    /** From tiles to collisions and back (the cells stay, as Forja) */
    function toggleType(m, cur) {
        m.layers[cur].type = m.layers[cur].type === COLLISIONS ? TILES : COLLISIONS;
        return { ok: true, layer: cur };
    }
    function toggleVisible(m, l) { m.layers[l].visible = !m.layers[l].visible; return { ok: true }; }   // (the chosen layer stays)
    function renameLayer(m, l, name) {
        name = String(name).slice(0, 255);
        if (!name || name === m.layers[l].name) return {};
        m.layers[l].name = name;
        return { ok: true, layer: l };
    }

    /** New width and height in cells: what fits stays, from the top left corner */
    function resize(m, w, h) {
        if (!(w >= 1 && h >= 1 && w <= MAX_SIDE && h <= MAX_SIDE) || (w === m.width && h === m.height)) return {};
        for (const l of m.layers) {
            const n = new Uint16Array(w * h);
            for (let y = 0; y < h && y < m.height; y++)
                for (let x = 0; x < w && x < m.width; x++) n[y * w + x] = l.cells[y * m.width + x];
            l.cells = n;
        }
        m.width = w; m.height = h;
        return { ok: true };
    }
    function setTileSize(m, t) {
        if (![8, 16, 32].includes(t) || t === m.tile) return {};
        for (const o of m.objects) { o.x = Math.round(o.x / m.tile * t); o.y = Math.round(o.y / m.tile * t); }
        m.tile = t;
        return { ok: true };
    }

    // --- objects: points in pixels with a kind; each takes a cell from its corner
    /** The object at pixel px, py of the map (the one on top is the last); -1 if none */
    function objectAt(m, px, py) {
        for (let i = m.objects.length - 1; i >= 0; i--) {
            const o = m.objects[i];
            if (px >= o.x && py >= o.y && px < o.x + m.tile && py < o.y + m.tile) return i;
        }
        return -1;
    }
    function addObject(m, cx, cy, kind) {
        if (m.objects.length >= IFF.MAX_OBJECTS) return { message: 'Un mapa tiene como mucho 256 objetos.' };
        m.objects.push({ x: cx * m.tile, y: cy * m.tile, kind, name: '', sprite: '' });
        return { ok: true, object: m.objects.length - 1 };
    }
    function removeObject(m, i) {
        if (i < 0 || i >= m.objects.length) return {};
        m.objects.splice(i, 1);
        return { ok: true, object: -1 };
    }
    /** Moves object i to cell cx, cy (Forja moves them a cell at a time) */
    function moveObject(m, i, cx, cy) {
        const o = m.objects[i];
        if (!o) return false;
        const x = Math.max(0, Math.min(m.width - 1, cx)) * m.tile, y = Math.max(0, Math.min(m.height - 1, cy)) * m.tile;
        if (o.x === x && o.y === y) return false;
        o.x = x; o.y = y;
        return true;
    }
    function setObject(m, i, fields) {
        const o = m.objects[i];
        if (!o) return {};
        let changed = false;
        for (const k of ['kind', 'name', 'sprite'])
            if (k in fields && String(fields[k]).slice(0, 255) !== o[k]) { o[k] = String(fields[k]).slice(0, 255); changed = true; }
        return changed ? { ok: true, object: i } : {};
    }

    /** The value a click puts: the collision type in a collision layer, else the tile with its mirrors */
    function value(m, layer, tile, mirror, collision) {
        if (isCollisions(m, layer)) return collision;
        return tile ? tile + mirror : 0;
    }

    /**
     * The Dash lines that load the map and its tileset and draw the first screen (file: the map's name): the same
     * text Forja copies (mp_codigo)
     */
    function code(m, file) {
        const ts = m.tile;
        let t = `# ${file}: mapa de ${m.width} x ${m.height} tiles de ${ts}, ${m.layers.length} capas\n`;
        t += `if not tilemap_load(0, "${file}")\n    Print "No se puede cargar ${file}"\nend\n`;
        if (m.tileset) {
            t += `if not bob_load(1, "${m.tileset}")\n    Print "No se puede cargar ${m.tileset}"\nend\n`;
            t += '# los colores del tileset, en la paleta de la pantalla\n';
            t += `bob_load_colors("${m.tileset}", 0)\n`;
        }
        const cols = Math.floor(320 / ts), rows = Math.floor(256 / ts);
        t += `# pintar la pantalla (aquí, 320 x 256 de tiles de ${ts}): la capa 0 y las demás encima\n`;
        t += `tilemap_draw(0, 0, 1, 0, 0, ${cols}, ${rows}, 0, 0)\n`;
        for (let l = 1; l < m.layers.length; l++) {
            if (isCollisions(m, l))
                t += `# la capa ${l} es de choques: no se pinta; tilemap_get(0, ${l}, x, y) dice qué hay en la celda x, y (1 sólido, 2 plataforma, 3 escalera, 4 daño)\n`;
            else t += `tilemap_draw_masked(0, ${l}, 1, 0, 0, ${cols}, ${rows}, 0, 0)\n`;
        }
        if (m.objects.length) {
            t += `# ${m.objects.length} objetos: tilemap_object_find busca los de una clase; x e y en píxeles del mapa\n`;
            const seen = new Set();
            for (const o of m.objects) {
                if (seen.has(o.kind)) continue;
                seen.add(o.kind);
                t += `o = tilemap_object_find(0, "${o.kind}", 0)\n`;
                t += `while o >= 0\n    # ${o.kind}: tilemap_object_x(0, o), tilemap_object_y(0, o)\n    o = tilemap_object_find(0, "${o.kind}", o + 1)\nend\n`;
            }
        }
        return t;
    }

    const api = { IFF, TOOLS, TOOL_KEYS, TOOL_NAMES, TILES, COLLISIONS, COLLISION_NAMES, COLLISION_COLOURS, CLASSES,
        MAX_SIDE, clone, isCollisions, get, set, line, box, fill, addLayer, removeLayer, moveLayer, toggleType,
        toggleVisible, renameLayer, resize, setTileSize, objectAt, addObject, removeObject, moveObject, setObject,
        value, code };
    if (typeof module === 'object' && module.exports) module.exports = api;
    else root.DashMap = api;
})(typeof window !== 'undefined' ? window : globalThis);
