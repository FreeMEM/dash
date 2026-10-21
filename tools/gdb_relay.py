#!/usr/bin/env python3
"""Between m68k-amigaos-gdb and bgdbserver: everything goes through as it is, except the answer to
qOffsets, so that gdb finds the program's global variables.

bgdbserver answers where each hunk of the program was loaded (Text=, Data=, Bss=: the first three
hunks), and gdb adds that to each section. That is right for the code, but the DWARF of a program
of the bebbo toolchain keeps the addresses of the ELF the linker made it from, where .data goes after
.text and .bss after both: a global in .data is at Data + (its place in the ELF), which is the
hunk's start plus the size of the code. So gdb read the globals that far from where they are. Here
Data becomes Data - size(hunk 0) and Bss becomes Bss - size(hunk 0) - size(hunk 1).

    tools/gdb_relay.py --listen 2345 --to localhost:2346 bin/prog     # gdb: target remote :2345

tools/emu_run.py --gdbserver PORT puts it in front of the emulator's bgdbserver by itself.
"""
import argparse
import re
import socket
import struct
import threading
from pathlib import Path

HUNK_HEADER = 0x3F3


def hunk_sizes(exe):
    """The sizes in bytes of the hunks of an Amiga executable, in order."""
    data = Path(exe).read_bytes()
    if len(data) < 4 or struct.unpack_from(">I", data, 0)[0] != HUNK_HEADER:
        raise ValueError(f"{exe}: not an Amiga executable")
    pos = 4
    while True:                                   # resident library names (none in a program)
        n = struct.unpack_from(">I", data, pos)[0]
        pos += 4
        if n == 0:
            break
        pos += 4 * n
    _table, first, last = struct.unpack_from(">III", data, pos)
    pos += 12
    return [4 * (struct.unpack_from(">I", data, pos + 4 * i)[0] & 0x3FFFFFFF) for i in range(last - first + 1)]


def _checksum(body):
    return "%02x" % (sum(body) & 0xFF)


def fix_offsets(packet, sizes):
    """A qOffsets answer ($Text=..;Data=..;Bss=..#cs) with Data and Bss where the DWARF wants them."""
    m = re.fullmatch(rb"\$Text=([0-9a-fA-F]+);Data=([0-9a-fA-F]+);Bss=([0-9a-fA-F]+)#[0-9a-fA-F]{2}", packet)
    if not m:
        return packet
    text, data, bss = (int(g, 16) for g in m.groups())
    code_size = sizes[0] if sizes else 0
    data_size = sizes[1] if len(sizes) > 1 else 0
    if data:
        data = (data - code_size) & 0xFFFFFFFF
    if bss and len(sizes) > 2:
        bss = (bss - code_size - data_size) & 0xFFFFFFFF
    elif bss:                                     # no third hunk: bgdbserver repeats Data
        bss = data
    body = b"Text=%08x;Data=%08x;Bss=%08x" % (text, data, bss)
    return b"$" + body + b"#" + _checksum(body).encode()


def _pipe(src, dst, sizes=None):
    """Copies src to dst; with sizes, the server's side: its qOffsets answer is changed on the way."""
    pending = b""
    try:
        while True:
            chunk = src.recv(65536)
            if not chunk:
                break
            if sizes is None:
                dst.sendall(chunk)
                continue
            pending += chunk
            out = b""
            while True:                               # whole packets out; one not ended yet waits
                start = pending.find(b"$")
                if start < 0:
                    out, pending = out + pending, b""
                    break
                end = pending.find(b"#", start)
                if end < 0 or len(pending) < end + 3:
                    out, pending = out + pending[:start], pending[start:]
                    break
                out += pending[:start] + fix_offsets(pending[start:end + 3], sizes)
                pending = pending[end + 3:]
            if out:
                dst.sendall(out)
    except OSError:
        pass
    finally:
        for s in (src, dst):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def relay(listen_port, host, port, exe, ready=None):
    """Listens on listen_port (one gdb at a time, as bgdbserver) and joins each gdb with host:port.
    ready(): called before listening (e.g. to wait until the server is up). Runs until the process ends."""
    sizes = hunk_sizes(exe)
    if ready is not None:
        ready()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", listen_port))
    server.listen(1)
    while True:
        client, _ = server.accept()
        try:
            upstream = socket.create_connection((host, port))
        except OSError:
            client.close()
            continue
        for s in (client, upstream):
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        threading.Thread(target=_pipe, args=(client, upstream), daemon=True).start()
        threading.Thread(target=_pipe, args=(upstream, client, sizes), daemon=True).start()


def main():
    parser = argparse.ArgumentParser(description="gdb <-> bgdbserver, with the globals where gdb looks for them")
    parser.add_argument("--listen", type=int, required=True, metavar="PORT", help="the port gdb connects to")
    parser.add_argument("--to", required=True, metavar="HOST:PORT", help="bgdbserver (on the Amiga)")
    parser.add_argument("program", help="the Amiga executable being debugged (the one bgdbserver runs)")
    args = parser.parse_args()
    host, _, port = args.to.rpartition(":")
    try:
        relay(args.listen, host or "localhost", int(port), args.program)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
