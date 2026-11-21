#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "dashc.h"
#include "zlib.h"

#ifdef __amigaos__
#define Node AmigaNode        /* (el Node de exec; dashc tiene el suyo) */
#include <proto/dos.h>
#undef Node
#else
#include <sys/stat.h>
#endif
#ifdef __amigaos__
/* en el Amiga: 128 KB de pila (el shell da 4 KB); libnix cambia de pila antes de main. Con 64 KB, Forja (un texto de
   mil trozos sumados) la agotaba */
extern void __stkinit(void);
void *__stkinit_ref = (void *)__stkinit;
#ifndef DASHC_STACK
#define DASHC_STACK 131072
#endif
unsigned long __stack = DASHC_STACK;
#endif

/* el runtime ya compilado, metido en dashc (build/rt_blob.c) */
#define DASH_VERSION "2.18.2"
#ifndef DASH_FECHA
#define DASH_FECHA "?"
#endif
/* para la orden Version del Amiga ("version dash"): la única "$VER:" de dash (la fecha la pone el Makefile) */
static const char __attribute__((used)) dash_ver[] = "$VER: dash " DASH_VERSION " (" DASH_FECHA ")";

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

/* --texto ruta=fichero: el texto de ruta (un módulo o el programa) se lee de fichero. Forja comprueba así lo que aún
   no ha guardado; los errores dicen ruta */
static struct { const char *path, *from; } textos[16];
static int n_textos;

/* ¿son el mismo fichero? (si no existen los dos, el mismo nombre) */
static int same_file(const char *a, const char *b)
{
#ifdef __amigaos__
    BPTR la = Lock((STRPTR)a, SHARED_LOCK), lb;
    if (la) {
        lb = Lock((STRPTR)b, SHARED_LOCK);
        if (lb) {
            int r = SameLock(la, lb) == LOCK_SAME;
            UnLock(lb);
            UnLock(la);
            return r;
        }
        UnLock(la);
    }
    return !stricmp(a, b);
#else
    struct stat sa, sb;
    if (!stat(a, &sa) && !stat(b, &sb)) return sa.st_dev == sb.st_dev && sa.st_ino == sb.st_ino;
    return !strcmp(a, b);
#endif
}

static const char *texto_de(const char *path)
{
    int i;
    for (i = 0; i < n_textos; i++)
        if (same_file(textos[i].path, path)) return textos[i].from;
    return path;
}

/* el fichero entero, con un 0 detrás: de una vez si se sabe su tamaño (en el Amiga, leerlo a trozos de 4 KB
   copiando lo leído cada vez que crecía costaba con un fichero grande, como dash_mc.drt) */
static uint8_t *slurp(FILE *f, size_t *len)
{
    Buf b = {0};
    char tmp[4096];
    size_t n;
    long size = -1;
    if (!fseek(f, 0, SEEK_END)) size = ftell(f);
    if (size >= 0 && !fseek(f, 0, SEEK_SET)) {
        b.p = xmalloc((size_t)size + 1);
        b.cap = (size_t)size + 1;
        while (b.n < (size_t)size && (n = fread(b.p + b.n, 1, (size_t)size - b.n, f)) > 0) b.n += n;
    } else {
        rewind(f);
        b.n = 0;
    }
    while ((n = fread(tmp, 1, sizeof tmp, f)) > 0) buf_bytes(&b, tmp, n);   /* (si creció, o sin tamaño) */
    fclose(f);
    *len = b.n;
    buf_byte(&b, 0);
    return b.p;
}

char *read_text(const char *path)
{
    FILE *f = fopen(texto_de(path), "rb");
    size_t len;
    if (!f) return NULL;
    return (char *)slurp(f, &len);
}

static uint8_t *read_file(const char *path, size_t *len)
{
    FILE *f = fopen(path, "rb");
    if (!f) fatal("no se puede leer %s", path);
    return slurp(f, len);
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
            "  --check        solo comprueba: da los errores sin hacer el ejecutable (sin -o); vale un módulo sin Main\n"
            "  --texto r=f    el texto de r (un módulo o el programa) se lee de f: lo que aún no se ha guardado\n"
            "  --stack N      pide al menos N bytes de pila (como @stack N)\n"
            "  --runtime X    otro runtime (un objeto Hunk o uno preparado: para probar)\n"
            "  --tiempos      lo que lleva cada fase (y la memoria en uso)\n");
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
    mem_init();
    find_dash_home(argv[0]);
    const char *in = NULL, *out = NULL, *rt_path = NULL, *header = NULL;
    const uint8_t *rt = NULL;
    size_t rtlen = 0, len;
    uint8_t *src;
    Program *prog;
    static Obj obj;
    long cli_stack = 0;
    int i, fpu = 0, check = 0;

    for (i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "-o") && i + 1 < argc) out = argv[++i];
        else if (!strcmp(argv[i], "--runtime") && i + 1 < argc) rt_path = argv[++i];
        else if (!strcmp(argv[i], "--memcheck")) memcheck = 1;
        else if (!strcmp(argv[i], "--be")) elf_be = 1;
        else if (!strcmp(argv[i], "--debug")) debug = 1;
        else if (!strcmp(argv[i], "--debug-info") && i + 1 < argc) return debug_info_show(argv[i + 1]);
        else if (!strcmp(argv[i], "--perfil") || !strcmp(argv[i], "--profile")) profile = 1;
        else if (!strcmp(argv[i], "--fpu")) fpu = cpu020 = fpu881 = 1;   /* (la FPU pide un 68020) */
        else if (!strcmp(argv[i], "--cabecera") && i + 1 < argc) header = argv[++i];
        else if (!strcmp(argv[i], "--cpu") && i + 1 < argc) {
            const char *c = argv[++i];
            if (strcmp(c, "68000") && strcmp(c, "68020") && strcmp(c, "68030") && strcmp(c, "68040") &&
                strcmp(c, "68060"))
                fatal("--cpu: 68000, 68020, 68030, 68040 o 68060");
            cpu020 = strcmp(c, "68000") != 0;          /* muls.l y divs.l */
        }
        else if (!strcmp(argv[i], "--tiempos")) tiempos = 1;
        else if (!strcmp(argv[i], "--check")) check = check_mode = 1;
        else if ((!strcmp(argv[i], "--texto") || !strcmp(argv[i], "--text")) && i + 1 < argc) {
            /* --texto ruta=fichero (con --check): el texto sin guardar de un módulo o del programa */
            char *a = argv[++i], *eq = strrchr(a, '=');
            if (!eq || eq == a || !eq[1]) fatal("--texto ruta=fichero: el texto de ruta se lee de fichero");
            if (n_textos == 16) fatal("--texto: como mucho 16");
            textos[n_textos].path = xstrndup(a, (size_t)(eq - a));
            textos[n_textos++].from = eq + 1;
        }
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
    if (!in || (!out && !header && !check)) usage();
    if (check) atexit(check_flush);
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
    src = read_file(texto_de(in), &len);
    if (rt_path) rt = read_file(rt_path, &rtlen);

    rt_blob = rt;
    rt_blob_len = rtlen;
    tiempo("inicio");
    parse_module_ok = header && !out;
    {
        char *sin_asm = asm_extract((const char *)src);   /* los bloques asm ... end (asm68k.c) */
        Token *toks = lex(sin_asm ? sin_asm : (const char *)src);
        prog = parse(toks);
        xfree(toks);                                   /* (el árbol no apunta a los tokens, ni al texto) */
        xfree(sin_asm);
        xfree(src);
    }
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
    node_free_all();                                   /* (el árbol ya no hace falta: su memoria, para enlazar) */
    tiempo("generar");
    if (check) {
        check_flush();
        return check_errors ? 1 : 0;
    }   /* --check: los errores salen al generar; sin ejecutable */
#ifdef DASH_A64
    write_elf_obj(&obj, out);   /* (se enlaza aparte con el runtime para ARM: docs/AARCH64_LOOP.md) */
#else
    link_exe(&obj, rt, rtlen, out);
#endif
    tiempo("escribir");
    return 0;
}
