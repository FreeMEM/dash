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

A test can list the exact output it must print when run on the Amiga with
"# expect-out: <line>" lines (one per printed line, in order). With --emu
those tests run in FS-UAE (tools/emu_run.py, Kickstart from $DASH_KICKSTART
or the AROS ROM built into FS-UAE) and their output is compared.
"# emu-needs: asl.library" runs a test only when $DASH_EMU_SYS/Libs has it
(tools/emu_sys_from_hdf.sh extracts Libs/ and C/ from a Workbench hard file).
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


def run_test(test_file: Path, verbose: bool = False) -> TestResult:
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
        result = subprocess.run(
            transpile_cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=30
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

    # Step 1b: lines '# expect-c: <text>' must appear in the generated C
    c_text = c_file.read_text(errors="replace")
    for line in test_file.read_text().splitlines():
        if line.startswith("# expect-c:"):
            wanted = line[len("# expect-c:"):].strip()
            if wanted not in c_text:
                return TestResult(
                    name=name,
                    passed=False,
                    transpile_ok=True,
                    compile_ok=False,
                    error_message=f"generated C lacks: {wanted}",
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

    compile_cmd = [
        gcc_path,
        "-noixemul",
        "-O2",  # same as ./dash by default
        "-I/opt/amiga/m68k-amigaos/ndk-include",
        "-L/opt/amiga/m68k-amigaos/lib",
        str(c_file),
        "-o", str(exe_file),
        "-lm",
    ]
    from compiler.softfloat import softfloat_objects, uses_float
    if uses_float(c_file.read_text()):
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
                       CTemplates.STRING_RUNTIME, CTemplates.REFCOUNT_RUNTIME])
    build_dir = PROJECT_ROOT / "build"
    build_dir.mkdir(exist_ok=True)
    src = build_dir / "runtime_host.c"
    exe = build_dir / "runtime_host"
    src.write_text(harness.replace("/*RUNTIME*/", runtime))
    build = subprocess.run(["gcc", "-std=gnu99", "-Wall", "-Wno-unused-function", "-o", str(exe), str(src)],
                           capture_output=True, text=True)
    if build.returncode != 0:
        error = "host build failed: " + build.stderr.strip()[:200]
    else:
        run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30)
        error = None if run.returncode == 0 else run.stdout.strip()[:200]
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
            build = subprocess.run(
                [gcc_path, "-noixemul", "-O2", "-I/opt/amiga/m68k-amigaos/ndk-include", f"-I{out_dir}",
                 "-L/opt/amiga/m68k-amigaos/lib", *c_files, *softfloat, "-o", str(out_dir / "a.out"), "-lm"],
                capture_output=True, text=True, timeout=120
            )
            if build.returncode != 0:
                error = build.stderr.strip()[:200]
    return TestResult(name=name, passed=error is None, transpile_ok=error is None,
                      compile_ok=error is None, error_message=error,
                      duration=time.time() - start_time)


def expected_output(test_file: Path) -> Optional[List[str]]:
    """Lines declared with '# expect-out:', or None if the test declares none."""
    lines = [l.split("# expect-out:", 1)[1].strip()
             for l in test_file.read_text().splitlines() if l.strip().startswith("# expect-out:")]
    return lines or None


def emu_needs_met(test_file: Path) -> bool:
    """'# emu-needs: x.library': run only if $DASH_EMU_SYS/Libs has it (Workbench
    libraries are not in the Kickstart ROM)."""
    needs = [l.split("# emu-needs:", 1)[1].strip()
             for l in test_file.read_text().splitlines() if l.startswith("# emu-needs:")]
    system = os.environ.get("DASH_EMU_SYS")
    missing = [n for n in needs if not (system and (Path(system) / "Libs" / n).exists())]
    if missing:
        print(f"  emu/{test_file.stem}: SKIP (needs {', '.join(missing)} in $DASH_EMU_SYS/Libs)")
    return not missing


def run_emu_tests(tests: List[Path], compiled: set, a500: bool = False) -> List[TestResult]:
    """Run the compiled tests that declare '# expect-out:' in FS-UAE, all in one boot."""
    sys.path.insert(0, str(PROJECT_ROOT / "tools"))
    from emu_run import run_programs
    selected = [(t, expected_output(t)) for t in tests
                if t.stem in compiled and expected_output(t) and emu_needs_met(t)]
    if not selected:
        return []
    start_time = time.time()
    try:
        if a500:
            # 68000: catches what a 68020 forgives (libgcc calls for 32-bit mul/div/mod,
            # odd addresses). Kickstart 3.1 A500 ROM in $DASH_KICKSTART_A500
            rom = os.environ.get("DASH_KICKSTART_A500")
            if not rom:
                raise RuntimeError("--emu-a500 needs $DASH_KICKSTART_A500 (Kickstart for the A500)")
            runs = run_programs([PROJECT_ROOT / "bin" / f"test_{t.stem}" for t, _ in selected], timeout=400,
                                kickstart=rom, extra_config="amiga_model = A500\n")
        else:
            runs = run_programs([PROJECT_ROOT / "bin" / f"test_{t.stem}" for t, _ in selected], timeout=180)
    except RuntimeError as e:
        return [TestResult(name="emu", passed=False, transpile_ok=True, compile_ok=True,
                           error_message=str(e))]
    duration = (time.time() - start_time) / len(selected)
    results = []
    for (test_file, wanted), run in zip(selected, runs):
        got = [l.rstrip() for l in (run.output or "").splitlines()]
        if run.timed_out:
            error = "timeout (program did not end)"
        elif run.rc != 0:
            error = f"return code {run.rc}"
        elif got != wanted:
            diff = next((i for i, (a, b) in enumerate(zip(got, wanted)) if a != b), min(len(got), len(wanted)))
            error = (f"output line {diff + 1}: got {got[diff] if diff < len(got) else '<end>'!r}, "
                     f"expected {wanted[diff] if diff < len(wanted) else '<end>'!r}")
        else:
            error = None
        results.append(TestResult(name=f"{'emu500' if a500 else 'emu'}/{test_file.stem}", passed=error is None,
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
        result = run_test(test_file, verbose=args.verbose)
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
    for enabled, a500, label in ((args.emu, False, "FS-UAE A1200"), (args.emu_a500, True, "FS-UAE A500")):
        if not enabled:
            continue
        print(f"Testing: emu ({label})...", flush=True)
        for result in run_emu_tests(tests, compiled, a500):
            results.append(result)
            print(f"  {result.name}: {'OK' if result.passed else 'FAIL'}")

    success = print_results(results)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
