/* Dash en DashOS (AArch64 big-endian, docs/AARCH64_LOOP.md): lo que el runtime de Dash toma de AmigaOS, sin
   AmigaOS debajo. Los tipos tienen el tamaño de los del Amiga (LONG de 32 bits) y los punteros, el del
   procesador (64 bits). Las funciones de memoria y de salida tienen el nombre y el comportamiento de las de exec
   y dos; las pone plat.c sobre las funciones de plataforma (dash_plat_*), las únicas que saben del sistema. */
#ifndef DASH_DASHOS_H
#define DASH_DASHOS_H
#define _DASH_DASHOS 1

#include <stddef.h>
#include <stdint.h>
#include <stdarg.h>

typedef int32_t LONG;
typedef uint32_t ULONG;
typedef int16_t WORD;
typedef uint16_t UWORD;
typedef int8_t BYTE;
typedef uint8_t UBYTE;
typedef int16_t BOOL;
typedef void *APTR;
typedef unsigned char *STRPTR;
typedef const unsigned char *CONST_STRPTR;
typedef intptr_t BPTR;
typedef float FLOAT;
typedef double DOUBLE;
typedef void VOID;
typedef intptr_t _DashP;   /* un entero del tamaño de un puntero (en el Amiga, LONG) */
#define CONST const
#define TRUE 1
#define FALSE 0
#ifndef NULL
#define NULL ((void *)0)
#endif

#define MEMF_ANY 0UL
#define MEMF_PUBLIC (1UL << 0)
#define MEMF_CHIP (1UL << 1)
#define MEMF_FAST (1UL << 2)
#define MEMF_CLEAR (1UL << 16)

/* exec */
APTR CreatePool(ULONG flags, ULONG puddle, ULONG threshold);
void DeletePool(APTR pool);
APTR AllocPooled(APTR pool, ULONG size);
void FreePooled(APTR pool, APTR mem, ULONG size);
APTR AllocMem(ULONG size, ULONG flags);
void FreeMem(APTR mem, ULONG size);
APTR AllocVec(ULONG size, ULONG flags);
void FreeVec(APTR mem);
void CopyMem(const void *src, void *dst, ULONG size);

/* dos: la salida del programa. Printf y VPrintf entienden lo de RawDoFmt que usa Dash (%s %ld %lu %lx %lX %c
   %%, ancho, relleno con 0 y "-"); un %d sin l es también un LONG (todos los argumentos lo son) */
extern APTR DOSBase, IntuitionBase;
BPTR Output(void);
LONG Printf(CONST_STRPTR fmt, ...);
LONG VPrintf(CONST_STRPTR fmt, const intptr_t *args);
LONG PutStr(CONST_STRPTR s);
LONG Write(BPTR fh, const void *buf, LONG len);
LONG Flush(BPTR fh);

/* la libc que usa el runtime */
void *memcpy(void *d, const void *s, size_t n);
void *memmove(void *d, const void *s, size_t n);
void *memset(void *d, int c, size_t n);
int memcmp(const void *a, const void *b, size_t n);
size_t strlen(const char *s);
int strcmp(const char *a, const char *b);
int strncmp(const char *a, const char *b, size_t n);
char *strcpy(char *d, const char *s);
char *strchr(const char *s, int c);
void exit(int code) __attribute__((noreturn));

/* Las funciones de plataforma (plat.c tiene las de DashOS y las de Linux, para qemu-aarch64_be; quien aloje el
   runtime de otra manera pone las suyas): */
long dash_plat_write(const void *buf, long len);      /* a la salida del programa */
void dash_plat_exit(int code) __attribute__((noreturn));
void *dash_plat_pages(unsigned long bytes);           /* páginas nuevas, a cero, alineadas a 4 KB; NULL sin memoria */

#endif
