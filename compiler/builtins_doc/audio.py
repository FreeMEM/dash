"""Audio (AUDIO_FUNCTIONS)."""

GROUPS = {
    "AUDIO_FUNCTIONS": {
        "es": """\
Sonido con los cuatro canales del Amiga (Paula), por el `audio.device` del sistema: efectos (`sound_*`), música de
ProTracker (`music_*`) y tonos (`tone_play`).

**Canales.** Hay 4, del 0 al 3: el 0 y el 3 suenan por la izquierda, el 1 y el 2 por la derecha. Cada canal toca un
sonido a la vez; uno nuevo en el mismo canal corta el anterior. Se reservan al primer sonido y se devuelven al
acabar el programa.

**Sonidos.** Se cargan de un fichero IFF 8SVX sin comprimir (`sound_load`) o se hacen muestra a muestra
(`sound_create` y `sound_sample`), con un número del 0 al 31. Viven en memoria chip. Todo es asíncrono:
`sound_play` vuelve enseguida y el sonido sigue mientras el programa hace otras cosas.

**Música.** `music_load` carga un módulo de ProTracker de 4 canales; mientras suena, los canales son suyos: un
`sound_*` a la vez se pisaría con ella. Los efectos más usados están (los de la tabla del manual, sección 15).
""",
        "en": """\
Sound with the Amiga's four channels (Paula), through the system's `audio.device`: effects (`sound_*`), ProTracker
music (`music_*`) and tones (`tone_play`).

**Channels.** There are 4, 0 to 3: 0 and 3 sound on the left, 1 and 2 on the right. Each channel plays one sound at
a time; a new one on the same channel cuts the previous one. They are taken on the first sound and given back when
the program ends.

**Sounds.** They load from an uncompressed IFF 8SVX file (`sound_load`) or are built sample by sample
(`sound_create` and `sound_sample`), with a number from 0 to 31. They live in chip memory. Everything is
asynchronous: `sound_play` returns at once and the sound goes on while the program does other things.

**Music.** `music_load` loads a 4-channel ProTracker module; while it plays, the channels are its own: a `sound_*`
at the same time would clash with it. The most used effects are there (the list in the manual, section 15).
""",
        "example": "tests/test_doc_audio.dash",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_ID_ES = "- `id`: el número del sonido, de 0 a 31.\n"
_ID_EN = "- `id`: the sound's number, 0 to 31.\n"
_CH_ES = "- `channel`: el canal, de 0 a 3.\n"
_CH_EN = "- `channel`: the channel, 0 to 3.\n"

FUNCS = {
    "sound_load": _f(_ID_ES + """\
- `filename`: un fichero IFF 8SVX sin comprimir.

Lo carga con su frecuencia de muestreo (8363 si no la dice). Devuelve `false` si no se puede leer, está comprimido
o falta memoria chip.
""", _ID_EN + """\
- `filename`: an uncompressed IFF 8SVX file.

Loads it with its sample rate (8363 if it does not say). Returns `false` if it cannot be read, is compressed or
chip memory is short.
""", ["sound_play", "sound_free"]),
    "sound_create": _f(_ID_ES + """\
- `length`: cuántas muestras, 2 como poco.
- `rate`: cuántas muestras por segundo: 8000 está bien para efectos; el Amiga llega a unas 28000.

Crea un sonido en silencio en memoria chip, para llenarlo con `sound_sample`. Devuelve `false` sin memoria.
""", _ID_EN + """\
- `length`: how many samples, at least 2.
- `rate`: how many samples a second: 8000 is fine for effects; the Amiga reaches about 28000.

Creates a silent sound in chip memory, to fill with `sound_sample`. Returns `false` without memory.
""", ["sound_sample", "sound_play"]),
    "sound_sample": _f(_ID_ES + """\
- `index`: la muestra, desde 0.
- `value`: su valor, de -128 a 127.

Cambia una muestra de un sonido de `sound_create`. Una onda que sube y baja 440 veces por segundo suena como un
La.
""", _ID_EN + """\
- `index`: the sample, from 0.
- `value`: its value, -128 to 127.

Changes one sample of a `sound_create` sound. A wave going up and down 440 times a second sounds like an A.
""", ["sound_create"]),
    "sound_free": _f(_ID_ES + "\nLibera su memoria. No lo hagas mientras suena: `sound_stop` antes.\n",
                     _ID_EN + "\nFrees its memory. Not while it plays: `sound_stop` first.\n", ["sound_stop"]),
    "sound_play": _f(_ID_ES + _CH_ES + """\
Lo toca una vez en ese canal, a su frecuencia, con el volumen del canal. Vuelve enseguida. Si el canal ya sonaba,
corta lo de antes.
""", _ID_EN + _CH_EN + """\
Plays it once on that channel, at its rate, with the channel's volume. It returns at once. If the channel was
playing, it cuts what was there.
""", ["sound_loop", "sound_playing", "sound_volume"]),
    "sound_loop": _f(_ID_ES + _CH_ES + "\nLo toca una y otra vez hasta `sound_stop`. Para un motor, la lluvia o una nota sostenida.\n",
                     _ID_EN + _CH_EN + "\nPlays it over and over until `sound_stop`. For an engine, rain or a held note.\n",
                     ["sound_stop", "sound_play"]),
    "sound_stop": _f(_CH_ES + "\nCalla ese canal.\n", _CH_EN + "\nSilences that channel.\n", ["sound_play"]),
    "sound_playing": _f(_CH_ES + "\nDevuelve `true` si el canal sigue sonando.\n",
                        _CH_EN + "\nReturns `true` if the channel is still playing.\n", ["sound_play"]),
    "sound_volume": _f(_CH_ES + "- `vol`: de 0 (nada) a 64 (todo).\n\nEl volumen de ese canal, también para lo que ya suena.\n",
                       _CH_EN + "- `vol`: 0 (silent) to 64 (full).\n\nThat channel's volume, also for what is already playing.\n",
                       ["sound_period"]),
    "sound_period": _f(_CH_ES + """\
- `period`: el periodo, de 124 a 65535: la frecuencia es 3546895 dividido por él en PAL. Cuanto más bajo, más
  agudo.

Cambia el tono de lo que suena en el canal, sin volver a empezarlo. Para un motor que acelera o una sirena.
""", _CH_EN + """\
- `period`: the period, 124 to 65535: the frequency is 3546895 divided by it on PAL. The lower, the higher the
  pitch.

Changes the pitch of what plays on the channel, without restarting it. For an engine speeding up or a siren.
""", ["sound_volume"]),
    "music_load": _f("""\
- `filename`: un módulo de ProTracker de 4 canales y 31 instrumentos (M.K., M!K!, FLT4, 4CHN).

Lo carga entero en memoria chip; la música de antes se libera. No empieza a sonar hasta `music_play`. Devuelve
`false` si no se puede leer, no es de ese tipo o no cabe.
""", """\
- `filename`: a 4-channel, 31-instrument ProTracker module (M.K., M!K!, FLT4, 4CHN).

Loads it whole into chip memory; the previous music is freed. It does not start until `music_play`. Returns `false`
if it cannot be read, is not that kind or does not fit.
""", ["music_play", "music_free"]),
    "music_play": _f("Empieza a tocar la música desde el principio. Calla los sonidos que hubiera: los canales pasan a ser suyos.\n",
                     "Starts playing the music from the beginning. It silences any sounds: the channels become its own.\n",
                     ["music_stop", "music_pause"]),
    "music_stop": _f("Para la música y devuelve los canales a los `sound_*`.\n",
                     "Stops the music and gives the channels back to the `sound_*` functions.\n", ["music_play"]),
    "music_pause": _f("La deja callada donde está; `music_resume` sigue desde ahí.\n",
                      "Silences it where it is; `music_resume` carries on from there.\n", ["music_resume"]),
    "music_resume": _f("Sigue tocando después de un `music_pause`.\n", "Carries on playing after a `music_pause`.\n",
                       ["music_pause"]),
    "music_volume": _f("- `vol`: de 0 a 64.\n\nEl volumen de toda la música, para bajarla bajo los efectos o hacer un fundido.\n",
                       "- `vol`: 0 to 64.\n\nThe volume of the whole music, to lower it under the effects or fade it.\n",
                       ["music_play"]),
    "music_position": _f("""\
- `pos`: la posición en la lista de orden de la canción, desde 0; fuera de ella, 0.

Mientras suena, salta ahí, al principio del patrón: para cambiar de parte en un juego (la del menú, la del nivel).
`music_play` empieza siempre desde el principio.
""", """\
- `pos`: the position in the song's order list, from 0; outside it, 0.

While it plays, jumps there, to the start of the pattern: to switch sections in a game (the menu's, the level's).
`music_play` always starts from the beginning.
""", ["music_pos", "music_row"]),
    "music_pos": _f("Devuelve la posición de la lista de orden que suena ahora.\n",
                    "Returns the position in the order list playing now.\n", ["music_row", "music_position"]),
    "music_row": _f("Devuelve la fila del patrón que suena, de 0 a 63. Para sincronizar algo con la música.\n",
                    "Returns the pattern row playing, 0 to 63. To sync something with the music.\n", ["music_pos"]),
    "music_free": _f("Para la música si sonaba y libera su memoria.\n", "Stops the music if it was playing and frees its memory.\n",
                     ["music_load"]),
    "tone_play": _f(_CH_ES.replace("`channel`", "`channel`") + """\
- `freq`: la frecuencia en hercios: 440 es el La.
- `vol`: el volumen, de 0 a 64.
- `duration`: cuánto dura, en milisegundos.

Toca un tono puro (una onda senoidal) y vuelve enseguida, sin esperar a que acabe. Para pitidos y avisos sin
ningún fichero.
""", _CH_EN + """\
- `freq`: the frequency in hertz: 440 is A.
- `vol`: the volume, 0 to 64.
- `duration`: how long it lasts, in milliseconds.

Plays a pure tone (a sine wave) and returns at once, without waiting for it to end. For beeps and alerts without any
file.
""", ["sound_play"]),
}
