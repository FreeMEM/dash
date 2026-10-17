#!/usr/bin/env python3
"""
Dash Language Test Runner

Runs all .dash test files and reports results.
Tests pass if they:
1. Transpile to C without errors
2. Compile to Amiga executable without errors

Usage:
    python3 tests/run_tests.py           # Run all tests
    python3 tests/run_tests.py test_x    # Run specific test
    python3 tests/run_tests.py --verbose # Show detailed output
    python3 tests/run_tests.py --emu     # Also run tests with "# expect-out:" in FS-UAE
    python3 tests/run_tests.py --emu --emu-a500 --emu-32   # on all three emulated machines

A test can list the exact output it must print when run on the Amiga with
"# expect-out: <line>" lines (one per printed line, in order). With --emu
those tests run in FS-UAE (tools/emu_run.py, Kickstart from $DASH_KICKSTART
or the AROS ROM built into FS-UAE) and their output is compared.
"# emu-needs: asl.library" runs a test only when $DASH_EMU_SYS has Libs/asl.library
(or Classes/ for a .class, .gadget or .image; tools/emu_sys_from_hdf.sh extracts them
from a Workbench hard file).

Machines (EMU_MACHINES): --emu is an A1200 with Kickstart 3.1, --emu-a500 an A500
(68000) with 3.1 ($DASH_KICKSTART_A500), --emu-32 an A1200 with AmigaOS 3.2
($DASH_KICKSTART_32 and $DASH_EMU_SYS_32: the files of a 3.2 Workbench).
Tests with "# emu-net: PORT" run in their own boot with FS-UAE's bsdsocket.library (the PC's
network) and an echo server on 127.0.0.1:PORT of the PC (one line in, "eco: <line>" out);
"# emu-net-tls: PORT" makes it a TLS server. Tests with "# emu-needs: amisslmaster.library" boot
the system in $DASH_EMU_SYS_SSL / $DASH_EMU_SYS_32_SSL (tools/emu_sys_amissl.sh), not on the A500.
Tests with "# emu-needs: muimaster.library" run in a second boot with MUI 5 installed
($DASH_EMU_SYS_MUI, $DASH_EMU_SYS_32_MUI: tools/emu_sys_mui.sh); not on the A500 (MUI needs a 68020).
"# emu-shot: SECONDS X Y RRGGBB" (repeatable) runs a test in its own boot with a screenshot that many
seconds after boot (tools/emu_run.py --screenshot, all of them in the same run): pixel X,Y of the front
screen must have that colour. Not on the A500 (reading the screen takes seconds there).
"# fpu" builds a test as ./dash --fpu and runs it on a 68040 (with C:SetPatch and 68040.library from the
Workbench files, tools/emu_sys_from_hdf.sh); not on the A500.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import time

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    transpile_ok: bool
    compile_ok: bool
    error_message: Optional[str] = None
    duration: float = 0.0
    compile_skipped: bool = False


def find_tests(test_dir: Path, pattern: Optional[str] = None) -> List[Path]:
    """Find all test files."""
    tests = []
    for f in sorted(test_dir.glob("*.dash")):
        if pattern is None or pattern in f.stem:
            tests.append(f)
    return tests


def autoclose_seconds(test_file: Path) -> str:
    """'# autoclose: N': built in test mode (DASH_TEST_AUTOCLOSE, as tools/emu_run.py --autoclose)."""
    for l in test_file.read_text().splitlines():
        if l.strip().startswith("# autoclose:"):
            return l.split("# autoclose:", 1)[1].strip()
    return ""


def wants_profile(test_file: Path) -> bool:
    """'# profile': built as ./dash --profile (dashweb D23)."""
    return any(l.strip() == "# profile" for l in test_file.read_text().splitlines())


def ignored_output(test_file: Path) -> List[str]:
    """'# ignore-out: <prefix>': output lines starting so are not compared (they change run to run)."""
    return [l.split("# ignore-out:", 1)[1].strip()
            for l in test_file.read_text().splitlines() if l.strip().startswith("# ignore-out:")]


def wants_fpu(test_file: Path) -> bool:
    """'# fpu': built as ./dash --fpu (68020 + 68881 code) and, with --emu, run on a 68040 (D46)."""
    return any(l.strip() == "# fpu" for l in test_file.read_text().splitlines())


def wants_memcheck(test_file: Path) -> bool:
    """'# memcheck': the test itself is about --memcheck (its summary is expected output)."""
    return any(l.strip() == "# memcheck" for l in test_file.read_text().splitlines())


def check_memcheck(lines: List[str]) -> Optional[str]:
    """--memcheck run of a test: no warnings, and nothing alive at exit but what escaped."""
    import re
    errors = [l for l in lines if l.startswith("memcheck: ERROR")]
    if errors:
        return errors[0]
    summary = [l for l in lines if l.startswith("memcheck: vivos")]
    if not summary:
        return "memcheck: no exit summary"
    m = re.match(r"memcheck: vivos (\d+) objetos y (\d+) strings \(escapados (\d+) y (\d+)\), errores (\d+)",
                 summary[-1])
    if not m:
        return f"memcheck: unreadable summary {summary[-1]!r}"
    objs, strs, obj_esc, str_esc, errs = map(int, m.groups())
    if errs or objs > obj_esc or strs > str_esc:
        return summary[-1]
    return None


def run_test(test_file: Path, verbose: bool = False, memcheck: bool = False) -> TestResult:
    """Run a single test."""
    name = test_file.stem
    start_time = time.time()

    build_dir = PROJECT_ROOT / "build"
    bin_dir = PROJECT_ROOT / "bin"
    build_dir.mkdir(exist_ok=True)
    bin_dir.mkdir(exist_ok=True)

    c_file = build_dir / f"{name}.c"
    exe_file = bin_dir / f"test_{name}"

    # Step 1: Transpile to C
    transpile_cmd = [
        sys.executable, "-m", "compiler.main",
        str(test_file), "-o", str(c_file)
    ]

    try:
        mc = memcheck or wants_memcheck(test_file)
        result = subprocess.run(
            transpile_cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=30,
            env=dict(os.environ, DASH_MEMCHECK_C="1" if mc else "0",
                     DASH_PROFILE="1" if wants_profile(test_file) else "0",
                     DASH_TEST_AUTOCLOSE=autoclose_seconds(test_file))
        )
        transpile_ok = result.returncode == 0

        if not transpile_ok:
            duration = time.time() - start_time
            error_msg = result.stderr.strip() if result.stderr else "Transpilation failed"
            if verbose:
                print(f"  Transpile error: {error_msg}")
            return TestResult(
                name=name,
                passed=False,
                transpile_ok=False,
                compile_ok=False,
                error_message=error_msg,
                duration=duration
            )
    except subprocess.TimeoutExpired:
        return TestResult(
            name=name,
            passed=False,
            transpile_ok=False,
            compile_ok=False,
            error_message="Transpilation timeout",
            duration=30.0
        )
    except Exception as e:
        return TestResult(
            name=name,
            passed=False,
            transpile_ok=False,
            compile_ok=False,
            error_message=str(e),
            duration=time.time() - start_time
        )

    # Step 1b: lines '# expect-c: <text>' must appear in the generated C, and
    # '# expect-no-c: <text>' must not ("\\n" in it stands for a line break)
    c_text = c_file.read_text(errors="replace")
    # with --memcheck the C has its checks (_DASH_NN...): the expected C is the normal one
    for line in ([] if memcheck and not wants_memcheck(test_file) else test_file.read_text().splitlines()):
        problem = None
        if line.startswith("# expect-c:"):
            wanted = line[len("# expect-c:"):].strip()
            if wanted not in c_text:
                problem = f"generated C lacks: {wanted}"
        elif line.startswith("# expect-no-c:"):
            unwanted = line[len("# expect-no-c:"):].strip().replace("\\n", "\n")
            if unwanted in c_text:
                problem = f"generated C has: {unwanted}"
        if problem:
            return TestResult(
                name=name,
                passed=False,
                transpile_ok=True,
                compile_ok=False,
                error_message=problem,
                duration=time.time() - start_time
            )

    # Step 2: Compile C to Amiga executable
    gcc_path = "/opt/amiga/bin/m68k-amigaos-gcc"
    if not os.path.exists(gcc_path):
        # Skip compilation if GCC not available
        duration = time.time() - start_time
        if verbose:
            print(f"  GCC not found, skipping compilation")
        return TestResult(
            name=name,
            passed=True,  # Pass if transpilation worked
            transpile_ok=True,
            compile_ok=False,
            duration=duration,
            compile_skipped=True
        )

    from compiler.cflags import opt_flags
    compile_cmd = [
        gcc_path,
        "-noixemul",
        *opt_flags(),  # same as ./dash by default (compiler/cflags.py)
        "-I/opt/amiga/m68k-amigaos/ndk-include",
        "-L/opt/amiga/m68k-amigaos/lib",
        str(c_file),
        "-o", str(exe_file),
        "-lm",
    ]
    # '# memcheck' (or run_tests.py --memcheck): built as ./dash --memcheck
    if memcheck or wants_memcheck(test_file):
        compile_cmd.insert(1, "-DDASH_MEMCHECK")
    if wants_fpu(test_file):   # as ./dash --fpu
        compile_cmd[1:1] = ["-m68020", "-m68881"]
    from compiler.cflags import mui_flags
    try:   # MUI SDK headers (tools/get_mui_sdk.sh), same as ./dash
        compile_cmd[1:1] = mui_flags([c_file.read_text()])
        from compiler.cflags import amissl_flags   # AmiSSL SDK (tools/get_amissl.sh)
        compile_cmd[1:1] = amissl_flags([c_file.read_text()])
        from compiler.cflags import link_flags     # @link (dashweb D10), as ./dash
        link_includes, link_files = link_flags([c_file.read_text()])
        compile_cmd[1:1] = link_includes
        compile_cmd[compile_cmd.index(str(c_file)) + 1:compile_cmd.index(str(c_file)) + 1] = link_files
    except FileNotFoundError as e:
        return TestResult(name=name, passed=False, transpile_ok=True, compile_ok=False,
                          error_message=str(e), duration=time.time() - start_time)
    from compiler.softfloat import softfloat_objects, uses_float
    if uses_float(c_file.read_text()) and not wants_fpu(test_file):
        compile_cmd[-3:-3] = softfloat_objects(gcc_path)  # same as ./dash

    try:
        result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        compile_ok = result.returncode == 0

        if not compile_ok:
            duration = time.time() - start_time
            error_msg = result.stderr.strip() if result.stderr else "Compilation failed"
            if verbose:
                print(f"  Compile error: {error_msg}")
            return TestResult(
                name=name,
                passed=False,
                transpile_ok=True,
                compile_ok=False,
                error_message=error_msg,
                duration=duration
            )
    except subprocess.TimeoutExpired:
        return TestResult(
            name=name,
            passed=False,
            transpile_ok=True,
            compile_ok=False,
            error_message="Compilation timeout",
            duration=60.0
        )
    except Exception as e:
        return TestResult(
            name=name,
            passed=False,
            transpile_ok=True,
            compile_ok=False,
            error_message=str(e),
            duration=time.time() - start_time
        )

    duration = time.time() - start_time
    return TestResult(
        name=name,
        passed=True,
        transpile_ok=True,
        compile_ok=True,
        duration=duration
    )


def run_error_test(test_file: Path) -> TestResult:
    """Run a test that must fail to transpile with an expected message.

    The file declares the message with a line '# expect: <text>'.
    """
    name = f"errors/{test_file.stem}"
    start_time = time.time()
    expected = None
    for line in test_file.read_text().splitlines():
        if line.startswith("# expect:"):
            expected = line[len("# expect:"):].strip()
            break

    result = subprocess.run(
        [sys.executable, "-m", "compiler.main", str(test_file),
         "-o", str(PROJECT_ROOT / "build" / f"err_{test_file.stem}.c")],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=30
    )
    output = result.stdout + result.stderr
    duration = time.time() - start_time

    if expected is None:
        error = "missing '# expect:' line"
    elif result.returncode == 0:
        error = f"transpiled but should fail with: {expected}"
    elif expected not in output:
        error = f"expected '{expected}', got: {output.strip()[:200]}"
    else:
        error = None

    return TestResult(name=name, passed=error is None, transpile_ok=False,
                      compile_ok=False, error_message=error, duration=duration)


def run_runtime_host_test() -> Optional[TestResult]:
    """Build and run tests/runtime/host_harness.c with the host gcc.
    Returns None when no host gcc is available."""
    import shutil
    if not shutil.which("gcc"):
        return None
    from compiler.codegen import CTemplates
    start_time = time.time()
    harness = (PROJECT_ROOT / "tests" / "runtime" / "host_harness.c").read_text()
    runtime = "".join([CTemplates.MEMORY_RUNTIME, CTemplates.ARRAY_RUNTIME,
                       CTemplates.STRING_RUNTIME, CTemplates.REFCOUNT_RUNTIME, CTemplates.FIXED_RUNTIME])
    build_dir = PROJECT_ROOT / "build"
    build_dir.mkdir(exist_ok=True)
    src = build_dir / "runtime_host.c"
    exe = build_dir / "runtime_host"
    src.write_text(harness.replace("/*RUNTIME*/", runtime))
    # normal build, then the --memcheck build with AddressSanitizer (catches a
    # runtime that reads or writes outside its blocks) when the host gcc has it
    error = None
    for flags in ([], ["-DDASH_MEMCHECK", "-fsanitize=address,undefined", "-g"]):
        build = subprocess.run(["gcc", "-std=gnu99", "-Wall", "-Wno-unused-function", *flags, "-o", str(exe), str(src), "-lm"],
                               capture_output=True, text=True)
        if build.returncode != 0 and flags:
            build = subprocess.run(["gcc", "-std=gnu99", "-Wall", "-Wno-unused-function", "-DDASH_MEMCHECK",
                                    "-o", str(exe), str(src), "-lm"], capture_output=True, text=True)
        tag = " (memcheck)" if flags else ""
        if build.returncode != 0:
            error = f"host build failed{tag}: " + build.stderr.strip()[:200]
            break
        # the pool is deleted at exit without freeing each block: not leaks
        run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=60,
                             env=dict(os.environ, ASAN_OPTIONS="detect_leaks=0"))
        if run.returncode != 0:
            error = (run.stdout.strip() + " " + run.stderr.strip())[:300] + tag
            break
    return TestResult(name="runtime/host", passed=error is None, transpile_ok=True,
                      compile_ok=error is None, error_message=error,
                      duration=time.time() - start_time)


def run_multifile_test(test_file: Path) -> TestResult:
    """Transpile a test that imports modules with --multifile and compile every .c."""
    import shutil
    name = f"multifile/{test_file.stem}"
    start_time = time.time()
    out_dir = PROJECT_ROOT / "build" / f"{test_file.stem}_multi"
    shutil.rmtree(out_dir, ignore_errors=True)
    result = subprocess.run(
        [sys.executable, "-m", "compiler.main", str(test_file), "-o", str(out_dir), "--multifile"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=60
    )
    error = None
    if result.returncode != 0:
        error = (result.stderr or "multifile transpile failed").strip()[:200]
    else:
        gcc_path = "/opt/amiga/bin/m68k-amigaos-gcc"
        if os.path.exists(gcc_path):
            c_files = [str(f) for f in sorted(out_dir.glob("*.c"))]
            from compiler.softfloat import softfloat_objects, uses_float
            softfloat = (softfloat_objects(gcc_path)
                         if any(uses_float(Path(f).read_text()) for f in c_files) else [])
            from compiler.cflags import mui_flags
            from compiler.cflags import link_flags
            try:   # MUI SDK headers when a module uses MUI; @link files (dashweb D10)
                mui = mui_flags(Path(f).read_text() for f in c_files)
                link_includes, link_files = link_flags([Path(f).read_text() for f in c_files])
            except FileNotFoundError as e:
                mui, link_includes, link_files, error = [], [], [], str(e)
            build = subprocess.run(
                [gcc_path, "-noixemul", "-O2", "-I/opt/amiga/m68k-amigaos/ndk-include", f"-I{out_dir}", *mui,
                 *link_includes, "-L/opt/amiga/m68k-amigaos/lib", *c_files, *link_files, *softfloat,
                 "-o", str(out_dir / "a.out"), "-lm"],
                capture_output=True, text=True, timeout=120
            )
            if build.returncode != 0 and not error:
                error = build.stderr.strip()[:200]
    return TestResult(name=name, passed=error is None, transpile_ok=error is None,
                      compile_ok=error is None, error_message=error,
                      duration=time.time() - start_time)


def expected_output(test_file: Path) -> Optional[List[str]]:
    """Lines declared with '# expect-out:', or None if the test declares none."""
    lines = [l.split("# expect-out:", 1)[1].strip()
             for l in test_file.read_text().splitlines() if l.strip().startswith("# expect-out:")]
    return lines or None


# Emulated machines: option, result prefix, label, Kickstart and Workbench files
# variables (None: FS-UAE's defaults), FS-UAE options, timeout for the whole boot (all
# the tests of a machine run in one boot; --memcheck builds are slower, and other
# sessions may be running emulators at the same time)
EMU_MACHINES = [
    dict(option="emu", prefix="emu", label="FS-UAE A1200", rom_env=None, sys_env="DASH_EMU_SYS",
         mui_sys_env="DASH_EMU_SYS_MUI", config="", timeout=360, workbench=False),
    # 68000: catches what a 68020 forgives (libgcc calls for 32-bit mul/div/mod, odd addresses)
    dict(option="emu_a500", prefix="emu500", label="FS-UAE A500", rom_env="DASH_KICKSTART_A500",
         sys_env="DASH_EMU_SYS", mui_sys_env=None, config="amiga_model = A500\n", timeout=700, workbench=False),
    # AmigaOS 3.2: the current system, and the only one with ReAction. Its window.class
    # waits for the Workbench, so LoadWB runs first, as on a real Amiga
    dict(option="emu_32", prefix="emu32", label="FS-UAE A1200 OS 3.2", rom_env="DASH_KICKSTART_32",
         sys_env="DASH_EMU_SYS_32", mui_sys_env="DASH_EMU_SYS_32_MUI", config="", timeout=480, workbench=True),
]


def emu_needs(test_file: Path) -> List[str]:
    return [l.split("# emu-needs:", 1)[1].strip()
            for l in test_file.read_text().splitlines() if l.startswith("# emu-needs:")]


def emu_args(test_file: Path) -> str:
    """'# emu-args: uno "dos tres"': what follows the program name in the Shell (dashweb D19)."""
    for l in test_file.read_text().splitlines():
        if l.startswith("# emu-args:"):
            return l.split(":", 1)[1].strip()
    return ""


def emu_shots(test_file: Path) -> List[tuple]:
    """'# emu-shot: SECONDS X Y RRGGBB' lines: (seconds, x, y, colour)."""
    shots = []
    for l in test_file.read_text().splitlines():
        if l.startswith("# emu-shot:"):
            seconds, x, y, rgb = l.split(":", 1)[1].split()
            shots.append((float(seconds), int(x), int(y), int(rgb, 16)))
    return shots


def png_pixel(png: Path, x: int, y: int) -> int:
    """0xRRGGBB of a pixel of a PNG made by tools/emu_run.py (8-bit RGB, filter 0 on every row)."""
    import struct
    import zlib
    data = png.read_bytes()
    width = struct.unpack(">I", data[16:20])[0]
    pos, idat = 8, b""
    while pos < len(data):
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        if data[pos + 4:pos + 8] == b"IDAT":
            idat += data[pos + 8:pos + 8 + size]
        pos += 12 + size
    rows = zlib.decompress(idat)
    at = y * (1 + width * 3) + 1 + x * 3
    return (rows[at] << 16) | (rows[at + 1] << 8) | rows[at + 2]


def emu_net_port(test_file: Path) -> Optional[int]:
    """'# emu-net: PORT' (dashweb D8): the test uses the network. It runs in a boot with FS-UAE's
    bsdsocket.library (the PC's network) and, on 127.0.0.1:PORT of the PC, an echo server that
    reads one line and answers "eco: <line>" before closing."""
    for l in test_file.read_text().splitlines():
        if l.startswith("# emu-net:") or l.startswith("# emu-net-tls:"):
            return int(l.split(":", 1)[1].strip())
    return None


def emu_net_tls(test_file: Path) -> bool:
    """'# emu-net-tls: PORT' (dashweb D11): the echo server speaks TLS, with a certificate for
    127.0.0.1 and localhost signed by the test CA of tools/emu_sys_amissl.sh."""
    return any(l.startswith("# emu-net-tls:") for l in test_file.read_text().splitlines())


class _EchoServer:
    """The server of '# emu-net:' tests, in a thread while the emulator runs (TLS on tls_ports)."""
    def __init__(self, ports, tls_ports=()):
        import socketserver
        import threading
        context = self._tls_context() if tls_ports else None

        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                line = self.rfile.readline()
                self.wfile.write(b"eco: " + line)

        class TLSServer(socketserver.ThreadingTCPServer):
            def get_request(self):
                sock, addr = super().get_request()
                return context.wrap_socket(sock, server_side=True), addr

            def handle_error(self, request, client_address):
                pass   # a client that refuses the certificate (a test of that) is not an error here

        socketserver.ThreadingTCPServer.allow_reuse_address = True
        self.servers = [(TLSServer if port in tls_ports else socketserver.ThreadingTCPServer)(("127.0.0.1", port), Handler)
                        for port in ports]
        for server in self.servers:
            threading.Thread(target=server.serve_forever, daemon=True).start()

    @staticmethod
    def _tls_context():
        """A certificate for 127.0.0.1/localhost signed by the test CA (openssl on the PC)."""
        import ssl
        import subprocess
        import tempfile
        ca = Path(os.path.expanduser("~/.cache/dash-amissl/testca"))
        tmp = Path(tempfile.mkdtemp(prefix="dash_tls_"))
        subprocess.run(["openssl", "req", "-newkey", "rsa:2048", "-nodes", "-subj", "/CN=localhost",
                        "-keyout", tmp / "srv.key", "-out", tmp / "srv.csr"], check=True, capture_output=True)
        (tmp / "ext.cnf").write_text("subjectAltName=DNS:localhost,IP:127.0.0.1\n")
        subprocess.run(["openssl", "x509", "-req", "-in", tmp / "srv.csr", "-CA", ca / "ca.pem", "-CAkey",
                        ca / "ca.key", "-CAcreateserial", "-CAserial", tmp / "ca.srl", "-days", "2",
                        "-extfile", tmp / "ext.cnf", "-out", tmp / "srv.pem"], check=True, capture_output=True)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(tmp / "srv.pem", tmp / "srv.key")
        return context

    def close(self):
        for server in self.servers:
            server.shutdown()
            server.server_close()


def emu_needs_met(test_file: Path, system: Optional[str], prefix: str = "emu") -> bool:
    """'# emu-needs: x.library': run only if the Workbench files have it (they are not
    in the Kickstart ROM): Libs/x.library (or MUI/Libs), or Classes/... for a class, gadget or image."""
    needs = emu_needs(test_file)

    def found(name):
        if not system:
            return False
        if name.endswith(".library"):
            return any((Path(system) / d / name).exists() for d in ("Libs", "MUI/Libs", "AmiSSL/Libs"))
        return any(p.name.lower() == name.lower() for p in (Path(system) / "Classes").rglob("*"))

    missing = [n for n in needs if not found(n)]
    if missing:
        print(f"  {prefix}/{test_file.stem}: SKIP (needs {', '.join(missing)} in the Workbench files)")
    return not missing


def run_emu_tests(tests: List[Path], compiled: set, machine: dict = EMU_MACHINES[0],
                  memcheck: bool = False) -> List[TestResult]:
    """Run the compiled tests that declare '# expect-out:' in FS-UAE, all in one boot
    (and the MUI ones, '# emu-needs: muimaster.library', in a second boot with MUI installed)."""
    prefix = machine["prefix"]
    rom = os.environ.get(machine["rom_env"]) if machine["rom_env"] else None
    if machine["rom_env"] and not rom:
        return [TestResult(name=prefix, passed=False, transpile_ok=True, compile_ok=True,
                           error_message=f"--{machine['option'].replace('_', '-')} needs ${machine['rom_env']}")]
    runnable = [t for t in tests if t.stem in compiled and expected_output(t)]
    shot_tests = [t for t in runnable if emu_shots(t)]
    fpu_tests = [t for t in runnable if wants_fpu(t) and t not in shot_tests]
    runnable = [t for t in runnable if t not in shot_tests and t not in fpu_tests]
    mui = [t for t in runnable if "muimaster.library" in emu_needs(t)]
    net = [t for t in runnable if emu_net_port(t) is not None and t not in mui]
    results = run_emu_boot([t for t in runnable if t not in mui and t not in net], machine, rom,
                           os.environ.get(machine["sys_env"]), memcheck)
    if net:
        # AmiSSL (tls_*): a system with it installed, $<sys_env>_SSL (tools/emu_sys_amissl.sh); 68020+
        ssl_tests = [t for t in net if "amisslmaster.library" in emu_needs(t)]
        plain = [t for t in net if t not in ssl_tests]
        ssl_system = os.environ.get(machine["sys_env"] + "_SSL")
        if ssl_tests and "A500" in machine["config"]:
            for t in ssl_tests:
                print(f"  {prefix}/{t.stem}: SKIP (AmiSSL needs a 68020)")
            ssl_tests = []
        elif ssl_tests and not ssl_system:
            for t in ssl_tests:
                print(f"  {prefix}/{t.stem}: SKIP (needs ${machine['sys_env']}_SSL, see tools/emu_sys_amissl.sh)")
            ssl_tests = []
        servers = plain + ssl_tests
        if servers:
            server = _EchoServer(sorted({emu_net_port(t) for t in servers}),
                                 {emu_net_port(t) for t in servers if emu_net_tls(t)})
            try:
                if plain:
                    results += run_emu_boot(plain, machine, rom, os.environ.get(machine["sys_env"]), memcheck,
                                            extra_config="bsdsocket_library = 1\n")
                if ssl_tests:
                    results += run_emu_boot(ssl_tests, machine, rom, ssl_system, memcheck,
                                            extra_config="bsdsocket_library = 1\n")
            finally:
                server.close()
    if mui and not machine["mui_sys_env"]:
        for t in mui:   # MUI 5 for AmigaOS 3 is built for the 68020
            print(f"  {prefix}/{t.stem}: SKIP (MUI needs a 68020)")
    elif mui:
        mui_system = os.environ.get(machine["mui_sys_env"])
        if not mui_system:
            for t in mui:
                print(f"  {prefix}/{t.stem}: SKIP (needs ${machine['mui_sys_env']}, see tools/emu_sys_mui.sh)")
        else:
            results += run_emu_boot(mui, machine, rom, mui_system, memcheck)
    if shot_tests and "A500" in machine["config"]:
        # on the 68000 reading the screen takes seconds (the picture changes half-way) and the boot
        # shell's console window comes in front: not a place for timed pictures
        for t in shot_tests:
            print(f"  {prefix}/{t.stem}: SKIP (screenshots are not timed on the A500)")
        shot_tests = []
    if fpu_tests:
        # '# fpu': a 68040, whose FPU leaves some instructions to 68040.library (C:SetPatch loads it,
        # tools/emu_run.py runs it on a 68040; tools/emu_sys_from_hdf.sh copies both)
        system = os.environ.get(machine["sys_env"])
        fpu_machine = dict(machine, config=machine["config"] + "cpu = 68040\nfpu = 68040\n")
        if "A500" in machine["config"]:
            for t in fpu_tests:
                print(f"  {prefix}/{t.stem}: SKIP (--fpu is 68020 code)")
            fpu_tests = []
        elif not system or not (Path(system) / "C" / "SetPatch").exists():
            for t in fpu_tests:
                print(f"  {prefix}/{t.stem}: SKIP (needs C/SetPatch and Libs/68040.library in "
                      f"${machine['sys_env']}, see tools/emu_sys_from_hdf.sh)")
            fpu_tests = []
        if fpu_tests:
            results += run_emu_boot(fpu_tests, fpu_machine, rom, system, memcheck)
    for t in shot_tests:   # each in its own boot: the screenshots are timed from the boot
        system = os.environ.get(machine["mui_sys_env"] if "muimaster.library" in emu_needs(t) else machine["sys_env"])
        results += run_emu_boot([t], machine, rom, system, memcheck, shots=emu_shots(t))
    return results


def run_emu_boot(tests: List[Path], machine: dict, rom: Optional[str], system: Optional[str],
                 memcheck: bool, extra_config: str = "", shots: List[tuple] = ()) -> List[TestResult]:
    """Run these tests in one boot of the machine with these Workbench files (shots: emu_shots of
    the only test, checked after it)."""
    sys.path.insert(0, str(PROJECT_ROOT / "tools"))
    from emu_run import run_programs
    prefix = machine["prefix"]
    selected = [(t, expected_output(t)) for t in tests if emu_needs_met(t, system, prefix)]
    if not selected:
        return []
    start_time = time.time()
    shot_dir = PROJECT_ROOT / "build" / "shots"
    shot_files = [shot_dir / f"{prefix}_{selected[0][0].stem}_{i}.png" for i in range(len(shots))]
    if shots:
        shot_dir.mkdir(parents=True, exist_ok=True)
        for f in shot_files:
            f.unlink(missing_ok=True)
    try:
        runs = run_programs([PROJECT_ROOT / "bin" / f"test_{t.stem}" for t, _ in selected],
                            args=[emu_args(t) for t, _ in selected],
                            timeout=machine["timeout"], kickstart=rom, extra_config=machine["config"] + extra_config,
                            system=system, workbench=machine["workbench"],
                            screenshot=[(s[0], f) for s, f in zip(shots, shot_files)] or None)
    except RuntimeError as e:
        return [TestResult(name=prefix, passed=False, transpile_ok=True, compile_ok=True,
                           error_message=str(e))]
    duration = (time.time() - start_time) / len(selected)
    results = []
    for (test_file, wanted), run in zip(selected, runs):
        got = [l.rstrip() for l in (run.output or "").splitlines()]
        mc_error = None
        if memcheck and not wants_memcheck(test_file):
            uses_memory = "#define _DASH_MEMORY_RUNTIME" in (PROJECT_ROOT / "build" / f"{test_file.stem}.c").read_text()
            mc_error = check_memcheck(got) if uses_memory and not run.timed_out else None
            got = [l for l in got if not l.startswith("memcheck:")]
        for prefix_ignored in ignored_output(test_file):
            got = [l for l in got if not l.startswith(prefix_ignored)]
        if run.timed_out:
            error = "timeout (program did not end)"
        elif run.rc != 0:
            error = f"return code {run.rc}"
        elif got != wanted:
            diff = next((i for i, (a, b) in enumerate(zip(got, wanted)) if a != b), min(len(got), len(wanted)))
            error = (f"output line {diff + 1}: got {got[diff] if diff < len(got) else '<end>'!r}, "
                     f"expected {wanted[diff] if diff < len(wanted) else '<end>'!r}")
        else:
            error = mc_error
        for (seconds, x, y, rgb), f in zip(shots, shot_files):
            if error:
                break
            if not f.exists():
                error = f"no screenshot at {seconds} s"
            elif png_pixel(f, x, y) != rgb:
                error = f"screenshot at {seconds} s: pixel {x},{y} is {png_pixel(f, x, y):06x}, expected {rgb:06x}"
        results.append(TestResult(name=f"{prefix}/{test_file.stem}", passed=error is None,
                                  transpile_ok=True, compile_ok=True,
                                  error_message=error, duration=duration))
    return results


def print_results(results: List[TestResult]):
    """Print test results summary."""
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    skipped = sum(1 for r in results if r.compile_skipped)

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    # Show failed tests first
    for r in results:
        if not r.passed:
            print(f"  FAIL: {r.name}")
            if r.error_message:
                # Truncate long error messages
                msg = r.error_message[:100] + "..." if len(r.error_message) > 100 else r.error_message
                print(f"        {msg}")

    # Show passed tests
    for r in results:
        if r.passed:
            tag = "PASS (transpile only)" if r.compile_skipped else "PASS"
            print(f"  {tag}: {r.name} ({r.duration:.2f}s)")

    print("-" * 60)
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")

    if failed == 0:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {failed} test(s) failed")

    if skipped:
        print(f"\n! GCC not found: {skipped} test(s) only transpiled, C not compiled")

    return failed == 0


def main():
    parser = argparse.ArgumentParser(description="Dash Language Test Runner")
    parser.add_argument("pattern", nargs="?", help="Test name pattern to filter")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--emu", action="store_true",
                        help="Also run tests with '# expect-out:' lines in FS-UAE")
    parser.add_argument("--emu-a500", action="store_true",
                        help="Also run them on an emulated A500 (68000; needs $DASH_KICKSTART_A500)")
    parser.add_argument("--emu-32", action="store_true",
                        help="Also run them on an A1200 with AmigaOS 3.2 (needs $DASH_KICKSTART_32 "
                             "and $DASH_EMU_SYS_32)")
    parser.add_argument("--memcheck", action="store_true",
                        help="Build every test as ./dash --memcheck; with --emu, a test also fails on a memory "
                             "warning or on objects/strings alive at exit that did not escape")
    args = parser.parse_args()

    test_dir = PROJECT_ROOT / "tests"

    if not test_dir.exists():
        print(f"Error: Test directory not found: {test_dir}")
        sys.exit(1)

    tests = find_tests(test_dir, args.pattern)

    if not tests and not list((test_dir / "errors").glob("*.dash")):
        print("No tests found")
        sys.exit(1)

    print(f"Running {len(tests)} test(s)...")
    print("-" * 60)

    results = []
    for test_file in tests:
        print(f"Testing: {test_file.stem}...", end=" ", flush=True)
        result = run_test(test_file, verbose=args.verbose, memcheck=args.memcheck)
        results.append(result)

        if result.passed and result.compile_skipped:
            print("OK (transpile only)")
        elif result.passed:
            print("OK")
        else:
            print("FAIL")

    error_dir = test_dir / "errors"
    for test_file in find_tests(error_dir, args.pattern) if error_dir.exists() else []:
        print(f"Testing: errors/{test_file.stem}...", end=" ", flush=True)
        result = run_error_test(test_file)
        results.append(result)
        print("OK" if result.passed else "FAIL")

    # Tests that import modules are also built in --multifile mode
    for test_file in tests:
        if "import " not in test_file.read_text():
            continue
        print(f"Testing: multifile/{test_file.stem}...", end=" ", flush=True)
        result = run_multifile_test(test_file)
        results.append(result)
        print("OK" if result.passed else "FAIL")

    if args.pattern is None or args.pattern in "docs/builtins":
        print("Testing: docs/builtins...", end=" ", flush=True)
        start_time = time.time()
        check = subprocess.run([sys.executable, str(PROJECT_ROOT / "tools" / "gen_builtins_doc.py"), "--check"],
                               capture_output=True, text=True)
        results.append(TestResult(name="docs/builtins", passed=check.returncode == 0,
                                  transpile_ok=True, compile_ok=True,
                                  error_message=check.stdout.strip() or None,
                                  duration=time.time() - start_time))
        print("OK" if check.returncode == 0 else "FAIL")

    if args.pattern is None or args.pattern in "runtime":
        print("Testing: runtime/host...", end=" ", flush=True)
        result = run_runtime_host_test()
        if result is None:
            print("SKIP (no host gcc)")
        else:
            results.append(result)
            print("OK" if result.passed else "FAIL")

    compiled = {r.name for r in results if r.passed and r.compile_ok}
    for machine in EMU_MACHINES:
        if not getattr(args, machine["option"]):
            continue
        print(f"Testing: emu ({machine['label']})...", flush=True)
        for result in run_emu_tests(tests, compiled, machine, args.memcheck):
            results.append(result)
            print(f"  {result.name}: {'OK' if result.passed else 'FAIL'}")

    success = print_results(results)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
