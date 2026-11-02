/* Dash's font_from_ttf (Dash 2.0, what Tachyon did with @native in lib/fuente_web.dash): a TrueType font (TTF, an OTF
   with TrueType outlines, or a WOFF 1.0 or 2.0 of them) made an Amiga TextFont in memory with stb_truetype: the
   Latin-1 characters (32-255, the same Unicode code points) at a size (the em), in a 1-bit plane, for font_use.
   WOFF 1.0 with Dash's zlib, WOFF 2.0 with Brotli. The font read (already TrueType) is kept for the other sizes
   (the last 8 files). All memory from exec. The C below comes from Tachyon (its comments in Spanish). */
#include <exec/memory.h>
#include <exec/nodes.h>
#include <dos/dos.h>
#include <graphics/text.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <string.h>
#include <brotli/decode.h>

long dash_zlib_inflate_auto(const void *src, long n, void *dst, long max);

/* stb_truetype's and Brotli's memory (Brotli is compiled with -Dmalloc=dash_fontweb_malloc...: compiler/clibs.py),
   from exec with the size in front */
void *dash_fontweb_malloc(size_t n)
{
    ULONG *p = (ULONG *)AllocVec(n + 4, MEMF_ANY);
    if (!p) return NULL;
    p[0] = (ULONG)n;
    return p + 1;
}

void dash_fontweb_free_mem(void *p)
{
    if (p) FreeVec((ULONG *)p - 1);
}

/* stb_truetype's maths on Dash's fdlibm (not -lm: libnix's goes to the ROM's math libraries) */
double dash_fd_floor(double);
double dash_fd_ceil(double);
double dash_fd_cos(double);
double dash_fd_fabs(double);
double __ieee754_sqrt(double);
double __ieee754_pow(double, double);
double __ieee754_fmod(double, double);
double __ieee754_acos(double);
#define STBTT_ifloor(x) ((int)dash_fd_floor(x))
#define STBTT_iceil(x) ((int)dash_fd_ceil(x))
#define STBTT_sqrt(x) __ieee754_sqrt(x)
#define STBTT_pow(x, y) __ieee754_pow(x, y)
#define STBTT_fmod(x, y) __ieee754_fmod(x, y)
#define STBTT_cos(x) dash_fd_cos(x)
#define STBTT_acos(x) __ieee754_acos(x)
#define STBTT_fabs(x) dash_fd_fabs(x)
#define STBTT_malloc(x, u) ((void)(u), dash_fontweb_malloc(x))
#define STBTT_free(x, u) ((void)(u), dash_fontweb_free_mem(x))
#define STBTT_assert(x)
#define STBTT_strlen(x) strlen(x)
#define STBTT_memcpy memcpy
#define STBTT_memset memset
#define STB_TRUETYPE_IMPLEMENTATION
#include "stb_truetype.h"

static char _fw_nombre[] = "dash-web.font";

/* El fichero entero en memoria (AllocVec); NULL si no se puede */
static UBYTE *_fw_leer(const char *fichero, LONG *largo) {
    BPTR fh = Open((CONST_STRPTR)fichero, MODE_OLDFILE);
    UBYTE *d = NULL;
    LONG n;
    if (!fh) return NULL;
    Seek(fh, 0, OFFSET_END);
    n = Seek(fh, 0, OFFSET_BEGINNING);
    if (n > 0 && n < 8 * 1024 * 1024 && (d = (UBYTE *)AllocVec(n, MEMF_ANY))) {
        if (Read(fh, d, n) != n) { FreeVec(d); d = NULL; }
    }
    Close(fh);
    *largo = n;
    return d;
}


static ULONG _fw_u32(const UBYTE *p) { return ((ULONG)p[0] << 24) | ((ULONG)p[1] << 16) | ((ULONG)p[2] << 8) | p[3]; }
static UWORD _fw_u16(const UBYTE *p) { return (UWORD)((p[0] << 8) | p[1]); }
static void _fw_p32(UBYTE *p, ULONG v) { p[0] = v >> 24; p[1] = v >> 16; p[2] = v >> 8; p[3] = v; }
static void _fw_p16(UBYTE *p, UWORD v) { p[0] = v >> 8; p[1] = v; }

/* WOFF 1.0 a la fuente TrueType de dentro (cada tabla, descomprimida si vino con zlib); NULL si no se puede */
static UBYTE *_fw_de_woff(const UBYTE *w, LONG largo, LONG *salida) {
    UWORD n, i, potencia = 1, exponente = 0;
    ULONG total, pos;
    UBYTE *s;
    if (largo < 44 || _fw_u32(w) != 0x774F4646) return NULL;
    n = _fw_u16(w + 12);
    total = _fw_u32(w + 16);
    if (n == 0 || n > 200 || 44 + 20L * n > largo || total < 12 + 16UL * n || total > 16 * 1024 * 1024) return NULL;
    if (!(s = (UBYTE *)AllocVec(total, MEMF_CLEAR))) return NULL;
    while (potencia * 2 <= n) { potencia *= 2; exponente++; }
    _fw_p32(s, _fw_u32(w + 4));
    _fw_p16(s + 4, n);
    _fw_p16(s + 6, potencia * 16);
    _fw_p16(s + 8, exponente);
    _fw_p16(s + 10, n * 16 - potencia * 16);
    pos = 12 + 16UL * n;
    for (i = 0; i < n; i++) {
        const UBYTE *e = w + 44 + 20 * i;
        ULONG off = _fw_u32(e + 4), comp = _fw_u32(e + 8), orig = _fw_u32(e + 12);
        if (off + comp > (ULONG)largo || pos + orig > total) { FreeVec(s); return NULL; }
        CopyMem((APTR)e, s + 12 + 16 * i, 4);
        _fw_p32(s + 12 + 16 * i + 4, _fw_u32(e + 16));
        _fw_p32(s + 12 + 16 * i + 8, pos);
        _fw_p32(s + 12 + 16 * i + 12, orig);
        if (comp < orig) {
            if (dash_zlib_inflate_auto(w + off, comp, s + pos, orig) != (long)orig) { FreeVec(s); return NULL; }
        } else {
            CopyMem((APTR)(w + off), s + pos, orig);
        }
        pos += (orig + 3) & ~3UL;
    }
    *salida = total;
    return s;
}

/* === WOFF 2.0 (tarea 37g): Brotli (third_party/brotli) y la reconstrucción de glyf/loca y hmtx transformadas === */

static const char *_fw2_tags[63] = {
    "cmap", "head", "hhea", "hmtx", "maxp", "name", "OS/2", "post", "cvt ", "fpgm", "glyf", "loca", "prep", "CFF ",
    "VORG", "EBDT", "EBLC", "gasp", "hdmx", "kern", "LTSH", "PCLT", "VDMX", "vhea", "vmtx", "BASE", "GDEF", "GPOS",
    "GSUB", "EBSC", "JSTF", "MATH", "CBDT", "CBLC", "COLR", "CPAL", "SVG ", "sbix", "acnt", "avar", "bdat", "bloc",
    "bsln", "cvar", "fdsc", "feat", "fmtx", "fvar", "gvar", "hsty", "just", "lcar", "mort", "morx", "opbd", "prop",
    "trak", "Zapf", "Silf", "Glat", "Gloc", "Feat", "Sill"};

#define _FW2_GLYF 0x676C7966UL
#define _FW2_LOCA 0x6C6F6361UL
#define _FW2_HMTX 0x686D7478UL
#define _FW2_HEAD 0x68656164UL
#define _FW2_HHEA 0x68686561UL
#define _FW2_MAXP 0x6D617870UL

/* Un lector con límite: ok a 0 en cuanto se pasa */
typedef struct { const UBYTE *p; ULONG n, i; int ok; } _Fw2L;
static ULONG _fw2_u8(_Fw2L *l) { if (l->i + 1 > l->n) { l->ok = 0; return 0; } return l->p[l->i++]; }
static ULONG _fw2_u16(_Fw2L *l) { ULONG v; if (l->i + 2 > l->n) { l->ok = 0; return 0; } v = _fw_u16(l->p + l->i); l->i += 2; return v; }
static ULONG _fw2_u32(_Fw2L *l) { ULONG v; if (l->i + 4 > l->n) { l->ok = 0; return 0; } v = _fw_u32(l->p + l->i); l->i += 4; return v; }
static LONG _fw2_s16(_Fw2L *l) { return (WORD)_fw2_u16(l); }
static ULONG _fw2_base128(_Fw2L *l) {
    ULONG v = 0, b; int k;
    for (k = 0; k < 5; k++) {
        b = _fw2_u8(l);
        if (k == 0 && b == 0x80) { l->ok = 0; return 0; }
        if (v & 0xFE000000UL) { l->ok = 0; return 0; }
        v = (v << 7) | (b & 0x7F);
        if (!(b & 0x80)) return v;
    }
    l->ok = 0;
    return 0;
}
static ULONG _fw2_255(_Fw2L *l) {
    ULONG c = _fw2_u8(l);
    if (c == 253) return _fw2_u16(l);
    if (c == 255) return _fw2_u8(l) + 253;
    if (c == 254) return _fw2_u8(l) + 506;
    return c;
}
static const UBYTE *_fw2_bytes(_Fw2L *l, ULONG n) { const UBYTE *r; if (l->i + n > l->n) { l->ok = 0; return NULL; } r = l->p + l->i; l->i += n; return r; }

/* Un búfer que crece */
typedef struct { UBYTE *p; ULONG n, cap; int ok; } _Fw2B;
static void _fw2_cabe(_Fw2B *b, ULONG mas) {
    UBYTE *q; ULONG c;
    if (!b->ok || b->n + mas <= b->cap) return;
    c = b->cap ? b->cap * 2 : 4096;
    while (c < b->n + mas) c *= 2;
    if (!(q = (UBYTE *)AllocVec(c, MEMF_ANY))) { b->ok = 0; return; }
    if (b->p) { CopyMem(b->p, q, b->n); FreeVec(b->p); }
    b->p = q; b->cap = c;
}
static void _fw2_w8(_Fw2B *b, ULONG v) { _fw2_cabe(b, 1); if (b->ok) b->p[b->n++] = (UBYTE)v; }
static void _fw2_w16(_Fw2B *b, ULONG v) { _fw2_cabe(b, 2); if (b->ok) { _fw_p16(b->p + b->n, (UWORD)v); b->n += 2; } }
static void _fw2_wb(_Fw2B *b, const UBYTE *d, ULONG n) { _fw2_cabe(b, n); if (b->ok && n) { CopyMem((APTR)d, b->p + b->n, n); b->n += n; } }

/* El desplazamiento de un punto de la tabla de tripletes de la especificación (5.2) */
static LONG _fw2_signo(ULONG f, LONG v) { return (f & 1) ? v : -v; }
static int _fw2_triplete(_Fw2L *g, ULONG f, LONG *dx, LONG *dy) {
    ULONG a, b, c, d;
    if (f < 10) { a = _fw2_u8(g); *dx = 0; *dy = _fw2_signo(f, ((f & 14) << 7) + a); }
    else if (f < 20) { a = _fw2_u8(g); *dx = _fw2_signo(f, (((f - 10) & 14) << 7) + a); *dy = 0; }
    else if (f < 84) { ULONG b0 = f - 20; a = _fw2_u8(g); *dx = _fw2_signo(f, 1 + (b0 & 0x30) + (a >> 4)); *dy = _fw2_signo(f >> 1, 1 + ((b0 & 0x0c) << 2) + (a & 0x0f)); }
    else if (f < 120) { ULONG b0 = f - 84; a = _fw2_u8(g); b = _fw2_u8(g); *dx = _fw2_signo(f, 1 + ((b0 / 12) << 8) + a); *dy = _fw2_signo(f >> 1, 1 + (((b0 % 12) >> 2) << 8) + b); }
    else if (f < 124) { a = _fw2_u8(g); b = _fw2_u8(g); c = _fw2_u8(g); *dx = _fw2_signo(f, (a << 4) + (b >> 4)); *dy = _fw2_signo(f >> 1, ((b & 0x0f) << 8) + c); }
    else { a = _fw2_u8(g); b = _fw2_u8(g); c = _fw2_u8(g); d = _fw2_u8(g); *dx = _fw2_signo(f, (a << 8) + b); *dy = _fw2_signo(f >> 1, (c << 8) + d); }
    return g->ok;
}

/* glyf transformada -> glyf y loca de TrueType (5.1 y 5.3); 0 si no se puede */
static int _fw2_glyf(const UBYTE *t, ULONG n, _Fw2B *glyf, _Fw2B *loca, ULONG *formato_loca, ULONG *num_glifos, WORD **xmins) {
    _Fw2L h = {t, n, 0, 1}, nc, np, fl, gs, cs, bb, is;
    ULONG opciones, glifos, formato, tam[7], pos, i, k, bitmap_len;
    const UBYTE *bitmap;
    LONG *pts = NULL; ULONG cap_pts = 0;
    _fw2_u16(&h); opciones = _fw2_u16(&h); glifos = _fw2_u16(&h); formato = _fw2_u16(&h);
    for (k = 0; k < 7; k++) tam[k] = _fw2_u32(&h);
    if (!h.ok || glifos == 0) return 0;
    pos = h.i;
    for (k = 0; k < 7; k++) if (pos + tam[k] > n || pos + tam[k] < pos) return 0; else pos += tam[k];
    pos = h.i;
    nc.p = t + pos; nc.n = tam[0]; nc.i = 0; nc.ok = 1; pos += tam[0];
    np.p = t + pos; np.n = tam[1]; np.i = 0; np.ok = 1; pos += tam[1];
    fl.p = t + pos; fl.n = tam[2]; fl.i = 0; fl.ok = 1; pos += tam[2];
    gs.p = t + pos; gs.n = tam[3]; gs.i = 0; gs.ok = 1; pos += tam[3];
    cs.p = t + pos; cs.n = tam[4]; cs.i = 0; cs.ok = 1; pos += tam[4];
    bb.p = t + pos; bb.n = tam[5]; bb.i = 0; bb.ok = 1; pos += tam[5];
    is.p = t + pos; is.n = tam[6]; is.i = 0; is.ok = 1;
    (void)opciones;
    bitmap_len = ((glifos + 31) >> 5) << 2;
    bitmap = _fw2_bytes(&bb, bitmap_len);
    if (!bitmap) return 0;
    if (!(*xmins = (WORD *)AllocVec(glifos * sizeof(WORD), MEMF_CLEAR))) return 0;
    for (i = 0; i < glifos; i++) {
        LONG ncont = _fw2_s16(&nc);
        int con_caja = (bitmap[i >> 3] >> (7 - (i & 7))) & 1;
        ULONG inicio = glyf->n;
        if (formato) { _fw2_w16(loca, inicio >> 16); _fw2_w16(loca, inicio & 0xFFFF); } else _fw2_w16(loca, inicio >> 1);
        if (ncont == 0) {
            /* vacío */
        } else if (ncont > 0) {
            ULONG total = 0, j; LONG x = 0, y = 0, xmin = 0x7FFF, ymin = 0x7FFF, xmax = -0x8000, ymax = -0x8000, ilen;
            ULONG ends_pos;
            const UBYTE *ins;
            _fw2_w16(glyf, (ULONG)ncont);
            ends_pos = glyf->n;
            _fw2_w16(glyf, 0); _fw2_w16(glyf, 0); _fw2_w16(glyf, 0); _fw2_w16(glyf, 0);   /* la caja, luego */
            for (j = 0; j < (ULONG)ncont; j++) { total += _fw2_255(&np); _fw2_w16(glyf, total - 1); }
            if (total > cap_pts) {
                if (pts) FreeVec(pts);
                cap_pts = total + 64;
                if (!(pts = (LONG *)AllocVec(cap_pts * 3 * sizeof(LONG), MEMF_ANY))) { cap_pts = 0; glyf->ok = 0; break; }
            }
            for (j = 0; j < total; j++) {
                ULONG f = _fw2_u8(&fl); LONG dx, dy;
                if (!_fw2_triplete(&gs, f & 0x7F, &dx, &dy)) break;
                x += dx; y += dy;
                if (x < xmin) xmin = x; if (x > xmax) xmax = x; if (y < ymin) ymin = y; if (y > ymax) ymax = y;
                pts[j * 3] = (f & 0x80) ? 0 : 1; pts[j * 3 + 1] = dx; pts[j * 3 + 2] = dy;
            }
            ilen = _fw2_255(&gs);
            ins = _fw2_bytes(&is, ilen);
            if (!fl.ok || !gs.ok || !is.ok || !np.ok) { glyf->ok = 0; break; }
            _fw2_w16(glyf, ilen); _fw2_wb(glyf, ins, ilen);
            for (j = 0; j < total; j++) _fw2_w8(glyf, pts[j * 3]);        /* en la curva o no; x e y de 2 bytes */
            for (j = 0; j < total; j++) _fw2_w16(glyf, (ULONG)(pts[j * 3 + 1] & 0xFFFF));
            for (j = 0; j < total; j++) _fw2_w16(glyf, (ULONG)(pts[j * 3 + 2] & 0xFFFF));
            if (con_caja) { xmin = _fw2_s16(&bb); ymin = _fw2_s16(&bb); xmax = _fw2_s16(&bb); ymax = _fw2_s16(&bb); }
            else if (total == 0) xmin = ymin = xmax = ymax = 0;
            if (glyf->ok) {
                _fw_p16(glyf->p + ends_pos, (UWORD)xmin); _fw_p16(glyf->p + ends_pos + 2, (UWORD)ymin);
                _fw_p16(glyf->p + ends_pos + 4, (UWORD)xmax); _fw_p16(glyf->p + ends_pos + 6, (UWORD)ymax);
            }
            (*xmins)[i] = (WORD)xmin;
        } else {
            /* compuesto: su caja siempre explícita; los componentes tal cual; instrucciones si las lleva */
            ULONG flags, desde, con_ins = 0; LONG xmin;
            _fw2_w16(glyf, 0xFFFF);
            xmin = _fw2_s16(&bb);
            _fw2_w16(glyf, (ULONG)xmin & 0xFFFF);
            _fw2_w16(glyf, (ULONG)_fw2_s16(&bb) & 0xFFFF); _fw2_w16(glyf, (ULONG)_fw2_s16(&bb) & 0xFFFF); _fw2_w16(glyf, (ULONG)_fw2_s16(&bb) & 0xFFFF);
            (*xmins)[i] = (WORD)xmin;
            do {
                ULONG extra;
                desde = cs.i;
                flags = _fw2_u16(&cs);
                _fw2_u16(&cs);
                extra = (flags & 0x0001) ? 4 : 2;
                if (flags & 0x0008) extra += 2; else if (flags & 0x0040) extra += 4; else if (flags & 0x0080) extra += 8;
                if (!_fw2_bytes(&cs, extra)) break;
                if (flags & 0x0100) con_ins = 1;
                _fw2_wb(glyf, cs.p + desde, cs.i - desde);
            } while (cs.ok && (flags & 0x0020));
            if (con_ins) {
                ULONG ilen = _fw2_255(&gs);
                const UBYTE *ins = _fw2_bytes(&is, ilen);
                _fw2_w16(glyf, ilen); _fw2_wb(glyf, ins, ilen);
            }
            if (!cs.ok || !bb.ok || !gs.ok || !is.ok) { glyf->ok = 0; break; }
        }
        while (glyf->n & 3) _fw2_w8(glyf, 0);
        if (!nc.ok || !glyf->ok || !loca->ok) break;
    }
    if (pts) FreeVec(pts);
    if (formato) { _fw2_w16(loca, glyf->n >> 16); _fw2_w16(loca, glyf->n & 0xFFFF); } else _fw2_w16(loca, glyf->n >> 1);
    *formato_loca = formato;
    *num_glifos = glifos;
    return nc.ok && glyf->ok && loca->ok && i == glifos;
}

/* hmtx transformada (5.4) -> hmtx: los lsb que faltan son el xMin de cada glifo */
static int _fw2_hmtx(const UBYTE *t, ULONG n, ULONG num_h, ULONG glifos, const WORD *xmins, _Fw2B *out) {
    _Fw2L l = {t, n, 0, 1};
    ULONG flags = _fw2_u8(&l), i;
    const UBYTE *aw = _fw2_bytes(&l, num_h * 2), *lsb = NULL, *lsb2 = NULL;
    if (!(flags & 1)) lsb = _fw2_bytes(&l, num_h * 2);
    if (!(flags & 2)) lsb2 = _fw2_bytes(&l, (glifos - num_h) * 2);
    if (!l.ok || num_h > glifos || !xmins) return 0;
    for (i = 0; i < num_h; i++) { _fw2_wb(out, aw + i * 2, 2); if (lsb) _fw2_wb(out, lsb + i * 2, 2); else _fw2_w16(out, (UWORD)xmins[i]); }
    for (i = num_h; i < glifos; i++) { if (lsb2) _fw2_wb(out, lsb2 + (i - num_h) * 2, 2); else _fw2_w16(out, (UWORD)xmins[i]); }
    return out->ok;
}

/* WOFF 2.0 a TrueType; NULL si no se puede (colecciones, CFF transformado...) */
static UBYTE *_fw_de_woff2(const UBYTE *w, LONG largo, LONG *salida) {
    _Fw2L h = {w, (ULONG)largo, 0, 1};
    ULONG flavor, ntab, comp_size, i, total = 0, pos, glifos = 0, formato_loca = 0, num_h = 0, potencia = 1, exponente = 0;
    ULONG tags[64], orig[64], trans[64], ver[64], off[64], fin[64];
    size_t dec_size;
    UBYTE *dec = NULL, *s = NULL;
    _Fw2B glyf = {NULL, 0, 0, 1}, loca = {NULL, 0, 0, 1}, hmtx = {NULL, 0, 0, 1};
    WORD *xmins = NULL;
    int i_glyf = -1, i_loca = -1, i_hmtx = -1, i_hhea = -1, i_head = -1;
    if (_fw2_u32(&h) != 0x774F4632) return NULL;
    flavor = _fw2_u32(&h);
    _fw2_u32(&h);
    ntab = _fw2_u16(&h);
    _fw2_u16(&h); _fw2_u32(&h);
    comp_size = _fw2_u32(&h);
    h.i = 48;
    if (!h.ok || ntab == 0 || ntab > 64 || flavor == 0x74746366) return NULL;
    for (i = 0; i < ntab; i++) {
        ULONG f = _fw2_u8(&h), idx = f & 63;
        if (idx == 63) tags[i] = _fw2_u32(&h);
        else tags[i] = _fw_u32((const UBYTE *)_fw2_tags[idx]);
        ver[i] = (f >> 6) & 3;
        orig[i] = _fw2_base128(&h);
        trans[i] = orig[i];
        if (((tags[i] == _FW2_GLYF || tags[i] == _FW2_LOCA) && ver[i] == 0) || (tags[i] == _FW2_HMTX && ver[i] == 1)) trans[i] = _fw2_base128(&h);
        else if ((tags[i] == _FW2_GLYF || tags[i] == _FW2_LOCA) ? ver[i] != 3 : ver[i] != 0) return NULL;   /* transformación que no conoce */
        off[i] = total;
        total += trans[i];
        if (tags[i] == _FW2_GLYF) i_glyf = i;
        if (tags[i] == _FW2_LOCA) i_loca = i;
        if (tags[i] == _FW2_HMTX) i_hmtx = i;
        if (tags[i] == _FW2_HHEA) i_hhea = i;
        if (tags[i] == _FW2_HEAD) i_head = i;
    }
    if (!h.ok || total == 0 || total > 16 * 1024 * 1024 || h.i + comp_size > (ULONG)largo) return NULL;
    if (!(dec = (UBYTE *)AllocVec(total, MEMF_ANY))) return NULL;
    dec_size = total;
    if (BrotliDecoderDecompress(comp_size, w + h.i, &dec_size, dec) != BROTLI_DECODER_RESULT_SUCCESS || dec_size != total) { FreeVec(dec); return NULL; }
    /* glyf/loca transformadas: se rehacen */
    if (i_glyf >= 0 && ver[i_glyf] == 0) {
        if (i_loca < 0 || !_fw2_glyf(dec + off[i_glyf], trans[i_glyf], &glyf, &loca, &formato_loca, &glifos, &xmins)) goto mal;
    }
    if (i_hmtx >= 0 && ver[i_hmtx] == 1) {
        if (i_hhea < 0 || trans[i_hhea] < 36 || !xmins) goto mal;
        num_h = _fw_u16(dec + off[i_hhea] + 34);
        if (!_fw2_hmtx(dec + off[i_hmtx], trans[i_hmtx], num_h, glifos, xmins, &hmtx)) goto mal;
    }
    /* el tamaño de cada tabla en la fuente de salida */
    for (i = 0; i < ntab; i++) {
        fin[i] = trans[i];
        if ((int)i == i_glyf && glyf.p) fin[i] = glyf.n;
        else if ((int)i == i_loca && loca.p) fin[i] = loca.n;
        else if ((int)i == i_hmtx && hmtx.p) fin[i] = hmtx.n;
    }
    pos = 12 + 16 * ntab;
    for (i = 0; i < ntab; i++) pos += (fin[i] + 3) & ~3UL;
    if (!(s = (UBYTE *)AllocVec(pos, MEMF_CLEAR))) goto mal;
    *salida = pos;
    while (potencia * 2 <= ntab) { potencia *= 2; exponente++; }
    _fw_p32(s, flavor);
    _fw_p16(s + 4, ntab);
    _fw_p16(s + 6, potencia * 16);
    _fw_p16(s + 8, exponente);
    _fw_p16(s + 10, ntab * 16 - potencia * 16);
    pos = 12 + 16 * ntab;
    {
        /* el directorio, por etiqueta (como pide TrueType) */
        ULONG orden[64], j, k;
        for (i = 0; i < ntab; i++) orden[i] = i;
        for (i = 1; i < ntab; i++) for (j = i; j > 0 && tags[orden[j - 1]] > tags[orden[j]]; j--) { k = orden[j]; orden[j] = orden[j - 1]; orden[j - 1] = k; }
        for (j = 0; j < ntab; j++) {
            const UBYTE *src;
            i = orden[j];
            src = dec + off[i];
            if ((int)i == i_glyf && glyf.p) src = glyf.p;
            else if ((int)i == i_loca && loca.p) src = loca.p;
            else if ((int)i == i_hmtx && hmtx.p) src = hmtx.p;
            _fw_p32(s + 12 + 16 * j, tags[i]);
            _fw_p32(s + 12 + 16 * j + 8, pos);
            _fw_p32(s + 12 + 16 * j + 12, fin[i]);
            CopyMem((APTR)src, s + pos, fin[i]);
            if ((int)i == i_head && loca.p && fin[i] >= 54) _fw_p16(s + pos + 50, (UWORD)formato_loca);
            pos += (fin[i] + 3) & ~3UL;
        }
    }
    FreeVec(dec);
    if (glyf.p) FreeVec(glyf.p);
    if (loca.p) FreeVec(loca.p);
    if (hmtx.p) FreeVec(hmtx.p);
    if (xmins) FreeVec(xmins);
    return s;
mal:
    FreeVec(dec);
    if (glyf.p) FreeVec(glyf.p);
    if (loca.p) FreeVec(loca.p);
    if (hmtx.p) FreeVec(hmtx.p);
    if (xmins) FreeVec(xmins);
    return NULL;
}

/* The last fonts read, already TrueType: (file, data) */
#define _FW_GUARDADAS 8
static struct { char nombre[108]; UBYTE *datos; LONG largo; } _fw_guardadas[_FW_GUARDADAS];
static LONG _fw_siguiente = 0;

#define _FW_LO 32
#define _FW_HI 255
static LONG _fw_icono = 0;     /* font_ttf_icon: el carácter que va en la "A" (un icono de la web), mientras se hace */
#define _FW_N (_FW_HI - _FW_LO + 2)      /* y uno más: el que sale con los que no tiene */

/* Si el píxel (x, y) del glifo en grises va con tinta en el plano de 1 bit: con gris de 112 o más, o si es el más
   oscuro de una pareja (con el de al lado o el de arriba o abajo) que entre los dos pasa de 150 sin que ninguno llegue
   a 112. Un trazo fino (Lato 300 a 15 px) que cae entre dos píxeles al 50 % se quedaba sin ninguno: "_os" por "Los" */
static int _fw_tinta(const UBYTE *g, int w, int h, int x, int y) {
    int v = g[y * w + x], l, r, u, d;
    if (v >= 112) return 1;
    if (v < 40) return 0;
    l = x > 0 ? g[y * w + x - 1] : 0;
    r = x < w - 1 ? g[y * w + x + 1] : 0;
    u = y > 0 ? g[(y - 1) * w + x] : 0;
    d = y < h - 1 ? g[(y + 1) * w + x] : 0;
    /* en una pareja empatada se queda el de la izquierda (o el de arriba) */
    return (r < 112 && v + r >= 150 && v >= r) || (l < 112 && v + l >= 150 && v > l) ||
           (d < 112 && v + d >= 150 && v >= d) || (u < 112 && v + u >= 150 && v > u);
}

/* Un TextFont (y sus tablas y su plano, en un solo AllocVec) con los glifos de datos a tam px de em */
static struct TextFont *_fw_crear(UBYTE *datos, LONG largo, LONG tam, LONG ancho) {
    stbtt_fontinfo fi;
    float esc, escx;
    int asc, desc, gap, c, i, base, alto, total = 0, x0, y0, x1, y1, adv, lsb;
    int ws[_FW_N], xs[_FW_N], ads[_FW_N], gl[_FW_N], igual[_FW_N], j;
    LONG modulo, tam_bloque;
    UBYTE *bloque, *plano, *gris;
    struct TextFont *tf;
    ULONG *loc;
    WORD *esp, *ker;
    if (tam < 4 || tam > 200) return NULL;
    if (!stbtt_InitFont(&fi, datos, stbtt_GetFontOffsetForIndex(datos, 0))) return NULL;
    esc = stbtt_ScaleForMappingEmToPixels(&fi, (float)tam);
    /* font-stretch (ancho en %): las letras más anchas o estrechas, como el eje wdth de una fuente variable */
    escx = ancho > 0 ? esc * (float)ancho / 100.0f : esc;
    stbtt_GetFontVMetrics(&fi, &asc, &desc, &gap);
    base = (int)(asc * esc + 0.999f);
    alto = base + (int)(-desc * esc + 0.999f);
    if (alto < 1) return NULL;
    for (i = 0; i < _FW_N; i++) {
        c = i < _FW_N - 1 ? _FW_LO + i : '?';
        if (_fw_icono && c != 'A') {
            /* (una fuente para un icono: solo su "A"; las demás letras, vacías) */
            gl[i] = 0; ads[i] = 0; ws[i] = 0; xs[i] = 0;
            continue;
        }
        gl[i] = stbtt_FindGlyphIndex(&fi, _fw_icono ? _fw_icono : c);
        stbtt_GetGlyphHMetrics(&fi, gl[i], &adv, &lsb);
        ads[i] = (int)(adv * escx + 0.5f);
        stbtt_GetGlyphBitmapBox(&fi, gl[i], escx, esc, &x0, &y0, &x1, &y1);
        if (x1 < x0 || c == ' ') x1 = x0;
        ws[i] = x1 - x0;
        xs[i] = x0;
        /* (Dash: un glifo que ya está, el de otro carácter, no se dibuja otra vez: comparten su trozo del plano;
           los que la fuente no tiene son todos el .notdef, y dibujar cada glifo cuesta sin FPU) */
        igual[i] = -1;
        for (j = 0; j < i && igual[i] < 0; j++)
            if (gl[j] == gl[i] && ws[j] == ws[i] && igual[j] < 0) igual[i] = j;
        if (igual[i] < 0) total += ws[i];
    }
    modulo = ((total + 15) / 16) * 2;
    if (modulo < 2) modulo = 2;
    tam_bloque = sizeof(struct TextFont) + _FW_N * (sizeof(ULONG) + 2 * sizeof(WORD)) + modulo * alto;
    bloque = (UBYTE *)AllocVec(tam_bloque, MEMF_CLEAR);
    if (!bloque) return NULL;
    tf = (struct TextFont *)bloque;
    loc = (ULONG *)(bloque + sizeof(struct TextFont));
    esp = (WORD *)(loc + _FW_N);
    ker = esp + _FW_N;
    plano = (UBYTE *)(ker + _FW_N);
    total = 0;
    for (i = 0; i < _FW_N; i++) {
        int w = ws[i], gx0, gy0, gx1, gy1, gh, yy, xx;
        ker[i] = (WORD)xs[i];
        esp[i] = (WORD)(ads[i] - xs[i]);
        if (igual[i] >= 0) {
            loc[i] = loc[igual[i]];
            continue;
        }
        loc[i] = ((ULONG)total << 16) | (ULONG)w;
        if (w > 0) {
            stbtt_GetGlyphBitmapBox(&fi, gl[i], escx, esc, &gx0, &gy0, &gx1, &gy1);
            gh = gy1 - gy0;
            if (gh > 0 && (gris = (UBYTE *)AllocVec(w * gh, MEMF_CLEAR))) {
                stbtt_MakeGlyphBitmap(&fi, gris, w, gh, w, escx, esc, gl[i]);
                for (yy = 0; yy < gh; yy++) {
                    int fila = base + gy0 + yy;
                    if (fila < 0 || fila >= alto) continue;
                    for (xx = 0; xx < w; xx++)
                        if (_fw_tinta(gris, w, gh, xx, yy)) {
                            int bit = total + xx;
                            plano[fila * modulo + (bit >> 3)] |= 0x80 >> (bit & 7);
                        }
                }
                FreeVec(gris);
            }
        }
        total += w;
    }
    tf->tf_Message.mn_Node.ln_Name = _fw_nombre;
    tf->tf_Message.mn_Node.ln_Type = NT_FONT;
    tf->tf_YSize = alto;
    tf->tf_Style = 0;
    tf->tf_Flags = FPF_PROPORTIONAL | FPF_DESIGNED;
    tf->tf_XSize = ads['n' - _FW_LO] > 0 ? ads['n' - _FW_LO] : tam / 2;
    tf->tf_Baseline = base > 0 ? base - 1 : 0;
    /* la negrita del Amiga (FSF_BOLD) corre el trazo estos px: crece con el tamaño (un titular de 64 px en negrita
       con 1 px apenas se nota; las fuentes variables solo dan su instancia por defecto, la fina; tarea 37g) */
    tf->tf_BoldSmear = tam >= 18 ? tam / 18 : 1;
    tf->tf_LoChar = _FW_LO;
    tf->tf_HiChar = _FW_HI;
    tf->tf_CharData = plano;
    tf->tf_Modulo = modulo;
    tf->tf_CharLoc = loc;
    tf->tf_CharSpace = esp;
    tf->tf_CharKern = ker;
    return tf;
}

/* The fonts made (to free what is left at the end) */
#define _FW_HECHAS 64
static struct TextFont *_fw_hechas[_FW_HECHAS];

/* The TrueType data of the file (read, and taken out of its WOFF or WOFF2, once): NULL if it is not a font */
static UBYTE *_fw_datos(const char *fichero, LONG *largo)
{
    LONG i, n = 0, m = 0;
    UBYTE *d, *t;
    for (i = 0; i < _FW_GUARDADAS; i++)
        if (_fw_guardadas[i].datos && !strcmp(_fw_guardadas[i].nombre, fichero)) {
            *largo = _fw_guardadas[i].largo;
            return _fw_guardadas[i].datos;
        }
    if (strlen(fichero) >= sizeof(_fw_guardadas[0].nombre) || !(d = _fw_leer(fichero, &n))) return NULL;
    t = d;
    m = n;
    if (n >= 4 && _fw_u32(d) == 0x774F4646) {             /* wOFF */
        t = _fw_de_woff(d, n, &m);
        FreeVec(d);
    } else if (n >= 4 && _fw_u32(d) == 0x774F4632) {      /* wOF2 */
        t = _fw_de_woff2(d, n, &m);
        FreeVec(d);
    }
    if (!t) return NULL;
    i = _fw_siguiente;
    _fw_siguiente = (_fw_siguiente + 1) % _FW_GUARDADAS;
    if (_fw_guardadas[i].datos) FreeVec(_fw_guardadas[i].datos);
    strcpy(_fw_guardadas[i].nombre, fichero);
    _fw_guardadas[i].datos = t;
    _fw_guardadas[i].largo = m;
    *largo = m;
    return t;
}

/* font_from_ttf: the TextFont of the file at size px of em and width % of its width (0: 100); NULL if it cannot */
void *dash_fontweb_open(const char *file, long size, long width)
{
    LONG largo = 0, i;
    UBYTE *d;
    struct TextFont *tf;
    if (!file || !(d = _fw_datos(file, &largo))) return NULL;
    if (!(tf = _fw_crear(d, largo, size, width > 0 ? width : 100))) return NULL;
    for (i = 0; i < _FW_HECHAS && _fw_hechas[i]; i++) ;
    if (i < _FW_HECHAS) _fw_hechas[i] = tf;
    return tf;
}

/* font_ttf_icon: a font of the file whose "A" is the character code (an icon of a web font, in Unicode's private
   area), the other letters empty; NULL if it cannot */
void *dash_fontweb_icon(const char *file, long size, long code)
{
    void *f;
    if (code <= 0) return NULL;
    _fw_icono = code;
    f = dash_fontweb_open(file, size, 100);
    _fw_icono = 0;
    return f;
}

/* font_ttf_free (never CloseFont: the font is one AllocVec) */
void dash_fontweb_free(void *f)
{
    LONG i;
    if (!f) return;
    for (i = 0; i < _FW_HECHAS; i++)
        if (_fw_hechas[i] == f) _fw_hechas[i] = NULL;
    FreeVec(f);
}

/* font_ttf_forget: the file's data, read again next time (it may have changed) */
void dash_fontweb_forget(const char *file)
{
    LONG i;
    for (i = 0; i < _FW_GUARDADAS; i++)
        if (_fw_guardadas[i].datos && file && !strcmp(_fw_guardadas[i].nombre, file)) {
            FreeVec(_fw_guardadas[i].datos);
            _fw_guardadas[i].datos = NULL;
        }
}

/* At the end: the fonts and data left */
void dash_fontweb_cleanup(void)
{
    LONG i;
    for (i = 0; i < _FW_HECHAS; i++)
        if (_fw_hechas[i]) {
            FreeVec(_fw_hechas[i]);
            _fw_hechas[i] = NULL;
        }
    for (i = 0; i < _FW_GUARDADAS; i++)
        if (_fw_guardadas[i].datos) {
            FreeVec(_fw_guardadas[i].datos);
            _fw_guardadas[i].datos = NULL;
        }
}
