/*
 * Dash Language Runtime - Array Support
 * For Amiga systems using exec.library
 */

#ifndef DASH_ARRAY_H
#define DASH_ARRAY_H

#include <exec/types.h>
#include <proto/exec.h>

/* Array structure for LONG values */
typedef struct {
    LONG *data;
    LONG length;
    LONG capacity;
} DashArrayLong;

/* Create a new array with given capacity and length */
static DashArrayLong* DashArray_create(LONG size) {
    DashArrayLong *arr = (DashArrayLong *)AllocMem(sizeof(DashArrayLong), MEMF_CLEAR);
    if (!arr) return NULL;

    if (size > 0) {
        arr->data = (LONG *)AllocMem(sizeof(LONG) * size, MEMF_CLEAR);
        if (!arr->data) {
            FreeMem(arr, sizeof(DashArrayLong));
            return NULL;
        }
    } else {
        arr->data = NULL;
    }

    arr->length = size;
    arr->capacity = size;
    return arr;
}

/* Get element at index (with bounds checking) */
static LONG DashArray_get(DashArrayLong *arr, LONG index) {
    if (!arr || index < 0 || index >= arr->length) {
        return 0; /* Return 0 for out of bounds */
    }
    return arr->data[index];
}

/* Set element at index (with bounds checking) */
static void DashArray_set(DashArrayLong *arr, LONG index, LONG value) {
    if (!arr || index < 0 || index >= arr->length) {
        return; /* Silently ignore out of bounds */
    }
    arr->data[index] = value;
}

/* Get array length */
static LONG DashArray_length(DashArrayLong *arr) {
    return arr ? arr->length : 0;
}

/* Free array memory */
static void DashArray_free(DashArrayLong *arr) {
    if (arr) {
        if (arr->data) {
            FreeMem(arr->data, sizeof(LONG) * arr->capacity);
        }
        FreeMem(arr, sizeof(DashArrayLong));
    }
}

#endif /* DASH_ARRAY_H */
