/* Lo de libc, libm y libgcc que pide el C de @link (QuickJS...) y el runtime no usa. Va en la librería con
   una sección por función: solo entra en un ejecutable lo que algo llama. La salida de stdio va a Output(),
   con su búfer (como Print), sea stdout o stderr. */
#include <exec/types.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <stdarg.h>
#include <stddef.h>
/* (stdio.h de libnix trae fputc en línea: con otro nombre, para definir aquí la de verdad) */
#define fputc dash_libnix_fputc
#include <stdio.h>
#undef fputc
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <dos/var.h>

double dash_fd_floor(double);
double __ieee754_log(double);
double __ieee754_sqrt(double);
void _dash_quit(int code) __attribute__((noreturn));

/* ---- texto ---- */

char *strchr(const char *s, int c)
{
    for (;; s++) {
        if (*s == (char)c) return (char *)s;
        if (!*s) return NULL;
    }
}

char *strrchr(const char *s, int c)
{
    const char *r = NULL;
    for (;; s++) {
        if (*s == (char)c) r = s;
        if (!*s) return (char *)r;
    }
}

/* vsnprintf: flags - 0 + espacio, anchura y precisión (también *), h l ll, d i u x X o c s p % (los de coma
   flotante salen como "?": el runtime no los usa y QuickJS solo en sus volcados) */
typedef struct { char *o; size_t n, max; } Out;

static void put(Out *w, char c)
{
    if (w->n + 1 < w->max) w->o[w->n] = c;
    w->n++;
}

static void pad(Out *w, char c, int k)
{
    while (k-- > 0) put(w, c);
}

static void put_u(Out *w, unsigned long long v, int base, int upper, const char *sign, int width, int prec,
                  int zero, int left)
{
    char tmp[24];
    int n = 0, len, sl = (int)strlen(sign), z;
    const char *dig = upper ? "0123456789ABCDEF" : "0123456789abcdef";
    if (v >> 32) {
        while (v) {
            tmp[n++] = dig[v % base];
            v /= base;
        }
    } else {
        unsigned long u = (unsigned long)v;   /* (de 32 bits: sin la división de 64) */
        while (u) {
            tmp[n++] = dig[u % base];
            u /= base;
        }
    }
    if (prec < 0 && !n) tmp[n++] = '0';
    z = prec > n ? prec - n : 0;
    if (prec < 0 && zero && !left && width > n + sl) z = width - n - sl;
    len = n + z + sl;
    if (!left) pad(w, ' ', width - len);
    while (*sign) put(w, *sign++);
    pad(w, '0', z);
    while (n) put(w, tmp[--n]);
    if (left) pad(w, ' ', width - len);
}

int vsnprintf(char *out, size_t max, const char *f, va_list ap)
{
    Out w;
    w.o = out;
    w.n = 0;
    w.max = max;
    for (; *f; f++) {
        int left = 0, zero = 0, plus = 0, space = 0, width = 0, prec = -1, lng = 0;
        if (*f != '%') {
            put(&w, *f);
            continue;
        }
        for (f++;; f++) {
            if (*f == '-') left = 1;
            else if (*f == '0') zero = 1;
            else if (*f == '+') plus = 1;
            else if (*f == ' ') space = 1;
            else if (*f != '#') break;
        }
        if (*f == '*') {
            width = va_arg(ap, int);
            if (width < 0) { left = 1; width = -width; }
            f++;
        } else
            while (*f >= '0' && *f <= '9') width = width * 10 + *f++ - '0';
        if (*f == '.') {
            f++;
            prec = 0;
            if (*f == '*') {
                prec = va_arg(ap, int);
                f++;
            } else
                while (*f >= '0' && *f <= '9') prec = prec * 10 + *f++ - '0';
        }
        while (*f == 'l' || *f == 'h' || *f == 'z' || *f == 'j' || *f == 't' || *f == 'q' || *f == 'L') {
            if (*f == 'l' || *f == 'q' || *f == 'j') lng++;
            f++;
        }
        switch (*f) {
        case 'd': case 'i': {
            long long v = lng >= 2 ? va_arg(ap, long long) : (long long)va_arg(ap, long);
            const char *sign = v < 0 ? "-" : plus ? "+" : space ? " " : "";
            put_u(&w, v < 0 ? 0ull - (unsigned long long)v : (unsigned long long)v, 10, 0, sign, width, prec,
                  zero, left);
            break;
        }
        case 'u': case 'x': case 'X': case 'o': {
            unsigned long long v = lng >= 2 ? va_arg(ap, unsigned long long) : va_arg(ap, unsigned long);
            put_u(&w, v, *f == 'u' ? 10 : *f == 'o' ? 8 : 16, *f == 'X', "", width, prec, zero, left);
            break;
        }
        case 'p':
            put_u(&w, (unsigned long)va_arg(ap, void *), 16, 0, "0x", width, -1, 0, left);
            break;
        case 'c':
            if (!left) pad(&w, ' ', width - 1);
            put(&w, (char)va_arg(ap, int));
            if (left) pad(&w, ' ', width - 1);
            break;
        case 's': {
            const char *s = va_arg(ap, const char *);
            int len = 0, k;
            if (!s) s = "(null)";
            while (s[len] && (prec < 0 || len < prec)) len++;
            if (!left) pad(&w, ' ', width - len);
            for (k = 0; k < len; k++) put(&w, s[k]);
            if (left) pad(&w, ' ', width - len);
            break;
        }
        case 'e': case 'E': case 'f': case 'F': case 'g': case 'G': case 'a': case 'A':
            (void)va_arg(ap, double);
            put(&w, '?');
            break;
        case '%':
            put(&w, '%');
            break;
        case 0:
            f--;
            break;
        default:
            put(&w, *f);
        }
    }
    if (max) out[w.n < max ? w.n : max - 1] = 0;
    return (int)w.n;
}

int snprintf(char *out, size_t max, const char *f, ...)
{
    va_list ap;
    int n;
    va_start(ap, f);
    n = vsnprintf(out, max, f, ap);
    va_end(ap);
    return n;
}

/* ---- memoria (malloc y free son de api.c: un pool, con el tamaño delante) ---- */

void *realloc(void *p, size_t n)
{
    void *q;
    size_t old;
    if (!p) return malloc(n);
    if (!n) {
        free(p);
        return NULL;
    }
    old = ((ULONG *)p)[-1] - 4;
    if (n <= old && n + 64 > old) return p;   /* (encoger un poco: se queda) */
    if (!(q = malloc(n))) return NULL;
    memcpy(q, p, n < old ? n : old);
    free(p);
    return q;
}

void *calloc(size_t n, size_t size)
{
    void *p = malloc(n * size);
    if (p) memset(p, 0, n * size);
    return p;
}

void abort(void)
{
    if (Output()) FPuts(Output(), (CONST_STRPTR)"abort\n");
    _dash_quit(20);
}

/* ---- stdio: stdout y stderr a Output() (con su búfer, como Print); los ficheros de fopen, a uno de DOS ---- */

static FILE dash_files[3];
static FILE *dash_sf[3] = {&dash_files[0], &dash_files[1], &dash_files[2]};
FILE **__sF = dash_sf;

/* un fichero de fopen: el FILE de libnix delante (sus macros ven _r y _w a 0 y llaman a las funciones) */
typedef struct { FILE f; BPTR fh; int eof; } DashFile;

static BPTR dash_fh(FILE *f)
{
    if (!f || f == &dash_files[0] || f == &dash_files[1] || f == &dash_files[2]) return Output();
    return ((DashFile *)f)->fh;
}

FILE *fopen(const char *name, const char *mode)
{
    DashFile *d;
    LONG m = mode[0] == 'r' ? MODE_OLDFILE : mode[0] == 'w' ? MODE_NEWFILE : MODE_READWRITE;
    BPTR fh;
    if (mode[0] == 'r' && strchr(mode, '+')) m = MODE_OLDFILE;
    if (!(fh = Open((CONST_STRPTR)name, m))) return NULL;
    if (mode[0] == 'a') Seek(fh, 0, OFFSET_END);
    if (!(d = (DashFile *)AllocVec(sizeof(DashFile), MEMF_CLEAR))) {
        Close(fh);
        return NULL;
    }
    d->fh = fh;
    return &d->f;
}

int fclose(FILE *f)
{
    DashFile *d = (DashFile *)f;
    if (!f || dash_fh(f) == Output()) return 0;
    Close(d->fh);
    FreeVec(d);
    return 0;
}

size_t fread(void *p, size_t size, size_t n, FILE *f)
{
    LONG r;
    if (!size || !n) return 0;
    r = Read(dash_fh(f), p, size * n);
    if (r <= 0) {
        if (dash_fh(f) != Output()) ((DashFile *)f)->eof = 1;
        return 0;
    }
    return (size_t)r / size;
}

int fseek(FILE *f, long off, int whence)
{
    if (dash_fh(f) == Output()) return -1;
    ((DashFile *)f)->eof = 0;
    return Seek(((DashFile *)f)->fh, off, whence == SEEK_SET ? OFFSET_BEGINNING : whence == SEEK_CUR ?
                OFFSET_CURRENT : OFFSET_END) < 0 ? -1 : 0;
}

long ftell(FILE *f)
{
    return dash_fh(f) == Output() ? -1 : Seek(((DashFile *)f)->fh, 0, OFFSET_CURRENT);
}

int setvbuf(FILE *f, char *buf, int mode, size_t size)
{
    (void)f; (void)buf; (void)mode; (void)size;
    return 0;
}

int vfprintf(FILE *f, const char *fmt, va_list ap)
{
    char buf[512];
    int n = vsnprintf(buf, sizeof buf, fmt, ap);
    BPTR fh = dash_fh(f);
    if (fh) FWrite(fh, (APTR)buf, 1, n < (int)sizeof buf ? n : (int)sizeof buf - 1);
    return n;
}

int fprintf(FILE *f, const char *fmt, ...)
{
    va_list ap;
    int n;
    va_start(ap, fmt);
    n = vfprintf(f, fmt, ap);
    va_end(ap);
    return n;
}

int printf(const char *fmt, ...)
{
    va_list ap;
    int n;
    va_start(ap, fmt);
    n = vfprintf(NULL, fmt, ap);
    va_end(ap);
    return n;
}

size_t fwrite(const void *p, size_t size, size_t n, FILE *f)
{
    BPTR fh = dash_fh(f);
    if (fh && size * n) FWrite(fh, (APTR)p, 1, size * n);
    return n;
}

int fputc(int c, FILE *f)
{
    BPTR fh = dash_fh(f);
    if (fh) FPutC(fh, c);
    return c;
}

int fputs(const char *s, FILE *f)
{
    BPTR fh = dash_fh(f);
    if (fh) FPuts(fh, (CONST_STRPTR)s);
    return 0;
}

int puts(const char *s)
{
    if (Output()) {
        FPuts(Output(), (CONST_STRPTR)s);
        FPutC(Output(), '\n');
    }
    return 0;
}

/* ---- más de libc: getenv, strcspn, assert, clock ---- */

char *getenv(const char *name)
{
    static char buf[256];
    return GetVar((CONST_STRPTR)name, (STRPTR)buf, sizeof buf, 0) >= 0 ? buf : NULL;
}

size_t strcspn(const char *s, const char *reject)
{
    size_t n = 0;
    for (; s[n]; n++)
        if (strchr(reject, s[n])) break;
    return n;
}

void __assert_func(const char *file, int line, const char *func, const char *expr)
{
    char b[200];
    snprintf(b, sizeof b, "assert: %s (%s, %s:%d)\n", expr ? expr : "?", func ? func : "?", file ? file : "?", line);
    if (Output()) FPuts(Output(), (CONST_STRPTR)b);
    _dash_quit(20);
}

clock_t clock(void)
{
    /* (los tics de 1/50 s desde la primera llamada, en las unidades de CLOCKS_PER_SEC) */
    static LONG first = -1;
    struct DateStamp d;
    LONG t;
    DateStamp(&d);
    t = (d.ds_Days * 1440 + d.ds_Minute) * 3000 + d.ds_Tick;
    if (first < 0) first = t;
    return (clock_t)((t - first) * (CLOCKS_PER_SEC / 50));
}

/* ---- fecha (la del reloj del sistema, sin zona horaria: como si fuera UTC) ---- */

int gettimeofday(struct timeval *tv, struct timezone *tz)
{
    struct DateStamp d;
    (void)tz;
    DateStamp(&d);
    if (tv) {
        tv->tv_sec = 252460800L + d.ds_Days * 86400L + d.ds_Minute * 60L + d.ds_Tick / 50;   /* 1978 - 1970 */
        tv->tv_usec = (d.ds_Tick % 50) * 20000L;
    }
    return 0;
}

/* días desde el 1-1-1970 y fecha civil (Howard Hinnant) */
static long days_from_civil(long y, long m, long d)
{
    long era, yoe, doy, doe;
    y -= m <= 2;
    era = (y >= 0 ? y : y - 399) / 400;
    yoe = y - era * 400;
    doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1;
    doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    return era * 146097 + doe - 719468;
}

struct tm *gmtime(const time_t *t)
{
    static struct tm r;
    long s = (long)*t, days = s / 86400, sec = s % 86400, era, doe, yoe, doy, mp, y;
    if (sec < 0) {
        sec += 86400;
        days--;
    }
    r.tm_hour = (int)(sec / 3600);
    r.tm_min = (int)(sec / 60 % 60);
    r.tm_sec = (int)(sec % 60);
    r.tm_wday = (int)((days % 7 + 11) % 7);   /* el 1-1-1970 fue jueves */
    days += 719468;
    era = (days >= 0 ? days : days - 146096) / 146097;
    doe = days - era * 146097;
    yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    y = yoe + era * 400;
    doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    mp = (5 * doy + 2) / 153;
    r.tm_mday = (int)(doy - (153 * mp + 2) / 5 + 1);
    r.tm_mon = (int)(mp < 10 ? mp + 2 : mp - 10);
    y += r.tm_mon <= 1;
    r.tm_year = (int)(y - 1900);
    r.tm_yday = (int)(days_from_civil(y, r.tm_mon + 1, r.tm_mday) - days_from_civil(y, 1, 1));
    r.tm_isdst = 0;
    return &r;
}

struct tm *localtime(const time_t *t)
{
    return gmtime(t);
}

time_t mktime(struct tm *tm)
{
    long y = tm->tm_year + 1900L, m = tm->tm_mon, t;
    y += m / 12;
    m %= 12;
    if (m < 0) {
        m += 12;
        y--;
    }
    t = days_from_civil(y, m + 1, 1) + tm->tm_mday - 1;
    t = t * 86400L + tm->tm_hour * 3600L + tm->tm_min * 60L + tm->tm_sec;
    *tm = *gmtime((time_t *)&t);
    return (time_t)t;
}

/* ---- matemáticas (con las de fdlibm del runtime) ---- */

static int is_nan(double x) { return x != x; }

double trunc(double x)
{
    return x < 0 ? -dash_fd_floor(-x) : dash_fd_floor(x);
}

double round(double x)
{
    double a = x < 0 ? -x : x, t = dash_fd_floor(a);
    if (a - t >= 0.5) t += 1.0;
    return x < 0 ? -t : t;
}

long lrint(double x)
{
    double t = dash_fd_floor(x), d = x - t;
    if (d > 0.5 || (d == 0.5 && (long)t % 2 != 0)) t += 1.0;
    return (long)t;
}

double fmax(double a, double b)
{
    if (is_nan(a)) return b;
    if (is_nan(b)) return a;
    return a > b ? a : b;
}

double fmin(double a, double b)
{
    if (is_nan(a)) return b;
    if (is_nan(b)) return a;
    return a < b ? a : b;
}

double log2(double x)
{
    /* x = m * 2^e con m en [1, 2): e + log(m) / log(2), exacto en las potencias de 2 */
    union { double d; unsigned long w[2]; } u;
    long e;
    if (is_nan(x) || x <= 0 || x > 1.7976931348623157e308) return __ieee754_log(x) * 1.4426950408889634;
    u.d = x;
    e = (long)((u.w[0] >> 20) & 0x7FF);
    if (!e) return __ieee754_log(x) * 1.4426950408889634;   /* (subnormal) */
    e -= 1023;
    u.w[0] = (u.w[0] & 0x800FFFFFul) | 0x3FF00000ul;
    return (double)e + __ieee754_log(u.d) * 1.4426950408889634;
}

double asinh(double x)
{
    double a = x < 0 ? -x : x, r;
    if (is_nan(x) || a == 0) return x;
    r = a > 1e150 ? __ieee754_log(a) + 0.6931471805599453 : __ieee754_log(a + __ieee754_sqrt(a * a + 1.0));
    return x < 0 ? -r : r;
}

double acosh(double x)
{
    if (x > 1e150) return __ieee754_log(x) + 0.6931471805599453;
    return __ieee754_log(x + __ieee754_sqrt(x * x - 1.0));
}

double atanh(double x)
{
    return 0.5 * __ieee754_log((1.0 + x) / (1.0 - x));
}

/* los nombres de libm (el fdlibm del runtime los lleva con otro nombre: dash_fd_*, __ieee754_*) */
double dash_fd_ceil(double);
double dash_fd_sin(double);
double dash_fd_cos(double);
double dash_fd_tan(double);
double dash_fd_atan(double);
double dash_fd_fabs(double);
double __ieee754_log10(double);
double __ieee754_exp(double);
double __ieee754_pow(double, double);
double __ieee754_fmod(double, double);
double __ieee754_acos(double);
double __ieee754_asin(double);
double __ieee754_atan2(double, double);

double floor(double x) { return dash_fd_floor(x); }
double ceil(double x) { return dash_fd_ceil(x); }
double fabs(double x) { return dash_fd_fabs(x); }
double sin(double x) { return dash_fd_sin(x); }
double cos(double x) { return dash_fd_cos(x); }
double tan(double x) { return dash_fd_tan(x); }
double atan(double x) { return dash_fd_atan(x); }
double sqrt(double x) { return __ieee754_sqrt(x); }
double log(double x) { return __ieee754_log(x); }
double log10(double x) { return __ieee754_log10(x); }
double exp(double x) { return __ieee754_exp(x); }
double pow(double x, double y) { return __ieee754_pow(x, y); }
double fmod(double x, double y) { return __ieee754_fmod(x, y); }
double acos(double x) { return __ieee754_acos(x); }
double asin(double x) { return __ieee754_asin(x); }
double atan2(double y, double x) { return __ieee754_atan2(y, x); }

/* ---- números de un texto, ordenar y sscanf (nanosvg) ---- */

long long strtoll(const char *s, char **end, int base)
{
    const char *p = s;
    unsigned long long v = 0;
    int neg = 0, any = 0;
    while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r' || *p == '\f' || *p == '\v') p++;
    if (*p == '-' || *p == '+') neg = *p++ == '-';
    if ((base == 0 || base == 16) && p[0] == '0' && (p[1] == 'x' || p[1] == 'X')) {
        p += 2;
        base = 16;
    } else if (base == 0) {
        base = *p == '0' ? 8 : 10;
    }
    for (;; p++, any = 1) {
        int d = *p >= '0' && *p <= '9' ? *p - '0' : *p >= 'a' && *p <= 'z' ? *p - 'a' + 10 :
                *p >= 'A' && *p <= 'Z' ? *p - 'A' + 10 : 99;
        if (d >= base) break;
        v = v * base + d;
    }
    if (end) *end = (char *)(any ? p : s);
    return neg ? -(long long)v : (long long)v;
}

long strtol(const char *s, char **end, int base)
{
    return (long)strtoll(s, end, base);
}

unsigned long strtoul(const char *s, char **end, int base)
{
    return (unsigned long)strtoll(s, end, base);
}

void qsort(void *base, size_t n, size_t size, int (*cmp)(const void *, const void *))
{
    /* (Shell: sin recursión ni memoria aparte; los saltos de Ciura) */
    static const size_t gaps[] = {701, 301, 132, 57, 23, 10, 4, 1};
    unsigned char *a = (unsigned char *)base, tmp[64];
    size_t g, i, j, k;
    if (size > sizeof tmp) {
        /* elementos grandes: inserción con intercambios de byte en byte */
        for (i = 1; i < n; i++)
            for (j = i; j > 0 && cmp(a + (j - 1) * size, a + j * size) > 0; j--)
                for (k = 0; k < size; k++) {
                    unsigned char c = a[(j - 1) * size + k];
                    a[(j - 1) * size + k] = a[j * size + k];
                    a[j * size + k] = c;
                }
        return;
    }
    for (g = 0; g < sizeof gaps / sizeof gaps[0]; g++) {
        size_t gap = gaps[g];
        while (gap * 3 < n && g == 0 && gap < n / 3) gap = gap * 9 / 4;   /* (más saltos para listas largas) */
        for (i = gap; i < n; i++) {
            memcpy(tmp, a + i * size, size);
            for (j = i; j >= gap && cmp(a + (j - gap) * size, tmp) > 0; j -= gap)
                memcpy(a + j * size, a + (j - gap) * size, size);
            memcpy(a + j * size, tmp, size);
        }
    }
}

/* sscanf con lo que usa nanosvg: espacios, texto literal y %d %u %x con anchura */
int sscanf(const char *s, const char *f, ...)
{
    va_list ap;
    int n = 0;
    va_start(ap, f);
    for (; *f; f++) {
        if (*f == ' ') {
            while (*s == ' ' || *s == '\t' || *s == '\n' || *s == '\r') s++;
            continue;
        }
        if (*f != '%') {
            if (*s != *f) break;
            s++;
            continue;
        }
        f++;
        if (*f == '%') {
            if (*s++ != '%') break;
            continue;
        }
        {
            int width = 0, base, neg = 0, got = 0;
            long v = 0;
            while (*f >= '0' && *f <= '9') width = width * 10 + *f++ - '0';
            while (*f == 'l' || *f == 'h') f++;
            base = *f == 'x' || *f == 'X' ? 16 : 10;
            if (*f != 'd' && *f != 'i' && *f != 'u' && *f != 'x' && *f != 'X') break;
            if (base == 10) while (*s == ' ' || *s == '\t' || *s == '\n' || *s == '\r') s++;
            if (base == 10 && (*s == '-' || *s == '+')) {
                neg = *s++ == '-';
                if (width) width--;
            }
            for (;;) {
                int d = *s >= '0' && *s <= '9' ? *s - '0' : *s >= 'a' && *s <= 'f' ? *s - 'a' + 10 :
                        *s >= 'A' && *s <= 'F' ? *s - 'A' + 10 : 99;
                if (d >= base || (width && got >= width)) break;
                v = v * base + d;
                s++;
                got++;
            }
            if (!got) break;
            *va_arg(ap, int *) = (int)(neg ? -v : v);
            n++;
        }
    }
    va_end(ap);
    return n;
}

/* ---- lo que pide Hubbub (el HTML5 de Tachyon) y otros: bsearch, strncasecmp y la tabla de ctype de libnix
   (sus macros isalpha... la leen: el EOF delante y los 256 caracteres; ASCII, la configuración C) ---- */

const char _ctype_[1 + 256] = {
    0, 32, 32, 32, 32, 32, 32, 32, 32, 32, 40, 40, 40, 40, 40, 32,
    32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
    32, 136, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    16, 68, 68, 68, 68, 68, 68, 68, 68, 68, 68, 16, 16, 16, 16, 16,
    16, 16, 65, 65, 65, 65, 65, 65, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 16, 16, 16, 16,
    16, 16, 66, 66, 66, 66, 66, 66, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 16, 16, 16, 16,
    32, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0
};

static int dash_lower(int c) { return c >= 'A' && c <= 'Z' ? c + 32 : c; }

int strncasecmp(const char *a, const char *b, size_t n)
{
    for (; n; n--, a++, b++) {
        int x = dash_lower((unsigned char)*a), y = dash_lower((unsigned char)*b);
        if (x != y || !x) return x - y;
    }
    return 0;
}

int strcasecmp(const char *a, const char *b)
{
    return strncasecmp(a, b, (size_t)-1);
}

void *bsearch(const void *key, const void *base, size_t n, size_t size, int (*cmp)(const void *, const void *))
{
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        const void *p = (const char *)base + mid * size;
        int r = cmp(key, p);
        if (!r) return (void *)p;
        if (r < 0) hi = mid;
        else lo = mid + 1;
    }
    return NULL;
}

/* las de float de libm, sobre las de double (el fdlibm del runtime) */
double dash_fd_sin(double);
double dash_fd_cos(double);
double dash_fd_tan(double);
double dash_fd_ceil(double);
double __ieee754_exp(double);

float sqrtf(float x) { return (float)__ieee754_sqrt(x); }
float floorf(float x) { return (float)dash_fd_floor(x); }
float ceilf(float x) { return (float)dash_fd_ceil(x); }
float roundf(float x) { return x < 0 ? -(float)dash_fd_floor(0.5 - x) : (float)dash_fd_floor(x + 0.5); }
float fabsf(float x) { return x < 0 ? -x : x; }
float sinf(float x) { return (float)dash_fd_sin(x); }
float cosf(float x) { return (float)dash_fd_cos(x); }
float tanf(float x) { return (float)dash_fd_tan(x); }
float atan2f(float y, float x) { return (float)__ieee754_atan2(y, x); }
float acosf(float x) { return (float)__ieee754_acos(x); }
float powf(float x, float y) { return (float)__ieee754_pow(x, y); }
float expf(float x) { return (float)__ieee754_exp(x); }
float logf(float x) { return (float)__ieee754_log(x); }
