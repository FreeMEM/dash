/*
 * Host test for the C runtime embedded in compiler/codegen.py.
 * tests/run_tests.py replaces the RUNTIME marker with the runtime
 * templates, builds this file with the host gcc and runs it.
 * exec.library calls are replaced by malloc-based stubs.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <stdint.h>
#include <stdarg.h>
#include <math.h>
typedef int32_t LONG; typedef uint32_t ULONG; typedef char *STRPTR; typedef const char *CONST_STRPTR; typedef short BOOL; typedef void *APTR; typedef unsigned char UBYTE; typedef uint16_t UWORD;
#define MEMF_ANY 0
#define MEMF_CLEAR 0x10000
static APTR CreatePool(ULONG r, ULONG p, ULONG t){ return malloc(1); }
static long live = 0;   /* pooled blocks not yet freed */
static APTR AllocPooled(APTR pool, ULONG n){ live++; return calloc(1,n); }
static void FreePooled(APTR pool, APTR m, ULONG n){ live--; free(m); }
#define TRUE 1
#define FALSE 0
static void DeletePool(APTR pool){ free(pool); }
/* dos.library's Printf: LONG is 32 bits here, so %ld is printed as %d */
static int Printf(CONST_STRPTR f, ...){ char fmt[256]; int j=0; va_list ap;
 for(int i=0; f[i] && j<250; i++){ if(f[i]=='%' && f[i+1]=='l' && f[i+2]=='d'){ fmt[j++]='%'; fmt[j++]='d'; i+=2; } else fmt[j++]=f[i]; }
 fmt[j]=0; va_start(ap,f); int n=vprintf(fmt,ap); va_end(ap); return n; }

/*RUNTIME*/

/* blocks parked in the small-string free lists count as freed */
static long cached_blocks(void){ long n=0; for(int c=0;c<_DASH_SMALL_CLASSES;c++) for(APTR b=_dash_small_free[c];b;b=*(APTR*)b) n++;
#ifdef DASH_MEMCHECK
 for(int i=0;i<_DASH_MC_HOLD;i++) if(_dash_mc_held[i]) n++;   /* freed, held back by --memcheck */
#endif
 return n; }
#define LIVE (live - cached_blocks())
#define CHECK(c) do{ if(!(c)){ printf("FALLO linea %d: %s\n", __LINE__, #c); fails++; } }while(0)
int main(void){ int fails=0;
 DashArrayLong *a = DashArray_from(5, (LONG[]){1,2,3,4,5});
 CHECK(DashArray_length(a)==5); CHECK(DashArray_get(a,4)==5); CHECK(DashArray_get(a,5)==0); CHECK(DashArray_get(a,-1)==0);
 DashArray_set(a,9,7); DashArray_set(a,-1,7); CHECK(DashArray_get(a,0)==1);
 DashArrayLong *s1 = DashArray_slice(a,1,3); CHECK(DashArray_length(s1)==2 && DashArray_get(s1,0)==2);
 DashArrayLong *s2 = DashArray_slice(a,-3,99); CHECK(DashArray_length(s2)==5);
 DashArrayLong *s3 = DashArray_slice(a,4,2); CHECK(DashArray_length(s3)==0);
 DashArrayLong *s4 = DashArray_slice(a,7,9); CHECK(DashArray_length(s4)==0);
 DashArrayLong *e = DashArray_create(0); CHECK(DashArray_length(e)==0); CHECK(DashArray_get(e,0)==0);
 CHECK(DashArray_length(NULL)==0); CHECK(DashArray_get(NULL,0)==0);
 CHECK(DashArray_slice(NULL,0,1)==NULL);
 CHECK(strcmp(DashString_concat("ab","cd"),"abcd")==0);
 CHECK(strcmp(DashString_concat(NULL,"cd"),"cd")==0);
 CHECK(strcmp(DashString_concat("ab",NULL),"ab")==0);
 CHECK(DashString_length(NULL)==0); CHECK(DashString_length("hola")==4);
 CHECK(DashString_char_at("hola",0)=='h'); CHECK(DashString_char_at("hola",4)==0); CHECK(DashString_char_at("hola",-1)==0); CHECK(DashString_char_at(NULL,0)==0);
 CHECK(strcmp(DashString_from_int(INT32_MIN),"-2147483648")==0); CHECK(strcmp(DashString_from_int(0),"0")==0);
 CHECK(strcmp(DashString_from_char('x'),"x")==0);
 /* String memory: temporaries, marks, ownership, escapes */
 {
  long base = LIVE; ULONG m0 = _dash_tmp_mark(), m = m0; STRPTR v = NULL, w = NULL, t;
  t = DashString_concat("ab", "cd"); CHECK(LIVE == base + 1);
  _dash_tmp_release(m); CHECK(LIVE == base); CHECK(_dash_tmp == NULL || _dash_tmp->serial <= m);
  /* a loop that concatenates keeps one live block per variable */
  m = _dash_tmp_mark();
  for (int i = 0; i < 1000; i++) {
   ULONG it = _dash_tmp_mark();
   _dash_str_set(&v, DashString_concat(DashString_concat(v, "x"), ""));   /* two temporaries, one adopted */
   _dash_tmp_release(it);
  }
  CHECK(strlen(v) == 1000); CHECK(LIVE == base + 1);
  /* copying a variable makes an independent copy; literals are copied too */
  _dash_str_set(&w, v); CHECK(w != v && strcmp(w, v) == 0); CHECK(LIVE == base + 2);
  _dash_str_set(&w, "lit"); CHECK(strcmp(w, "lit") == 0); CHECK(LIVE == base + 2);
  _dash_str_set(&w, w); CHECK(strcmp(w, "lit") == 0); CHECK(LIVE == base + 2);
  /* a temporary taken out of the middle of the list does not break marks */
  m = _dash_tmp_mark();
  t = DashString_concat("1", "");  DashString_concat("2", ""); DashString_concat("3", "");
  _dash_str_set(&w, t); CHECK(LIVE == base + 4);   /* old w freed, t adopted, k and "3" still temporaries */
  _dash_tmp_release(m); CHECK(LIVE == base + 2); CHECK(strcmp(w, "1") == 0);
  /* escaped text is never freed by its owner */
  t = _dash_str_escape(DashString_concat("kept", "")); _dash_tmp_release(m0); CHECK(strcmp(t, "kept") == 0);
  CHECK(LIVE == base + 3);
  { STRPTR e = _dash_str_escape(w); CHECK(e != w && strcmp(e, w) == 0); }   /* owned text: a permanent copy */
  CHECK(LIVE == base + 4); _dash_str_set(&w, "otro"); CHECK(LIVE == base + 4);   /* the copy stays */
  CHECK(_dash_str_escape(NULL) == NULL);
  /* return values survive the callee's release and become the caller's temporaries */
  m = _dash_tmp_mark();
  { ULONG fm = _dash_tmp_mark(); STRPTR r = DashString_concat("ret", ""); DashString_concat("tmp", "");
    _dash_tmp_release_keep(fm, r); CHECK(LIVE == base + 5); CHECK(strcmp(r, "ret") == 0);
    CHECK(_dash_str_ret(r) == r); CHECK(_dash_str_ret(v) != v); CHECK(LIVE == base + 6); }
  _dash_tmp_release(m); CHECK(LIVE == base + 4);
  _dash_str_set(&v, NULL); _dash_str_set(&w, NULL); CHECK(LIVE == base + 2);   /* t and the kept old w remain */
  CHECK(_dash_tmp_take("literal") == FALSE); CHECK(_dash_tmp_take(NULL) == FALSE);
 }
 /* Objects (arrays, structs): new ones are temporaries; references keep them */
 {
  long base = LIVE; ULONG m = _dash_tmp_mark(); DashArrayLong *a1 = NULL, *a2 = NULL;
  void *o = _dash_rc_alloc(16); CHECK(_dash_refcount(o) == 0);
  _dash_retain(o); CHECK(_dash_refcount(o) == 1); _dash_retain(o); CHECK(_dash_refcount(o) == 2);
  _dash_release(o); _dash_release(o); CHECK(LIVE == base);              /* last reference: freed */
  DashArray_from(3, (LONG[]){1, 2, 3}); CHECK(LIVE == base + 2);         /* object + data */
  _dash_tmp_release(m); CHECK(LIVE == base);                             /* unused temporary */
  for (int i = 0; i < 1000; i++) {                                       /* a = [..] in a loop */
   ULONG it = _dash_tmp_mark();
   _dash_obj_set((void **)&a1, DashArray_from(2, (LONG[]){i, i}));
   _dash_tmp_release(it);
  }
  CHECK(LIVE == base + 2); CHECK(DashArray_get(a1, 1) == 999);
  _dash_obj_set((void **)&a2, a1); CHECK(_dash_refcount(a1) == 2);       /* shared */
  _dash_obj_set((void **)&a1, NULL); CHECK(LIVE == base + 2); CHECK(DashArray_get(a2, 0) == 999);
  /* a returned object survives the callee and becomes the caller's temporary */
  m = _dash_tmp_mark();
  { ULONG fm = _dash_tmp_mark(); DashArrayLong *r = DashArray_create(4);
    _dash_retain(r); _dash_tmp_release(fm); _dash_obj_float(r);
    CHECK(LIVE == base + 4); CHECK(_dash_refcount(r) == 0); }
  _dash_tmp_release(m); CHECK(LIVE == base + 2);
  /* a returned object someone else holds is not a temporary */
  _dash_retain(a2); _dash_obj_float(a2); CHECK(_dash_refcount(a2) == 1);
  _dash_obj_escape(a2); _dash_obj_set((void **)&a2, NULL); CHECK(LIVE == base + 2);   /* escaped: kept */
  _dash_release(NULL); _dash_retain(NULL); CHECK(_dash_obj_float(NULL) == NULL);
 }
 /* Fixed 16.16: against the exact value (long double), many pairs */
 {
  #define FX(x) ((DashFixed)((x) * 65536.0))
  CHECK(_dash_fx_mul(FX(1.5), FX(2)) == FX(3)); CHECK(_dash_fx_mul(FX(-1.5), FX(2)) == FX(-3));
  CHECK(_dash_fx_mul(FX(0.5), FX(0.5)) == FX(0.25)); CHECK(_dash_fx_mul(FX(-0.5), FX(-0.5)) == FX(0.25));
  CHECK(_dash_fx_div(FX(3), FX(2)) == FX(1.5)); CHECK(_dash_fx_div(FX(-3), FX(2)) == FX(-1.5));
  CHECK(_dash_fx_div(FX(1), FX(3)) == 21845); CHECK(_dash_fx_div(FX(5), 0) == 0x7FFFFFFF);
  CHECK(_dash_fx_div(FX(-5), 0) == -0x7FFFFFFF);
  CHECK(_dash_fx_int(FX(2.75)) == 2); CHECK(_dash_fx_int(FX(-2.75)) == -2); CHECK(_dash_fx_int(FX(-0.5)) == 0);
  CHECK(strcmp(DashString_from_fixed(FX(1.5)), "1.5") == 0);
  CHECK(strcmp(DashString_from_fixed(FX(-0.25)), "-0.25") == 0);
  CHECK(strcmp(DashString_from_fixed(FX(3)), "3.0") == 0);
  CHECK(strcmp(DashString_from_fixed(FX(0.1)), "0.1") == 0);
  CHECK(strcmp(DashString_from_fixed(FX(-32768)), "-32768.0") == 0);
  CHECK(strcmp(DashString_from_fixed(0x7FFFFFFF), "32768.0") == 0);     /* 32767.99998 rounded */
  CHECK(strcmp(DashString_from_fixed(1), "0.0") == 0);              /* below 0.00005 */
  CHECK(strcmp(DashString_from_fixed(-7), "-0.0001") == 0);
  CHECK(strcmp(DashString_from_fixed(FX(2.0001)), "2.0001") == 0);
  CHECK(_dash_fx_sqrt(FX(4)) == FX(2)); CHECK(_dash_fx_sqrt(FX(2)) == 92681); CHECK(_dash_fx_sqrt(FX(-1)) == 0);
  CHECK(_dash_fx_sqrt(0x7FFFFFFF) == 11863283);
  CHECK(_dash_fx_sin(FX(30)) == FX(0.5)); CHECK(_dash_fx_sin(FX(90)) == FX(1)); CHECK(_dash_fx_sin(FX(-90)) == FX(-1));
  CHECK(_dash_fx_sin(FX(180)) == 0); CHECK(_dash_fx_cos(FX(60)) == FX(0.5)); CHECK(_dash_fx_cos(FX(0)) == FX(1));
  { int bad = 0; unsigned seed = 12345;
    for (int i = 0; i < 200000; i++) {
      seed = seed * 1103515245 + 12345; LONG a = (LONG)seed >> (seed % 17);
      seed = seed * 1103515245 + 12345; LONG b = (LONG)seed >> (seed % 17);
      long long p = ((long long)a * b);
      LONG mul = (LONG)((p < 0 ? -((-p) >> 16) : p >> 16));          /* truncated toward zero */
      if (_dash_fx_mul(a, b) != mul) bad++;
      if (b != 0) {
        long long q = ((long long)a * 65536) / b;                      /* C: toward zero */
        if (q >= -2147483647LL && q <= 2147483647LL && _dash_fx_div(a, b) != (LONG)q) bad++;
      }
      if (a > 0) {
        long double r = sqrtl((long double)a * 65536.0L); LONG s = _dash_fx_sqrt(a);
        if (s != (LONG)r) bad++;
      }
    }
    CHECK(bad == 0); if (bad) printf("fixed: %d differences\n", bad); }
  { int worst = 0;
    for (LONG a = -FX(720); a <= FX(720); a += 977) {
      LONG s = _dash_fx_sin(a), exact = (LONG)lroundl(sinl(a / 65536.0L * 3.14159265358979323846L / 180) * 65536);
      int d = s > exact ? s - exact : exact - s; if (d > worst) worst = d; }
    CHECK(worst <= 12); if (worst > 12) printf("fx_sin worst %d\n", worst); }
 }
 #ifdef DASH_MEMCHECK
 /* --memcheck: the code above made no errors; freed objects and strings are recognised */
 {
  CHECK(_dash_mc_errors == 0);
  LONG objs = _dash_mc_objs, strs = _dash_mc_strs, obj_esc = _dash_mc_obj_esc, str_esc = _dash_mc_str_esc;
  void *o = _dash_rc_alloc(8); CHECK(_dash_mc_objs == objs + 1);
  _dash_retain(o); _dash_release(o); CHECK(_dash_mc_objs == objs);
  _dash_retain(o); CHECK(_dash_mc_errors == 1);                 /* used after being freed */
  _dash_release(o); CHECK(_dash_mc_errors == 2);
  CHECK(_dash_refcount(o) == 0); CHECK(_dash_mc_errors == 3);
  CHECK(_dash_obj_float(o) == o); CHECK(_dash_mc_errors == 4);
  void *t = _dash_rc_alloc(8); _dash_release(t); CHECK(_dash_mc_errors == 5);   /* no reference to release */
  STRPTR s = _dash_str_dup("hola", FALSE); CHECK(_dash_mc_strs == strs + 1);
  _dash_str_free(s); CHECK(_dash_mc_strs == strs); CHECK(_dash_mc_errors == 5);
  _dash_str_free(s); CHECK(_dash_mc_errors == 6);                /* freed twice */
  STRPTR v = NULL; _dash_str_set(&v, "a"); _dash_str_set(&v, "b"); CHECK(_dash_mc_strs == strs + 1);
  _dash_str_escape(DashString_concat("x", "y")); CHECK(_dash_mc_str_esc == str_esc + 1);
  _dash_obj_escape(t); CHECK(_dash_mc_obj_esc == obj_esc + 1);
  /* more frees than the hold: the oldest held blocks are reused, still recognised while held */
  for (int i = 0; i < 3 * _DASH_MC_HOLD; i++) { void *k = _dash_rc_alloc(8); _dash_retain(k); _dash_release(k); }
  CHECK(_dash_mc_errors == 6);
  APTR blk = _dash_block_get(16); _dash_block_put(blk, 16); _dash_block_put(blk, 16);
  CHECK(_dash_mc_errors == 7);                                   /* a block returned twice */
 }
 #endif
 { /* var = var + add past 8 MB (Tachyon, a 10.8 MB script): the doubled room would pass 16 MB, the exact
      size fits (the 3 MB were lost); past 16 MB, var stays as it was */
   const LONG MB = 1024 * 1024;
   STRPTR big = NULL, six = malloc(6 * MB + 1), three = malloc(3 * MB + 1);
   memset(six, 'a', 6 * MB); six[6 * MB] = 0;
   memset(three, 'b', 3 * MB); three[3 * MB] = 0;
   _dash_str_append(&big, six); _dash_str_append(&big, three);
   CHECK(big && _dash_str_len(big) == 9 * MB && big[9 * MB - 1] == 'b' && big[6 * MB - 1] == 'a');
   _dash_str_append(&big, six); CHECK(_dash_str_len(big) == 15 * MB);
   _dash_str_append(&big, three); CHECK(_dash_str_len(big) == 15 * MB && big[15 * MB] == 0);
   _dash_str_free(big); free(six); free(three);
 }
 { /* D36: a temporary taken right after it was made gives its number back, so the release of the
      iteration has nothing to do; a mark handed out in between keeps it (that release must still
      free what comes after the mark) */
   ULONG m = _dash_tmp_mark(), m2;
   STRPTR v = NULL, t, u;
   _dash_str_set(&v, _dash_str_dup("uno", TRUE));
   CHECK(_dash_tmp_serial == m && _dash_tmp_take(v) == FALSE);
   t = _dash_str_dup("dos", TRUE);
   m2 = _dash_tmp_mark();
   CHECK(_dash_tmp_take(t) && _dash_tmp_serial == m2);
   u = _dash_str_dup("tres", TRUE);
   CHECK(_dash_tmp == _DASH_STR_HDR(u));
   _dash_tmp_release(m2);
   CHECK(!_dash_tmp || _dash_tmp->serial <= m2);     /* "tres" came after the mark: freed */
   _dash_str_free(t); _dash_str_free(v);
   _dash_tmp_release(m);
 }
 _dash_mem_cleanup(); CHECK(_dash_pool==NULL);
 printf("fallos: %d\n", fails); return fails; }
