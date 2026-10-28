/* nanosvg (memononen/nanosvg, zlib license; Tachyon's copy: runtime/imgdec/LEEME) for Dash's image_decode: the
   parser and the rasterizer. Its maths go to dash_imgdec_mathf.c (Dash's fdlibm, not -lm: libnix's goes to the
   ROM's math libraries, which hang without an FPU in FS-UAE), and its memory to exec (it may run in a task). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define sqrtf dash_imgdec_sqrtf
#define fabsf dash_imgdec_fabsf
#define sinf dash_imgdec_sinf
#define cosf dash_imgdec_cosf
#define tanf dash_imgdec_tanf
#define roundf dash_imgdec_roundf
#define ceilf dash_imgdec_ceilf
#define floorf dash_imgdec_floorf
#define atan2f dash_imgdec_atan2f
#define acosf dash_imgdec_acosf
#define sqrt dash_imgdec_sqrt
#define pow dash_imgdec_pow
#define fabs dash_imgdec_fabs
float sqrtf(float x);
float fabsf(float x);
float sinf(float x);
float cosf(float x);
float tanf(float x);
float roundf(float x);
float ceilf(float x);
float floorf(float x);
float atan2f(float y, float x);
float acosf(float x);
double sqrt(double x);
double pow(double x, double y);
double fabs(double x);
#define NANOSVG_IMPLEMENTATION
#include "nanosvg.h"
#define NANOSVGRAST_IMPLEMENTATION
#include "nanosvgrast.h"
