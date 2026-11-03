#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "dashc.h"
#include "zlib.h"

#ifdef __amigaos__
/* en el Amiga: 64 KB de pila (el shell da 4 KB); libnix cambia de pila antes de main */
extern void __stkinit(void);
void *__stkinit_ref = (void *)__stkinit;
unsigned long __stack = 65536;
#endif

/* el runtime ya compilado, metido en dashc (build/rt_blob.c) */
#define DASH_VERSION "2.1.0"

/* los runtimes (build/rt_blob.c, runtime/rt_blob.py): el normal tal cual; el de --memcheck, comprimido */
extern const unsigned char rt_normal[], rt_mc_z[];
extern const unsigned int rt_normal_len, rt_mc_zlen, rt_mc_len;
/* el de --fpu (build/rt_fpu_blob.c), preparado como el normal; en el dashc del Amiga, aparte (rt_fpu_len = 0) */
extern const unsigned char rt_fpu[], rt_fpu_mc[];
extern const unsigned int rt_fpu_len, rt_fpu_mc_len;

/* descomprime z en dst, que tiene sitio para raw bytes */
static void rt_unpack(const unsigned char *z, unsigned int zlen, uint8_t *dst, unsigned int raw)
{
    z_stream s;
    memset(&s, 0, sizeof s);
    s.next_in = (Bytef *)z;
    s.avail_in = zlen;
    s.next_out = dst;
    s.avail_out = raw;
    if (inflateInit(&s) != Z_OK || inflate(&s, Z_FINISH) != Z_STREAM_END || s.total_out != raw)
        fatal("el runtime de dentro está estropeado");
    inflateEnd(&s);
}

char *read_text(const char *path)
{
    FILE *f = fopen(path, "rb");
    Buf b = {0};
    char tmp[4096];
    size_t n;
    if (!f) return NULL;
    while ((n = fread(tmp, 1, sizeof tmp, f)) > 0) buf_bytes(&b, tmp, n);
    fclose(f);
    buf_byte(&b, 0);
    return (char *)b.p;
}

static uint8_t *read_file(const char *path, size_t *len)
{
    FILE *f = fopen(path, "rb");
    Buf b = {0};
    char tmp[4096];
    size_t n;
    if (!f) fatal("no se puede leer %s", path);
    while ((n = fread(tmp, 1, sizeof tmp, f)) > 0) buf_bytes(&b, tmp, n);
    fclose(f);
    *len = b.n;
    buf_byte(&b, 0);
    return b.p;
}

const uint8_t *rt_blob;
size_t rt_blob_len;

static void usage(void)
{
    err_printf(
            "uso: dash programa.dash -o ejecutable [--fpu] [--memcheck] [--stack bytes] [--version]\n"
            "Compila Dash a un ejecutable de Amiga sin compilador de C (Dash 2.0).\n"
            "  --fpu          Float y Double con la FPU (68020 y 68881/68882, o 68040/68060)\n"
            "  --cpu X        68000 (por defecto) o 68020...68060: multiplica y divide con muls.l y divs.l\n"
            "  --memcheck     comprueba la memoria (avisa de nil y dice lo vivo al acabar)\n"
            "  --perfil       al acabar, en qué funciones se fue el tiempo (también --profile)\n"
            "  --cabecera x.h los structs del programa en C, para el C de @link (sin -o, solo eso)\n"
            "  --stack N      pide al menos N bytes de pila (como @stack N)\n"
            "  --runtime X    otro runtime (un objeto Hunk o uno preparado: para probar)\n"
            "  --tiempos      lo que lleva cada fase\n");
    exit(1);
}

/* dashc --debug-info prog: el texto del HUNK_DEBUG de un ejecutable hecho con --debug */
static uint32_t be32(const uint8_t *p) { return (uint32_t)p[0] << 24 | p[1] << 16 | p[2] << 8 | p[3]; }

static int debug_info_show(const char *path)
{
    size_t len, at;
    uint8_t *d = read_file(path, &len);
    uint32_t first, last, n, type;
    if (len < 20 || be32(d) != 0x3F3) fatal("%s no es un ejecutable de Amiga", path);
    first = be32(d + 12);
    last = be32(d + 16);
    at = 20 + 4 * (size_t)(last - first + 1);
    while (at + 4 <= len) {
        type = be32(d + at) & 0x3FFFFFFF;
        at += 4;
        if (type == 0x3E9 || type == 0x3EA) at += 4 + 4 * (size_t)be32(d + at);           /* código, datos */
        else if (type == 0x3EB) at += 4;                                                    /* BSS */
        else if (type == 0x3EC) {                                                           /* RELOC32 */
            while ((n = be32(d + at)) != 0) at += 8 + 4 * (size_t)n;
            at += 4;
        } else if (type == 0x3F1) {                                                         /* DEBUG */
            n = be32(d + at);
            if (n >= 3 && !memcmp(d + at + 4, "DASH-DEBUG", 10)) {
                size_t k = 0;
                while (k < 4 * (size_t)n && d[at + 4 + k]) k++;
                fwrite(d + at + 4, 1, k, stdout);
                return 0;
            }
            at += 4 + 4 * (size_t)n;
        } else if (type != 0x3F2) break;                                                    /* END */
    }
    err_printf("dash: %s no lleva información de depuración (compílalo con --debug)\n", path);
    return 1;
}

/* La carpeta de Dash, para los import de lib/ desde cualquier sitio: $DASH_HOME, y si no, la de arriba de
   la de dashc (dashc/dashc en el repositorio); en el Amiga, la de dashc (PROGDIR:) */
char dash_home[1024];

static void find_dash_home(const char *argv0)
{
    const char *e = getenv("DASH_HOME"), *slash;
#ifdef __amigaos__
    (void)argv0;
    snprintf(dash_home, sizeof dash_home, "%s", e && *e ? e : "PROGDIR:");
#else
    if (e && *e) { snprintf(dash_home, sizeof dash_home, "%s", e); return; }
    slash = argv0 ? strrchr(argv0, '/') : NULL;
    if (slash) snprintf(dash_home, sizeof dash_home, "%.*s/..", (int)(slash - argv0), argv0);
#endif
}

int main(int argc, char **argv)
{
    find_dash_home(argv[0]);
    const char *in = NULL, *out = NULL, *rt_path = NULL, *header = NULL;
    const uint8_t *rt = NULL;
    size_t rtlen = 0, len;
    uint8_t *src;
    Program *prog;
    static Obj obj;
    long cli_stack = 0;
    int i, fpu = 0;

    for (i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "-o") && i + 1 < argc) out = argv[++i];
        else if (!strcmp(argv[i], "--runtime") && i + 1 < argc) rt_path = argv[++i];
        else if (!strcmp(argv[i], "--memcheck")) memcheck = 1;
        else if (!strcmp(argv[i], "--debug")) debug = 1;
        else if (!strcmp(argv[i], "--debug-info") && i + 1 < argc) return debug_info_show(argv[i + 1]);
        else if (!strcmp(argv[i], "--perfil") || !strcmp(argv[i], "--profile")) profile = 1;
        else if (!strcmp(argv[i], "--fpu")) fpu = cpu020 = 1;   /* (la FPU pide un 68020) */
        else if (!strcmp(argv[i], "--cabecera") && i + 1 < argc) header = argv[++i];
        else if (!strcmp(argv[i], "--cpu") && i + 1 < argc) {
            const char *c = argv[++i];
            if (strcmp(c, "68000") && strcmp(c, "68020") && strcmp(c, "68030") && strcmp(c, "68040") &&
                strcmp(c, "68060"))
                fatal("--cpu: 68000, 68020, 68030, 68040 o 68060");
            cpu020 = strcmp(c, "68000") != 0;          /* muls.l y divs.l */
        }
        else if (!strcmp(argv[i], "--tiempos")) tiempos = 1;
        else if (!strcmp(argv[i], "--stack") && i + 1 < argc) cli_stack = atol(argv[++i]);
        else if (!strcmp(argv[i], "--version")) {
            printf("Dash %s\n", DASH_VERSION);
            return 0;
        }
        else if (!strcmp(argv[i], "--preparar") && i + 2 < argc) {
            /* al construir dashc: el runtime (objeto Hunk) ya leído, troceado y atado (hunk.c) */
            size_t n;
            uint8_t *o = read_file(argv[i + 1], &n);
            prepare_runtime(o, n, argv[i + 2]);
            return 0;
        }
        else if (!strcmp(argv[i], "--dashui") && i + 1 < argc) {
            /* el código Dash de un .dashui (para ver lo que compila un import) */
            char *t = read_text(argv[++i]);
            if (!t) fatal("no se puede leer %s", argv[i]);
            fputs(dashui_generate(t, argv[i]), stdout);
            return 0;
        }
        else if (argv[i][0] == '-') usage();
        else if (!in) in = argv[i];
        else usage();
    }
    if (!in || (!out && !header)) usage();
    tiempo("cargar");

    rt = rt_normal;
    rtlen = rt_normal_len;
    if (memcheck && fpu) {
        /* --fpu --memcheck: el suyo (el de --memcheck lleva el Float por software, y mezclado con el C de @link
           compilado para FPU daba números rotos) */
        if (rt_fpu_mc_len) {
            rt = rt_fpu_mc;
            rtlen = rt_fpu_mc_len;
        } else {
            FILE *f = fopen("PROGDIR:dash_fpu_mc.drt", "rb");
            if (!f) fatal("--fpu --memcheck necesita dash_fpu_mc.drt junto a dash");
            fclose(f);
            rt = read_file("PROGDIR:dash_fpu_mc.drt", &rtlen);
        }
    } else if (memcheck && !rt_mc_len) {
        /* el dashc del Amiga no lo lleva dentro (es la mitad de su tamaño): dashc_mc.drt, junto a él */
        FILE *f = fopen("PROGDIR:dash_mc.drt", "rb");
        if (!f) fatal("--memcheck necesita dash_mc.drt junto a dash");
        fclose(f);
        rt = read_file("PROGDIR:dash_mc.drt", &rtlen);
        tiempo("descomprimir");
    } else if (memcheck) {
        uint8_t *buf = xmalloc(rt_mc_len);
        rt_unpack(rt_mc_z, rt_mc_zlen, buf, rt_mc_len);
        tiempo("descomprimir");
        rt = buf;
        rtlen = rt_mc_len;
    } else if (fpu && rt_fpu_len) {
        rt = rt_fpu;
        rtlen = rt_fpu_len;
    } else if (fpu) {
        FILE *f = fopen("PROGDIR:dash_fpu.drt", "rb");
        if (!f) fatal("--fpu necesita dash_fpu.drt junto a dash");
        fclose(f);
        rt = read_file("PROGDIR:dash_fpu.drt", &rtlen);
    }
    src_name = in;
    VEC_PUSH(src_files, in);
    lex_file = 0;
    src = read_file(in, &len);
    if (rt_path) rt = read_file(rt_path, &rtlen);

    rt_blob = rt;
    rt_blob_len = rtlen;
    tiempo("inicio");
    parse_module_ok = header && !out;
    prog = parse(lex((const char *)src));
    if (cli_stack > prog->stack_min) prog->stack_min = cli_stack;   /* --stack N: como @stack N */
    if (header) {
        /* los structs del programa para el C de un módulo de @link */
        FILE *f = fopen(header, "w");
        if (!f) fatal("no se puede escribir %s", header);
        write_c_header(prog, f);
        fclose(f);
        if (!out) return 0;
    }
    tiempo("leer");
    gen_program(prog, &obj);
    tiempo("generar");
#ifdef DASH_A64
    write_elf_obj(&obj, out);   /* (se enlaza aparte con el runtime para ARM: docs/AARCH64_LOOP.md) */
#else
    link_exe(&obj, rt, rtlen, out);
#endif
    tiempo("escribir");
    return 0;
}
