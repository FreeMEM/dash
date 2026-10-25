#include <stdio.h>
int main(void) {
    long a[10] = {0}, i;
    for (i = 1; i <= 100000; i++) a[i % 10] = a[(i + 1) % 10] + 1;
    printf("%ld\n", a[0]);
    return 0;
}
