#include <stdio.h>
long f(long n, long i) {
    long r = n + i;
    if (r > 1000000) r = r - 1000000;
    return r;
}
int main(void) {
    long y = 0, i;
    for (i = 1; i <= 100000; i++) y = f(y, i);
    printf("%ld\n", y);
    return 0;
}
