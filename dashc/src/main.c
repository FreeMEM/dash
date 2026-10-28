#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "dashc.h"

#ifdef __amigaos__
/* en el Amiga: 64 KB de pila (el shell da 4 KB); libnix cambia de pila antes de main */
extern void __stkinit(void);
void *__stkinit_ref = (void *)__stkinit;
unsigned long __stack = 65536;
#endif

/* el runtime ya compilado, metido en dashc (build/rt_blob.c) */
extern const unsigned char dashrt_o[];
extern const unsigned int dashrt_o_len;

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

static void usage(void)
{
    fprintf(stderr,
            "uso: dashc programa.dash -o ejecutable [--runtime objeto.o]\n"
            "Prueba de concepto: compila Dash a un ejecutable de Amiga sin compilador de C.\n");
    exit(1);
}

int main(int argc, char **argv)
{
    const char *in = NULL, *out = NULL, *rt_path = NULL;
    const uint8_t *rt = dashrt_o;
    size_t rtlen = dashrt_o_len, len;
    uint8_t *src;
    Program *prog;
    static Obj obj;
    int i;

    for (i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "-o") && i + 1 < argc) out = argv[++i];
        else if (!strcmp(argv[i], "--runtime") && i + 1 < argc) rt_path = argv[++i];
        else if (argv[i][0] == '-') usage();
        else if (!in) in = argv[i];
        else usage();
    }
    if (!in || !out) usage();

    src_name = in;
    src = read_file(in, &len);
    if (rt_path) rt = read_file(rt_path, &rtlen);

    prog = parse(lex((const char *)src));
    gen_program(prog, &obj);
    link_exe(&obj, rt, rtlen, out);
    return 0;
}
