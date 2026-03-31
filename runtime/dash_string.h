/* Dash String Runtime for AmigaOS */
#ifndef DASH_STRING_H
#define DASH_STRING_H

#include <exec/types.h>
#include <proto/exec.h>
#include <string.h>

/* String concatenation - caller must free result with DashString_free */
static STRPTR DashString_concat(STRPTR a, STRPTR b) {
    LONG len_a = a ? strlen(a) : 0;
    LONG len_b = b ? strlen(b) : 0;
    LONG total = len_a + len_b + 1;

    STRPTR result = (STRPTR)AllocMem(total, MEMF_CLEAR);
    if (!result) return NULL;

    if (a) strcpy(result, a);
    if (b) strcpy(result + len_a, b);

    return result;
}

/* Get character at index (returns 0 if out of bounds) */
static char DashString_char_at(STRPTR s, LONG index) {
    if (!s || index < 0 || index >= strlen(s)) return 0;
    return s[index];
}

/* Get string length */
static LONG DashString_length(STRPTR s) {
    return s ? strlen(s) : 0;
}

/* Free a dynamically allocated string */
static void DashString_free(STRPTR s) {
    if (s) FreeMem(s, strlen(s) + 1);
}

/* Convert integer to string (returns static buffer - not thread safe) */
static STRPTR DashString_from_int(LONG n) {
    static char buffer[32];
    LONG i = 0;
    BOOL negative = FALSE;

    if (n < 0) {
        negative = TRUE;
        n = -n;
    }

    if (n == 0) {
        buffer[0] = '0';
        buffer[1] = '\0';
        return buffer;
    }

    /* Build string in reverse */
    char temp[32];
    while (n > 0) {
        temp[i++] = '0' + (n % 10);
        n /= 10;
    }

    /* Add negative sign and reverse */
    LONG j = 0;
    if (negative) buffer[j++] = '-';
    while (i > 0) buffer[j++] = temp[--i];
    buffer[j] = '\0';

    return buffer;
}

#endif /* DASH_STRING_H */
