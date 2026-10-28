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

/* ---- stdio, a Output() ---- */

static FILE dash_files[3];
static FILE *dash_sf[3] = {&dash_files[0], &dash_files[1], &dash_files[2]};
FILE **__sF = dash_sf;

int vfprintf(FILE *f, const char *fmt, va_list ap)
{
    char buf[512];
    int n = vsnprintf(buf, sizeof buf, fmt, ap);
    (void)f;
    if (Output()) FWrite(Output(), (APTR)buf, 1, n < (int)sizeof buf ? n : (int)sizeof buf - 1);
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
    (void)f;
    if (Output() && size * n) FWrite(Output(), (APTR)p, 1, size * n);
    return n;
}

int fputc(int c, FILE *f)
{
    (void)f;
    if (Output()) FPutC(Output(), c);
    return c;
}

int fputs(const char *s, FILE *f)
{
    (void)f;
    if (Output()) FPuts(Output(), (CONST_STRPTR)s);
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
