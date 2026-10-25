/* timeit LISTFILE: runs each command of LISTFILE (one per line, "name command...") with NIL: for input
   and output, and prints "name ms peak_bytes": EClock time, and the largest drop of free memory while it
   runs (a helper process samples AvailMem every tick). */
#include <exec/types.h>
#include <dos/dos.h>
#include <dos/dostags.h>
#include <devices/timer.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/timer.h>
#include <stdio.h>
#include <string.h>

struct Device *TimerBase;
static volatile ULONG low;
static volatile BOOL sampling, sampler_done;

static ULONG now(ULONG *freq) {   /* low 32 bits: wraps after 100 minutes at 709 kHz */
    struct EClockVal e;
    *freq = ReadEClock(&e);
    return e.ev_lo;
}

static void sampler(void) {
    while (sampling) {
        ULONG m = AvailMem(MEMF_ANY);
        if (m < low) low = m;
        Delay(1);
    }
    Forbid();
    sampler_done = TRUE;
}

int main(int argc, char **argv) {
    static struct timerequest tr;
    FILE *list;
    char line[512];
    if (argc < 2 || !(list = fopen(argv[1], "r"))) return 20;
    if (OpenDevice((STRPTR)TIMERNAME, UNIT_ECLOCK, (struct IORequest *)&tr, 0)) return 20;
    TimerBase = tr.tr_node.io_Device;
    while (fgets(line, sizeof(line), list)) {
        char *cmd;
        BPTR nil;
        ULONG freq, before, t0, t1;
        LONG rc;
        line[strcspn(line, "\r\n")] = 0;
        if (!line[0] || line[0] == '#') continue;
        cmd = strchr(line, ' ');
        if (!cmd) continue;
        *cmd++ = 0;
        Delay(25);
        before = low = AvailMem(MEMF_ANY);
        sampling = TRUE;
        sampler_done = FALSE;
        CreateNewProcTags(NP_Entry, (ULONG)sampler, NP_Name, (ULONG)"timeit sampler", NP_Priority, 1, TAG_DONE);
        nil = Open((STRPTR)"NIL:", MODE_NEWFILE);
        t0 = now(&freq);
        rc = SystemTags((STRPTR)cmd, SYS_Input, nil, SYS_Output, NULL, NP_StackSize, 65536, TAG_DONE);
        t1 = now(&freq);
        Close(nil);
        sampling = FALSE;
        while (!sampler_done) Delay(1);
        printf("%s %ld %ld %ld\n", line, (long)((t1 - t0) / (freq / 1000)), (long)(before - low), (long)rc);
        fflush(stdout);
    }
    CloseDevice((struct IORequest *)&tr);
    fclose(list);
    return 0;
}
