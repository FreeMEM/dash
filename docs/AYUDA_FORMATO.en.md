*English | [Castellano](AYUDA_FORMATO.md)*

# Dash's help on the Amiga: the .ayuda format

`tools/gen_ayuda.py` makes four files out of Dash's documentation, and `tools/paquete_amiga.py` puts them in the
`Ayuda` drawer of the package (on the Amiga, `DASH:Ayuda/`):

| File | What it is |
|---|---|
| `Dash.ayuda`, `Dash_en.ayuda` | The help with indexes, for a program (Forja) to read in pieces (Spanish, English) |
| `Dash.guide`, `Dash_en.guide` | The same in AmigaGuide, for MultiView |

The sources: the builtins (`compiler/amiga_builtins.py`, `compiler/builtins_es.py`, `compiler/builtins_doc/`), the
example of each group (`tests/test_doc_*.dash`), `docs/SINTAXIS.md` and `docs/MANUAL_REFERENCIA.md`, with their
`.en.md`. The files are not in git: they are made when packaging. `tests/unit/test_gen_ayuda.py` checks that every
function has its page and that the links lead to pages that exist.

```
python3 tools/gen_ayuda.py                  # build/ayuda/
python3 tools/gen_ayuda.py --salida DIR
python3 tools/gen_ayuda.py --check          # only checks
```

## The pages

Everything is a page ("ficha"), with a unique key (letters, digits and `_`):

| Type | Key | What it has |
|---|---|---|
| `F` function | its name: `file_seek`, `RA_EVENT_CLOSE` | signature, what it does, parameters, example, see also, DashOS |
| `G` group | the one in `docs/BUILTINS.md`, lowercase: `audio_functions` | introduction, whole example, list of functions |
| `M` manual | `m6` (chapter 6), `m6_1` (its first section), `m20b`, `mx26` (the appendix) | the text of the chapter or section |
| `S` syntax | `sintaxis` | `docs/SINTAXIS.en.md` |
| `I` cover and indexes | `inicio`, `manual`, `grupos`, `indice` | lists of links |

The `m...` keys are the same in both languages (the English manual has the same sections; the generator checks it).

## The file

Latin-1 (ISO-8859-1) text, lines ending in `\n` (10). Numbers are decimal, zero-padded and fixed-width, so every
record of an index has the same length and record `i` is at `start + i * length`: one `file_seek` and one
`file_read` reach it, without loading the index.

Parts, in this order: header, page table, names, words, ids, groups, sections and the text of the pages.

### Header

A few text lines, under 512 bytes, ending in a line with a dot:

```
DASHAYUDA 1
idioma en
version 2.15.0
fichas 00000213 01277 047
nombres 00060232 01329 035
palabras 00106747 05341 039
ids 00315046 00214170
grupos 00529216 00041
secciones 00530377 00218
texto 00536910 01206024
.
```

- `DASHAYUDA 1`: the format, version 1. A reader that does not know it must not go on.
- `idioma`: the language (`es`, `en`).
- `fichas`, `nombres`, `palabras` (pages, names, words): where the table starts (byte from the beginning), how many
  records and the length of each one (with its `\n`).
- `ids`: where the id area starts and how many bytes it has.
- `grupos`, `secciones` (groups, sections): where they start and how many lines they have.
- `texto`: where the text of the pages starts and how many bytes it has.

A reader must take the widths from the header, not from this document: they may change when regenerating.

### Page table

One record per page, in the order of the text. The number of a page (its id, from 0) is its place in this table.

```
00600555 000428 I inicio
```

Position of the page (8 digits), its length in bytes (6), its type (1 letter) and its key, padded with spaces to the
record length. Columns: 0, 9, 16 and 18.

### Names

For "Help on the word under the cursor": the names sorted byte by byte, lowercase, with the id of their page.

```
file_seek                    00538
```

The name, padded with spaces to `length - 7`, a space and the id (5 digits). Every page's key is there (lowercase:
`ra_event_close`), and the words of the language and topics that lead to a section of the manual (`if`, `while`,
`struct`, `eventloop`, `window`, `nil`, `memcheck`...). Binary search: the name asked for in lowercase, compared with
the record's without its trailing spaces.

### Words and ids

The index for searching. Every word of the pages (also those in the code of the examples), folded: lowercase,
without accents, and anything that is not `a-z`, `0-9` or `_` as a separator:

| Latin-1 | Becomes |
|---|---|
| `à á â ã ä å` | `a` |
| `ç` | `c` |
| `è é ê ë` | `e` |
| `ì í î ï` | `i` |
| `ñ` | `n` |
| `ò ó ô õ ö` | `o` |
| `ù ú û ü` | `u` |
| `ý ÿ` | `y` |
| `æ ð ÷ ø þ ß` and the rest | separator |

(in code, a table with one character per code from 0xE0: `"aaaaaa ceeeeiiii nooooo  uuuuy y"`). A name with `_` is
there whole and in parts (`sound_play`, `sound`, `play`). Left out: words under 3 letters or over 24, numbers, some
empty words (`de`, `the`...) and those found in more than a quarter of the pages.

```
music                    00315046 0013
```

The word, padded to `length - 15`, a space, where its ids are (8 digits) and how many (4). The ids are 5-digit
numbers, each followed by a space except the last, followed by `\n`: id `k` of the list is at `position + k * 6`.
They go from more to fewer points: 10 if the word is in the key or the title of the page, and one for each time it
appears in its text.

As they are sorted, a binary search also gives the first word starting with a prefix, to complete what is typed.

### Groups and sections

Text lines, to show the contents without reading the pages:

```
00041 Basic graphics                (groups: id and title, in the order of docs/BUILTINS.en.md)
00003 1 1. Introduction             (sections: id, level 1 chapter or 2 section, and title)
```

### The text of a page

From its position, its length in bytes; between a page and the next there is a blank line that does not count. The
first character of each line says what it is:

| Prefix | Line |
|---|---|
| `@` | The first one: `@key type title` |
| `%` | A field: `%name value` (below) |
| `#` | A subheading |
| ` ` (space) | Text, already cut at 76 columns (77 with the prefix); lists and tables already aligned |
| `\|` | A line of code, as it is (not cut: it may go past 76) |
| `*` | A link: `*key text`. The key is another page's; the text, what is shown |
| (empty) | A blank line |

Fields of the functions: `%firma file_seek(handle, position, mode) -> Int` (signature), `%devuelve Int` (returns; `-`
if nothing), `%grupo dos_functions` (its group's key), `%dashos si|no|solo` (whether it is on DashOS,
`./dash --dashos`; `solo`: only there) and `%ejemplo tests/test_doc_ficheros.dash` (where its example comes from, if
it has one). Those of the groups: `%funciones 42` and `%ejemplo ...`. A reader must skip the fields it does not know.

The text carries no Markdown marks. Function names inside the text are not links in the `.ayuda` (in the AmigaGuide
they are); a reader can look a word of the text up in the names index to make it a link.

## Reading it from Dash

`lib/ayuda.dash` does it with little memory (a 512-byte buffer and the one of the page being read):

```dash
import "lib/ayuda.dash"

Main
    a = ayuda_abrir("DASH:Ayuda/Dash_en.ayuda")
    if a == nil
        return
    end
    for l in ayuda_ficha(a, ayuda_buscar(a, "file_seek"))
        Print l
    end
    for id in ayuda_palabra(a, "music")
        Print ayuda_clave(a, id) + ": " + ayuda_titulo(a, id)
    end
    ayuda_cerrar(a)
end
```

Also: `ayuda_fichas` (how many there are), `ayuda_tipo`, `ayuda_prefijo(a, "sou", 10)` (words starting like that) and
`ayuda_plegar`. `tests/ayuda/leer_fichas.dash` is the test: `tests/unit/test_gen_ayuda.py` runs it in the emulator
with `tests/run_tests.py --emu`.

## The AmigaGuide

One node per page, named by its key (the cover is `MAIN`), in the same order, so `Browse` goes from a group to its
functions. `@index` is the `indice` node; `Contents` (`@toc`) goes from a function to its group and from a section
to its chapter. In the text, the names of functions that have a page are links. It opens in AmigaOS 3.1's MultiView
(tried in the emulator: it needs `REXX:` and `HELP:` assigned, as on a normal Workbench); it takes a few seconds to
load, as it is 1.2 MB.
