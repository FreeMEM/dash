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
static APTR AllocPooled(APTR pool, ULONG n){ return calloc(1,n); }
static void FreePooled(APTR pool, APTR m, ULONG n){ free(m); }
static void DeletePool(APTR pool){ free(pool); }

/*RUNTIME*/

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
 void *o = _dash_rc_alloc(16); CHECK(_dash_refcount(o)==1); _dash_retain(o); CHECK(_dash_refcount(o)==2); _dash_release(o); _dash_release(o);
 _dash_mem_cleanup(); CHECK(_dash_pool==NULL);
 printf("fallos: %d\n", fails); return fails; }
