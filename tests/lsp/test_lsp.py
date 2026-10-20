"""The language server (compiler/lsp.py) spoken to as VS Code does: real JSON-RPC messages over a pipe.

    python3 -m unittest tests/lsp/test_lsp.py      (tests/run_tests.py runs them too)
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Client:
    def __init__(self):
        self.proc = subprocess.Popen([sys.executable, "-m", "compiler.lsp"], cwd=ROOT, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.next_id = 0
        self.pending = []                     # notifications that came while waiting for something else

    def send(self, message):
        message["jsonrpc"] = "2.0"
        body = json.dumps(message).encode()
        self.proc.stdin.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
        self.proc.stdin.flush()

    def read(self):
        length = 0
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise EOFError("the server ended")
            if line in (b"\r\n", b"\n"):
                break
            name, _, value = line.partition(b":")
            if name.strip().lower() == b"content-length":
                length = int(value)
        return json.loads(self.proc.stdout.read(length))

    def request(self, method, params):
        self.next_id += 1
        self.send({"id": self.next_id, "method": method, "params": params})
        while True:
            message = self.read()
            if message.get("id") == self.next_id and "method" not in message:
                return message
            self.pending.append(message)

    def notify(self, method, params):
        self.send({"method": method, "params": params})

    def diagnostics(self, uri, timeout=20):
        """The next diagnostics published for uri."""
        end = time.time() + timeout
        while time.time() < end:
            for i, message in enumerate(self.pending):
                if message.get("method") == "textDocument/publishDiagnostics" and message["params"]["uri"] == uri:
                    del self.pending[i]
                    return message["params"]["diagnostics"]
            self.pending.append(self.read())
        raise TimeoutError(uri)

    def close(self):
        try:
            self.request("shutdown", None)
            self.notify("exit", None)
            self.proc.wait(timeout=10)
        finally:
            if self.proc.poll() is None:
                self.proc.kill()
            self.proc.stdin.close()
            self.proc.stdout.close()


def uri(path):
    return "file://" + os.path.abspath(path)


class LanguageServerTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory(prefix="dash_lsp_")
        self.client = Client()
        reply = self.client.request("initialize", {"processId": None, "rootUri": uri(self.dir.name), "capabilities": {}})
        self.capabilities = reply["result"]["capabilities"]
        self.client.notify("initialized", {})

    def tearDown(self):
        self.client.close()
        self.dir.cleanup()

    def open(self, name, text):
        path = os.path.join(self.dir.name, name)
        with open(path, "w", newline="") as f:          # its line ends as they are (CRLF too)
            f.write(text)
        self.client.notify("textDocument/didOpen", {"textDocument": {
            "uri": uri(path), "languageId": "dash", "version": 1, "text": text}})
        return uri(path)

    def test_initialize_says_what_it_does(self):
        self.assertEqual(self.capabilities["textDocumentSync"]["change"], 1)

    def test_no_errors(self):
        u = self.open("bien.dash", "Main\n    x = 1\n    Print x\nend\n")
        self.assertEqual(self.client.diagnostics(u), [])

    def test_semantic_error_has_its_range(self):
        u = self.open("mal.dash", "Main\n    x = 1\n    Print x + nada\nend\n")
        [d] = self.client.diagnostics(u)
        self.assertEqual(d["severity"], 1)
        self.assertIn("nada", d["message"])
        self.assertEqual(d["range"], {"start": {"line": 2, "character": 14}, "end": {"line": 2, "character": 18}})

    def test_syntax_error(self):
        u = self.open("sintaxis.dash", "Main\n    y = (1 + 2))\nend\n")
        [d] = self.client.diagnostics(u)
        self.assertIn("sintaxis", d["message"])
        self.assertEqual(d["range"]["start"]["line"], 1)

    def test_change_fixes_the_error(self):
        u = self.open("cambia.dash", "Main\n    Print nada\nend\n")
        self.assertEqual(len(self.client.diagnostics(u)), 1)
        self.client.notify("textDocument/didChange", {"textDocument": {"uri": u, "version": 2},
                                                      "contentChanges": [{"text": "Main\n    Print 1\nend\n"}]})
        self.assertEqual(self.client.diagnostics(u), [])

    def test_error_in_an_imported_module_goes_to_its_file(self):
        module = os.path.join(self.dir.name, "modulo.dash")
        with open(module, "w") as f:
            f.write("func f() -> Int\n    return otra\nend\n")
        u = self.open("usa.dash", 'import "modulo.dash"\nMain\n    Print f()\nend\n')
        mod_diags = self.client.diagnostics(uri(module))
        self.assertEqual(len(mod_diags), 1)
        self.assertEqual(mod_diags[0]["range"]["start"]["line"], 1)
        self.assertEqual(self.client.diagnostics(u), [])

    def test_open_module_text_is_used_not_the_disk(self):
        module = os.path.join(self.dir.name, "m2.dash")
        with open(module, "w") as f:
            f.write("func g() -> Int\n    return 1\nend\n")
        self.client.notify("textDocument/didOpen", {"textDocument": {
            "uri": uri(module), "languageId": "dash", "version": 1, "text": "func g2() -> Int\n    return 1\nend\n"}})
        u = self.open("usa2.dash", 'import "m2.dash"\nMain\n    Print g2()\nend\n')
        self.assertEqual(self.client.diagnostics(u), [])

    # --- completion and signature help (after the first check: it uses the program's last analysis) ---
    PROGRAM = (
        "struct Punto\n"            # 1
        "    x: Int = 0\n"
        "    nombre: String = \"\"\n"
        "    func mover(dx: Int)\n"
        "        self.x = self.x + dx\n"   # 5
        "    end\n"
        "end\n"
        "enum Color\n"
        "    ROJO\n"
        "    VERDE\n"                    # 10
        "end\n"
        "const MAXIMO = 10\n"
        "func suma(a: Int, b: Int) -> Int\n"
        "    return a + b\n"
        "end\n"                          # 15
        "Main\n"
        "    p = Punto(1, \"a\")\n"
        "    lista = [1, 2]\n"
        "    total = suma(1, 2)\n"
        "    Print total\n"              # 20
        "end\n")

    def complete(self, u, line, character):
        reply = self.client.request("textDocument/completion", {"textDocument": {"uri": u},
                                                                "position": {"line": line, "character": character}})
        return {item["label"]: item for item in reply["result"]["items"]}

    def edit(self, u, text):
        self.client.notify("textDocument/didChange", {"textDocument": {"uri": u, "version": 2},
                                                      "contentChanges": [{"text": text}]})

    def test_completion_builtins_keywords_and_symbols(self):
        u = self.open("c1.dash", self.PROGRAM)
        self.client.diagnostics(u)
        items = self.complete(u, 19, 4)          # start of "    Print total"
        self.assertIn("mui_window_open", items)
        self.assertEqual(items["mui_window_open"]["insertText"], "mui_window_open(${1:win})")
        for name in ("while", "Main", "suma", "Punto", "Color", "MAXIMO", "p", "lista", "total"):
            self.assertIn(name, items)
        self.assertEqual(items["suma"]["detail"], "suma(a: Int, b: Int) -> Int")

    def test_completion_members(self):
        u = self.open("c2.dash", self.PROGRAM)
        self.client.diagnostics(u)
        # the user is typing "p." on line 20: the last analysis is still the one that parsed
        self.edit(u, self.PROGRAM.replace("    Print total\n", "    p.\n"))
        self.assertEqual(sorted(self.complete(u, 19, 6)), ["mover", "nombre", "x"])
        self.edit(u, self.PROGRAM.replace("    Print total\n", "    Color.\n"))
        self.assertEqual(sorted(self.complete(u, 19, 10)), ["ROJO", "VERDE"])
        self.edit(u, self.PROGRAM.replace("    Print total\n", "    lista.\n"))
        self.assertIn("push", self.complete(u, 19, 10))
        self.edit(u, self.PROGRAM.replace("            self.x = self.x + dx\n", "            self.\n"))
        self.assertIn("nombre", self.complete(u, 4, 13))

    def test_completion_types_and_imports(self):
        u = self.open("c3.dash", self.PROGRAM)
        self.client.diagnostics(u)
        self.edit(u, self.PROGRAM.replace("func suma(a: Int,", "func suma(a: Pu,"))
        types = self.complete(u, 12, 14)
        self.assertIn("Punto", types)
        self.assertIn("String", types)
        self.assertNotIn("while", types)
        with open(os.path.join(self.dir.name, "otro.dash"), "w") as f:
            f.write("func h()\nend\n")
        self.edit(u, 'import "' + "\n" + self.PROGRAM)
        self.assertIn("otro.dash", self.complete(u, 0, 8))

    def test_trigger_characters_only_where_they_mean_something(self):
        # VS Code asks when " / or . are typed (import paths, members); elsewhere nothing must open
        u = self.open("c4.dash", self.PROGRAM)
        self.client.diagnostics(u)

        def typed(line, character, char):
            reply = self.client.request("textDocument/completion", {
                "textDocument": {"uri": u}, "position": {"line": line, "character": character},
                "context": {"triggerKind": 2, "triggerCharacter": char}})
            return [i["label"] for i in reply["result"]["items"]]
        self.edit(u, self.PROGRAM.replace("    Print total\n", '    Print "adiós"\n'))
        self.assertEqual(typed(19, 17, '"'), [])                  # the closing quote of a text
        self.edit(u, self.PROGRAM.replace("    Print total\n", "    x = 1.\n"))
        self.assertEqual(typed(19, 10, "."), [])                  # a number
        self.edit(u, self.PROGRAM.replace("    Print total\n", "    x = 4 / \n"))
        self.assertEqual(typed(19, 11, "/"), [])                  # a division
        self.edit(u, self.PROGRAM.replace("    Print total\n", "    p.\n"))
        self.assertEqual(sorted(typed(19, 6, ".")), ["mover", "nombre", "x"])
        with open(os.path.join(self.dir.name, "otro2.dash"), "w") as f:
            f.write("func h()\nend\n")
        self.edit(u, 'import "' + "\n" + self.PROGRAM)
        self.assertIn("otro2.dash", typed(0, 8, '"'))

    def test_signature_help(self):
        u = self.open("s1.dash", self.PROGRAM)
        self.client.diagnostics(u)
        self.edit(u, self.PROGRAM.replace("    total = suma(1, 2)\n", "    total = suma(1, \n"))
        reply = self.client.request("textDocument/signatureHelp", {"textDocument": {"uri": u},
                                                                   "position": {"line": 18, "character": 20}})
        help_ = reply["result"]
        self.assertEqual(help_["signatures"][0]["label"], "suma(a: Int, b: Int) -> Int")
        self.assertEqual(help_["activeParameter"], 1)
        self.edit(u, self.PROGRAM.replace("    Print total\n", '    mui_window_begin("x", \n'))
        reply = self.client.request("textDocument/signatureHelp", {"textDocument": {"uri": u},
                                                                   "position": {"line": 19, "character": 26}})
        sig = reply["result"]["signatures"][0]
        self.assertTrue(sig["label"].startswith("mui_window_begin(title, id)"))
        start, end = sig["parameters"][1]["label"]
        self.assertEqual(sig["label"][start:end], "id")

    # --- hover, definition, references (PROGRAM's lines: 0-based in LSP) ---
    def at(self, method, u, line, character, **extra):
        params = {"textDocument": {"uri": u}, "position": {"line": line, "character": character}}
        params.update(extra)
        return self.client.request(method, params)["result"]

    def test_hover(self):
        u = self.open("h1.dash", self.PROGRAM)
        self.client.diagnostics(u)
        h = self.at("textDocument/hover", u, 18, 13)                 # suma in "total = suma(1, 2)"
        self.assertIn("suma(a: Int, b: Int) -> Int", h["contents"]["value"])
        h = self.at("textDocument/hover", u, 19, 11)                 # total in "Print total"
        self.assertIn("total: Int", h["contents"]["value"])
        h = self.at("textDocument/hover", u, 4, 13)                  # x in "self.x"
        self.assertIn("Punto.x: Int", h["contents"]["value"])
        self.edit(u, self.PROGRAM.replace("    Print total\n", "    mui_text(\"a\")\n"))
        h = self.at("textDocument/hover", u, 19, 6)
        self.assertIn("mui_text(text)", h["contents"]["value"])

    def test_definition_here_in_a_module_and_from_an_import(self):
        u = self.open("d1.dash", self.PROGRAM)
        self.client.diagnostics(u)
        d = self.at("textDocument/definition", u, 18, 13)            # suma -> func suma
        self.assertEqual(d["uri"], u)
        self.assertEqual(d["range"]["start"], {"line": 12, "character": 5})
        d = self.at("textDocument/definition", u, 16, 9)             # Punto( -> struct Punto
        self.assertEqual(d["range"]["start"]["line"], 0)
        d = self.at("textDocument/definition", u, 19, 11)            # total -> its assignment
        self.assertEqual(d["range"]["start"], {"line": 18, "character": 4})
        module = os.path.join(self.dir.name, "mod.dash")
        with open(module, "w") as f:
            f.write("# un módulo\nfunc doble(n: Int) -> Int\n    return n * 2\nend\n")
        u2 = self.open("d2.dash", 'import "mod.dash"\nMain\n    Print doble(2)\nend\n')
        self.client.diagnostics(u2)
        d = self.at("textDocument/definition", u2, 2, 11)
        self.assertEqual(d["uri"], uri(module))
        self.assertEqual(d["range"]["start"], {"line": 1, "character": 5})
        d = self.at("textDocument/definition", u2, 0, 10)            # inside "mod.dash"
        self.assertEqual(d["uri"], uri(module))

    def test_definition_of_a_dashui_window(self):
        import shutil
        shutil.copy(os.path.join(ROOT, "tests", "lib", "ventana_prueba.dashui"), self.dir.name)
        u = self.open("v.dash", 'import "ventana_prueba.dashui"\nMain\n    v = Prueba_create()\nend\n')
        self.client.diagnostics(u)
        d = self.at("textDocument/definition", u, 2, 10)
        self.assertTrue(d["uri"].endswith("ventana_prueba.dashui"))
        with open(os.path.join(self.dir.name, "ventana_prueba.dashui")) as f:
            line = f.read().split("\n")[d["range"]["start"]["line"]]
        self.assertRegex(line, r'"name"\s*:\s*"Prueba"')

    def test_references_and_highlight(self):
        u = self.open("r1.dash", self.PROGRAM)
        self.client.diagnostics(u)
        refs = self.at("textDocument/references", u, 13, 11, context={"includeDeclaration": True})   # a in suma
        self.assertEqual(sorted((r["range"]["start"]["line"], r["range"]["start"]["character"]) for r in refs),
                         [(12, 10), (13, 11)])                        # the parameter and its use, not other a's
        refs = self.at("textDocument/references", u, 4, 13, context={"includeDeclaration": True})    # field x
        self.assertEqual(sorted(r["range"]["start"]["line"] for r in refs), [1, 4, 4])
        marks = self.at("textDocument/documentHighlight", u, 18, 13)                                   # suma
        self.assertEqual(sorted(m["range"]["start"]["line"] for m in marks), [12, 18])

    # --- symbols and rename ---
    def test_document_symbols(self):
        u = self.open("o1.dash", self.PROGRAM)
        self.client.diagnostics(u)
        symbols = self.client.request("textDocument/documentSymbol", {"textDocument": {"uri": u}})["result"]
        self.assertEqual([s["name"] for s in symbols], ["Punto", "Color", "MAXIMO", "suma", "Main"])
        punto = symbols[0]
        self.assertEqual([c["name"] for c in punto["children"]], ["x", "nombre", "mover"])
        self.assertEqual((punto["range"]["start"]["line"], punto["range"]["end"]["line"]), (0, 6))
        self.assertEqual([c["name"] for c in symbols[1]["children"]], ["ROJO", "VERDE"])
        self.assertEqual(symbols[3]["detail"], "suma(a: Int, b: Int) -> Int")

    def test_workspace_symbols(self):
        u = self.open("w1.dash", self.PROGRAM)
        self.client.diagnostics(u)
        found = self.client.request("workspace/symbol", {"query": "sma"})["result"]
        self.assertIn("suma", [f["name"] for f in found])
        self.assertTrue(all(f["location"]["uri"] == u for f in found if f["name"] == "suma"))

    def rename(self, u, line, character, new):
        return self.client.request("textDocument/rename", {"textDocument": {"uri": u},
                                   "position": {"line": line, "character": character}, "newName": new})

    def test_rename(self):
        u = self.open("n1.dash", self.PROGRAM)
        self.client.diagnostics(u)
        edits = self.rename(u, 18, 13, "sumar")["result"]["changes"][u]           # the function
        self.assertEqual(sorted(e["range"]["start"]["line"] for e in edits), [12, 18])
        edits = self.rename(u, 13, 11, "primero")["result"]["changes"][u]         # a parameter
        self.assertEqual(sorted(e["range"]["start"]["line"] for e in edits), [12, 13])
        edits = self.rename(u, 4, 13, "posx")["result"]["changes"][u]             # a field
        self.assertEqual(sorted(e["range"]["start"]["line"] for e in edits), [1, 4, 4])
        self.assertIn("error", self.rename(u, 19, 6, "otro"))                     # Print: a keyword
        self.edit(u, self.PROGRAM.replace("    Print total\n", "    mui_text(\"a\")\n"))
        reply = self.client.request("textDocument/prepareRename", {"textDocument": {"uri": u},
                                                                   "position": {"line": 19, "character": 6}})
        self.assertIn("del lenguaje", reply["error"]["message"])
        self.assertIn("error", self.rename(u, 18, 13, "while"))                   # a keyword as the new name

    # --- formatting and quick fixes ---
    def test_formatting(self):
        messy = ("func f(a)\nif a > 1\n  return 1\n      else\nreturn 2   \n   end\nend\n"
                 "Main\n Print f(1)\n        # comentario\nend\n")
        u = self.open("f1.dash", messy)
        reply = self.client.request("textDocument/formatting", {"textDocument": {"uri": u},
                                    "options": {"tabSize": 4, "insertSpaces": True}})
        [edit] = reply["result"]
        self.assertEqual(edit["newText"], "func f(a)\n    if a > 1\n        return 1\n    else\n        return 2\n"
                                          "    end\nend\nMain\n    Print f(1)\n    # comentario\nend\n")
        self.edit(u, edit["newText"])
        reply = self.client.request("textDocument/formatting", {"textDocument": {"uri": u},
                                    "options": {"tabSize": 4, "insertSpaces": True}})
        self.assertEqual(reply["result"], [])                     # already formatted: nothing to do

    def test_formatting_keeps_windows_line_ends(self):
        # (v10 of docs/IDE_VIDEO_LOOP.md: a CRLF file always came back changed, with \n)
        good = "func f(a)\r\n    if a > 1\r\n        return 1\r\n    end\r\nend\r\n"
        u = self.open("crlf1.dash", good)
        options = {"tabSize": 4, "insertSpaces": True}
        self.assertEqual(self.client.request("textDocument/formatting", {"textDocument": {"uri": u},
                                                                          "options": options})["result"], [])
        u = self.open("crlf2.dash", good.replace("        return", "return"))
        [edit] = self.client.request("textDocument/formatting", {"textDocument": {"uri": u},
                                                                  "options": options})["result"]
        self.assertEqual(edit["newText"], good)

    def test_odd_text(self):
        # a module has no Main: not a problem; a CRLF line and a tab-indented one keep their columns
        self.assertEqual(self.client.diagnostics(self.open("modulo2.dash", "func f()\nend\n")), [])
        self.assertEqual(self.client.diagnostics(self.open("vacio.dash", "")), [])
        [d] = self.client.diagnostics(self.open("crlf3.dash", "Main\r\n    Print 1 + nada\r\nend\r\n"))
        self.assertEqual(d["range"]["start"], {"line": 1, "character": 14})
        [d] = self.client.diagnostics(self.open("tab.dash", "Main\n\tPrint 1 + nada\nend\n"))
        self.assertEqual(d["range"]["start"], {"line": 1, "character": 11})

    def test_untitled_document(self):
        # (v11: its errors went to file:///…/Untitled-1, a file that is not there: counted, not underlined)
        u = "untitled:Untitled-1"
        self.client.notify("textDocument/didOpen", {"textDocument": {
            "uri": u, "languageId": "dash", "version": 1, "text": "Main\n    Print nada\nend\n"}})
        [d] = self.client.diagnostics(u)
        self.assertIn("nada", d["message"])

    def actions(self, u, diagnostic):
        return self.client.request("textDocument/codeAction", {"textDocument": {"uri": u}, "range": diagnostic["range"],
                                   "context": {"diagnostics": [diagnostic]}})["result"]

    def test_quick_fixes(self):
        with open(os.path.join(self.dir.name, "util.dash"), "w") as f:
            f.write("func doble(n: Int) -> Int\n    return n * 2\nend\n")
        u = self.open("q1.dash", "Main\n    total = 1\n    Print doble(totl, 3)\nend\n")
        diags = self.client.diagnostics(u)
        by_name = {("doble" if "doble" in d["message"] else "totl"): d for d in diags}
        titles = [a["title"] for a in self.actions(u, by_name["doble"])]
        self.assertIn("Crear la función doble(a, b)", titles)
        self.assertIn('Importar doble de "util.dash"', titles)
        create = next(a for a in self.actions(u, by_name["doble"]) if a["title"].startswith("Crear"))
        [edit] = create["edit"]["changes"][u]
        self.assertEqual(edit["range"]["start"]["line"], 0)       # before Main
        self.assertEqual(edit["newText"], "func doble(a, b)\n    \nend\n\n")
        titles = [a["title"] for a in self.actions(u, by_name["totl"])]
        self.assertIn("Cambiar a 'total'", titles)

    def test_unknown_request_gets_an_error_not_a_crash(self):
        reply = self.client.request("textDocument/noExiste", {})
        self.assertEqual(reply["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
