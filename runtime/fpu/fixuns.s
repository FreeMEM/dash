| Para el 68881/68882 y la FPU del 68040/68060: lo enlazan ./dash --fpu (dashc/runtime/build_lib.py, en lugar de los de
| libgcc) y ./dash --gcc --fpu (dash1, delante de libgcc).
| Double a entero sin signo, de 32 y de 64 bits, hacia el cero (como C). Los de la libgcc de m68k-amigaos-gcc 6.5
| (libm020/libm881) usan fmove.l sin fintrz ni cambiar el FPCR: redondeaban al más cercano, y __fixdfdi de
| 1709164800000.0 daba 2^32 de más (cuando el bit 31 de la parte baja vale 1; lo vio Tachyon). Con el FPCR hacia el
| cero mientras tanto, como ___fixsfsi. Un valor de 2^31 a 2^32 se convierte restándole 2^31 y sumándolo luego.
	.globl	___fixunsdfsi
___fixunsdfsi:
	fmove.l	fpcr,d1
	move.l	d1,d0
	and.b	#0xcf,d0
	or.b	#0x10,d0
	fmove.l	d0,fpcr
	fmove.d	4(sp),fp0
	fcmp.s	L2e31(pc),fp0
	fbge	1f
	fmove.l	fp0,d0
	fmove.l	d1,fpcr
	rts
1:	fsub.s	L2e31(pc),fp0
	fmove.l	fp0,d0
	add.l	#0x80000000,d0
	fmove.l	d1,fpcr
	rts

| (d0 la parte alta, d1 la baja)
	.globl	___fixunsdfdi
___fixunsdfdi:
	fmove.l	fpcr,d1
	move.l	d1,a0
	move.l	d1,d0
	and.b	#0xcf,d0
	or.b	#0x10,d0
	fmove.l	d0,fpcr
	fmove.d	4(sp),fp0
	fmove.x	fp0,fp1
	fmul.s	L2em32(pc),fp1
	fcmp.s	L2e31(pc),fp1
	fbge	1f
	fmove.l	fp1,d0
	bra.s	2f
1:	fsub.s	L2e31(pc),fp1
	fmove.l	fp1,d0
	add.l	#0x80000000,d0
	| la parte alta, ya entera, otra vez en fp1 (sin signo) y por 2^32: lo que queda es la baja, exacta
2:	fmove.l	d0,fp1
	tst.l	d0
	bge.s	3f
	fadd.s	L2e32(pc),fp1
3:	fmul.s	L2e32(pc),fp1
	fsub.x	fp1,fp0
	fcmp.s	L2e31(pc),fp0
	fbge	4f
	fmove.l	fp0,d1
	bra.s	5f
4:	fsub.s	L2e31(pc),fp0
	fmove.l	fp0,d1
	add.l	#0x80000000,d1
5:	move.l	a0,-(sp)
	fmove.l	(sp)+,fpcr
	rts

	.even
L2e31:	.long	0x4f000000		| 2^31 en simple
L2e32:	.long	0x4f800000		| 2^32
L2em32:	.long	0x2f800000		| 2^-32
