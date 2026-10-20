"""Language server for Dash (the Language Server Protocol over stdin/stdout, no dependencies).

    python3 -m compiler.lsp          # started by the VS Code extension (editor/vscode)

It uses the compiler itself (DashCompiler.analyze: parser, imports and analyzer, no C), so what the
editor says is what ./dash would say. The text of the files open in the editor goes to the compiler
as an overlay, so imports see what is being typed, not what is on disk. A document is checked a
moment after the last change (CHECK_DELAY), not on every key.

Done so far: diagnostics (errors and warnings, also those of imported modules, in their files),
completion (builtins with their parameters, keywords, the program's symbols, the variables seen at the
cursor, members after "x.", types after ":", files after import ") and signature help.
"""
import json
import os
import re
import select
import sys
import time
import traceback
import urllib.parse

from compiler.main import DashCompiler, CompilationError
from compiler import lsp_index

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
        self.dirty = {}                 # uri -> time of its last change: checked CHECK_DELAY after it
        self.published = {}             # uri of a checked document -> uris it published diagnostics to
        self.shutting_down = False
        self.tree_cache = {}            # file -> (text, Lark tree): unchanged files are not parsed again
        self.programs = {}              # uri -> program of the last analysis that parsed (completion...)

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
            # the delay counts from the last change of each document, not from the last message
            # (completion requests while typing come more often than CHECK_DELAY)
            timeout = None
            if self.dirty:
                timeout = max(0.0, min(self.dirty.values()) + CHECK_DELAY - time.monotonic())
            message = self.read_message(timeout)
            now = time.monotonic()
            for uri, changed in list(self.dirty.items()):
                if now - changed >= CHECK_DELAY:
                    del self.dirty[uri]
                    if uri in self.docs:
                        self.check(uri)
            if message is None:
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
                "completionProvider": {"triggerCharacters": [".", '"', "/"]},
                "signatureHelpProvider": {"triggerCharacters": ["(", ","], "retriggerCharacters": [","]},
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
        self.dirty[doc["uri"]] = time.monotonic()

    def on_textDocument_didChange(self, params):
        uri = params["textDocument"]["uri"]
        changes = params.get("contentChanges") or []
        if uri in self.docs and changes:
            self.docs[uri] = changes[-1]["text"]           # full sync (textDocumentSync.change = 1)
            # only this one now (a check of dashweb with its modules takes ~1 s); the documents that
            # import it are checked again when it is saved
            self.dirty[uri] = time.monotonic()

    def on_textDocument_didSave(self, params):
        now = time.monotonic()
        for uri in self.docs:
            self.dirty.setdefault(uri, now)

    def on_textDocument_didClose(self, params):
        uri = params["textDocument"]["uri"]
        self.docs.pop(uri, None)
        self.dirty.pop(uri, None)
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
            self.programs[uri] = analysis.program
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

    # --- completion and signatures ------------------------------------------------------------
    def index(self, uri):
        if uri not in self.programs and uri in self.docs:
            self.dirty.pop(uri, None)              # never analyzed yet: now, not a moment later
            self.check(uri)
        program = self.programs.get(uri)
        return lsp_index.Index(program, uri_to_path(uri)) if program is not None else None

    def _text_before(self, params, limit=4000):
        text = self.docs.get(params["textDocument"]["uri"], "")
        lines = text.split("\n")
        row, col = params["position"]["line"], params["position"]["character"]
        if row >= len(lines):
            return "", ""
        before = "\n".join(lines[:row] + [lines[row][:col]])
        return before[-limit:], lines[row][:col]

    def on_textDocument_completion(self, params):
        uri = params["textDocument"]["uri"]
        line = params["position"]["line"] + 1
        _, current = self._text_before(params)
        index = self.index(uri)
        m = re.match(r'^\s*import\s+"([^"]*)$', current)
        if m:
            return {"isIncomplete": False, "items": self._import_items(uri, m.group(1))}
        if current.count('"') % 2 == 1 and not re.search(r"#\{[^}]*$", current):
            return {"isIncomplete": False, "items": []}          # inside a text
        m = re.search(r"([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.([A-Za-z0-9_]*)$", current)
        if m:
            if index is None:
                return {"isIncomplete": False, "items": []}
            t = index.chain_type(m.group(1), line)
            kinds = {"field": 5, "method": 2, "enum": 20, "property": 10}
            return {"isIncomplete": False, "items": [
                {"label": name, "kind": kinds.get(kind, 6), "detail": detail, "documentation": doc}
                for name, kind, detail, doc in index.members(t)]}
        if re.search(r"(?::|->)\s*[A-Za-z_]*$", current):
            names = lsp_index.TYPE_NAMES + (sorted(index.structs) + sorted(index.enums) if index else [])
            return {"isIncomplete": False, "items": [
                {"label": n, "kind": 25 if n in lsp_index.TYPE_NAMES else 22} for n in names]}
        return {"isIncomplete": False, "items": self._general_items(index, line)}

    @staticmethod
    def _snippet(name, params):
        inside = ", ".join(f"${{{i + 1}:{p.split(':')[0].strip()}}}" for i, p in enumerate(params))
        return f"{name}({inside})"

    def _general_items(self, index, line):
        items = [{"label": k, "kind": 14} for k in lsp_index.keywords()]
        for name, b in lsp_index.builtins().items():
            items.append({"label": name, "kind": 3, "detail": lsp_index.builtin_signature(b),
                          "documentation": b.description or "", "insertTextFormat": 2,
                          "insertText": self._snippet(name, b.params)})
        if index is None:
            return items
        for name, f in index.functions.items():
            params = [lsp_index._param_label(p) for p in f.params or []]
            items.append({"label": name, "kind": 3, "detail": lsp_index.function_signature(f, name),
                          "insertTextFormat": 2, "insertText": self._snippet(name, params)})
        for name, st in index.structs.items():
            items.append({"label": name, "kind": 22, "detail": "struct " + name, "insertTextFormat": 2,
                          "insertText": self._snippet(name, [f.name for f in st.fields])})
        for name in index.enums:
            items.append({"label": name, "kind": 13, "detail": "enum " + name})
        for name in index.windows:
            items.append({"label": name, "kind": 7, "detail": "Window " + name})
        for name in index.constants:
            items.append({"label": name, "kind": 21, "detail": "const " + name})
        for name, g in index.globals.items():
            items.append({"label": name, "kind": 6, "detail": f"var {name}: {g.var_type}"})
        for name, (_, t) in index.locals_at(line).items():
            items.append({"label": name, "kind": 6, "detail": f"{name}: {t}" if t else name,
                          "sortText": "0" + name})                 # the variables at hand first
        return items

    def _import_items(self, uri, typed):
        base = os.path.dirname(uri_to_path(uri))
        folder, _, _ = typed.rpartition("/")
        where = os.path.normpath(os.path.join(base, folder)) if folder else base
        items = []
        try:
            for entry in sorted(os.listdir(where)):
                full = os.path.join(where, entry)
                if os.path.isdir(full) and not entry.startswith("."):
                    items.append({"label": entry + "/", "kind": 19, "command": {
                        "title": "", "command": "editor.action.triggerSuggest"}})
                elif entry.endswith((".dash", ".dashui")) and os.path.abspath(full) != uri_to_path(uri):
                    items.append({"label": entry, "kind": 17})
        except OSError:
            pass
        return items

    def on_textDocument_signatureHelp(self, params):
        before, _ = self._text_before(params)
        call = lsp_index.call_at(before)
        index = self.index(params["textDocument"]["uri"])
        if call is None:
            return None
        callee, active = call
        sig = (index.signature_of(callee, params["position"]["line"] + 1) if index is not None
               else lsp_index.Index.signature_of(_NoProgram(), callee, 0))
        if sig is None:
            return None
        label, plabels, doc = sig
        offsets, at = [], label.find("(") + 1
        for p in plabels:
            start = label.find(p, at)
            if start < 0:
                break
            offsets.append({"label": [start, start + len(p)]})
            at = start + len(p)
        return {"signatures": [{"label": label, "documentation": doc, "parameters": offsets}],
                "activeSignature": 0, "activeParameter": min(active, max(0, len(offsets) - 1))}

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


class _NoProgram:
    """Signature help before the first analysis: only the builtins are known."""
    structs, functions = {}, {}


def main():
    out = sys.stdout.buffer
    sys.stdout = sys.stderr          # anything the compiler prints must not get into the protocol
    Server(sys.stdin.fileno(), out).run()


if __name__ == "__main__":
    main()
