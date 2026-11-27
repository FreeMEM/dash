"""tools/doc_indices.py: el índice y los enlaces de vuelta de docs/*.md (lo pidió Ferrán García). Pasarlo dos veces
da lo mismo, quitar() devuelve el documento sin nada de lo suyo y cada enlace interno de los documentos y de
BUILTINS.md lleva a un ancla que existe.

    python3 -m unittest tests/unit/test_doc_indices.py      (tests/run_tests.py lo corre también)
"""
import re
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
import doc_indices  # noqa: E402

EJEMPLO = """# Título

Intro.

## Uno
texto
```
## dentro de código: no cuenta
```

## Dos `con código`
más

---

## Uno
repetido
"""


def anclas(md: str) -> set:
    ids = set(re.findall(r'<a id="([^"]+)"', md))
    ids |= {doc_indices.slug(l.lstrip("#")) for l in md.splitlines() if l.startswith("#")}
    return ids


class TestDocIndices(unittest.TestCase):
    def test_ejemplo(self):
        hecho = doc_indices.poner(EJEMPLO, "es")
        self.assertIn("- [Uno](#uno)", hecho)
        self.assertIn("- [Dos `con código`](#dos-con-código)", hecho)
        self.assertIn("- [Uno](#uno-1)", hecho)                  # el repetido, numerado como en GitHub
        self.assertNotIn("dentro de código", hecho.split("<!-- /indice -->")[0])
        self.assertEqual(hecho.count("[Volver al índice](#indice)"), 3)
        # el enlace de vuelta, antes de la raya que separa los apartados
        self.assertIn("más\n\n[Volver al índice](#indice)\n\n---", hecho)
        self.assertEqual(doc_indices.poner(hecho, "es"), hecho)
        self.assertEqual(doc_indices.quitar(hecho), EJEMPLO)

    def test_documentos(self):
        for doc in doc_indices.DOCS:
            for lang, nombre in (("es", f"{doc}.md"), ("en", f"{doc}.en.md")):
                with self.subTest(nombre):
                    md = (RAIZ / "docs" / nombre).read_text()
                    self.assertEqual(doc_indices.poner(md, lang), md, "python3 tools/doc_indices.py")
                    self.assertEqual(doc_indices.poner(doc_indices.quitar(md), lang), md)
                    ids = anclas(md)
                    rotos = [x for x in re.findall(r"\]\(#([^)]+)\)", md) if x not in ids]
                    self.assertEqual(rotos, [])

    def test_builtins(self):
        for nombre in ("BUILTINS.md", "BUILTINS.en.md"):
            with self.subTest(nombre):
                md = (RAIZ / "docs" / nombre).read_text()
                ids = anclas(md)
                rotos = sorted({x for x in re.findall(r"\]\(#([^)]+)\)", md) if x not in ids})
                self.assertEqual(rotos, [])


if __name__ == "__main__":
    unittest.main()
