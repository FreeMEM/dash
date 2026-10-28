| Lo que libnix y amiga.lib daban al C del runtime y dashc no lleva (runtime/build_lib.py).
|
| Las bases de librería que libnix abre sola (LayersBase, UtilityBase): cada una va en una sección con
| su función de abrir y cerrar, y un puntero débil (__dash_weak_lib_*) a esa función. Si el programa no
| usa la base, hunk.c deja fuera la sección y el puntero vale 0 (_dash_init y _dash_finish lo miran).

	.macro	LIB name, base, file
	.section .text.dl_lib_\name,"ax"
	.globl	_\base
_\base:	.long	0
| dl_lib_\name(abrir): abre la librería (1) o la cierra (0)
dl_lib_\name:
	move.l	a6,-(sp)
	move.l	4.w,a6
	tst.l	8(sp)
	jeq	1f
	lea	2f(pc),a1
	moveq	#37,d0
	jsr	-552(a6)		| OpenLibrary
	move.l	d0,_\base
	jra	3f
1:	move.l	_\base,d0
	jeq	3f
	move.l	d0,a1
	jsr	-414(a6)		| CloseLibrary
	clr.l	_\base
3:	move.l	(sp)+,a6
	rts
2:	.asciz	"\file"
	.even
	.section .data.dl_weak_lib_\name,"aw"
	.globl	__dash_weak_lib_\name
__dash_weak_lib_\name:
	.long	dl_lib_\name
	.endm

	LIB	layers, LayersBase, layers.library
	LIB	utility, UtilityBase, utility.library

| DoMethod(obj, id, ...) y DoMethodA(obj, msg) de amiga.lib: el despachador de la clase del objeto
| (OCLASS(obj), la palabra de antes) con a0 = clase, a2 = objeto y a1 = mensaje
	.section .text.dl_domethod,"ax"
	.globl	_DoMethod
	.globl	_DoMethodA
_DoMethod:
	lea	8(sp),a1
	jra	1f
_DoMethodA:
	move.l	8(sp),a1
1:	movem.l	a2-a3,-(sp)
	move.l	12(sp),d0
	jeq	2f
	move.l	d0,a2
	move.l	-4(a2),a0
	move.l	8(a0),a3		| cl_Dispatcher.h_Entry
	jsr	(a3)
2:	movem.l	(sp)+,a2-a3
	rts

| BeginIO(io) de amiga.lib: la función BEGINIO (-30) del dispositivo de la petición (io_Device, a 20)
	.section .text.dl_beginio,"ax"
	.globl	_BeginIO
_BeginIO:
	move.l	4(sp),a1
	move.l	a6,-(sp)
	move.l	20(a1),a6
	jsr	-30(a6)
	move.l	(sp)+,a6
	rts

| DoSuperMethod(cl, obj, id, ...) y DoSuperMethodA(cl, obj, msg) de amiga.lib: el despachador de la clase madre
| (cl_Super, a 24) con a0 = esa clase, a2 = objeto y a1 = mensaje (0 si falta la clase o el objeto)
	.section .text.dl_dosuper,"ax"
	.globl	_DoSuperMethod
	.globl	_DoSuperMethodA
_DoSuperMethod:
	lea	12(sp),a1
	jra	1f
_DoSuperMethodA:
	move.l	12(sp),a1
1:	movem.l	a2-a3,-(sp)
	moveq	#0,d0
	move.l	12(sp),a0		| cl
	move.l	16(sp),a2		| obj
	move.l	a2,d1
	jeq	2f
	move.l	a0,d1
	jeq	2f
	move.l	24(a0),a0		| cl_Super
	move.l	8(a0),a3		| h_Entry
	jsr	(a3)
2:	movem.l	(sp)+,a2-a3
	rts
