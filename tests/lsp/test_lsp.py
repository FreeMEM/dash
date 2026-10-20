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
        reply = self.client.request("initialize", {"processId": None, "rootUri": None, "capabilities": {}})
        self.capabilities = reply["result"]["capabilities"]
        self.client.notify("initialized", {})

    def tearDown(self):
        self.client.close()
        self.dir.cleanup()

    def open(self, name, text):
        path = os.path.join(self.dir.name, name)
        with open(path, "w") as f:
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

    def test_unknown_request_gets_an_error_not_a_crash(self):
        reply = self.client.request("textDocument/noExiste", {})
        self.assertEqual(reply["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
