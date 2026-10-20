// A gdb -i=dap that only answers what the proxy test asks (test/run.js, debugProxy.js)
let buffer = Buffer.alloc(0);
const out = (m) => {
    const body = Buffer.from(JSON.stringify(m), 'utf8');
    process.stdout.write(`Content-Length: ${body.length}\r\n\r\n`);
    process.stdout.write(body);
};
const event = (event, body) => out({ seq: 0, type: 'event', event, body });
process.stdin.on('data', (data) => {
    buffer = Buffer.concat([buffer, data]);
    for (;;) {
        const head = buffer.indexOf('\r\n\r\n');
        if (head < 0) return;
        const length = Number(/Content-Length:\s*(\d+)/i.exec(buffer.slice(0, head).toString())[1]);
        if (buffer.length < head + 4 + length) return;
        const m = JSON.parse(buffer.slice(head + 4, head + 4 + length).toString());
        buffer = buffer.slice(head + 4 + length);
        const reply = (body) => out({ seq: 0, type: 'response', request_seq: m.seq, command: m.command, success: true, body });
        if (m.command === 'initialize') {
            reply({ supportsConfigurationDoneRequest: true, exceptionBreakpointFilters: [{ filter: 'ada', label: 'Ada exceptions' }] });
            process.stderr.write('No symbol table is loaded.  Use the "file" command.\n');
            setTimeout(() => {          // after the stderr line (two pipes: no order between them otherwise)
                event('output', { category: 'stdout', output: '\u274c\ufe0f No source file named /tmp/x/p.dash.\n' });
                event('output', { category: 'console', output: 'Breakpoint 1 (-source /tmp/x/p.dash -line 3) pending.\n' });
                event('stopped', { reason: 'breakpoint', threadId: 1 });
                event('output', { category: 'stderr', output: 'No symbol table is loaded.  (later: shown)\n' });
            }, 200);
        } else if (m.command === 'attach') {
            reply({});
            event('stopped', { reason: 'attach', threadId: 7 });
        } else if (m.command === 'continue') {
            reply({ allThreadsContinued: true });
            event('output', { category: 'console', output: `continue ${m.arguments.threadId}\n` });
        } else if (m.command === 'next') {           // (the test of the program's end)
            reply({});
            event('exited', { exitCode: 0 });
            event('terminated', {});
        } else if (m.command === 'scopes') {
            reply({ scopes: [{ name: 'Locals', variablesReference: 1 }, { name: 'Registers', variablesReference: 2 },
                             { name: 'Globals', variablesReference: 3 }] });
        } else {
            reply({});
        }
    }
});
