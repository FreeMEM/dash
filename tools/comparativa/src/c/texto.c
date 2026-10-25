#include <stdio.h>
int main(void) {
    char s[16];
    long i;
    for (i = 1; i <= 20000; i++) sprintf(s, "x%ld", i);
    printf("%s\n", s);
    return 0;
}
