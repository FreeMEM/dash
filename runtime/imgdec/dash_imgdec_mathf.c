/* The maths nanosvg uses, on Dash's fdlibm (compiler/clibs.py "fdlibm": its names are dash_fd_* and
   __ieee754_*), computed in double */
double dash_fd_floor(double);
double dash_fd_ceil(double);
double dash_fd_sin(double);
double dash_fd_cos(double);
double dash_fd_tan(double);
double dash_fd_fabs(double);
double __ieee754_sqrt(double);
double __ieee754_pow(double, double);
double __ieee754_atan2(double, double);
double __ieee754_acos(double);

float dash_imgdec_sqrtf(float x) { return (float)__ieee754_sqrt(x); }
float dash_imgdec_fabsf(float x) { return x < 0 ? -x : x; }
float dash_imgdec_sinf(float x) { return (float)dash_fd_sin(x); }
float dash_imgdec_cosf(float x) { return (float)dash_fd_cos(x); }
float dash_imgdec_tanf(float x) { return (float)dash_fd_tan(x); }
float dash_imgdec_ceilf(float x) { return (float)dash_fd_ceil(x); }
float dash_imgdec_floorf(float x) { return (float)dash_fd_floor(x); }
float dash_imgdec_roundf(float x) { return x < 0 ? -(float)dash_fd_floor(0.5 - x) : (float)dash_fd_floor(x + 0.5); }
float dash_imgdec_atan2f(float y, float x) { return (float)__ieee754_atan2(y, x); }
float dash_imgdec_acosf(float x) { return (float)__ieee754_acos(x); }
double dash_imgdec_sqrt(double x) { return __ieee754_sqrt(x); }
double dash_imgdec_pow(double x, double y) { return __ieee754_pow(x, y); }
double dash_imgdec_fabs(double x) { return dash_fd_fabs(x); }
