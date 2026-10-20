"""Language server for Dash (the Language Server Protocol over stdin/stdout, no dependencies).

    python3 -m compiler.lsp          # started by the VS Code extension (editor/vscode)

It uses the compiler itself (DashCompiler.analyze: parser, imports and analyzer, no C), so what the
editor says is what ./dash would say. The text of the files open in the editor goes to the compiler
as an overlay, so imports see what is being typed, not what is on disk. A document is checked a
moment after the last change (CHECK_DELAY), not on every key.

Done so far: diagnostics (errors and warnings, also those of imported modules, in their files).
"""
import json
import os
import re
import select
import sys
import traceback
import urllib.parse

from compiler.main import DashCompiler, CompilationError

CHECK_DELAY = 0.3          # seconds without changes before a document is checked
SEVERITY = {"Error": 1, "Warning": 2}


def uri_to_path(uri: str) -> str:
    return urllib.parse.unquote(urllib.parse.urlparse(uri).path)


def path_to_uri(path: str) -> str:
    return "file://" + urllib.parse.quote(os.path.abspath(path))


class Server:
    def __init__(self, fd_in: int, out):
        self.fd_in = fd_in
        self.out = out                  # binary stream for the protocol (stdout's)
        self.buffer = b""
        self.docs = {}                  # uri -> text of the open documents
        self.dirty = set()              # uris to check when the typing stops
        self.published = {}             # uri of a checked document -> uris it published diagnostics to
        self.shutting_down = False
        self.tree_cache = {}            # file -> (text, Lark tree): unchanged files are not parsed again

    # --- the wire: "Content-Length: n\r\n\r\n" + n bytes of JSON ---------------------------------
    def read_message(self, timeout):
        """The next message, or None if nothing came within timeout seconds (None: wait)."""
        while True:
            head_end = self.buffer.find(b"\r\n\r\n")
            if head_end >= 0:
                length = 0
                for line in self.buffer[:head_end].split(b"\r\n"):
                    name, _, value = line.partition(b":")
                    if name.strip().lower() == b"content-length":
                        length = int(value.strip())
                body_start = head_end + 4
                if len(self.buffer) - body_start >= length:
                    body = self.buffer[body_start:body_start + length]
                    self.buffer = self.buffer[body_start + length:]
                    return json.loads(body.decode("utf-8"))
            ready, _, _ = select.select([self.fd_in], [], [], timeout)
            if not ready:
                return None
            data = os.read(self.fd_in, 65536)
            if not data:
                sys.exit(0 if self.shutting_down else 1)
            self.buffer += data

    def send(self, message: dict):
        message["jsonrpc"] = "2.0"
        body = json.dumps(message, ensure_ascii=False).encode("utf-8")
        self.out.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
        self.out.flush()

    def notify(self, method: str, params):
        self.send({"method": method, "params": params})

    # --- the loop ------------------------------------------------------------------------------
    def run(self):
        while True:
            message = self.read_message(CHECK_DELAY if self.dirty else None)
            if message is None:
                for uri in list(self.dirty):
                    self.dirty.discard(uri)
                    if uri in self.docs:
                        self.check(uri)
                continue
            try:
                self.handle(message)
            except SystemExit:
                raise
            except Exception:   # a bug here must not take the editor's server down
                traceback.print_exc(file=sys.stderr)
                if "id" in message and "method" in message:
                    self.send({"id": message["id"], "error": {"code": -32603, "message": "internal error"}})

    def handle(self, message: dict):
        method = message.get("method")
        params = message.get("params") or {}
        if method is None:
            return                                          # a response to us: we ask nothing
        handler = getattr(self, "on_" + re.sub(r"[/$]", "_", method), None)
        if "id" in message:                                 # a request: it gets an answer
            if handler is None:
                self.send({"id": message["id"], "error": {"code": -32601, "message": f"no {method}"}})
            else:
                self.send({"id": message["id"], "result": handler(params)})
        elif handler is not None:                           # a notification
            handler(params)

    # --- lifecycle -----------------------------------------------------------------------------
    def on_initialize(self, params):
        return {
            "capabilities": {
                "textDocumentSync": {"openClose": True, "change": 1, "save": {"includeText": False}},
            },
            "serverInfo": {"name": "dash-lsp", "version": "0.1"},
        }

    def on_initialized(self, params):
        pass

    def on_shutdown(self, params):
        self.shutting_down = True
        return None

    def on_exit(self, params):
        sys.exit(0 if self.shutting_down else 1)

    # --- documents -----------------------------------------------------------------------------
    def on_textDocument_didOpen(self, params):
        doc = params["textDocument"]
        if doc.get("languageId", "dash") != "dash":
            return
        self.docs[doc["uri"]] = doc["text"]
        self.dirty.add(doc["uri"])

    def on_textDocument_didChange(self, params):
        uri = params["textDocument"]["uri"]
        changes = params.get("contentChanges") or []
        if uri in self.docs and changes:
            self.docs[uri] = changes[-1]["text"]           # full sync (textDocumentSync.change = 1)
            # only this one now (a check of dashweb with its modules takes ~1 s); the documents that
            # import it are checked again when it is saved
            self.dirty.add(uri)

    def on_textDocument_didSave(self, params):
        self.dirty.update(self.docs)

    def on_textDocument_didClose(self, params):
        uri = params["textDocument"]["uri"]
        self.docs.pop(uri, None)
        self.dirty.discard(uri)
        for target in self.published.pop(uri, set()):
            if target not in self._published_by_others(uri):
                self.notify("textDocument/publishDiagnostics", {"uri": target, "diagnostics": []})

    def _published_by_others(self, uri):
        return set().union(*[targets for other, targets in self.published.items() if other != uri])

    # --- diagnostics ---------------------------------------------------------------------------
    def check(self, uri: str):
        """Analyze the document and publish its errors (and those of its imports, in their files)."""
        path = uri_to_path(uri)
        compiler = DashCompiler()
        compiler.overlay = {uri_to_path(u): text for u, text in self.docs.items()}
        compiler.tree_cache = self.tree_cache
        found = []                                   # (path, line, column, severity, message)
        try:
            analysis = compiler.analyze(self.docs[uri], path)
            for item, severity in [(e, "Error") for e in analysis.errors] + \
                                  [(w, "Warning") for w in analysis.warnings]:
                location = item.location
                if location is not None:
                    found.append((location.filename or path, location.line, location.column, severity, item.message))
                else:
                    found.append((path, 1, 1, severity, item.message))
        except CompilationError as e:
            found.append(self._from_message(str(e), path))
        except Exception as e:                       # the compiler broke: say so, at the top
            traceback.print_exc(file=sys.stderr)
            found.append((path, 1, 1, "Error", f"error interno del compilador: {type(e).__name__}: {e}"))

        by_uri = {uri: []}
        for file, line, column, severity, message in found:
            target = path_to_uri(file)
            text = self.docs.get(target)
            if text is None:
                try:
                    with open(file, encoding="utf-8", errors="replace") as f:
                        text = f.read()
                except OSError:
                    text = ""
            by_uri.setdefault(target, []).append(self._diagnostic(text, line, column, severity, message))
        before = self.published.get(uri, set())
        self.published[uri] = set(by_uri)
        for target in before - set(by_uri) - self._published_by_others(uri):
            by_uri[target] = []                      # fixed: clear what was said there
        for target, diagnostics in by_uri.items():
            self.notify("textDocument/publishDiagnostics", {"uri": target, "diagnostics": diagnostics})

    @staticmethod
    def _from_message(message: str, path: str):
        """'file:line:col: Error: text' (a syntax or import error) as a place and a text."""
        m = re.match(r"^(.*?):(\d+):(\d+): (Error|Warning): (.*)$", message, re.S)
        if m:
            file = m.group(1) if m.group(1) not in ("", "<input>") else path
            return (file, int(m.group(2)), int(m.group(3)), m.group(4), m.group(5).strip())
        return (path, 1, 1, "Error", message)

    @staticmethod
    def _diagnostic(text: str, line: int, column: int, severity: str, message: str) -> dict:
        """A diagnostic over the word at line:column (1-based, as the compiler says them)."""
        lines = text.split("\n")
        row = max(0, min(line - 1, len(lines) - 1)) if lines else 0
        source_line = lines[row] if lines else ""
        start = max(0, min(column - 1, len(source_line)))
        word = re.match(r"[A-Za-z_][A-Za-z0-9_]*|\S", source_line[start:])
        end = start + (len(word.group(0)) if word else 0)
        if end == start:                             # at the end of the line: mark the last character
            start = max(0, start - 1)
            end = len(source_line)
        return {
            "range": {"start": {"line": row, "character": start}, "end": {"line": row, "character": end}},
            "severity": SEVERITY.get(severity, 1),
            "source": "dash",
            "message": message,
        }


def main():
    out = sys.stdout.buffer
    sys.stdout = sys.stderr          # anything the compiler prints must not get into the protocol
    Server(sys.stdin.fileno(), out).run()


if __name__ == "__main__":
    main()
