// @ts-check
// The files of Forja's sprite and map editors, read and written byte for byte as Forja and Dash do
// (docs/VSCODE_JUEGOS_LOOP.md, V1). Used by the extension (Node) and by the webviews (a plain script: window.DashIFF).
//
// Sprites and BOBs: IFF ILBM with the frames side by side (src/sprites.dash of Forja, sp_escribir and sp_leer).
//   BMHD with masking 2 (colour 0 is transparent), CMAP with 2^planes colours, GRAB (the grab point) and FRJA, a
//   text chunk of Forja: "1 kind width speed", kind 1 a hardware sprite (with 4 planes, attached), 0 a BOB; width is
//   the width of a frame and speed the ticks (1/50 s) per frame. Written without compression; read also ByteRun1
//   and the mask plane (masking 1). Without FRJA (a DPaint brush), the frames are square if they fit (bob_load's rule).
// Tile maps: IFF FORM FMAP (tilemap_save and tilemap_load of Dash's runtime, compiler/codegen.py): MHDR (version,
//   width, height, tile side, layers: five words), TSET (the tileset's file), a LAYR per layer (type, visible, the
//   name's length, the name, a zero byte if that is odd, then a word per cell: the tile in the low 14 bits, 1 the first
//   frame of the tileset and 0 empty, bit 14 mirrored left to right, bit 15 top to bottom) and OBJS (the count, then
//   each object: x, y, and kind, name and sprite, each a length byte and its characters, a zero byte if odd).
(function (root) {
    'use strict';

    const MIRROR_H = 16384, MIRROR_V = 32768, TILE_MASK = 16383;
    const MAX_LAYERS = 8, MAX_OBJECTS = 256;

    // the first 32 colours of a BOB, as Forja (then a 6x6x6 cube and greys)
    const FIRST = [0x000000, 0xFFFFFF, 0x777777, 0xBBBBBB, 0x444444, 0xAA0000, 0xFF5555, 0xAA5500,
        0xFFAA00, 0xFFFF55, 0x00AA00, 0x55FF55, 0x00AAAA, 0x55FFFF, 0x0000AA, 0x5555FF,
        0xAA00AA, 0xFF55FF, 0x553311, 0x996633, 0xDDAA77, 0xFFDDBB, 0x113355, 0x336699,
        0x6699CC, 0x224422, 0x447744, 0x88AA66, 0x552255, 0x884488, 0xCC77AA, 0x333344];

    /** The 256 colours a new image starts with (sp_paleta_inicial of Forja) */
    function initialPalette(hardware) {
        const p = FIRST.slice();
        while (p.length < 248) {
            const i = p.length - 32;
            p.push((Math.floor(i / 36) % 6) * 51 * 65536 + (Math.floor(i / 6) % 6) * 51 * 256 + (i % 6) * 51);
        }
        while (p.length < 256) {
            const g = (p.length - 247) * 28;
            p.push(g * 65536 + g * 256 + g);
        }
        if (hardware) { p[1] = 0xE0E0E0; p[2] = 0xE08030; p[3] = 0x3060C0; }
        return p;
    }

    /**
     * @typedef {{width: number, height: number, planes: number, hardware: boolean, palette: number[],
     *   frames: Uint8Array[], speed: number, grabX: number, grabY: number}} Sprite
     *   width and height of a frame; planes: 2^planes colours; hardware: a hardware sprite (16 wide, 2 planes, or 4
     *   attached); palette: 256 colours 0xRRGGBB (the first 2^planes are saved); frames: a colour per pixel
     */

    /** A new sprite: kind 'sprite' (16 wide, 3 colours), 'attached' (16 wide, 15 colours) or 'bob' */
    function newSprite(kind, width, height, planes) {
        const hardware = kind === 'sprite' || kind === 'attached';
        const w = hardware ? 16 : Math.max(1, width | 0);
        const h = Math.max(1, height | 0);
        const pl = kind === 'sprite' ? 2 : kind === 'attached' ? 4 : Math.min(8, Math.max(1, planes | 0));
        return { width: w, height: h, planes: pl, hardware, palette: initialPalette(hardware),
            frames: [new Uint8Array(w * h)], speed: 6, grabX: 0, grabY: 0 };
    }

    function isAttached(s) { return s.hardware && s.planes === 4; }

    function text(bytes, at, n) {
        let t = '';
        for (let i = 0; i < n && at + i < bytes.length; i++) t += String.fromCharCode(bytes[at + i]);
        return t;
    }
    function latin1(t) {
        const out = new Uint8Array(t.length);
        for (let i = 0; i < t.length; i++) { const c = t.charCodeAt(i); out[i] = c < 256 ? c : 63; }
        return out;
    }
    const u16 = (b, o) => (b[o] << 8) | b[o + 1];
    const s16 = (b, o) => { const v = u16(b, o); return v & 0x8000 ? v - 0x10000 : v; };
    const u32 = (b, o) => ((b[o] << 24) >>> 0) + (b[o + 1] << 16) + (b[o + 2] << 8) + b[o + 3];

    /** Is it FORM....<type>? */
    function isForm(bytes, type) {
        return bytes.length >= 12 && text(bytes, 0, 4) === 'FORM' && text(bytes, 8, 4) === type;
    }

    /** The chunks of a FORM: [{id, at, length}] (at: where its data starts) */
    function chunks(bytes) {
        const out = [];
        const end = Math.min(bytes.length, 8 + u32(bytes, 4));
        let pos = 12;
        while (pos + 8 <= end) {
            const id = text(bytes, pos, 4);
            let n = u32(bytes, pos + 4);
            const at = pos + 8;
            if (at + n > end) n = end - at;            // cut short: what there is (as Forja)
            out.push({ id, at, length: n });
            pos = at + n + (n & 1);
        }
        return out;
    }

    /**
     * Reads an IFF ILBM as Forja does. Throws an Error with the reason (in Spanish, as Forja says it).
     * @param {Uint8Array} bytes @returns {Sprite}
     */
    function readIlbm(bytes) {
        if (!isForm(bytes, 'ILBM')) throw new Error('No es una imagen IFF ILBM.');
        let w = 0, h = 0, planes = 0, mask = 0, comp = 0, gx = 0, gy = 0, frja = '';
        let cmap = -1, ncol = 0, body = -1, bodyEnd = 0;
        for (const c of chunks(bytes)) {
            if (c.id === 'BMHD' && c.length >= 20) {
                w = u16(bytes, c.at); h = u16(bytes, c.at + 2);
                planes = bytes[c.at + 8]; mask = bytes[c.at + 9]; comp = bytes[c.at + 10];
            } else if (c.id === 'CMAP') { cmap = c.at; ncol = Math.floor(c.length / 3); }
            else if (c.id === 'GRAB' && c.length >= 4) { gx = s16(bytes, c.at); gy = s16(bytes, c.at + 2); }
            else if (c.id === 'FRJA') frja = text(bytes, c.at, c.length);
            else if (c.id === 'BODY') { body = c.at; bodyEnd = c.at + c.length; }
        }
        if (w <= 0 || h <= 0 || body < 0) throw new Error('A la imagen le falta BMHD o BODY.');
        if (planes < 1 || planes > 8 || comp > 1)
            throw new Error('Solo imágenes de 1 a 8 planos, sin comprimir o con ByteRun1.');
        const row = Math.floor((w + 15) / 16) * 2;
        const img = new Uint8Array(w * h);
        const tmp = new Uint8Array(row);
        const total = planes + (mask === 1 ? 1 : 0);
        let pos = body;
        for (let y = 0; y < h; y++) {
            for (let p = 0; p < total; p++) {
                pos = readRow(bytes, pos, bodyEnd, comp === 1, tmp, row);
                if (pos < 0) throw new Error('La imagen está cortada.');
                if (p >= planes) continue;
                const bit = 1 << p;
                for (let i = 0; i < row; i++) {
                    const v = tmp[i];
                    if (!v) continue;
                    for (let k = 0; k < 8; k++) {
                        const x = i * 8 + k;
                        if ((v & (0x80 >> k)) && x < w) img[y * w + x] |= bit;
                    }
                }
            }
        }
        // the width of a frame: FRJA's, or bob_load's rule (square frames)
        let hardware = false, speed = 6, fw = w;
        if (w > h && w % h === 0) fw = h;
        const parts = frja.trim().split(/ +/);
        if (parts.length >= 4 && parts[0] === '1') {
            const a = parseInt(parts[2], 10);
            if (a > 0 && w % a === 0) fw = a;
            const v = parseInt(parts[3], 10);
            if (v > 0) speed = v;
            hardware = parts[1] === '1' && fw === 16 && planes <= 4;
        }
        const palette = initialPalette(hardware);
        for (let i = 0; i < ncol && i < 256; i++)
            palette[i] = (bytes[cmap + i * 3] << 16) | (bytes[cmap + i * 3 + 1] << 8) | bytes[cmap + i * 3 + 2];
        if (hardware) planes = planes <= 2 ? 2 : 4;
        const frames = [];
        for (let f = 0; f < w / fw; f++) {
            const px = new Uint8Array(fw * h);
            for (let y = 0; y < h; y++)
                for (let x = 0; x < fw; x++) px[y * fw + x] = img[y * w + f * fw + x];
            frames.push(px);
        }
        return { width: fw, height: h, planes, hardware, palette, frames, speed, grabX: gx, grabY: gy };
    }

    // a row of a plane from pos of the BODY (ByteRun1 if compressed): the position after it, or -1 if cut short
    function readRow(b, pos, end, compressed, out, len) {
        if (!compressed) {
            if (pos + len > end) return -1;
            out.set(b.subarray(pos, pos + len));
            return pos + len;
        }
        let n = 0;
        while (n < len) {
            if (pos >= end) return -1;
            const c = b[pos++];
            if (c < 128) {
                let k = c + 1;
                if (pos + k > end) return -1;
                if (n + k > len) k = len - n;
                out.set(b.subarray(pos, pos + k), n);
                pos += c + 1; n += k;
            } else if (c > 128) {
                let k = 257 - c;
                if (pos >= end) return -1;
                if (n + k > len) k = len - n;
                out.fill(b[pos], n, n + k);
                pos++; n += k;
            }
        }
        return pos;
    }

    /** Writes a sprite as Forja does (the same bytes) @param {Sprite} s @returns {Uint8Array} */
    function writeIlbm(s) {
        const nf = s.frames.length, w = s.width * nf, h = s.height, planes = s.planes;
        const row = Math.floor((w + 15) / 16) * 2;
        const body = row * h * planes;
        const ncol = 1 << planes, cmap = ncol * 3;
        const frja = latin1(`1 ${s.hardware ? 1 : 0} ${s.width} ${s.speed}`);
        const frjaLen = frja.length + (frja.length & 1);
        const total = 4 + 28 + 8 + cmap + (cmap & 1) + 12 + 8 + frjaLen + 8 + body;
        const b = new Uint8Array(total + 8);
        const dv = new DataView(b.buffer);
        const chunk = (o, id, n) => { b.set(latin1(id), o); dv.setUint32(o + 4, n); return o + 8; };
        let o = chunk(0, 'FORM', total);
        b.set(latin1('ILBM'), o);
        o = chunk(o + 4, 'BMHD', 20);
        dv.setUint16(o, w); dv.setUint16(o + 2, h);
        b[o + 8] = planes; b[o + 9] = 2; b[o + 14] = 10; b[o + 15] = 11;
        dv.setUint16(o + 16, w); dv.setUint16(o + 18, h);
        o = chunk(o + 20, 'CMAP', cmap);
        for (let i = 0; i < ncol; i++) {
            const c = s.palette[i] || 0;
            b[o + i * 3] = (c >> 16) & 255; b[o + i * 3 + 1] = (c >> 8) & 255; b[o + i * 3 + 2] = c & 255;
        }
        o = chunk(o + cmap + (cmap & 1), 'GRAB', 4);
        dv.setInt16(o, s.grabX); dv.setInt16(o + 2, s.grabY);
        o = chunk(o + 4, 'FRJA', frja.length);
        b.set(frja, o);
        o = chunk(o + frjaLen, 'BODY', body);
        for (let y = 0; y < h; y++)
            for (let f = 0; f < nf; f++) {
                const px = s.frames[f];
                for (let x = 0; x < s.width; x++) {
                    const c = px[y * s.width + x];
                    if (!c) continue;
                    const gx = f * s.width + x, bit = 0x80 >> (gx & 7);
                    for (let p = 0; p < planes; p++)
                        if ((c >> p) & 1) b[o + (y * planes + p) * row + (gx >> 3)] |= bit;
                }
            }
        return b;
    }

    /**
     * @typedef {{name: string, type: number, visible: boolean, cells: Uint16Array}} Layer   type 0 tiles, 1 collisions
     * @typedef {{x: number, y: number, kind: string, name: string, sprite: string}} MapObject   x, y in pixels
     * @typedef {{width: number, height: number, tile: number, tileset: string, layers: Layer[], objects: MapObject[]}} TileMap
     */

    /** A new map of width x height tiles of tile pixels, with one layer */
    function newMap(width, height, tile, tileset) {
        return { width, height, tile, tileset: tileset || '',
            layers: [{ name: 'fondo', type: 0, visible: true, cells: new Uint16Array(width * height) }], objects: [] };
    }

    /** Reads an FMAP as tilemap_load does @param {Uint8Array} bytes @returns {TileMap} */
    function readFmap(bytes) {
        if (!isForm(bytes, 'FMAP')) throw new Error('No es un mapa IFF FORM FMAP.');
        /** @type {TileMap} */
        const m = { width: 0, height: 0, tile: 16, tileset: '', layers: [], objects: [] };
        let header = false;
        for (const c of chunks(bytes)) {
            const at = c.at;
            if (c.id === 'MHDR' && c.length >= 10 && !header) {
                header = true;
                m.width = u16(bytes, at + 2); m.height = u16(bytes, at + 4); m.tile = u16(bytes, at + 6);
            } else if (c.id === 'TSET') m.tileset = text(bytes, at, c.length).replace(/\0+$/, '');
            else if (c.id === 'LAYR' && header && c.length >= 3 && m.layers.length < MAX_LAYERS) {
                const n = bytes[at + 2];
                const start = at + ((3 + n + 1) & ~1);
                const cells = new Uint16Array(m.width * m.height);
                for (let i = 0; i < cells.length && start + i * 2 + 1 < at + c.length; i++) cells[i] = u16(bytes, start + i * 2);
                m.layers.push({ name: text(bytes, at + 3, n), type: bytes[at], visible: !!bytes[at + 1], cells });
            } else if (c.id === 'OBJS' && c.length >= 2) {
                let q = at + 2;
                const count = u16(bytes, at);
                for (let i = 0; i < count && m.objects.length < MAX_OBJECTS && q + 4 <= at + c.length; i++) {
                    const x = s16(bytes, q), y = s16(bytes, q + 2);
                    q += 4;
                    const t = [];
                    let e = 4 + 3;
                    for (let k = 0; k < 3; k++) {
                        const n = bytes[q];
                        t.push(text(bytes, q + 1, n));
                        q += 1 + n; e += n;
                    }
                    if (e & 1) q++;
                    m.objects.push({ x, y, kind: t[0], name: t[1], sprite: t[2] });
                }
            }
        }
        if (!header) throw new Error('Al mapa le falta MHDR.');
        return m;
    }

    /** Writes a map as tilemap_save does (the same bytes) @param {TileMap} m @returns {Uint8Array} */
    function writeFmap(m) {
        const parts = [];
        const word = (v) => [(v >> 8) & 255, v & 255];
        const chunk = (id, data) => {
            const n = data.length;
            const out = new Uint8Array(8 + n + (n & 1));
            out.set(latin1(id), 0);
            new DataView(out.buffer).setUint32(4, n);
            out.set(data, 8);
            parts.push(out);
        };
        chunk('MHDR', new Uint8Array([...word(1), ...word(m.width), ...word(m.height), ...word(m.tile), ...word(m.layers.length)]));
        chunk('TSET', latin1(m.tileset || ''));
        for (const l of m.layers) {
            const name = latin1(l.name);
            const head = (3 + name.length + 1) & ~1;
            const data = new Uint8Array(head + m.width * m.height * 2);
            data[0] = l.type; data[1] = l.visible ? 1 : 0; data[2] = name.length;
            data.set(name, 3);
            for (let i = 0; i < m.width * m.height; i++) {
                const v = l.cells[i] || 0;
                data[head + i * 2] = v >> 8; data[head + i * 2 + 1] = v & 255;
            }
            chunk('LAYR', data);
        }
        if (m.objects.length) {
            const bytes = [...word(m.objects.length)];
            for (const o of m.objects) {
                bytes.push(...word(o.x & 0xFFFF), ...word(o.y & 0xFFFF));
                let e = 4 + 3;
                for (const t of [o.kind, o.name, o.sprite]) {
                    const s = latin1(t || '').subarray(0, 255);
                    bytes.push(s.length, ...s);
                    e += s.length;
                }
                if (e & 1) bytes.push(0);
            }
            chunk('OBJS', new Uint8Array(bytes));
        }
        const size = parts.reduce((a, p) => a + p.length, 0);
        const out = new Uint8Array(12 + size);
        out.set(latin1('FORM'), 0);
        new DataView(out.buffer).setUint32(4, 4 + size);
        out.set(latin1('FMAP'), 8);
        let o = 12;
        for (const p of parts) { out.set(p, o); o += p.length; }
        return out;
    }

    const api = { MIRROR_H, MIRROR_V, TILE_MASK, MAX_LAYERS, MAX_OBJECTS, initialPalette, newSprite, isAttached,
        isForm, readIlbm, writeIlbm, newMap, readFmap, writeFmap };
    if (typeof module === 'object' && module.exports) module.exports = api;
    else root.DashIFF = api;
})(typeof window !== 'undefined' ? window : globalThis);
