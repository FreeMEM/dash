/* Dash's image_decode (Dash 2.0, what Tachyon did with @native in lib/imagen_dec.dash): a file decoded to RGB
   or RGBA pixels, made smaller until it is not much bigger than maxw x maxh (the aspect ratio kept). Baseline
   JPEG with TJpgDec, already reduced (1/2, 1/4, 1/8) while it decodes; WebP with libwebp, also scaled while it
   decodes; SVG drawn by nanosvg; PNG, GIF, BMP and progressive JPEG with stb_image, reduced after. All memory
   from exec: it may run in another process (task_start). */
#include <exec/memory.h>
#include <dos/dos.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <string.h>
#include "tjpgd.h"
#include "src/webp/decode.h"

/* nanosvg's declarations (its code is in nanosvg_dash.c) */
#include "nanosvg.h"
#include "nanosvgrast.h"

/* libwebp's malloc, calloc and free (compiled with -Dmalloc=dash_imgdec_malloc...: compiler/clibs.py): from
   exec, with the size in front, so that it may run in another process */
void *dash_imgdec_malloc(size_t n)
{
    ULONG *p = (ULONG *)AllocVec(n + 4, MEMF_ANY);
    if (!p) return NULL;
    p[0] = (ULONG)n;
    return p + 1;
}

void *dash_imgdec_calloc(size_t n, size_t size)
{
    ULONG *p = (ULONG *)AllocVec(n * size + 4, MEMF_CLEAR);
    if (!p) return NULL;
    p[0] = (ULONG)(n * size);
    return p + 1;
}

void dash_imgdec_free_mem(void *p)
{
    if (p) FreeVec((ULONG *)p - 1);
}

void *dash_imgdec_realloc(void *p, size_t n)
{
    void *q;
    size_t old;
    if (!p) return dash_imgdec_malloc(n);
    if (!n) {
        dash_imgdec_free_mem(p);
        return NULL;
    }
    old = ((ULONG *)p)[-1];
    if (!(q = dash_imgdec_malloc(n))) return NULL;
    CopyMem(p, q, old < n ? old : n);
    dash_imgdec_free_mem(p);
    return q;
}

typedef struct {
    long w, h, alpha;     /* alpha: 4 bytes per pixel (RGBA), else 3 (RGB) */
    unsigned char *px;
} DashImgDec;

extern unsigned char *stbi_load_from_memory(const unsigned char *buffer, int len, int *x, int *y, int *comp,
                                            int req_comp);
extern int stbi_info_from_memory(const unsigned char *buffer, int len, int *x, int *y, int *comp);
extern void stbi_image_free(void *p);

/* Set by Dash's cleanup at the end of the program (_dash_imgdec_stop, before it waits for its tasks): a decode still
   running in a process of image_decode_start stops soon (the long loops of TJpgDec, stb_image and libwebp look at
   it) and gives NULL; a 1280 x 1024 JPEG takes seconds on a 68040 and minutes on a 68020 (Tachyon after an abort) */
volatile long dash_imgdec_stopped = 0;

/* The whole file in memory; NULL if it cannot be read */
static UBYTE *dash_imgdec_file(const char *name, LONG *len)
{
    BPTR f = Open((CONST_STRPTR)name, MODE_OLDFILE);
    UBYTE *d = NULL;
    LONG n;
    if (!f) return NULL;
    Seek(f, 0, OFFSET_END);
    n = Seek(f, 0, OFFSET_BEGINNING);
    if (n > 0 && n < 64 * 1024 * 1024 && (d = (UBYTE *)AllocVec(n, MEMF_ANY))) {
        if (Read(f, d, n) != n) {
            FreeVec(d);
            d = NULL;
        }
    }
    Close(f);
    *len = n;
    return d;
}

static DashImgDec *dash_imgdec_new(long w, long h, long alpha)
{
    DashImgDec *img = (DashImgDec *)AllocVec(sizeof(DashImgDec), MEMF_CLEAR);
    if (!img) return NULL;
    img->w = w;
    img->h = h;
    img->alpha = alpha;
    if (!(img->px = (unsigned char *)AllocVec(w * h * (alpha ? 4 : 3), MEMF_CLEAR))) {
        FreeVec(img);
        return NULL;
    }
    return img;
}

void dash_imgdec_free(void *d)
{
    DashImgDec *img = (DashImgDec *)d;
    if (!img) return;
    if (img->px) FreeVec(img->px);
    FreeVec(img);
}

/* TJpgDec reads from memory and writes the decoded blocks into the picture */
typedef struct {
    UBYTE *data;
    LONG len, pos;
    DashImgDec *img;
} DashJpeg;

static size_t dash_jpeg_in(JDEC *jd, uint8_t *buf, size_t n)
{
    DashJpeg *j = (DashJpeg *)jd->device;
    if (n > (size_t)(j->len - j->pos)) n = j->len - j->pos;
    if (buf) memcpy(buf, j->data + j->pos, n);
    j->pos += n;
    return n;
}

static int dash_jpeg_out(JDEC *jd, void *bitmap, JRECT *r)
{
    DashJpeg *j = (DashJpeg *)jd->device;
    DashImgDec *img = j->img;
    UBYTE *src = (UBYTE *)bitmap;
    LONG width = r->right - r->left + 1, y, x0 = r->left, x1 = r->right;
    if (x1 >= img->w) x1 = img->w - 1;
    for (y = r->top; y <= r->bottom; y++, src += width * 3)
        if (y < img->h && x0 <= x1) memcpy(img->px + (y * img->w + x0) * 3, src, (x1 - x0 + 1) * 3);
    return !dash_imgdec_stopped;   /* (0: TJpgDec stops, JDR_INTR) */
}

/* A baseline JPEG reduced by 2^s; NULL if TJpgDec cannot (progressive JPEG...) */
static DashImgDec *dash_imgdec_jpeg(UBYTE *data, LONG len, LONG maxw, LONG maxh)
{
    JDEC jd;
    DashJpeg j;
    void *work = AllocVec(32768, MEMF_ANY);
    DashImgDec *img = NULL;
    int s = 0;
    if (!work) return NULL;
    j.data = data;
    j.len = len;
    j.pos = 0;
    if (jd_prepare(&jd, dash_jpeg_in, work, 32768, &j) == JDR_OK) {
        while (s < 3 && (jd.width >> (s + 1)) >= maxw && (jd.height >> (s + 1)) >= maxh) s++;
        img = dash_imgdec_new((jd.width + (1 << s) - 1) >> s, (jd.height + (1 << s) - 1) >> s, 0);
        j.img = img;
        if (img && jd_decomp(&jd, dash_jpeg_out, s) != JDR_OK) {
            dash_imgdec_free(img);
            img = NULL;
        }
    }
    FreeVec(work);
    return img;
}

/* Smaller by k in each direction (the average of each k x k square) */
static void dash_imgdec_reduce(DashImgDec *img, LONG k)
{
    LONG c = img->alpha ? 4 : 3, w = img->w / k, h = img->h / k, x, y, i, j, n, sum[4];
    UBYTE *px, *d;
    if (k < 2 || w < 1 || h < 1) return;
    if (!(px = (UBYTE *)AllocVec(w * h * c, MEMF_ANY))) return;
    for (y = 0, d = px; y < h && !dash_imgdec_stopped; y++)
        for (x = 0; x < w; x++) {
            sum[0] = sum[1] = sum[2] = sum[3] = 0;
            for (j = 0; j < k; j++) {
                UBYTE *s = img->px + ((y * k + j) * img->w + x * k) * c;
                for (i = 0; i < k; i++, s += c)
                    for (n = 0; n < c; n++) sum[n] += s[n];
            }
            for (n = 0; n < c; n++) *d++ = (UBYTE)(sum[n] / (k * k));
        }
    FreeVec(img->px);
    img->px = px;
    img->w = w;
    img->h = h;
}

/* PNG, GIF, BMP or a JPEG TJpgDec does not take, with stb_image; NULL if it cannot */
static DashImgDec *dash_imgdec_stb(UBYTE *data, LONG len, LONG maxw, LONG maxh)
{
    int w, h, comp, want;
    unsigned char *px;
    DashImgDec *img;
    LONG k = 1;
    if (!stbi_info_from_memory(data, len, &w, &h, &comp)) return NULL;
    want = comp == 2 || comp == 4 ? 4 : 3;
    if (!(px = stbi_load_from_memory(data, len, &w, &h, &comp, want))) return NULL;
    img = (DashImgDec *)AllocVec(sizeof(DashImgDec), MEMF_CLEAR);
    if (!img) {
        stbi_image_free(px);
        return NULL;
    }
    /* (its pixels, as they are: stb_image's block is AllocVec too, but with the size in front) */
    img->px = (unsigned char *)AllocVec((ULONG)w * h * want, MEMF_ANY);
    if (!img->px) {
        FreeVec(img);
        stbi_image_free(px);
        return NULL;
    }
    CopyMem(px, img->px, (ULONG)w * h * want);
    stbi_image_free(px);
    img->w = w;
    img->h = h;
    img->alpha = want == 4;
    if (maxw > 0 && maxh > 0)
        while (img->w / (k + 1) >= maxw && img->h / (k + 1) >= maxh) k++;
    dash_imgdec_reduce(img, k);
    return img;
}

/* A WebP (lossy or lossless, with alpha; not animated), decoded already scaled to the smallest size that still
   covers maxw x maxh (the aspect ratio kept); NULL if libwebp cannot */
static DashImgDec *dash_imgdec_webp(UBYTE *data, LONG len, LONG maxw, LONG maxh)
{
    WebPDecoderConfig cfg;
    WebPIDecoder *idec;
    VP8StatusCode st;
    DashImgDec *img;
    LONG w, h, tw, th, c, pos;
    if (!WebPInitDecoderConfig(&cfg)) return NULL;
    if (WebPGetFeatures(data, len, &cfg.input) != VP8_STATUS_OK || cfg.input.has_animation) return NULL;
    w = cfg.input.width;
    h = cfg.input.height;
    tw = w;
    th = h;
    if (w > maxw && h > maxh) {
        if (maxw * h > maxh * w) {
            tw = maxw;
            th = (h * maxw + w - 1) / w;
        } else {
            th = maxh;
            tw = (w * maxh + h - 1) / h;
        }
        cfg.options.use_scaling = 1;
        cfg.options.scaled_width = tw;
        cfg.options.scaled_height = th;
    }
    c = cfg.input.has_alpha ? 4 : 3;
    if (!(img = dash_imgdec_new(tw, th, c == 4))) return NULL;
    cfg.output.colorspace = c == 4 ? MODE_RGBA : MODE_RGB;
    cfg.output.is_external_memory = 1;
    cfg.output.u.RGBA.rgba = img->px;
    cfg.output.u.RGBA.stride = tw * c;
    cfg.output.u.RGBA.size = tw * th * c;
    /* (incremental, 16 KB more each time: between them it looks at dash_imgdec_stopped) */
    if (!(idec = WebPIDecode(NULL, 0, &cfg))) {
        dash_imgdec_free(img);
        return NULL;
    }
    for (pos = 0, st = VP8_STATUS_SUSPENDED; st == VP8_STATUS_SUSPENDED && !dash_imgdec_stopped; ) {
        pos = len - pos > 16384 ? pos + 16384 : len;
        st = WebPIUpdate(idec, data, pos);
        if (st == VP8_STATUS_SUSPENDED && pos == len) break;
    }
    WebPIDelete(idec);
    WebPFreeDecBuffer(&cfg.output);
    if (st != VP8_STATUS_OK) {
        dash_imgdec_free(img);
        return NULL;
    }
    return img;
}

/* Does it look like SVG text? (an XML declaration or comments, then an <svg ...> element) */
static int dash_imgdec_is_svg(UBYTE *data, LONG len)
{
    LONG i = 0, n = len < 4096 ? len : 4096;
    if (n >= 3 && data[0] == 0xEF && data[1] == 0xBB && data[2] == 0xBF) i = 3;
    while (i < n && (data[i] == ' ' || data[i] == '\t' || data[i] == '\r' || data[i] == '\n')) i++;
    if (i >= n || data[i] != '<') return 0;
    for (; i + 4 < n; i++)
        if (data[i] == '<' && data[i + 1] == 's' && data[i + 2] == 'v' && data[i + 3] == 'g' &&
            (data[i + 4] == ' ' || data[i + 4] == '>' || data[i + 4] == '\n' || data[i + 4] == '\r' ||
             data[i + 4] == '\t'))
            return 1;
    return 0;
}

/* An SVG drawn by nanosvg (RGBA): at its own size (width/height or viewBox), or, with maxw x maxh, at the smallest
   scale that covers it (it is drawn, not reduced: it may grow); with limit, at its own size but not bigger than
   maxw x maxh (the size at which it is seen is not known); NULL if it cannot be parsed */
static DashImgDec *dash_imgdec_svg(UBYTE *data, LONG len, LONG maxw, LONG maxh, int limit)
{
    char *text = (char *)AllocVec(len + 1, MEMF_ANY);
    NSVGimage *svg;
    NSVGrasterizer *r;
    DashImgDec *img;
    float scale = 1.0f, ex, ey;
    LONG w, h;
    if (!text) return NULL;
    CopyMem(data, text, len);
    text[len] = 0;
    svg = nsvgParse(text, "px", 96.0f);
    FreeVec(text);
    if (!svg) return NULL;
    if (svg->width < 1.0f || svg->height < 1.0f) {
        nsvgDelete(svg);
        return NULL;
    }
    if (maxw > 0 && maxh > 0 && maxw < 0x7FFFFFF) {
        ex = (float)maxw / svg->width;
        ey = (float)maxh / svg->height;
        if (!limit) scale = ex > ey ? ex : ey;
        else if (ex < 1.0f || ey < 1.0f) scale = ex < ey ? ex : ey;
    }
    w = (LONG)(svg->width * scale + 0.5f);
    h = (LONG)(svg->height * scale + 0.5f);
    if (w < 1) w = 1;
    if (h < 1) h = 1;
    if (w > 4096 || h > 4096 || !(r = nsvgCreateRasterizer())) {
        nsvgDelete(svg);
        return NULL;
    }
    if ((img = dash_imgdec_new(w, h, 1))) nsvgRasterize(r, svg, 0, 0, scale, img->px, w, h, w * 4);
    nsvgDeleteRasterizer(r);
    nsvgDelete(svg);
    return img;
}

/* The file decoded (NULL if it is not of these formats or cannot be read); maxw, maxh 0: its own size; negative:
   a limit (the same for the others; an SVG at its own size, made smaller to fit) */
void *dash_imgdec_decode(const char *file, long maxw, long maxh)
{
    LONG len = 0;
    UBYTE *data;
    DashImgDec *img = NULL;
    int limit = maxw < 0 && maxh < 0;
    if (!file || !(data = dash_imgdec_file(file, &len))) return NULL;
    if (limit) {
        maxw = -maxw;
        maxh = -maxh;
    }
    if (maxw <= 0 || maxh <= 0) maxw = maxh = 0x7FFFFFF;
    if (len > 2 && data[0] == 0xFF && data[1] == 0xD8) img = dash_imgdec_jpeg(data, len, maxw, maxh);
    else if (len > 12 && !memcmp(data, "RIFF", 4) && !memcmp(data + 8, "WEBP", 4))
        img = dash_imgdec_webp(data, len, maxw, maxh);
    else if (dash_imgdec_is_svg(data, len))
        img = dash_imgdec_svg(data, len, maxw, maxh, limit);
    if (!img && !dash_imgdec_stopped) img = dash_imgdec_stb(data, len, maxw, maxh);
    FreeVec(data);
    if (img && dash_imgdec_stopped) {
        dash_imgdec_free(img);
        img = NULL;
    }
    return img;
}

long dash_imgdec_width(void *d) { return d ? ((DashImgDec *)d)->w : 0; }
long dash_imgdec_height(void *d) { return d ? ((DashImgDec *)d)->h : 0; }
long dash_imgdec_alpha(void *d) { return d ? ((DashImgDec *)d)->alpha : 0; }
void *dash_imgdec_pixels(void *d) { return d ? ((DashImgDec *)d)->px : NULL; }
