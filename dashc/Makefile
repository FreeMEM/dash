# dashc: prueba de concepto de Dash autosuficiente (genera ejecutables de Amiga sin compilador de C).
#   make            dashc para este ordenador (solo hace falta un compilador de C del PC)
#   make amiga      dashc que corre en el Amiga (gcc de bebbo)
#   make runtime    rehace runtime/dashrt.o (gcc de bebbo y el Dash de Python); va en git para no necesitarlos
#   make test       compila tests/*.dash con dashc y con ./dash y compara su salida en FS-UAE
CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra -std=c99
AMIGA = /opt/amiga/bin/m68k-amigaos-
SRC = src/main.c src/util.c src/lexer.c src/parser.c src/gen68k.c src/hunk.c

dashc: $(SRC) src/dashc.h build/rt_blob.c
	$(CC) $(CFLAGS) -o $@ $(SRC) build/rt_blob.c

amiga: build/dashc.amiga
build/dashc.amiga: $(SRC) src/dashc.h build/rt_blob.c
	$(AMIGA)gcc -O2 -m68000 -noixemul -std=c99 -o $@ $(SRC) build/rt_blob.c

# los dos runtimes (normal y --memcheck), como arrays de C dentro de dashc
build/rt_blob.c: runtime/dashrt.o runtime/dashrt_mc.o
	@mkdir -p build
	python3 -c 'import sys; \
	[print("const unsigned char %s[] = {%s};\nconst unsigned int %s_len = %d;" % (n, ",".join(str(b) for b in d), n, len(d))) \
	 for n, d in (("dashrt_o", open(sys.argv[1],"rb").read()), ("dashrt_mc_o", open(sys.argv[2],"rb").read()))]' \
	runtime/dashrt.o runtime/dashrt_mc.o > $@

# el runtime de ./dash sacado por gen_lib.py, más api.c (incluido en él), libc mínima y rutinas en asm
runtime:
	@mkdir -p build
	python3 runtime/gen_lib.py build/dashlib_rt.c
	$(AMIGA)gcc -O2 -m68000 -noixemul -fomit-frame-pointer -fno-common -ffunction-sections -fdata-sections -Iruntime -c build/dashlib_rt.c -o build/dashlib.o
	$(AMIGA)gcc -O2 -m68000 -noixemul -fomit-frame-pointer -fno-common -ffunction-sections -fdata-sections -Iruntime \
	  -DDASH_MEMCHECK -c build/dashlib_rt.c -o build/dashlib_mc.o
	$(AMIGA)gcc -O2 -m68000 -noixemul -fomit-frame-pointer -fno-builtin -fno-tree-loop-distribute-patterns -ffunction-sections \
	  -c runtime/rt_libc.c -o build/rt_libc.o
	$(AMIGA)gcc -m68000 -c runtime/rt_math.s -o build/rt_math.o
	# sin ld -r, que juntaría las secciones: los objetos uno tras otro (hunk.c lee las unidades)
	cat build/dashlib.o build/rt_libc.o build/rt_math.o > runtime/dashrt.o
	cat build/dashlib_mc.o build/rt_libc.o build/rt_math.o > runtime/dashrt_mc.o

test: dashc
	python3 tests/run.py

clean:
	rm -rf dashc build

.PHONY: amiga runtime test clean
