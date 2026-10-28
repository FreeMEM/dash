| Multiplicar y dividir enteros de 32 bits en un 68000, que solo tiene mulu/muls
| y divu/divs de 16 bits. Entrada en d0 y d1, resultado en d0. Como en el resto
| del runtime, d0, d1, a0 y a1 se pueden machacar; los demás registros se guardan.

	.text
	.align	2

| En un 68020 o mejor (__dash_cpu020, de rt.c) los caminos lentos son una sola
| instrucción de 32 bits. Van como .short: el ensamblador está en modo 68000.
	.macro	MULS_L_D1_D0
	.short	0x4C01,0x0800	| muls.l d1,d0
	.endm
	.macro	DIVS_L_D1_D0
	.short	0x4C41,0x0800	| divs.l d1,d0
	.endm
	.macro	DIVSL_L_D1_D1_D0
	.short	0x4C41,0x0801	| divsl.l d1,d1:d0 (resto en d1)
	.endm

| d0 = d0 * d1 (los 32 bits bajos; el signo da igual)
	.globl	__dash_mul
__dash_mul:
	move.w	d0,a0		| ¿caben los dos en 16 bits con signo? muls.w
	cmp.l	a0,d0		| (move.w a un registro de dirección extiende el signo)
	jne	1f
	move.w	d1,a0
	cmp.l	a0,d1
	jne	1f
	muls.w	d1,d0
	rts
1:	tst.b	__dash_cpu020
	jeq	2f
	MULS_L_D1_D0
	rts
2:	move.l	d2,-(sp)
	move.l	d3,-(sp)	| a*b = alo*blo + ((ahi*blo + alo*bhi) << 16)
	move.w	d1,d2
	mulu.w	d0,d2		| d2 = alo*blo
	move.l	d1,d3
	swap	d3
	mulu.w	d0,d3		| d3 = alo*bhi
	swap	d0
	mulu.w	d1,d0		| d0 = ahi*blo
	add.w	d3,d0
	swap	d0
	clr.w	d0
	add.l	d2,d0
	move.l	(sp)+,d3
	move.l	(sp)+,d2
	rts

| Camino rápido de / y %: dividendo >= 0, divisor de 1 a 65535 y cociente de 16
| bits: un solo divu.w, que deja resto:cociente en d0. Si no, salta a 9f.
	.macro	DIVU_RAPIDO
	tst.l	d0
	jmi	9f
	cmp.l	#0xFFFF,d1
	jhi	9f		| también un divisor negativo (sin signo es enorme)
	tst.w	d1
	jeq	9f		| divisor 0: el camino lento da el error
	move.l	d0,a0
	swap	d0
	cmp.w	d1,d0
	jcc	8f		| parte alta del dividendo >= divisor: no cabe
	move.l	a0,d0
	divu.w	d1,d0
	.endm

| d0 = d0 / d1, redondeando hacia cero (como en C)
	.globl	__dash_div
__dash_div:
	DIVU_RAPIDO
	swap	d0
	clr.w	d0
	swap	d0		| el cociente, sin el resto
	rts
8:	move.l	a0,d0
9:	tst.b	__dash_cpu020
	jeq	1f
	tst.l	d1
	jeq	__dash_div_zero
	DIVS_L_D1_D0
	rts
1:	move.l	d3,-(sp)
	move.l	d0,d3
	eor.l	d1,d3		| bit 31 de d3: el signo del cociente
	tst.l	d0
	jpl	5f
	neg.l	d0
5:	tst.l	d1
	jpl	2f
	neg.l	d1
2:	jbsr	__dash_udivmod
	tst.l	d3
	jpl	3f
	neg.l	d0
3:	move.l	(sp)+,d3
	rts

| d0 = d0 % d1, con el signo del dividendo (como en C)
	.globl	__dash_mod
__dash_mod:
	DIVU_RAPIDO
	clr.w	d0
	swap	d0		| el resto
	rts
8:	move.l	a0,d0
9:	tst.b	__dash_cpu020
	jeq	1f
	tst.l	d1
	jeq	__dash_div_zero
	DIVSL_L_D1_D1_D0
	move.l	d1,d0
	rts
1:	move.l	d3,-(sp)
	move.l	d0,d3
	tst.l	d0
	jpl	1f
	neg.l	d0
1:	tst.l	d1
	jpl	2f
	neg.l	d1
2:	jbsr	__dash_udivmod
	move.l	d1,d0
	tst.l	d3
	jpl	3f
	neg.l	d0
3:	move.l	(sp)+,d3
	rts

| sin signo: d0 = d0 / d1, d1 = d0 % d1. Un divisor 0 es un error del programa.
__dash_udivmod:
	tst.l	d1
	jeq	__dash_div_zero
	move.l	d2,-(sp)
	cmp.l	#0xFFFF,d1
	jhi	3f
	moveq	#0,d2		| divisor de 16 bits: dos divu.w
	swap	d0
	move.w	d0,d2		| d2 = parte alta del dividendo
	divu.w	d1,d2		| d2 = resto1:cociente1
	move.w	d2,d0
	swap	d0		| d0 = cociente1:parte baja
	move.w	d0,d2		| d2 = resto1:parte baja
	divu.w	d1,d2		| d2 = resto2:cociente2
	move.w	d2,d0		| d0 = cociente1:cociente2
	clr.w	d2
	swap	d2
	move.l	d2,d1
	move.l	(sp)+,d2
	rts
3:	move.l	d3,-(sp)	| divisor de más de 16 bits: bit a bit
	moveq	#0,d2		| resto
	moveq	#31,d3
4:	add.l	d0,d0		| el bit alto del dividendo pasa a X...
	addx.l	d2,d2		| ...y entra en el resto
	cmp.l	d1,d2
	jcs	5f
	sub.l	d1,d2
	addq.l	#1,d0		| bit del cociente
5:	dbra	d3,4b
	move.l	d2,d1
	move.l	(sp)+,d3
	move.l	(sp)+,d2
	rts
