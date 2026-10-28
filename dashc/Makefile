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

build/rt_blob.c: runtime/dashrt.o
	@mkdir -p build
	python3 -c 'import sys; d=open(sys.argv[1],"rb").read(); \
	print("const unsigned char dashrt_o[] = {" + ",".join(str(b) for b in d) + "};"); \
	print("const unsigned int dashrt_o_len = %d;" % len(d))' runtime/dashrt.o > $@

# el runtime de ./dash sacado por gen_lib.py, más api.c (incluido en él), libc mínima y rutinas en asm
runtime:
	@mkdir -p build
	python3 runtime/gen_lib.py build/dashlib_rt.c
	$(AMIGA)gcc -O2 -m68000 -noixemul -fomit-frame-pointer -fno-common -Iruntime -c build/dashlib_rt.c -o build/dashlib.o
	$(AMIGA)gcc -O2 -m68000 -noixemul -fomit-frame-pointer -fno-builtin -fno-tree-loop-distribute-patterns \
	  -c runtime/rt_libc.c -o build/rt_libc.o
	$(AMIGA)gcc -m68000 -c runtime/rt_math.s -o build/rt_math.o
	$(AMIGA)ld -r build/dashlib.o build/rt_libc.o build/rt_math.o -o runtime/dashrt.o

test: dashc
	python3 tests/run.py

clean:
	rm -rf dashc build

.PHONY: amiga runtime test clean
