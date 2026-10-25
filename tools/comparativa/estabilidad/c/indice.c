#include <stdio.h>
int main(void) {
    long a[3] = {1, 2, 3};
    volatile long i = 100000;
    a[i] = 5;
    printf("%ld\n", a[i]);
    printf("sigue\n");
    return 0;
}
