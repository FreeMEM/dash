/* Ficheros y cajones de Dash en DashOS (docs/DASHOS_VENTANAS_LOOP.md, fase 2): lo que el runtime toma de dos.library
   (Open, Read, Write, Seek, Lock, Examine, ExNext, CreateDir, DeleteFile, Rename...), sobre el servicio "archivos" de
   DashOS (docs/referencia/servicios.md de DashOS) o, con DASH_PLAT_LINUX, sobre las llamadas de Linux (qemu-aarch64).
   Va al final de plat.c (#include): usa sus llamadas al sistema y su memoria.

   Un nombre del Amiga ("LOCALE:Catalogs/x", "lista.txt") es un sitio: una raíz y un camino desde ella. Provisional
   hasta que el runtime lea las asignaciones de DashOS (rama "asignaciones", ya en revision):
   - DashOS: SYS: y PROGDIR: son la raíz del cliente (asa 0), LOCALE: su cajón Locale; Elegido: el fichero que eligió el
     usuario en el selector y Carpeta: la carpeta que eligió para guardar (dash_plat_choose). Sin volumen, desde el
     cajón actual (CurrentDir; al empezar, la raíz).
   - Linux: X: es $DASH_X_DIR (DASH_RAM_DIR, DASH_T_DIR, DASH_ENV_DIR...); sin ella, LOCALE: es Locale y SYS: y
     PROGDIR: el cajón actual; los demás no están.
   Un camino que sube ("/x", "a//b") no vale. */

#define DOS_CAMINO 256

typedef struct { long root; char path[DOS_CAMINO]; } DSitio;
typedef struct { long size, date, type, prot; char comment[80]; } DInfo;   /* type: 1 fichero, 2 cajón, 3 enlace */

/* La protección del Amiga (fib_Protection: 0-3 d e w r puestos = no se puede; 4 a, 5 p, 6 s, 7 h) desde los permisos de
   Unix del dueño y los bits del Amiga del servicio de archivos (1 a, 2 p, 4 s, 8 h, 16 no borrar), y al revés */
static long dos_prot(long modo, long amiga)
{
    return (modo & 0400 ? 0 : 8) | (modo & 0200 ? 0 : 4) | (modo & 0100 ? 0 : 2) | (amiga & 16 ? 1 : 0) |
           (amiga & 1 ? 16 : 0) | (amiga & 2 ? 32 : 0) | (amiga & 4 ? 64 : 0) | (amiga & 8 ? 128 : 0);
}
static long dos_modo(long prot, long modo) { return (modo & 07077) | (prot & 8 ? 0 : 0400) | (prot & 4 ? 0 : 0200) | (prot & 2 ? 0 : 0100); }
static long __attribute__((unused)) dos_amiga(long prot)
{
    return (prot & 16 ? 1 : 0) | (prot & 32 ? 2 : 0) | (prot & 64 ? 4 : 0) | (prot & 128 ? 8 : 0) | (prot & 1 ? 16 : 0);
}

/* Junta base y resto en out ("a" + "b/c" = "a/b/c"), sin '/' de más; 0 si no cabe o el resto sube */
static int dos_juntar(const char *base, const char *resto, char *out)
{
    unsigned long n = 0;
    const char *p;
    if (*resto == '/') return 0;
    for (p = resto; *p; p++)
        if (*p == '/' && p[1] == '/') return 0;
    for (; *base && n + 1 < DOS_CAMINO; base++) out[n++] = *base;
    if (n && out[n - 1] != '/' && *resto && n + 1 < DOS_CAMINO) out[n++] = '/';
    for (; *resto && n + 1 < DOS_CAMINO; resto++) out[n++] = *resto;
    if (*base || *resto) return 0;
    while (n && out[n - 1] == '/') n--;
    out[n] = 0;
    return 1;
}

typedef struct DLock DLock;
static DLock *dos_actual;                 /* CurrentDir: NULL, la raíz (o el cajón actual de Linux) */
static int dos_sitio(const char *name, DSitio *s);

/* El último nombre de un camino */
static const char *dos_ultimo(const char *path)
{
    const char *u = path, *p;
    for (p = path; *p; p++)
        if (*p == '/' || *p == ':') u = p + 1;
    return u;
}

#ifdef DASH_PLAT_LINUX
/* ======== Linux ======== */
#define L_AT_FDCWD (-100)

/* Una variable del entorno, de /proc/self/environ (el programa no guarda su pila de arranque); NULL si no está */
const char *dash_plat_getenv(const char *name)
{
    static char env[8192];
    static long len = -1;
    long i, n = (long)strlen(name);
    if (len < 0) {
        long fd = _svc(56, L_AT_FDCWD, (long)"/proc/self/environ", 0, 0, 0, 0), r;   /* openat */
        len = 0;
        if (fd >= 0) {
            while (len < (long)sizeof env - 1 && (r = _svc(63, fd, (long)env + len, (long)sizeof env - 1 - len, 0, 0, 0)) > 0)
                len += r;
            _svc(57, fd, 0, 0, 0, 0, 0);
        }
        env[len] = 0;
    }
    for (i = 0; i < len; i += (long)strlen(env + i) + 1)
        if (!strncmp(env + i, name, (size_t)n) && env[i + n] == '=') return env + i + n + 1;
    return NULL;
}

static int dos_volumen(const char *vol, const char *resto, DSitio *s)
{
    char var[48];
    const char *base;
    if (strlen(vol) > 30) return 0;
    strcpy(var, "DASH_");
    strcat(var, vol);
    strcat(var, "_DIR");
    if (!(base = dash_plat_getenv(var))) {
        if (!strcmp(vol, "LOCALE")) base = "Locale";
        else if (!strcmp(vol, "SYS") || !strcmp(vol, "PROGDIR")) base = ".";
        else return 0;
    }
    s->root = L_AT_FDCWD;
    return dos_juntar(base, resto, s->path);
}

static const char *l_camino(const DSitio *s) { return s->path[0] ? s->path : "."; }

/* struct stat de Linux en AArch64 (128 bytes) */
typedef struct { unsigned long dev, ino; unsigned mode, nlink, uid, gid; unsigned long rdev, pad1; long size; int blksize, pad2;
                 long blocks, atime, atime_ns, mtime, mtime_ns, ctime, ctime_ns; unsigned u4, u5; } LStat;

static void l_info(const LStat *st, DInfo *d)
{
    long t = st->mode & 0170000;
    d->size = st->size;
    d->date = st->mtime;
    d->type = t == 0040000 ? 2 : t == 0120000 ? 3 : 1;
    d->prot = dos_prot(st->mode, 0);
    d->comment[0] = 0;
}

/* El comentario, en Linux, en el atributo extendido user.amiga.comment (si el sistema de archivos los tiene) */
static void l_comentario(long dir, const char *path, DInfo *d)
{
    char p[DOS_CAMINO + 2];
    long n;
    if (dir != L_AT_FDCWD) return;
    strcpy(p, path);
    n = _svc(8, (long)p, (long)"user.amiga.comment", (long)d->comment, sizeof d->comment - 1, 0, 0);   /* getxattr */
    d->comment[n > 0 ? n : 0] = 0;
}

static long ds_stat(const DSitio *s, DInfo *d)
{
    LStat st;
    if (_svc(79, s->root, (long)l_camino(s), (long)&st, 0, 0, 0) < 0) return -2;   /* newfstatat */
    l_info(&st, d);
    l_comentario(s->root, l_camino(s), d);
    return 0;
}

/* modo: 0 leer, 1 nuevo (vacío), 2 leer y escribir (lo crea si no está) */
static long ds_open(const DSitio *s, int modo, long *h)
{
    LStat st;
    long fl = modo == 0 ? 0 : modo == 1 ? 2 | 0100 | 01000 : 2 | 0100;   /* O_RDONLY, O_RDWR|O_CREAT|O_TRUNC... */
    long fd = _svc(56, s->root, (long)l_camino(s), fl | 02000000, 0666, 0, 0);   /* (O_CLOEXEC) */
    if (fd < 0) return fd;
    if (_svc(80, fd, (long)&st, 0, 0, 0, 0) < 0 || (st.mode & 0170000) == 0040000) {   /* un cajón no se abre */
        _svc(57, fd, 0, 0, 0, 0, 0);
        return -4;
    }
    *h = fd;
    return 0;
}
static long ds_pread(long h, long off, void *buf, long n) { return _svc(67, h, (long)buf, n, off, 0, 0); }
static long ds_pwrite(long h, long off, const void *buf, long n) { return _svc(68, h, (long)buf, n, off, 0, 0); }
static long ds_size(long h)
{
    LStat st;
    return _svc(80, h, (long)&st, 0, 0, 0, 0) < 0 ? -1 : st.size;
}
static void ds_close(long h) { _svc(57, h, 0, 0, 0, 0, 0); }
static long ds_mkdir(const DSitio *s) { return _svc(34, s->root, (long)l_camino(s), 0777, 0, 0, 0); }
static long ds_delete(const DSitio *s)
{
    long r = _svc(35, s->root, (long)l_camino(s), 0, 0, 0, 0);
    return r == -21 ? _svc(35, s->root, (long)l_camino(s), 0x200, 0, 0, 0) : r;   /* EISDIR: AT_REMOVEDIR */
}
static long ds_rename(const DSitio *a, const DSitio *b)
{
    return _svc(276, a->root, (long)l_camino(a), b->root, (long)l_camino(b), 1, 0);   /* renameat2, sin sobrescribir */
}
static long ds_protect(const DSitio *s, long prot)
{
    LStat st;
    if (_svc(79, s->root, (long)l_camino(s), (long)&st, 0, 0, 0) < 0) return -2;
    return _svc(53, s->root, (long)l_camino(s), dos_modo(prot, st.mode), 0, 0, 0);   /* fchmodat */
}
static long ds_comment(const DSitio *s, const char *t)
{
    long r;
    if (*t) return _svc(5, (long)l_camino(s), (long)"user.amiga.comment", (long)t, (long)strlen(t), 0, 0);   /* setxattr */
    r = _svc(14, (long)l_camino(s), (long)"user.amiga.comment", 0, 0, 0, 0);   /* removexattr */
    return r == -61 ? 0 : r;                                                    /* (ENODATA: no tenía) */
}
static long ds_setdate(const DSitio *s, long t)
{
    long ts[4] = { 0, (1L << 30) - 2, t, 0 };     /* el acceso igual (UTIME_OMIT), la modificación t */
    return _svc(88, s->root, (long)l_camino(s), (long)ts, 0, 0, 0);
}

/* Lo que tiene un cajón, entrada a entrada */
typedef struct { long h; unsigned char buf[4096]; long len, off; int fin; char camino[DOS_CAMINO]; } DList;
static long ds_list_open(const DSitio *s, DList *l)
{
    strcpy(l->camino, l_camino(s));
    l->h = _svc(56, s->root, (long)l_camino(s), 040000 | 02000000, 0, 0, 0);   /* O_DIRECTORY (el de AArch64) */
    l->len = l->off = 0;
    l->fin = 0;
    return l->h < 0 ? l->h : 0;
}
static int ds_list_next(DList *l, char *name, DInfo *d)
{
    for (;;) {
        unsigned char *e;
        LStat st;
        if (l->off >= l->len) {
            if (l->fin) return 0;
            l->len = _svc(61, l->h, (long)l->buf, sizeof l->buf, 0, 0, 0);   /* getdents64 */
            l->off = 0;
            if (l->len <= 0) { l->fin = 1; return 0; }
        }
        e = l->buf + l->off;
        l->off += *(unsigned short *)(e + 16);
        if (!strcmp((char *)e + 19, ".") || !strcmp((char *)e + 19, "..") || strlen((char *)e + 19) > 107) continue;
        if (_svc(79, l->h, (long)(e + 19), (long)&st, 0x100, 0, 0) < 0) continue;   /* (AT_SYMLINK_NOFOLLOW) */
        strcpy(name, (char *)e + 19);
        l_info(&st, d);
        if (strlen(l->camino) + strlen(name) + 2 < DOS_CAMINO) {
            char p[DOS_CAMINO];
            strcpy(p, l->camino);
            strcat(p, "/");
            strcat(p, name);
            l_comentario(L_AT_FDCWD, p, d);
        }
        return 1;
    }
}
static void ds_list_close(DList *l) { if (l->h >= 0) _svc(57, l->h, 0, 0, 0, 0, 0); }

static int ds_nombre(const DSitio *s, char *out, long cap)
{
    if (!s->path[0] || !strcmp(s->path, ".")) return _svc(17, (long)out, cap, 0, 0, 0, 0) > 0;   /* getcwd */
    if ((long)strlen(s->path) >= cap) return 0;
    strcpy(out, s->path);
    return 1;
}

long dash_plat_choose(int save) { (void)save; return -1; }   /* (no hay selector en Linux) */

#else
/* ======== DashOS: el servicio "archivos" ======== */
const char *dash_plat_getenv(const char *name) { (void)name; return NULL; }

/* El servicio de archivos, por la llave 2 (la de lo que lanza `sesiones` y la que da `inicio` a dash-ventana): una
   sesión con su canal de respuesta y su ventana de 64 KB. Órdenes y respuestas, en little-endian. */
#define ARCH_LLAVE 2
#define ARCH_VENTANA 0x4800000000UL
enum { A_SESION = 0, A_BUSCAR = 1, A_LEER = 2, A_ESCRIBIR = 3, A_LISTAR = 4, A_DATOS = 5, A_CERRAR = 6, A_CREAR = 7,
       A_BORRAR = 8, A_RENOMBRAR = 9, A_TAMANO = 10, A_COMENTARIO = 13, A_COMENTAR = 14, A_PROTEGER = 15, A_FECHAR = 35 };
static long arch_resp = 0;                         /* el lado que lee las respuestas; < 0, no hay servicio */
static unsigned long arch_win = 0;
static long dos_elegido = 0;                       /* la asa del fichero que eligió el usuario (Elegido:) */
static long dos_carpeta = 0;                       /* la raíz de la carpeta que eligió para guardar (Carpeta:) */

static void arch_pon(unsigned char *p, unsigned long v, int n) { while (n--) { *p++ = (unsigned char)v; v >>= 8; } }
static long arch_toma(const unsigned char *p, int n)
{
    unsigned long v = 0;
    while (n--) v = v << 8 | p[n];
    return (long)v;
}

/* Una orden: el estado (0 bien, < 0 el error del servicio); en r, a, b, c y la asa de la respuesta */
static long arch_orden(unsigned orden, long asa, long a, long b, const char *nombre, long n, long r[4])
{
    unsigned char m[256], resp[64];
    long got, out[2];
    if (n < 0 || n > 224) return -1;
    memset(m, 0, 32);
    arch_pon(m, orden, 4);
    arch_pon(m + 4, (unsigned long)asa, 4);
    arch_pon(m + 8, (unsigned long)a, 8);
    arch_pon(m + 16, (unsigned long)b, 8);
    arch_pon(m + 24, (unsigned long)n, 4);
    if (n) memcpy(m + 32, nombre, (unsigned long)n);
    if (dash_os_call(4, ARCH_LLAVE, (long)m, 32 + n, 0, 0, out) < 0) return -1;
    got = dash_os_call(5, arch_resp, (long)resp, sizeof resp, 0, 0, out);
    if (got < 32) return -1;
    r[0] = arch_toma(resp + 8, 8);
    r[1] = arch_toma(resp + 16, 8);
    r[2] = arch_toma(resp + 24, 8);
    r[3] = arch_toma(resp + 4, 4);
    return (long)(int)arch_toma(resp, 4);
}

static int arch_abrir(void)
{
    long out[2], a, got;
    unsigned b, ll[4];
    unsigned char m[32], r[64];
    if (arch_resp) return arch_resp > 0;
    arch_resp = -1;
    a = dash_os_call(3, 0, 0, 0, 0, 0, out);          /* canal_crear */
    if (a <= 0) return 0;
    b = (unsigned)out[0];
    memset(m, 0, sizeof m);                          /* orden 0, la sesión: con el lado de escribir de la respuesta */
    if (dash_os_call(4, ARCH_LLAVE, (long)m, 32, (long)&b, 1, out) < 0 ||
        (got = dash_os_call(5, a, (long)r, sizeof r, (long)ll, 4, out)) < 32 || arch_toma(r, 4) != 0 || out[0] <= 0 ||
        dash_os_call(8, ll[0], (long)ARCH_VENTANA, 3, 0, 0, out) != 0) {   /* (3: leer y escribir) */
        _svc(6, a, 0, 0, 0, 0, 0);
        return 0;
    }
    arch_win = (unsigned long)arch_toma(r + 8, 8);
    arch_resp = a;
    return arch_win > 0;
}

static int dos_volumen(const char *vol, const char *resto, DSitio *s)
{
    if (!strcmp(vol, "SYS") || !strcmp(vol, "PROGDIR")) s->root = 0;
    else if (!strcmp(vol, "LOCALE")) { s->root = 0; return dos_juntar("Locale", resto, s->path); }
    else if (!strcmp(vol, "CARPETA") && dos_carpeta) s->root = dos_carpeta;
    else if (!strcmp(vol, "ELEGIDO") && dos_elegido && !*resto) s->root = dos_elegido;
    else return 0;
    return dos_juntar("", resto, s->path);
}

static void a_info(const long r[4], DInfo *d)
{
    long t = (r[2] >> 16) & 0xFFFF;
    d->size = r[0];
    d->date = r[1];
    d->type = t;
    d->prot = dos_prot(r[2] & 07777, (r[2] >> 32) & 0xFFFF);
    d->comment[0] = 0;
}

/* Abre el sitio (su asa nueva en *h) */
static long a_buscar(const DSitio *s, long *h, long r[4])
{
    long e;
    if (!arch_abrir()) return -1;
    e = arch_orden(A_BUSCAR, s->root, 0, 0, s->path, (long)strlen(s->path), r);
    if (e == 0) *h = r[3];
    return e;
}

/* El cajón de arriba del sitio, abierto (*h; lo cierra quien llama) y el último nombre */
static long a_padre(const DSitio *s, long *h, const char **ultimo)
{
    DSitio p = *s;
    char *u = NULL, *q;
    long r[4];
    for (q = p.path; *q; q++)
        if (*q == '/') u = q;
    *ultimo = s->path + (u ? u - p.path + 1 : 0);
    if (!**ultimo) return -1;
    if (u) *u = 0; else p.path[0] = 0;
    return a_buscar(&p, h, r);
}

static long ds_stat(const DSitio *s, DInfo *d)
{
    long r[4], e;
    if (!arch_abrir()) return -1;
    e = arch_orden(A_BUSCAR, s->root, 1, 0, s->path, (long)strlen(s->path), r);   /* (a = 1: solo los datos) */
    if (e == 0) a_info(r, d);
    return e;
}

/* El comentario de un sitio (para Examine: listar ya lo trae) */
static void a_comentario(const DSitio *s, DInfo *d)
{
    long h, r[4], n;
    if (a_buscar(s, &h, r) != 0) return;
    if (arch_orden(A_COMENTARIO, h, 0, 0, NULL, 0, r) == 0 && (n = r[0]) > 0) {
        if (n > 79) n = 79;
        memcpy(d->comment, (void *)ARCH_VENTANA, (unsigned long)n);
        d->comment[n] = 0;
    }
    arch_orden(A_CERRAR, h, 0, 0, NULL, 0, r);
}

static long ds_open(const DSitio *s, int modo, long *h)
{
    long r[4], e = a_buscar(s, h, r), p;
    const char *u;
    if (e == 0) {
        if (((r[2] >> 16) & 0xFFFF) == 2) { arch_orden(A_CERRAR, *h, 0, 0, NULL, 0, r); return -4; }
        if (modo == 1 && r[0] && (e = arch_orden(A_TAMANO, *h, 0, 0, NULL, 0, r)) != 0)
            arch_orden(A_CERRAR, *h, 0, 0, NULL, 0, r);
        return e;
    }
    if (e != -2 || modo == 0) return e;
    if ((e = a_padre(s, &p, &u)) != 0) return e;         /* no está: se crea en su cajón */
    e = arch_orden(A_CREAR, p, 1, 0, u, (long)strlen(u), r);
    if (e == 0) *h = r[3];
    arch_orden(A_CERRAR, p, 0, 0, NULL, 0, r);
    return e;
}

static long ds_pread(long h, long off, void *buf, long n)
{
    long hecho = 0, r[4], k;
    while (hecho < n) {
        k = n - hecho > (long)arch_win ? (long)arch_win : n - hecho;
        if (arch_orden(A_LEER, h, off + hecho, k, NULL, 0, r) != 0) return hecho ? hecho : -1;
        if (r[0] <= 0) break;
        if (r[0] > k) r[0] = k;
        memcpy((char *)buf + hecho, (void *)ARCH_VENTANA, (unsigned long)r[0]);
        hecho += r[0];
        if (r[0] < k) break;
    }
    return hecho;
}
static long ds_pwrite(long h, long off, const void *buf, long n)
{
    long hecho = 0, r[4], k;
    while (hecho < n) {
        k = n - hecho > (long)arch_win ? (long)arch_win : n - hecho;
        memcpy((void *)ARCH_VENTANA, (const char *)buf + hecho, (unsigned long)k);
        if (arch_orden(A_ESCRIBIR, h, off + hecho, k, NULL, 0, r) != 0 || r[0] <= 0) return hecho ? hecho : -1;
        hecho += r[0];
    }
    return hecho;
}
static long ds_size(long h)
{
    long r[4];
    return arch_orden(A_DATOS, h, 0, 0, NULL, 0, r) == 0 ? r[0] : -1;
}
static void ds_close(long h)
{
    long r[4];
    if (h != dos_elegido) arch_orden(A_CERRAR, h, 0, 0, NULL, 0, r);
}

static long ds_mkdir(const DSitio *s)
{
    long p, r[4], e;
    const char *u;
    if ((e = a_padre(s, &p, &u)) != 0) return e;
    e = arch_orden(A_CREAR, p, 2, 0, u, (long)strlen(u), r);
    if (e == 0) arch_orden(A_CERRAR, r[3], 0, 0, NULL, 0, r);
    arch_orden(A_CERRAR, p, 0, 0, NULL, 0, r);
    return e;
}
static long ds_delete(const DSitio *s)
{
    long p, r[4], e;
    const char *u;
    if ((e = a_padre(s, &p, &u)) != 0) return e;
    e = arch_orden(A_BORRAR, p, 0, 0, u, (long)strlen(u), r);
    arch_orden(A_CERRAR, p, 0, 0, NULL, 0, r);
    return e;
}
static long ds_rename(const DSitio *a, const DSitio *b)
{
    long pa, pb, r[4], e, na, nb;
    const char *ua, *ub;
    char m[224];
    if ((e = a_padre(a, &pa, &ua)) != 0) return e;
    if ((e = a_padre(b, &pb, &ub)) != 0) { arch_orden(A_CERRAR, pa, 0, 0, NULL, 0, r); return e; }
    na = (long)strlen(ua);
    nb = (long)strlen(ub);
    if (na + 1 + nb > (long)sizeof m) e = -1;
    else {
        memcpy(m, ua, (unsigned long)na);
        m[na] = 0;
        memcpy(m + na + 1, ub, (unsigned long)nb);
        e = arch_orden(A_RENOMBRAR, pa, 0, pb, m, na + 1 + nb, r);
    }
    arch_orden(A_CERRAR, pa, 0, 0, NULL, 0, r);
    arch_orden(A_CERRAR, pb, 0, 0, NULL, 0, r);
    return e;
}
static long ds_protect(const DSitio *s, long prot)
{
    long h, r[4], e = a_buscar(s, &h, r);
    if (e != 0) return e;
    e = arch_orden(A_PROTEGER, h, dos_amiga(prot), dos_modo(prot, r[2] & 07777), NULL, 0, r);
    arch_orden(A_CERRAR, h, 0, 0, NULL, 0, r);
    return e;
}
static long ds_comment(const DSitio *s, const char *t)
{
    long h, r[4], e = a_buscar(s, &h, r);
    if (e != 0) return e;
    e = arch_orden(A_COMENTAR, h, 0, 0, t, (long)strlen(t), r);
    arch_orden(A_CERRAR, h, 0, 0, NULL, 0, r);
    return e;
}
static long ds_setdate(const DSitio *s, long t)       /* (FECHAR: a, segundos desde 1970; b, nanosegundos) */
{
    long h, r[4], e = a_buscar(s, &h, r);
    if (e != 0) return e;
    e = arch_orden(A_FECHAR, h, t, 0, NULL, 0, r);
    arch_orden(A_CERRAR, h, 0, 0, NULL, 0, r);
    return e;
}

/* Lo que tiene un cajón: el servicio pone en la ventana las entradas desde la número "desde", y se copian aquí */
typedef struct { long h; unsigned char *buf; long len, off, quedan, sig; int fin; } DList;
static long ds_list_open(const DSitio *s, DList *l)
{
    long r[4];
    l->buf = NULL;
    l->len = l->off = l->quedan = l->sig = 0;
    l->fin = 0;
    return a_buscar(s, &l->h, r);
}
static int ds_list_next(DList *l, char *name, DInfo *d)
{
    long r[4];
    for (;;) {
        unsigned char *e;
        long largo, lcom, total;
        if (!l->quedan) {
            if (l->fin) return 0;
            if (!l->buf && !(l->buf = AllocVec((ULONG)arch_win, MEMF_ANY))) return 0;
            if (arch_orden(A_LISTAR, l->h, l->sig, 0, NULL, 0, r) != 0 || r[0] <= 0) { l->fin = 1; return 0; }
            l->len = r[2] > (long)arch_win ? (long)arch_win : r[2];
            memcpy(l->buf, (void *)ARCH_VENTANA, (unsigned long)l->len);
            l->off = 0;
            l->quedan = r[0];
            l->sig = r[1];
            l->fin = r[1] == -1;
        }
        if (l->off + 24 > l->len) { l->quedan = 0; continue; }
        e = l->buf + l->off;
        largo = e[19];
        lcom = e[22];
        total = 24 + largo + lcom;
        if (l->off + total > l->len) { l->quedan = 0; continue; }
        l->off += (total + 7) & ~7L;
        l->quedan--;
        if (!largo || largo > 107 || (largo == 1 && e[24] == '.') || (largo == 2 && e[24] == '.' && e[25] == '.'))
            continue;
        memcpy(name, e + 24, (unsigned long)largo);
        name[largo] = 0;
        d->size = arch_toma(e, 8);
        d->date = arch_toma(e + 8, 8);
        d->type = e[18];
        d->prot = dos_prot(arch_toma(e + 16, 2) & 07777, arch_toma(e + 20, 2));
        if (lcom > 79) lcom = 79;
        memcpy(d->comment, e + 24 + largo, (unsigned long)lcom);
        d->comment[lcom] = 0;
        return 1;
    }
}
static void ds_list_close(DList *l)
{
    long r[4];
    arch_orden(A_CERRAR, l->h, 0, 0, NULL, 0, r);
    if (l->buf) FreeVec(l->buf);
}

static int ds_nombre(const DSitio *s, char *out, long cap)
{
    const char *vol = s->root == 0 ? "SYS:" : s->root == dos_carpeta ? "Carpeta:" : "Elegido:";
    if ((long)(strlen(vol) + strlen(s->path)) >= cap) return 0;
    strcpy(out, vol);
    strcat(out, s->path);
    return 1;
}

/* El selector de ficheros de DashOS (usuario/src/bin/selector.rs): el usuario elige en su ventana un fichero para leer
   (lo cede como asa: Elegido:) o, para guardar, una carpeta (la cede como raíz 3, para leer y escribir: Carpeta:). 1 si
   eligió, 0 si no, -1 sin selector. Por la llave 4, si el programa nació con 4 (plat.c, _dash_keys_at_start: hoy solo
   dash-ventana, la prueba de `inicio`; `sesiones` aún no reparte el selector). El servicio de archivos no deja ceder
   una segunda carpeta (la raíz 3 ya está): Carpeta: sigue siendo la primera. */
#define SELECTOR_LLAVE 4
long dash_plat_choose(int save)
{
    long out[2], a, got;
    unsigned b;
    unsigned char r[8];
    if (keys_at_start != SELECTOR_LLAVE || !arch_abrir()) return -1;
    if (save && dos_carpeta) return 1;
    a = dash_os_call(3, 0, 0, 0, 0, 0, out);          /* canal_crear: la respuesta */
    if (a <= 0) return -1;
    b = (unsigned)out[0];
    if (dash_os_call(4, SELECTOR_LLAVE, (long)(save ? "carpeta" : "abrir"), save ? 7 : 5, (long)&b, 1, out) < 0) {
        _svc(6, a, 0, 0, 0, 0, 0);
        return -1;
    }
    got = dash_os_call(5, a, (long)r, sizeof r, 0, 0, out);   /* (espera: el selector caduca al minuto) */
    _svc(6, a, 0, 0, 0, 0, 0);
    if (got != 4 || !arch_toma(r, 4)) return 0;
    if (save) dos_carpeta = arch_toma(r, 4);
    else {
        long rr[4];
        if (dos_elegido) arch_orden(A_CERRAR, dos_elegido, 0, 0, NULL, 0, rr);
        dos_elegido = arch_toma(r, 4);
    }
    return 1;
}
#endif

/* ======== dos.library ======== */

/* Un nombre del Amiga como sitio: con volumen, el suyo; sin él, desde el cajón actual */
struct DLock { DSitio s; DList l; int listando; };

static int dos_sitio(const char *name, DSitio *s)
{
    const char *c = name ? strchr(name, ':') : NULL;
    char vol[32];
    unsigned long i;
    if (!name) return 0;
    if (c) {
        if ((unsigned long)(c - name) >= sizeof vol) return 0;
        for (i = 0; name + i < c; i++) vol[i] = name[i] >= 'a' && name[i] <= 'z' ? name[i] - 32 : name[i];
        vol[i] = 0;
        return dos_volumen(vol, c + 1, s);
    }
    if (dos_actual) { s->root = dos_actual->s.root; return dos_juntar(dos_actual->s.path, name, s->path); }
#ifdef DASH_PLAT_LINUX
    s->root = L_AT_FDCWD;
#else
    s->root = 0;
#endif
    return dos_juntar("", name, s->path);
}

/* Ficheros abiertos: con un búfer de 4 KB, para leer o escribir de poco en poco (FGetC, FPutC) sin un viaje al
   servicio cada vez. Con la memoria de los búferes de Dash (por debajo de 2 GB): file_open da el fichero a un Int, que
   en DashOS es de 32 bits */
#define DOS_BUF 4096
typedef struct { long h, pos, bpos, blen; int sucio; unsigned char buf[DOS_BUF]; } DFile;

static int dos_vaciar(DFile *f)
{
    long w = f->sucio && f->blen ? ds_pwrite(f->h, f->bpos, f->buf, f->blen) : f->blen;
    int ok = !f->sucio || w == f->blen;
    f->sucio = 0;
    f->blen = 0;
    return ok;
}

static LONG dos_flush(BPTR fh) { return fh ? dos_vaciar((DFile *)fh) : 0; }

BPTR Open(CONST_STRPTR name, LONG mode)
{
    DSitio s;
    DFile *f;
    long h;
    if (!dos_sitio((const char *)name, &s)) return 0;
    if (ds_open(&s, mode == MODE_OLDFILE ? 0 : mode == MODE_NEWFILE ? 1 : 2, &h) != 0) return 0;
    if (!(f = dash_plat_buffer_alloc(sizeof *f))) { ds_close(h); return 0; }
    f->h = h;
    return (BPTR)f;
}

LONG Close(BPTR fh)
{
    DFile *f = (DFile *)fh;
    int ok;
    if (!f || fh == 1) return 0;
    ok = dos_vaciar(f);
    ds_close(f->h);
    dash_plat_buffer_free(f);
    return ok;
}

LONG Read(BPTR fh, APTR buf, LONG len)
{
    DFile *f = (DFile *)fh;
    unsigned char *d = buf;
    long hecho = 0, k, r;
    if (!f || fh == 1 || len < 0) return -1;
    if (f->sucio && !dos_vaciar(f)) return -1;
    while (hecho < len) {
        if (f->pos >= f->bpos && f->pos < f->bpos + f->blen) {
            k = f->bpos + f->blen - f->pos;
            if (k > len - hecho) k = len - hecho;
            memcpy(d + hecho, f->buf + (f->pos - f->bpos), (unsigned long)k);
            hecho += k;
            f->pos += k;
            continue;
        }
        if (len - hecho >= DOS_BUF) {                  /* mucho de una vez: sin el búfer */
            r = ds_pread(f->h, f->pos, d + hecho, len - hecho);
            if (r < 0) return hecho ? hecho : -1;
            hecho += r;
            f->pos += r;
            break;
        }
        r = ds_pread(f->h, f->pos, f->buf, DOS_BUF);
        if (r < 0) return hecho ? hecho : -1;
        f->bpos = f->pos;
        f->blen = r;
        if (!r) break;
    }
    return hecho;
}

static LONG dos_write(BPTR fh, const void *buf, LONG len)
{
    DFile *f = (DFile *)fh;
    long r;
    if (!f || len < 0) return -1;
    if (f->sucio && f->pos == f->bpos + f->blen && f->blen + len <= DOS_BUF) {
        memcpy(f->buf + f->blen, buf, (unsigned long)len);
        f->blen += len;
        f->pos += len;
        return len;
    }
    if (!dos_vaciar(f)) return -1;
    if (len >= DOS_BUF) {
        r = ds_pwrite(f->h, f->pos, buf, len);
        if (r > 0) f->pos += r;
        return r;
    }
    memcpy(f->buf, buf, (unsigned long)len);
    f->bpos = f->pos;
    f->blen = len;
    f->sucio = 1;
    f->pos += len;
    return len;
}

LONG Seek(BPTR fh, LONG pos, LONG mode)
{
    DFile *f = (DFile *)fh;
    long antes, n;
    if (!f || fh == 1) return -1;
    antes = f->pos;
    if (mode == OFFSET_END) {
        if (f->sucio && !dos_vaciar(f)) return -1;
        if ((n = ds_size(f->h)) < 0) return -1;
        n += pos;
    } else n = mode == OFFSET_CURRENT ? f->pos + pos : pos;
    if (n < 0) return -1;
    f->pos = n;
    return (LONG)antes;
}

LONG FGetC(BPTR fh)
{
    unsigned char c;
    return Read(fh, &c, 1) == 1 ? c : -1;
}
LONG UnGetC(BPTR fh, LONG c)
{
    DFile *f = (DFile *)fh;
    if (!f || fh == 1 || c == -1 || !f->pos) return 0;
    f->pos--;
    return c;
}
STRPTR FGets(BPTR fh, STRPTR buf, ULONG len)
{
    ULONG n = 0;
    LONG c;
    if (!len) return NULL;
    while (n + 1 < len && (c = FGetC(fh)) != -1) {
        buf[n++] = (UBYTE)c;
        if (c == '\n') break;
    }
    buf[n] = 0;
    return n ? buf : NULL;
}
LONG FPutC(BPTR fh, LONG c)
{
    unsigned char b = (unsigned char)c;
    return Write(fh, &b, 1) == 1 ? c : -1;
}
LONG FPuts(BPTR fh, CONST_STRPTR s)
{
    LONG n = (LONG)strlen((const char *)s);
    return Write(fh, s, n) == n ? 0 : -1;
}

/* Cerrojos: un sitio que existe (y, al listar, lo que lleva leído) */
BPTR Lock(CONST_STRPTR name, LONG mode)
{
    DLock *l;
    DInfo d;
    (void)mode;
    if (!(l = AllocVec(sizeof *l, MEMF_CLEAR))) return 0;
    if (!dos_sitio((const char *)name, &l->s) || ds_stat(&l->s, &d) != 0) { FreeVec(l); return 0; }
    return (BPTR)l;
}
void UnLock(BPTR lock)
{
    DLock *l = (DLock *)lock;
    if (!l) return;
    if (l->listando) ds_list_close(&l->l);
    FreeVec(l);
}
BPTR DupLock(BPTR lock)
{
    DLock *l;
    if (!lock || !(l = AllocVec(sizeof *l, MEMF_CLEAR))) return 0;
    l->s = ((DLock *)lock)->s;
    return (BPTR)l;
}
BPTR CurrentDir(BPTR lock)
{
    DLock *antes = dos_actual;
    dos_actual = (DLock *)lock;
    return (BPTR)antes;
}

APTR AllocDosObject(ULONG type, const void *tags) { (void)tags; return type == DOS_FIB ? AllocVec(sizeof(struct FileInfoBlock), MEMF_CLEAR) : NULL; }
void FreeDosObject(ULONG type, APTR p) { (void)type; if (p) FreeVec(p); }

/* La fecha de Unix (segundos desde 1970) como DateStamp (días desde 1978, minutos y tics de 1/50 s) */
static void dos_fecha(long t, struct DateStamp *ds)
{
    t -= 252460800L;
    if (t < 0) t = 0;
    ds->ds_Days = (LONG)(t / 86400);
    ds->ds_Minute = (LONG)(t % 86400 / 60);
    ds->ds_Tick = (LONG)(t % 60 * 50);
}

static void dos_fib(struct FileInfoBlock *fib, const char *name, const DInfo *d)
{
    unsigned long n = strlen(name);
    if (n > sizeof fib->fib_FileName - 1) n = sizeof fib->fib_FileName - 1;
    memcpy(fib->fib_FileName, name, n);
    fib->fib_FileName[n] = 0;
    fib->fib_DirEntryType = fib->fib_EntryType = d->type == 2 ? ST_USERDIR : d->type == 3 ? ST_SOFTLINK : ST_FILE;
    fib->fib_Size = d->type == 2 ? 0 : (LONG)d->size;
    fib->fib_NumBlocks = (LONG)((d->size + 511) / 512);
    fib->fib_Protection = (LONG)d->prot;
    dos_fecha(d->date, &fib->fib_Date);
    strcpy(fib->fib_Comment, d->comment);
}

LONG Examine(BPTR lock, struct FileInfoBlock *fib)
{
    DLock *l = (DLock *)lock;
    DInfo d;
    if (!l || !fib || ds_stat(&l->s, &d) != 0) return 0;
#ifndef DASH_PLAT_LINUX
    a_comentario(&l->s, &d);
#endif
    if (l->listando) { ds_list_close(&l->l); l->listando = 0; }
    dos_fib(fib, *dos_ultimo(l->s.path) ? dos_ultimo(l->s.path) : "", &d);
    return 1;
}

LONG ExNext(BPTR lock, struct FileInfoBlock *fib)
{
    DLock *l = (DLock *)lock;
    DInfo d;
    char name[108];
    if (!l || !fib) return 0;
    if (!l->listando) {
        if (ds_list_open(&l->s, &l->l) != 0) return 0;
        l->listando = 1;
    }
    if (!ds_list_next(&l->l, name, &d)) return 0;
    dos_fib(fib, name, &d);
    return 1;
}

LONG NameFromLock(BPTR lock, STRPTR buf, LONG len)
{
    DSitio s;
    if (lock) return ds_nombre(&((DLock *)lock)->s, (char *)buf, len);
    return dos_sitio("", &s) && ds_nombre(&s, (char *)buf, len);
}

BPTR CreateDir(CONST_STRPTR name)
{
    DSitio s;
    if (!dos_sitio((const char *)name, &s) || ds_mkdir(&s) != 0) return 0;
    return Lock(name, ACCESS_READ);
}
LONG DeleteFile(CONST_STRPTR name)
{
    DSitio s;
    return dos_sitio((const char *)name, &s) && ds_delete(&s) == 0;
}
LONG Rename(CONST_STRPTR a, CONST_STRPTR b)
{
    DSitio sa, sb;
    return dos_sitio((const char *)a, &sa) && dos_sitio((const char *)b, &sb) && ds_rename(&sa, &sb) == 0;
}
LONG SetProtection(CONST_STRPTR name, LONG bits)
{
    DSitio s;
    return dos_sitio((const char *)name, &s) && ds_protect(&s, bits) == 0;
}
LONG SetComment(CONST_STRPTR name, CONST_STRPTR text)
{
    DSitio s;
    return dos_sitio((const char *)name, &s) && ds_comment(&s, (const char *)text) == 0;
}
LONG SetFileDate(CONST_STRPTR name, const struct DateStamp *ds)
{
    DSitio s;
    return dos_sitio((const char *)name, &s) &&
           ds_setdate(&s, 252460800L + ds->ds_Days * 86400L + ds->ds_Minute * 60L + ds->ds_Tick / 50) == 0;
}

/* Un fichero entero en memoria de AllocVec con un 0 detrás (los catálogos); NULL si no está */
void *dash_plat_file_load(const char *path, long *size)
{
    BPTR f = Open((CONST_STRPTR)path, MODE_OLDFILE);
    unsigned char *d;
    long n;
    if (!f) return NULL;
    Seek(f, 0, OFFSET_END);
    n = Seek(f, 0, OFFSET_BEGINNING);
    if (n < 0 || n > 0x1000000L || !(d = AllocVec((ULONG)n + 1, MEMF_ANY))) { Close(f); return NULL; }
    if (Read(f, d, n) != n) { Close(f); FreeVec(d); return NULL; }
    Close(f);
    d[n] = 0;
    *size = n;
    return d;
}
