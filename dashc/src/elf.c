/* dashc para DashOS (docs/AARCH64_LOOP.md, fase A4): el programa como objeto ELF64 de AArch64, little-endian (o
   big-endian con --be)
   (ET_REL), para enlazarlo con el runtime de dashc para ARM. Secciones: .text (el código; empieza por el arranque,
   el símbolo _dashc_start), .data (las globales, los textos...), .rela.text, .rela.data, .symtab, .strtab y
   .shstrtab. Las reubicaciones van a la sección .text o .data (con el sumando) o a un símbolo de fuera. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "dashc.h"

/* en el orden de bytes del objeto: little-endian (lo nativo de DashOS) o, con --be, big-endian (la caja Amiga) */
static void e16(Buf *b, unsigned v)
{
    if (elf_be) { buf_byte(b, (int)(v >> 8 & 0xFF)); buf_byte(b, (int)(v & 0xFF)); }
    else { buf_byte(b, (int)(v & 0xFF)); buf_byte(b, (int)(v >> 8 & 0xFF)); }
}
static void e32(Buf *b, uint32_t v)
{
    if (elf_be) { e16(b, v >> 16); e16(b, v & 0xFFFF); } else { e16(b, v & 0xFFFF); e16(b, v >> 16); }
}
static void e64(Buf *b, uint64_t v)
{
    if (elf_be) { e32(b, (uint32_t)(v >> 32)); e32(b, (uint32_t)v); } else { e32(b, (uint32_t)v); e32(b, (uint32_t)(v >> 32)); }
}

/* las secciones: 0 nula, 1 .text, 2 .data, 3 .rela.text, 4 .rela.data, 5 .symtab, 6 .strtab, 7 .shstrtab */
enum { S_TEXT = 1, S_DATA, S_RELT, S_RELD, S_SYM, S_STR, S_SHSTR, S_N };

typedef struct { uint32_t name; uint8_t info, other; uint16_t shndx; uint64_t value, size; } Sym;

static uint32_t str_add(Buf *b, const char *s)
{
    uint32_t off = (uint32_t)b->n;
    buf_bytes(b, s, (int)strlen(s));
    buf_byte(b, 0);
    return off;
}

void write_elf_obj(Obj *obj, const char *out)
{
    Buf strtab, shstr, symtab, relt, reld, file;
    struct { Sym *v; int n, cap; } syms = {0};
    struct { const char *name; int idx; } *ext = NULL;
    int next = 0, i, nlocal;
    uint32_t sh_name[S_N];
    uint64_t off[S_N], size[S_N];
    Sym s;
    FILE *f;

    memset(&strtab, 0, sizeof strtab); memset(&shstr, 0, sizeof shstr); memset(&symtab, 0, sizeof symtab);
    memset(&relt, 0, sizeof relt); memset(&reld, 0, sizeof reld); memset(&file, 0, sizeof file);
    buf_byte(&strtab, 0);
    buf_byte(&shstr, 0);
    /* símbolos: nulo, las secciones .text y .data (locales), y luego los globales */
    memset(&s, 0, sizeof s);
    VEC_PUSH(syms, s);
    s.info = 3;                                        /* STB_LOCAL, STT_SECTION */
    s.shndx = S_TEXT;
    VEC_PUSH(syms, s);
    s.shndx = S_DATA;
    VEC_PUSH(syms, s);
    nlocal = syms.n;
    memset(&s, 0, sizeof s);
    s.name = str_add(&strtab, "_dashc_start");         /* la entrada: el principio del código */
    s.info = 0x12;                                     /* STB_GLOBAL, STT_FUNC */
    s.shndx = S_TEXT;
    VEC_PUSH(syms, s);
    for (i = 0; i < obj->exports.n; i++) {
        memset(&s, 0, sizeof s);
        s.name = str_add(&strtab, obj->exports.v[i].name[0] == '_' ? obj->exports.v[i].name + 1 : obj->exports.v[i].name);
        s.info = 0x12;
        s.shndx = S_TEXT;
        s.value = obj->exports.v[i].off;
        VEC_PUSH(syms, s);
    }
    /* los de fuera, uno por nombre */
    ext = xmalloc(sizeof(*ext) * (size_t)(obj->relocs.n + 1));
    for (i = 0; i < obj->relocs.n; i++) {
        Reloc *r = &obj->relocs.v[i];
        int j;
        if (r->hunk >= 0) continue;
        for (j = 0; j < next && strcmp(ext[j].name, r->sym); j++) ;
        if (j < next) continue;
        memset(&s, 0, sizeof s);
        s.name = str_add(&strtab, r->sym);
        s.info = 0x10;                                 /* STB_GLOBAL, STT_NOTYPE, sin definir */
        ext[next].name = r->sym;
        ext[next].idx = syms.n;
        next++;
        VEC_PUSH(syms, s);
    }
    for (i = 0; i < syms.n; i++) {
        e32(&symtab, syms.v[i].name);
        buf_byte(&symtab, syms.v[i].info);
        buf_byte(&symtab, syms.v[i].other);
        e16(&symtab, syms.v[i].shndx);
        e64(&symtab, syms.v[i].value);
        e64(&symtab, syms.v[i].size);
    }
    /* las reubicaciones (Elf64_Rela: offset, info = símbolo << 32 | tipo, sumando), cada una en la suya */
    for (i = 0; i < obj->relocs.n; i++) {
        Reloc *r = &obj->relocs.v[i];
        Buf *b = r->in_data ? &reld : &relt;          /* (las de las tablas, en los datos) */
        uint64_t sym;
        if (r->hunk == HK_CODE) sym = 1;
        else if (r->hunk == HK_DATA) sym = 2;
        else {
            int j;
            for (j = 0; strcmp(ext[j].name, r->sym); j++) ;
            sym = (uint64_t)ext[j].idx;
        }
        e64(b, r->off);
        e64(b, sym << 32 | (uint32_t)r->type);
        e64(b, (uint64_t)r->addend);
    }
    sh_name[0] = 0;
    sh_name[S_TEXT] = str_add(&shstr, ".text");
    sh_name[S_DATA] = str_add(&shstr, ".data");
    sh_name[S_RELT] = str_add(&shstr, ".rela.text");
    sh_name[S_RELD] = str_add(&shstr, ".rela.data");
    sh_name[S_SYM] = str_add(&shstr, ".symtab");
    sh_name[S_STR] = str_add(&shstr, ".strtab");
    sh_name[S_SHSTR] = str_add(&shstr, ".shstrtab");

    /* el fichero: cabecera (64 bytes), las secciones (alineadas a 16) y la tabla de secciones */
    {
        Buf *body[S_N];
        uint64_t pos = 64;
        body[0] = NULL;
        body[S_TEXT] = &obj->code;
        body[S_DATA] = &obj->data;
        body[S_RELT] = &relt;
        body[S_RELD] = &reld;
        body[S_SYM] = &symtab;
        body[S_STR] = &strtab;
        body[S_SHSTR] = &shstr;
        off[0] = size[0] = 0;
        for (i = 1; i < S_N; i++) {
            pos = (pos + 15) & ~(uint64_t)15;
            off[i] = pos;
            size[i] = (uint64_t)body[i]->n;
            pos += size[i];
        }
        pos = (pos + 15) & ~(uint64_t)15;
        /* cabecera */
        buf_bytes(&file, "\177ELF", 4);
        buf_byte(&file, 2);                            /* ELFCLASS64 */
        buf_byte(&file, elf_be ? 2 : 1);               /* ELFDATA2MSB o ELFDATA2LSB */
        buf_byte(&file, 1);                            /* EV_CURRENT */
        for (i = 0; i < 9; i++) buf_byte(&file, 0);
        e16(&file, 1);                                /* ET_REL */
        e16(&file, 183);                              /* EM_AARCH64 */
        e32(&file, 1);
        e64(&file, 0);                                /* e_entry */
        e64(&file, 0);                                /* e_phoff */
        e64(&file, pos);                              /* e_shoff */
        e32(&file, 0);                                /* e_flags */
        e16(&file, 64);
        e16(&file, 0); e16(&file, 0);                /* sin cabeceras de programa */
        e16(&file, 64);                               /* e_shentsize */
        e16(&file, S_N);
        e16(&file, S_SHSTR);
        for (i = 1; i < S_N; i++) {
            while ((uint64_t)file.n < off[i]) buf_byte(&file, 0);
            buf_bytes(&file, (const char *)body[i]->p, body[i]->n);
        }
        while ((uint64_t)file.n < pos) buf_byte(&file, 0);
        /* la tabla de secciones */
        for (i = 0; i < S_N; i++) {
            static const uint32_t type[S_N] = {0, 1, 1, 4, 4, 2, 3, 3};   /* PROGBITS, RELA, SYMTAB, STRTAB */
            static const uint64_t flags[S_N] = {0, 6, 3, 0x40, 0x40, 0, 0, 0};   /* AX, WA, INFO_LINK */
            static const uint64_t align[S_N] = {0, 8, 8, 8, 8, 8, 1, 1};
            uint32_t link = 0, info = 0;
            uint64_t entsize = 0;
            if (i == S_RELT || i == S_RELD) { link = S_SYM; info = i == S_RELT ? S_TEXT : S_DATA; entsize = 24; }
            if (i == S_SYM) { link = S_STR; info = (uint32_t)nlocal; entsize = 24; }
            e32(&file, sh_name[i]);
            e32(&file, type[i]);
            e64(&file, flags[i]);
            e64(&file, 0);
            e64(&file, off[i]);
            e64(&file, size[i]);
            e32(&file, link);
            e32(&file, info);
            e64(&file, align[i]);
            e64(&file, entsize);
        }
    }
    f = fopen(out, "wb");
    if (!f) fatal("no se puede escribir %s", out);
    fwrite(file.p, 1, file.n, f);
    fclose(f);
    free(ext);
}
