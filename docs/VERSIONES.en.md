# Dash versions

*English | [Castellano](VERSIONES.md)*

What carries a number is the compiler: the language, its builtins, the runtime that goes inside every program and
the tools (`tools/`). A program already compiled does not depend on the version: it is an Amiga executable and
keeps working the same. The version tells which Dash a program needs to compile and what has changed.

`./dash --version` says which one you have. Each version is a `vX.Y.Z` tag of the repository with its page in
[Releases](https://github.com/FreeMEM/dash/releases) (the `vscode-X.Y.Z` tags belong to the VS Code extension,
which goes apart).

## What each number means

`X.Y.Z`, as in [Semantic Versioning](https://semver.org/):

- **Z (fixes):** bugs fixed, faster or smaller programs, documentation. Nothing to change in a program.
- **Y (new things):** new builtins, syntax or options. Every program that compiled still compiles and does the
  same; one that uses the new things needs this version or a later one.
- **X (breaking changes):** something no longer compiles or does something else (a builtin that changes its name or
  its arguments, a new reserved word). The release notes say what to change in each case.

Not counted as breaking: fixing a bug even if some program relied on it, different error messages, the generated
C (it may change in any version), whatever the documentation marks as experimental, and `@native` code that uses
internal functions of the runtime (`_dash_*`).

## How to update

With the repository cloned: `git pull` (or `git checkout v1.2.0` for a given version). Otherwise, the zip of the
version in Releases. The VS Code extension tells you once a day if there is a version newer than the one of the
compiler it uses (setting `dash.updates.check`; the request goes to `api.github.com`).

## Notes of each version

### 1.0.0 (2026-10-27)

The first version with a number. It gathers everything done so far (full log in [ROADMAP.md](ROADMAP.md)):

- **Language:** inferred types, `Int`, `Float` (in software) and `Fixed` (16.16), strings with interpolation,
  typed lists and dictionaries, structs with methods and interfaces, functions as values and lambdas, modules with
  a private part, automatic memory without a garbage collector (per-iteration temporaries and reference counts).
- **No Gurus from a slip:** a field of `nil` or a processor exception ends the program with a message and the
  normal clean-up; `--memcheck` checks memory and `--debug` stops in the debugger.
- **686 builtins** (94 of them MUI): Intuition, GadTools, ReAction, MUI 3.8 and 5, graphics (also RTG), sprites,
  Copper, Blitter, audio and ProTracker modules, IFF and datatypes, network (TCP, UDP and TLS with AmiSSL),
  processes, commodities, language catalogs, the clipboard, the Workbench backdrop and system monitors. List in
  [BUILTINS.en.md](BUILTINS.en.md).
- **Tools:** catalogs without FlexCat (`tools/catalogo.py`), the emulator without a window (`tools/emu_run.py`),
  benchmarks and the visual editor of MUI windows (`.dashui`).
- **VS Code:** colours, errors as you type, completion, compiling and running on the emulated Amiga, debugging
  (also on a real Amiga over the network) and the MUI visual editor. From this version it tells you about new
  versions of Dash.
- **What programs need:** Kickstart 3.0 and a 68000; MUI and TLS need a 68020. `--cpu 68020` to `68060` tunes
  the code for each processor.
- **To compile:** Python 3 with Lark and bebbo's Amiga gcc (6.5); see [INSTALACION.en.md](INSTALACION.en.md).
