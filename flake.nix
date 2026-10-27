{
  description = "D.A.S.H. - Dash for Amiga: compiler, m68k-amigaos-gcc toolchain, VS Code and Amiberry";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;   # VS Code
      };

      # GCC 6 (the toolchain's) does not build with the newest host compilers: gcc13 is the oldest left in nixpkgs
      hostStdenv = pkgs.gcc13Stdenv;

      python = pkgs.python3.withPackages (ps: [ ps.lark ]);

      # Everything the cross-toolchain build needs (docs/INSTALACION.md, step 2)
      buildDeps = with pkgs; [
        gnumake wget curl openssl git lhasa gperf perl patch automake autoconf
        flex bison gettext texinfo rsync which file unzip gnutar gzip bzip2 xz
        gmp.dev gmp mpfr.dev mpfr libmpc ncurses.dev readline.dev expat.dev zlib.dev
        pkg-config python3 python3.pkgs.setuptools
      ];

      # Builds bebbo's m68k-amigaos-gcc (GCC 6.5.0b) the first time and keeps it outside the
      # nix store, as the project docs do (make all + make sdk=cgx, with gdb for the debugger).
      buildToolchain = pkgs.writeShellScriptBin "dash-build-toolchain" ''
        set -euo pipefail
        prefix="''${DASH_TOOLCHAIN:?}"
        src="''${DASH_TOOLCHAIN_SRC:?}"
        if [ -e "$prefix/.dash-complete" ] && [ -z "''${1:-}" ]; then
          echo "Toolchain already installed in $prefix (dash-build-toolchain --force rebuilds it)"
          exit 0
        fi
        mkdir -p "$prefix" "$(dirname "$src")"
        if [ ! -d "$src/.git" ]; then
          git clone --depth 1 https://github.com/BlitterStudio/m68k-amigaos-gcc.git "$src"
        fi
        cd "$src"
        echo ">> Building m68k-amigaos-gcc into $prefix (30 min - 2 h, only the first time)"
        # upstream's Makefile looks for libpthread in libm020bb[32]/, newer aros-stuff builds it in libb[32]/libm020/
        sed -i 's|$(BUILD)/libpthread/libm020bb32/|$(BUILD)/libpthread/libb32/libm020/|; s|$(BUILD)/libpthread/libm020bb/|$(BUILD)/libpthread/libb/libm020/|' Makefile
        # an already configured binutils keeps the old CXXFLAGS (gdb needs C++17: no -std=gnu++14)
        for f in build-*/binutils/Makefile build-*/binutils/config.status; do
          [ -f "$f" ] && sed -i 's/ -std=gnu++14//g' "$f"
        done
        # configure refuses to run if CXXFLAGS differ from the cached ones: align the gcc caches
        find build-*/gcc -path '*/m68k-amigaos' -prune -o -name config.cache -print0 | xargs -0 -r \
          sed -i "s|^ac_cv_env_CXXFLAGS_value=.*|ac_cv_env_CXXFLAGS_value='$CXXFLAGS'|"
        rm -f build-*/binutils/gdbsupport/config.cache build-*/binutils/gdb/config.cache
        # newlib's configure (run in parallel with gdb's) needs its headers in sys-include already
        if [ -d projects/newlib-cygwin/newlib/libc/include ]; then
          mkdir -p "$prefix/m68k-amigaos/sys-include"
          rsync -a --no-group projects/newlib-cygwin/newlib/libc/include/ "$prefix/m68k-amigaos/sys-include"
          rsync -a --no-group projects/newlib-cygwin/newlib/libc/sys/amigaos/include/ "$prefix/m68k-amigaos/sys-include"
        fi
        # host side of gcc first, with the real ar/ranlib
        make gcc PREFIX="$prefix" -j"$(nproc)"
        # newlib runs the plain `ar`/`ranlib` from PATH; nix's binutils write no index for m68k objects
        shim="$src/.shim"
        mkdir -p "$shim"
        for t in ar ranlib; do
          # host archives (x86) fall back to the real tool
          printf '#!/bin/sh\n"%s/bin/m68k-amigaos-%s" "$@" && exit 0\nexec "%s" "$@"\n' "$prefix" "$t" "$(command -v "$t")" > "$shim/$t"
          chmod +x "$shim/$t"
        done
        export PATH="$shim:$PATH"
        # newlib's install leaves its archives without an index, and libstdc++'s configure cannot link
        find "$prefix/m68k-amigaos/lib" build-*/newlib \( -name libc.a -o -name libg.a -o -name libm.a \) -exec "$prefix/bin/m68k-amigaos-ranlib" {} +
        # a failed libstdc++ configure leaves a cache that the next run refuses
        if [ ! -e "$prefix/lib/gcc/m68k-amigaos/6.5.0b/libstdc++.a" ]; then
          find build-*/gcc/m68k-amigaos \( -name libstdc++-v3 -o -name libquadmath \) -type d -prune -exec rm -rf {} +
        fi
        # libgcc relinks gthr-default.h in every multilib dir while parallel compiles run: build it alone
        make libgcc PREFIX="$prefix" -j1
        make all PREFIX="$prefix" -j"$(nproc)"
        make sdk=cgx PREFIX="$prefix"
        touch "$prefix/.dash-complete"
        echo ">> Toolchain ready: $prefix"
      '';

      # nixpkgs' fs-uae does not build with GCC 16: its `numbers` clashes with std::numbers
      fsuae = pkgs.fsuae.overrideAttrs (old: {
        postPatch = (old.postPatch or "") + ''
          sed -i 's/\bnumbers\b/td_numbers/g' src/statusline.cpp
        '';
      });

      # On a non-NixOS host (SteamOS, Arch...) nix's SDL cannot find the host's GL drivers:
      # run fs-uae with nixpkgs' mesa (what nixGL does for Intel/AMD GPUs)
      fsuaeGL = pkgs.symlinkJoin {
        name = "fsuae-gl";
        paths = [ fsuae ];
        nativeBuildInputs = [ pkgs.makeWrapper ];
        postBuild = ''
          wrapProgram $out/bin/fs-uae \
            --prefix LD_LIBRARY_PATH : ${pkgs.mesa}/lib \
            --set LIBGL_DRIVERS_PATH ${pkgs.mesa}/lib/dri \
            --set __EGL_VENDOR_LIBRARY_FILENAMES ${pkgs.mesa}/share/glvnd/egl_vendor.d/50_mesa.json \
            --set __GLX_VENDOR_LIBRARY_NAME mesa
        '';
      };

      # VS Code with the Dash extension's tooling around it; the extension itself lives in editor/vscode
      code = pkgs.vscode;
    in
    {
      devShells.${system}.default = (pkgs.mkShell.override { stdenv = hostStdenv; }) {
        name = "dash-env";
        nativeBuildInputs = buildDeps ++ [
          python
          pkgs.nodejs         # npm install && npm run package (editor/vscode)
          code
          fsuaeGL             # Amiga emulator (the default of tools/emu_run.py and the tests)
          buildToolchain
        ];

        # GCC 6 sources are old C++/C: be permissive with a modern host compiler
        CFLAGS_FOR_BUILD = "-fcommon -fpermissive -Wno-error -w";
        CXXFLAGS_FOR_BUILD = "-fpermissive -Wno-error -w -std=gnu++14";
        CFLAGS = "-fcommon -w";
        CXXFLAGS = "-fpermissive -w -std=gnu++14";

        shellHook = ''
          export DASH_ROOT="$PWD"
          export DASH_TOOLCHAIN="''${DASH_TOOLCHAIN:-''${XDG_CACHE_HOME:-$HOME/.cache}/dash/amiga}"
          export DASH_TOOLCHAIN_SRC="''${XDG_CACHE_HOME:-$HOME/.cache}/dash/m68k-amigaos-gcc"
          export PATH="$DASH_TOOLCHAIN/bin:$PATH"
          export PYTHONDONTWRITEBYTECODE=1

          # the tests, emu_run.py and tools/get_*.sh use /opt/amiga as a fixed path
          if [ ! -e /opt/amiga ]; then
            echo "Hint: sudo ln -s $DASH_TOOLCHAIN /opt/amiga  (tests and tools/ use /opt/amiga)"
          fi

          if [ ! -e "$DASH_TOOLCHAIN/.dash-complete" ]; then
            echo "m68k-amigaos-gcc not found: building it now (first time only, 30 min - 2 h)..."
            dash-build-toolchain || echo "Toolchain build failed; run dash-build-toolchain again to retry"
          fi

          echo "Dash env ready. Try: ./dash examples/hola.dash -o bin/hola"
          echo "  code .                 VS Code"
          echo "  fs-uae                 Amiga emulator"
          echo "  DASH_TOOLCHAIN=$DASH_TOOLCHAIN"
        '';
      };
    };
}
