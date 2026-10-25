#include <stdio.h>
int main(void) {
    volatile long a = 10, b = 0;
    printf("%ld\n", a / b);
    printf("sigue\n");
    return 0;
}
