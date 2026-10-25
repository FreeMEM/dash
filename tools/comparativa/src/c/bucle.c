#include <stdio.h>
int main(void) {
    long x = 0, i;
    for (i = 1; i <= 300000; i++) {
        x = x + i * 3;
        if (x > 1000000) x = x - 1000000;
    }
    printf("%ld\n", x);
    return 0;
}
