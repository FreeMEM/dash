"""Expresiones largas por --gcc (lo pidió Forja): los pasos del Dash de Python recorren el árbol de forma
recursiva, y 562 líneas de "texto" + "texto" (un fichero de Forja) pasaban del tope de recursión de Python
("maximum recursion depth exceeded"). compiler/main.py corre en un hilo con pila grande y un tope alto, y las
preguntas sobre los dos lados de cada + se recuerdan (memo_pred): antes, una suma de 80 variables tardaba 10 s."""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def transpile(src):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "largo.dash")
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        r = subprocess.run([sys.executable, "-m", "compiler.main", path, "-o", os.path.join(tmp, "largo.c")],
                           cwd=ROOT, capture_output=True, text=True)
        c = ""
        if r.returncode == 0:
            with open(os.path.join(tmp, "largo.c"), encoding="latin-1") as f:
                c = f.read()
        return r, c


class DeepExpr(unittest.TestCase):
    def test_long_concat(self):
        n = 3000
        body = " +\n".join(f'        "linea {i}\\n"' for i in range(n))
        r, c = transpile(f"func texto() -> String\n    return {body.lstrip()}\nend\n\nMain\n    Print texto()\nend\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f'"linea {n - 1}\\n"', c)

    def test_long_sum(self):
        body = " + ".join(f"x{i % 3}" for i in range(600))
        r, _ = transpile(f"Main\n    x0 = 1\n    x1 = 2\n    x2 = 3\n    y = {body}\n    Print y\nend\n")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_exit_code(self):
        """sys.exit dentro del hilo llega al proceso: un error de compilación sale con 1"""
        r, _ = transpile("Main\n    x = y\nend\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("'y' is not defined", r.stderr)


if __name__ == "__main__":
    unittest.main()
