# dashc: prueba de concepto de Dash autosuficiente (genera ejecutables de Amiga sin compilador de C).
#   make            dashc para este ordenador (solo hace falta un compilador de C del PC)
#   make amiga      dashc que corre en el Amiga (gcc de bebbo)
#   make runtime    rehace runtime/dashrt.o (gcc de bebbo y el Dash de Python); va en git para no necesitarlos
#   make test       compila tests/*.dash con dashc y con ./dash y compara su salida en FS-UAE
CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra -std=c99
AMIGA = /opt/amiga/bin/m68k-amigaos-
# los literales Double, con el s2d de Ryu (exacto; el strtod de libnix falla en la última cifra)
RYU = -I../runtime/ryu ../runtime/ryu/dash_ryu.c
# zlib para descomprimir el runtime de --memcheck (build/rt_blob.c): la de runtime/zlib, solo lo de inflate
Z = ../runtime/zlib
ZLIB = -DZ_PREFIX -DNO_GZIP -I$(Z) $(Z)/inflate.c $(Z)/inftrees.c $(Z)/inffast.c $(Z)/zutil.c $(Z)/adler32.c $(Z)/crc32.c
SRC = src/main.c src/util.c src/lexer.c src/parser.c src/gen68k.c src/hunk.c src/dashui.c

dashc: $(SRC) src/dashc.h build/rt_blob.c build/builtins_tab.c
	$(CC) $(CFLAGS) -o $@ $(SRC) build/rt_blob.c build/builtins_tab.c $(RYU) $(ZLIB)

amiga: build/dashc.amiga
# (el runtime de --memcheck va aparte, en build/dashc_mc.drt: se copia junto a dashc)
build/dashc.amiga: $(SRC) src/dashc.h build/rt_blob_amiga.c build/dashc_mc.drt build/builtins_tab.c
	$(AMIGA)gcc -O2 -m68000 -noixemul -std=c99 -o $@ $(SRC) build/rt_blob_amiga.c build/builtins_tab.c $(RYU) $(ZLIB) \
		build/softfloat_df.o build/softfloat.o build/fastfp.o -lm   # (el float por software, como ./dash: el de la ROM se cuelga en FS-UAE)

# lo que pide y devuelve cada builtin (la tabla va en git: no hace falta Python para construir dashc)
build/builtins_tab.c: runtime/builtins_tab.c
	@mkdir -p build
	cp runtime/builtins_tab.c $@

# los dos runtimes dentro de dashc, ya preparados (dashc --preparar: leídos, con los textos troceados y los
# nombres atados; si no, eso costaba 5 s en cada compilación en un A1200): el normal tal cual y el de --memcheck
# comprimido. build/preparar es dashc sin runtime dentro.
build/rt_stub.c:
	@mkdir -p build
	echo 'const unsigned char rt_normal[1], rt_mc_z[1]; const unsigned int rt_normal_len, rt_mc_zlen, rt_mc_len;' > $@
build/preparar: $(SRC) src/dashc.h build/rt_stub.c build/builtins_tab.c
	$(CC) $(CFLAGS) -o $@ $(SRC) build/rt_stub.c build/builtins_tab.c $(RYU) $(ZLIB)
build/dashrt.drt: runtime/dashrt.o build/preparar
	build/preparar --preparar $< $@
build/dashrt_mc.drt: runtime/dashrt_mc.o build/preparar
	build/preparar --preparar $< $@
build/rt_blob.c: build/dashrt.drt build/dashrt_mc.drt runtime/rt_blob.py
	python3 runtime/rt_blob.py build/dashrt.drt build/dashrt_mc.drt > $@
build/rt_blob_amiga.c: build/dashrt.drt runtime/rt_blob.py
	python3 runtime/rt_blob.py build/dashrt.drt - > $@
build/dashc_mc.drt: build/dashrt.drt build/dashrt_mc.drt runtime/rt_blob.py
	python3 runtime/rt_blob.py build/dashrt.drt build/dashrt_mc.drt $@

# el runtime de ./dash (gen_lib.py), compilado y con lo que necesita: runtime/build_lib.py
runtime:
	python3 runtime/build_lib.py
	python3 runtime/gen_builtins_tab.py runtime/builtins_tab.c

test: dashc
	python3 tests/run.py

clean:
	rm -rf dashc build

.PHONY: amiga runtime test clean
