| Rutinas del runtime de dashc escritas a mano (D15): las que más tiempo se llevan en Tachyon según
| dashc/tests/perfil_pc.py (copiar textos y buscar en un diccionario). Solo para dashc: runtime/gen_lib.py
| cambia en el C del runtime las llamadas a ellas; el runtime de ./dash1 sigue con su C. Como en rt_math.s,
| d0, d1, a0 y a1 se pueden machacar; los demás registros se guardan. Argumentos en la pila, como en C.
| Cada una en su sección: el enlazador de dashc solo pone las que se usan.
| Un contador de 32 bits con dbra (que cuenta con 16): tras el dbra, "clr.w; subq.l #1; jcc" da las
| vueltas de 65.536 que falten, como hace gcc.

| void *memcpy(void *d, const void *s, size_t n)
| De 4 en 4 (16 por vuelta) si d y s tienen la misma paridad (el 68000 lee y escribe longs solo en
| direcciones pares: si los dos son impares, primero un byte); si no, o si son pocos, byte a byte.
	.section .text._memcpy,"ax"
	.align	2
	.globl	_memcpy
_memcpy:
	move.l	4(sp),a0		| d
	move.l	8(sp),a1		| s
	move.l	12(sp),d1		| n
	cmp.l	#8,d1
	jcs	5f			| pocos: byte a byte
	move.w	a0,d0
	sub.w	a1,d0
	btst	#0,d0
	jne	5f			| distinta paridad: byte a byte
	move.w	a1,d0
	btst	#0,d0
	jeq	1f
	move.b	(a1)+,(a0)+		| los dos impares: uno, y quedan pares
	subq.l	#1,d1
1:	move.l	d1,d0
	lsr.l	#4,d0			| vueltas de 16 bytes
	jra	3f
2:	move.l	(a1)+,(a0)+
	move.l	(a1)+,(a0)+
	move.l	(a1)+,(a0)+
	move.l	(a1)+,(a0)+
3:	dbra	d0,2b
	clr.w	d0
	subq.l	#1,d0
	jcc	2b
	moveq	#15,d0
	and.l	d0,d1			| lo que queda: 0 a 15
	move.w	d1,d0
	lsr.w	#2,d0
	jra	4f
31:	move.l	(a1)+,(a0)+
4:	dbra	d0,31b
	and.w	#3,d1
5:	move.l	d1,d0
	jra	7f
6:	move.b	(a1)+,(a0)+
7:	dbra	d0,6b
	clr.w	d0
	subq.l	#1,d0
	jcc	6b
	move.l	4(sp),d0
	rts

| LONG dl_dict_slot(STRPTR *keys, ULONG mask, STRPTR key)
| Como _dash_dict_slot (compiler/codegen.py): la casilla de key en la tabla (cap = mask + 1, potencia de 2), o la
| libre donde iría. El hash es el de _dash_dict_keyhash: h = h * 33 + byte desde 5381; de un texto de Dash, su
| largo de la cabecera (y el hash ya hecho de un literal de clave, _DASH_STR_HASHED); de otro, hasta el 0. Las
| claves de la tabla son textos de Dash: primero el largo, luego los bytes (de 4 en 4 si los dos son pares).
| Cabecera de un texto de Dash, delante del texto: size (con sus marcas), len, self (= dirección de la cabecera
| + _DASH_STR_KEY); el hash de un literal de clave, en el long anterior.
	.set	STR_KEY,0xDA5C7E57
	.set	STR_HASHED,0x02000000
	.section .text._dl_dict_slot,"ax"
	.align	2
	.globl	_dl_dict_slot
_dl_dict_slot:
	movem.l	d2-d5/a2-a3,-(sp)
	move.l	28(sp),a2		| keys
	move.l	32(sp),d5		| mask
	move.l	36(sp),a0		| key
	move.l	a0,d0
	btst	#0,d0
	jne	5f			| impar: no es de Dash
	lea	-12(a0),a1		| su cabecera, si es de Dash
	move.l	a1,d0
	add.l	#STR_KEY,d0
	cmp.l	8(a1),d0
	jne	5f
	move.l	4(a1),d3		| largo
	move.l	(a1),d0
	and.l	#STR_HASHED,d0
	jeq	3f
	move.l	-4(a1),d2		| el hash que puso dashc
	jra	6f
3:	move.l	#5381,d2
	move.l	d3,d4
	moveq	#0,d0
	jra	32f
31:	move.b	(a0)+,d0
	move.l	d2,d1
	lsl.l	#5,d1
	add.l	d1,d2
	add.l	d0,d2
32:	dbra	d4,31b
	clr.w	d4
	subq.l	#1,d4
	jcc	31b
	jra	6f
5:	move.l	#5381,d2		| texto de C: hasta el 0
	moveq	#0,d0
	move.l	a0,a1
51:	move.b	(a1)+,d0
	jeq	52f
	move.l	d2,d1
	lsl.l	#5,d1
	add.l	d1,d2
	add.l	d0,d2
	jra	51b
52:	move.l	a1,d3
	sub.l	a0,d3
	subq.l	#1,d3			| largo
6:	move.l	36(sp),d4		| key (para saber si es par)
	and.l	d5,d2			| i = hash & mask
7:	move.l	d2,d0
	add.l	d0,d0
	add.l	d0,d0
	move.l	0(a2,d0.l),d1		| k = keys[i]
	jeq	9f			| libre: aquí iría
	move.l	d1,a3
	cmp.l	-8(a3),d3
	jne	8f			| otro largo
	move.l	36(sp),a1
	move.l	d3,d0
	btst	#0,d4
	jne	74f			| key impar: byte a byte (k es de Dash: par)
	lsr.l	#2,d0
	jra	72f
71:	cmpm.l	(a1)+,(a3)+
	jne	8f
72:	dbra	d0,71b
	clr.w	d0
	subq.l	#1,d0
	jcc	71b
	moveq	#3,d0
	and.l	d3,d0
74:	jra	76f
75:	cmpm.b	(a1)+,(a3)+
	jne	8f
76:	dbra	d0,75b
	clr.w	d0
	subq.l	#1,d0
	jcc	75b
	jra	9f			| iguales
8:	addq.l	#1,d2
	and.l	d5,d2
	jra	7b
9:	move.l	d2,d0
	movem.l	(sp)+,d2-d5/a2-a3
	rts
