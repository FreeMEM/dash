// @ts-check
// "Dash: Nuevo sprite, BOB o mapa", as Amiga-B in Forja: the kinds and the bytes of each new file (V3).
const IFF = require('./media/iff.js');

/** The kinds offered, with Forja's sizes (sp_nuevo, and mp_nuevo(64, 32, 16)) */
const KINDS = [
    { id: 'sprite', label: 'Sprite de hardware', detail: '16 x 16, 3 colores y el transparente (sprite_load)', file: 'sprite.iff', view: 'dash.spriteEditor' },
    { id: 'attached', label: 'Sprite acoplado', detail: '16 x 16, 15 colores y el transparente (sprite_load_attached)', file: 'sprite.iff', view: 'dash.spriteEditor' },
    { id: 'bob', label: 'BOB', detail: '32 x 32, 16 colores; luego, del tamaño y los colores que quieras (bob_load)', file: 'bob.iff', view: 'dash.spriteEditor' },
    { id: 'map', label: 'Mapa de tiles', detail: '64 x 32 tiles de 16, con un BOB como tileset (tilemap_load)', file: 'mapa.fmap', view: 'dash.mapEditor' },
];

/** The bytes of a new file of that kind */
function newGraphicBytes(kind) {
    if (kind === 'map') return IFF.writeFmap(IFF.newMap(64, 32, 16, ''));
    if (kind === 'bob') return IFF.writeIlbm(IFF.newSprite('bob', 32, 32, 4));
    return IFF.writeIlbm(IFF.newSprite(kind, 16, 16, 0));
}

module.exports = { KINDS, newGraphicBytes };
