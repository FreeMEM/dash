/* Dash's image_decode (Dash 2.0, what Tachyon did with @native in lib/imagen_dec.dash): a file decoded to RGB
   or RGBA pixels, made smaller until it is not much bigger than maxw x maxh (the aspect ratio kept). Baseline
   JPEG with TJpgDec, already reduced (1/2, 1/4, 1/8) while it decodes; WebP with libwebp, also scaled while it
   decodes; PNG, GIF, BMP and progressive JPEG with stb_image, reduced after. All memory from exec: it may run in another process (task_start). */
#include <exec/memory.h>
#include <dos/dos.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <string.h>
#include "tjpgd.h"
#include "src/webp/decode.h"

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

typedef struct {
    long w, h, alpha;     /* alpha: 4 bytes per pixel (RGBA), else 3 (RGB) */
    unsigned char *px;
} DashImgDec;

extern unsigned char *stbi_load_from_memory(const unsigned char *buffer, int len, int *x, int *y, int *comp,
                                            int req_comp);
extern int stbi_info_from_memory(const unsigned char *buffer, int len, int *x, int *y, int *comp);
extern void stbi_image_free(void *p);

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
    return 1;
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
    for (y = 0, d = px; y < h; y++)
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
    DashImgDec *img;
    LONG w, h, tw, th, c;
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
    if (WebPDecode(data, len, &cfg) != VP8_STATUS_OK) {
        WebPFreeDecBuffer(&cfg.output);
        dash_imgdec_free(img);
        return NULL;
    }
    WebPFreeDecBuffer(&cfg.output);
    return img;
}

/* The file decoded (NULL if it is not of these formats or cannot be read); maxw, maxh 0: its own size */
void *dash_imgdec_decode(const char *file, long maxw, long maxh)
{
    LONG len = 0;
    UBYTE *data;
    DashImgDec *img = NULL;
    if (!file || !(data = dash_imgdec_file(file, &len))) return NULL;
    if (maxw <= 0 || maxh <= 0) maxw = maxh = 0x7FFFFFF;
    if (len > 2 && data[0] == 0xFF && data[1] == 0xD8) img = dash_imgdec_jpeg(data, len, maxw, maxh);
    else if (len > 12 && !memcmp(data, "RIFF", 4) && !memcmp(data + 8, "WEBP", 4))
        img = dash_imgdec_webp(data, len, maxw, maxh);
    if (!img) img = dash_imgdec_stb(data, len, maxw, maxh);
    FreeVec(data);
    return img;
}

long dash_imgdec_width(void *d) { return d ? ((DashImgDec *)d)->w : 0; }
long dash_imgdec_height(void *d) { return d ? ((DashImgDec *)d)->h : 0; }
long dash_imgdec_alpha(void *d) { return d ? ((DashImgDec *)d)->alpha : 0; }
void *dash_imgdec_pixels(void *d) { return d ? ((DashImgDec *)d)->px : NULL; }
