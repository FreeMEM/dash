#include <stdio.h>
int main(void) {
    float f = 0.0f, g = 1.0001f;
    long i;
    for (i = 1; i <= 20000; i++) f = f + g * 0.5f;
    printf("%ld\n", (long)f);
    return 0;
}
