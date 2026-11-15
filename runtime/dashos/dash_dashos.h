/* Dash en DashOS (AArch64, little-endian o big-endian; docs/AARCH64_LOOP.md): lo que el runtime de Dash toma de AmigaOS, sin
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
typedef uintptr_t _DashUP;  /* sin signo (ULONG) */
#define _DASH_SLOT_SH 3          /* los bytes de un elemento de lista (un _DashP) como desplazamiento */
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
void Delay(LONG ticks);

/* dos: ficheros y cajones (runtime/dashos/dos.c), sobre el servicio de archivos de DashOS o, en Linux, sus llamadas */
#define MODE_OLDFILE 1005
#define MODE_NEWFILE 1006
#define MODE_READWRITE 1004
#define OFFSET_BEGINNING (-1)
#define OFFSET_CURRENT 0
#define OFFSET_END 1
#define SHARED_LOCK (-2)
#define ACCESS_READ (-2)
#define EXCLUSIVE_LOCK (-1)
#define ACCESS_WRITE (-1)
#define DOS_FIB 2
#define ST_USERDIR 2
#define ST_SOFTLINK 3
#define ST_FILE (-3)
struct DateStamp { LONG ds_Days, ds_Minute, ds_Tick; };
struct FileInfoBlock {
    LONG fib_DiskKey, fib_DirEntryType;
    char fib_FileName[108];
    LONG fib_Protection, fib_EntryType, fib_Size, fib_NumBlocks;
    struct DateStamp fib_Date;
    char fib_Comment[80];
    UWORD fib_OwnerUID, fib_OwnerGID;
    char fib_Reserved[32];
};
BPTR Open(CONST_STRPTR name, LONG mode);
LONG Close(BPTR fh);
LONG Read(BPTR fh, APTR buf, LONG len);
LONG Seek(BPTR fh, LONG pos, LONG mode);
LONG FGetC(BPTR fh);
LONG UnGetC(BPTR fh, LONG c);
STRPTR FGets(BPTR fh, STRPTR buf, ULONG len);
LONG FPutC(BPTR fh, LONG c);
LONG FPuts(BPTR fh, CONST_STRPTR s);
BPTR Lock(CONST_STRPTR name, LONG mode);
void UnLock(BPTR lock);
BPTR DupLock(BPTR lock);
BPTR CurrentDir(BPTR lock);
APTR AllocDosObject(ULONG type, const void *tags);
void FreeDosObject(ULONG type, APTR p);
LONG Examine(BPTR lock, struct FileInfoBlock *fib);
LONG ExNext(BPTR lock, struct FileInfoBlock *fib);
LONG NameFromLock(BPTR lock, STRPTR buf, LONG len);
BPTR CreateDir(CONST_STRPTR name);
LONG DeleteFile(CONST_STRPTR name);
LONG Rename(CONST_STRPTR a, CONST_STRPTR b);
LONG SetProtection(CONST_STRPTR name, LONG bits);
LONG SetComment(CONST_STRPTR name, CONST_STRPTR text);
LONG SetFileDate(CONST_STRPTR name, const struct DateStamp *ds);

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
char *strcat(char *d, const char *s);
char *strncpy(char *d, const char *s, size_t n);
void exit(int code) __attribute__((noreturn));
void *malloc(size_t n);
void *calloc(size_t n, size_t size);
void *realloc(void *p, size_t n);
void free(void *p);

/* Las funciones de plataforma (plat.c tiene las de DashOS y las de Linux, para qemu-aarch64; quien aloje el
   runtime de otra manera pone las suyas): */
long dash_plat_write(const void *buf, long len);      /* a la salida del programa */
void dash_plat_exit(int code) __attribute__((noreturn));
void *dash_plat_pages(unsigned long bytes);           /* páginas nuevas, a cero, alineadas a 4 KB; NULL sin memoria */
void dash_plat_sleep(unsigned long us);               /* esperar sin gastar CPU (A7: Delay) */
/* una llamada al kernel de DashOS (A7: canales, llaves, procesos...): el número y hasta 5 argumentos; da x0, y x1 y
   x2 en out[0] y out[1]. En Linux (qemu-aarch64), plat.c imita en el propio programa los canales, las llaves, los
   temporizadores y la memoria; procesos y grupos dan E_TIPO (-6) */
long dash_os_call(long n, long a, long b, long c, long d, long e, long out[2]);
/* buffer_alloc y buffer_free (A7): memoria por debajo de 2 GB, a cero, para que un búfer quepa en un Int */
void *dash_plat_buffer_alloc(unsigned long bytes);
void dash_plat_buffer_free(void *p);
/* memoria para estructuras de AmigaOS (@amiga struct: amiga_alloc), por debajo de 4 GB: la de la caja Amiga */
void *dash_plat_box_alloc(unsigned long bytes);
void dash_plat_box_free(void *p, unsigned long bytes);
/* un fichero entero, por su nombre del Amiga ("LOCALE:Catalogs/..."), en memoria de AllocVec con un 0 detrás; NULL si
   no está o no se sabe dónde (los catálogos; los nombres, en runtime/dashos/dos.c) */
void *dash_plat_file_load(const char *path, long *size);
/* el selector de ficheros de DashOS: el usuario elige un fichero para leer (save 0: luego es "Elegido:") o una carpeta
   para guardar (save 1: "Carpeta:"); 1 si eligió, 0 si no, -1 si no hay selector (en Linux, nunca) */
long dash_plat_choose(int save);
/* una variable del entorno (en Linux; en DashOS aún no hay: NULL) */
const char *dash_plat_getenv(const char *name);
/* la llave del compositor ("ventanas"), según las que traía el programa al nacer: 3 si las tenía, si no 1 */
long dash_plat_windows_key(void);
#define _DASH_AMIGA_ALLOC(n) ((_DashP)dash_plat_box_alloc((unsigned long)(n)))
#define _DASH_AMIGA_FREE(p, n) dash_plat_box_free((void *)(_DashP)(p), (unsigned long)(n))

#endif
