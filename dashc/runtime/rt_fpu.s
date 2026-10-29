| Las funciones de Float que llama el código de dashc (en d0, como las de fp-bit: argumentos en la pila,
| resultado en d0), con la FPU (68881, 68882 o la del 68040/68060): van en el runtime de --fpu en vez de
| fp-bit y fastfp. Una suma, resta, producto o división de simple precisión en la FPU sale redondeada igual
| que la de fp-bit (la precisión extendida da para redondear bien a 24 bits). fp0 se puede machacar.

	.text
	.align	2

	.globl	___addsf3
___addsf3:
	fmove.s	4(sp),fp0
	fadd.s	8(sp),fp0
	fmove.s	fp0,d0
	rts

	.globl	___subsf3
___subsf3:
	fmove.s	4(sp),fp0
	fsub.s	8(sp),fp0
	fmove.s	fp0,d0
	rts

	.globl	___mulsf3
___mulsf3:
	fmove.s	4(sp),fp0
	fmul.s	8(sp),fp0
	fmove.s	fp0,d0
	rts

	.globl	___divsf3
___divsf3:
	fmove.s	4(sp),fp0
	fdiv.s	8(sp),fp0
	fmove.s	fp0,d0
	rts

| Int a Float
	.globl	___floatsisf
___floatsisf:
	fmove.l	4(sp),fp0
	fmove.s	fp0,d0
	rts

| Float a Int, hacia el cero (como C): redondeo hacia el cero en el FPCR mientras tanto (fintrz no está en el
| 68040: lo emularía la 68040.library, con una excepción en cada llamada)
	.globl	___fixsfsi
___fixsfsi:
	fmove.l	fpcr,d1
	move.l	d1,d0
	and.b	#0xcf,d0
	or.b	#0x10,d0
	fmove.l	d0,fpcr
	fmove.s	4(sp),fp0
	fmove.l	fp0,d0
	fmove.l	d1,fpcr
	rts

| -1 si a < b, 0 si a == b, 1 si a > b o si alguno es nan (como el __cmpsf2 de fp-bit)
	.globl	___cmpsf2
___cmpsf2:
	fmove.s	4(sp),fp0
	fcmp.s	8(sp),fp0
	fbun	1f
	fblt	2f
	fbgt	1f
	moveq	#0,d0
	rts
1:	moveq	#1,d0
	rts
2:	moveq	#-1,d0
	rts
