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
typedef int32_t LONG; typedef uint32_t ULONG; typedef char *STRPTR; typedef short BOOL; typedef void *APTR; typedef unsigned char UBYTE;
#define MEMF_ANY 0
#define MEMF_CLEAR 0x10000
static APTR CreatePool(ULONG r, ULONG p, ULONG t){ return malloc(1); }
static long live = 0;   /* pooled blocks not yet freed */
static APTR AllocPooled(APTR pool, ULONG n){ live++; return calloc(1,n); }
static void FreePooled(APTR pool, APTR m, ULONG n){ live--; free(m); }
#define TRUE 1
#define FALSE 0
static void DeletePool(APTR pool){ free(pool); }

/*RUNTIME*/

/* blocks parked in the small-string free lists count as freed */
static long cached_blocks(void){ long n=0; for(int c=0;c<_DASH_STR_CLASSES;c++) for(_DashStrHdr*h=_dash_str_free_list[c];h;h=h->next) n++; return n; }
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
 _dash_mem_cleanup(); CHECK(_dash_pool==NULL);
 printf("fallos: %d\n", fails); return fails; }
