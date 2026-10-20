"""Language server for Dash (the Language Server Protocol over stdin/stdout, no dependencies).

    python3 -m compiler.lsp          # started by the VS Code extension (editor/vscode)

It uses the compiler itself (DashCompiler.analyze: parser, imports and analyzer, no C), so what the
editor says is what ./dash would say. The text of the files open in the editor goes to the compiler
as an overlay, so imports see what is being typed, not what is on disk. A document is checked a
moment after the last change (CHECK_DELAY), not on every key.

Done so far: diagnostics (errors and warnings, also those of imported modules, in their files),
completion (builtins with their parameters, keywords, the program's symbols, the variables seen at the
cursor, members after "x.", types after ":", files after import ") and signature help; hover, go to
definition (also into modules and .dashui files, and from an import to its file), references and the
highlight of a name's uses in the document; document symbols (the outline), workspace symbols and
rename; formatting (indentation, compiler/lsp_format.py) and quick fixes (create a function that is
missing, import it from the file that has it, "did you mean" for a name written wrong).
"""
import difflib
import json
import os
import re
import select
import sys
import time
import traceback
import urllib.parse

from compiler.main import DashCompiler, CompilationError, read_source
from compiler.analyzer import NO_MAIN    # a module has none: not a problem in the editor
from compiler import lsp_index
from compiler.lsp_format import format_text

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
        self.roots = []                 # folders of the workspace (initialize), for workspace symbols
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
            except LspError as e:                      # a refusal, said to the editor
                if "id" in message:
                    self.send({"id": message["id"], "error": {"code": e.code, "message": e.message}})
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
        for folder in params.get("workspaceFolders") or []:
            self.roots.append(uri_to_path(folder["uri"]))
        if not self.roots and params.get("rootUri"):
            self.roots.append(uri_to_path(params["rootUri"]))
        return {
            "capabilities": {
                "textDocumentSync": {"openClose": True, "change": 1, "save": {"includeText": False}},
                "completionProvider": {"triggerCharacters": [".", '"', "/"]},
                "signatureHelpProvider": {"triggerCharacters": ["(", ","], "retriggerCharacters": [","]},
                "hoverProvider": True,
                "definitionProvider": True,
                "referencesProvider": True,
                "documentHighlightProvider": True,
                "documentSymbolProvider": True,
                "workspaceSymbolProvider": True,
                "renameProvider": {"prepareProvider": True},
                "documentFormattingProvider": True,
                "codeActionProvider": {"codeActionKinds": ["quickfix"]},
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
                                  [(w, "Warning") for w in analysis.warnings if w.message != NO_MAIN]:
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
            # the document itself by its own uri (an untitled one has no file: "untitled:Untitled-1")
            target = uri if file == path else path_to_uri(file)
            text = self.docs.get(target)
            if text is None:
                try:
                    text = read_source(file)
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
        # typed " or / (they are there for the paths of import) or . (members) where they are none of that:
        # nothing (else the whole list opened after the closing quote of a text, or after "1.")
        context = params.get("context") or {}
        typed = context.get("triggerCharacter") if context.get("triggerKind") == 2 else None
        if typed in ('"', "/") or (typed == "." and not re.search(r"[A-Za-z_][A-Za-z0-9_]*\.$", current)):
            return {"isIncomplete": False, "items": []}
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
        # inside "#{...}" of a text: an expression (not while, @native, Print...)
        expression = current.count('"') % 2 == 1
        return {"isIncomplete": False, "items": self._general_items(index, line, expression)}

    @staticmethod
    def _snippet(name, params):
        inside = ", ".join(f"${{{i + 1}:{p.split(':')[0].strip()}}}" for i, p in enumerate(params))
        return f"{name}({inside})"

    # the words of the language that go in an expression
    EXPRESSION_WORDS = {"true", "false", "nil", "not", "and", "or", "fn", "self"}

    def _general_items(self, index, line, expression=False):
        items = [{"label": k, "kind": 14} for k in lsp_index.keywords()
                 if not expression or k in self.EXPRESSION_WORDS]
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

    # --- hover, definition, references -------------------------------------------------------------
    def text_of(self, path):
        uri = path_to_uri(path)
        if uri in self.docs:
            return self.docs[uri]
        try:
            return read_source(path)
        except OSError:
            return ""

    def _at(self, params):
        """(index, chain, name, line, start, end) of the name under the cursor, or None."""
        uri = params["textDocument"]["uri"]
        row, col = params["position"]["line"], params["position"]["character"]
        lines = self.docs.get(uri, "").split("\n")
        if row >= len(lines):
            return None
        found = lsp_index.word_at(lines[row], col)
        index = self.index(uri)
        if found is None or index is None:
            return None
        chain, name, start, end = found
        return index, chain, name, row + 1, start, end

    def on_textDocument_hover(self, params):
        at = self._at(params)
        if at is None:
            return None
        index, chain, name, line, start, end = at
        what = index.resolve(chain, name, line)
        if what is None:
            return None
        kind, node, detail = what
        code, _, doc = detail.partition("\n\n")
        value = "```dash\n" + code + "\n```" + ("\n\n" + doc if doc else "")
        return {"contents": {"kind": "markdown", "value": value},
                "range": {"start": {"line": line - 1, "character": start}, "end": {"line": line - 1, "character": end}}}

    def _location(self, node, name, default_path):
        """Where node (a definition) is, as an LSP Location over its name."""
        loc = getattr(node, "location", None)
        if loc is None:
            return None
        path = loc.filename or default_path
        if path.endswith(".dashui"):
            # code made from the JSON of the visual editor: its lines are not the file's; the window's name is
            text = self.text_of(path)
            window = re.sub(r"_create$", "", name)
            m = re.search(r'"name"\s*:\s*"' + re.escape(window) + '"', text)
            row = text.count("\n", 0, m.start()) if m else 0
            return {"uri": path_to_uri(path), "range": {"start": {"line": row, "character": 0},
                                                        "end": {"line": row, "character": 0}}}
        lines = self.text_of(path).split("\n")
        row = max(0, loc.line - 1)
        text = lines[row] if row < len(lines) else ""
        m = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])").search(text, max(0, loc.column - 1))
        m = m or re.compile(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])").search(text)
        start, end = (m.start(), m.end()) if m else (max(0, loc.column - 1), max(0, loc.column - 1))
        return {"uri": path_to_uri(path), "range": {"start": {"line": row, "character": start},
                                                    "end": {"line": row, "character": end}}}

    def on_textDocument_definition(self, params):
        uri = params["textDocument"]["uri"]
        row, col = params["position"]["line"], params["position"]["character"]
        lines = self.docs.get(uri, "").split("\n")
        m = re.match(r'^(\s*import\s+")([^"]*)"', lines[row] if row < len(lines) else "")
        if m and m.start(2) <= col <= m.end(2):
            compiler = DashCompiler()
            compiler._base_dir = os.path.dirname(uri_to_path(uri))
            target = compiler._resolve_import_path(m.group(2))
            if os.path.exists(target):
                return {"uri": path_to_uri(target), "range": {"start": {"line": 0, "character": 0},
                                                              "end": {"line": 0, "character": 0}}}
            return None
        at = self._at(params)
        if at is None:
            return None
        index, chain, name, line, _, _ = at
        what = index.resolve(chain, name, line)
        if what is None or what[1] is None or what[0] in ("builtin", "list-method", "type"):
            return None
        return self._location(what[1], name, index.path)

    def _references(self, params, only_here=False):
        at = self._at(params)
        if at is None:
            return []
        index, chain, name, line, _, _ = at
        what = index.resolve(chain, name, line)
        if what is None:
            return []
        kind, node, _ = what
        here = index.path
        if kind == "local":
            first, last = index.body_range(line) or (1, None)
            places = [(here, n, a, b) for n, a, b in lsp_index.occurrences(self.text_of(here), name, False, first, last)]
        else:
            member = kind in ("field", "method", "enum-value", "list-method")
            files = [here] if only_here else sorted(index.files())
            places = [(path, n, a, b) for path in files
                      for n, a, b in lsp_index.occurrences(self.text_of(path), name, member)]
            if member and node is not None:              # the definition itself has no dot before it
                d = self._location(node, name, here)
                if d is not None and (not only_here or d["uri"] == path_to_uri(here)):
                    places.insert(0, (uri_to_path(d["uri"]), d["range"]["start"]["line"] + 1,
                                      d["range"]["start"]["character"], d["range"]["end"]["character"]))
        if only_here:
            places = [p for p in places if p[0] == here]
        return [{"uri": path_to_uri(path), "range": {"start": {"line": n - 1, "character": a},
                                                     "end": {"line": n - 1, "character": b}}}
                for path, n, a, b in places]

    def on_textDocument_references(self, params):
        return self._references(params)

    def on_textDocument_documentHighlight(self, params):
        return [{"range": r["range"], "kind": 1} for r in self._references(params, only_here=True)]

    # --- symbols ------------------------------------------------------------------------------------
    @staticmethod
    def _block_end(lines, row):
        """The line of the "end" of the block that starts at row (0-based), by indentation."""
        indent = len(lines[row]) - len(lines[row].lstrip())
        for i in range(row + 1, len(lines)):
            text = lines[i].strip()
            if not text or text.startswith("#"):
                continue
            if len(lines[i]) - len(lines[i].lstrip()) <= indent:
                return i if re.match(r"end\b", text) else i - 1
        return len(lines) - 1

    def _symbol(self, lines, node, name, kind, detail="", block=True, children=None):
        loc = getattr(node, "location", None)
        if loc is None:
            return None
        row = max(0, min(loc.line - 1, len(lines) - 1))
        text = lines[row] if lines else ""
        m = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])").search(text)
        start, end = (m.start(), m.end()) if m else (0, len(text))
        last = self._block_end(lines, row) if block else row
        symbol = {"name": name, "detail": detail, "kind": kind,
                  "range": {"start": {"line": row, "character": 0},
                            "end": {"line": last, "character": len(lines[last]) if last < len(lines) else 0}},
                  "selectionRange": {"start": {"line": row, "character": start}, "end": {"line": row, "character": end}}}
        if children:
            symbol["children"] = [c for c in children if c]
        return symbol

    def _symbols_of(self, program, path, text):
        """The outline of one file: what is defined at its top level, structs and enums with their parts."""
        lines = text.split("\n")
        mine = lambda n: lsp_index._file(n) == path
        out = []
        for w in program.windows:
            if mine(w):
                out.append(self._symbol(lines, w, w.name, 5, "Window"))
        for c in program.constants:
            if mine(c):
                out.append(self._symbol(lines, c, c.name, 14, "const", block=False))
        for g in program.global_vars:
            if mine(g):
                out.append(self._symbol(lines, g, g.name, 13, g.var_type or "", block=False))
        for e in program.enums:
            if mine(e):
                values = [self._symbol(lines, v, v.name, 22, block=False) for v in e.values]
                out.append(self._symbol(lines, e, e.name, 10, "enum", children=values))
        for st in program.structs:
            if mine(st):
                parts = [self._symbol(lines, f, f.name, 8, f.field_type, block=False) for f in st.fields]
                parts += [self._symbol(lines, m, m.name, 6, lsp_index.function_signature(m)) for m in st.methods or []]
                out.append(self._symbol(lines, st, st.name, 23, "struct", children=parts))
        for f in list(program.functions) + list(program.native_funcs) + list(program.extern_funcs):
            if mine(f):
                name = lsp_index.dash_name(f)
                out.append(self._symbol(lines, f, name, 12, lsp_index.function_signature(f, name),
                                        block=not isinstance(f, lsp_index.A.ExternFunc)))
        if program.main is not None and lsp_index._file(program.main) in (path, ""):
            out.append(self._symbol(lines, program.main, "Main", 12, "punto de entrada"))
        return sorted((s for s in out if s), key=lambda s: s["range"]["start"]["line"])

    def on_textDocument_documentSymbol(self, params):
        uri = params["textDocument"]["uri"]
        self.index(uri)                               # analyzed at least once
        program = self.programs.get(uri)
        if program is None:
            return []
        return self._symbols_of(program, uri_to_path(uri), self.docs.get(uri, ""))

    def _workspace_files(self, limit=500):
        files = set()
        for uri, program in self.programs.items():
            files |= lsp_index.Index(program, uri_to_path(uri)).files()
        for root in self.roots:
            for folder, dirs, names in os.walk(root):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "build", "bin")]
                files.update(os.path.join(folder, n) for n in names if n.endswith(".dash"))
                if len(files) > limit:
                    break
        return sorted(files)[:limit]

    def on_workspace_symbol(self, params):
        query = (params.get("query") or "").lower()
        found = []
        for path in self._workspace_files():
            text = self.text_of(path)
            compiler = DashCompiler()
            compiler.tree_cache = self.tree_cache
            try:
                program = compiler._parse_source(text, path)        # its own definitions, no imports
            except Exception:
                continue
            for symbol in self._symbols_of(program, path, text):
                for item in [symbol] + symbol.get("children", []):
                    if query and not _fuzzy(query, item["name"].lower()):
                        continue
                    found.append({"name": item["name"], "kind": item["kind"],
                                  "containerName": symbol["name"] if item is not symbol else os.path.basename(path),
                                  "location": {"uri": path_to_uri(path), "range": item["selectionRange"]}})
        return found[:1000]

    # --- rename ----------------------------------------------------------------------------------------
    def _renamable(self, params):
        """(what, start, end) of a name that can be renamed, or (None, message)."""
        at = self._at(params)
        if at is None:
            return None, "Aquí no hay un nombre."
        index, chain, name, line, start, end = at
        what = index.resolve(chain, name, line)
        if what is None:
            return None, f"No sé qué es '{name}'."
        kind, node = what[0], what[1]
        if kind in ("builtin", "type", "list-method") or name == "self":
            return None, f"'{name}' es del lenguaje: no se puede renombrar."
        loc = getattr(node, "location", None)
        if loc is not None and (loc.filename or "").endswith(".dashui"):
            return None, f"'{name}' sale de un .dashui: renómbralo en el editor de ventanas."
        return (index, chain, name, line, start, end), None

    def on_textDocument_prepareRename(self, params):
        found, message = self._renamable(params)
        if found is None:
            raise LspError(-32602, message)
        _, _, name, line, start, end = found
        return {"range": {"start": {"line": line - 1, "character": start}, "end": {"line": line - 1, "character": end}},
                "placeholder": name}

    def _rename_clash(self, params, found, new, refs):
        """Why renaming to `new` would join two things (a function with another, a variable with another; it
        was done, v16 of docs/IDE_VIDEO_LOOP.md), or None. A member: if its struct has one called that; else
        if `new` already means something where each use would change."""
        index, chain, name, line, _, _ = found
        what = index.resolve(chain, name, line)
        if what and what[0] in ("field", "method"):
            for s in index.structs.values():
                members = list(s.fields) + list(s.methods or [])
                if any(m is what[1] for m in members) and any(m.name == new for m in members):
                    return f"'{new}' ya es un campo o un método de {s.name}."
            return None
        here = params["textDocument"]["uri"]
        indexes = {here: index}
        for ref in refs:
            uri = ref["uri"]
            if uri not in indexes:
                indexes[uri] = self.index(uri)
            row = ref["range"]["start"]["line"] + 1
            if indexes[uri] is not None and indexes[uri].resolve([], new, row) is not None:
                return (f"'{new}' ya existe donde se usa '{name}' ({os.path.basename(uri_to_path(uri))}, línea {row}): "
                        "el cambio juntaría los dos.")
        return None

    def on_textDocument_rename(self, params):
        found, message = self._renamable(params)
        if found is None:
            raise LspError(-32602, message)
        new = params["newName"]
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", new):
            raise LspError(-32602, f"'{new}' no es un nombre válido.")
        if new in lsp_index.keywords() or new in lsp_index.builtins() or new in lsp_index.TYPE_NAMES:
            raise LspError(-32602, f"'{new}' ya es del lenguaje.")
        refs = self._references(params)
        clash = self._rename_clash(params, found, new, refs)
        if clash:
            raise LspError(-32602, clash)
        changes = {}
        for ref in refs:
            changes.setdefault(ref["uri"], []).append({"range": ref["range"], "newText": new})
        for edits in changes.values():                # one edit per place
            unique = {(e["range"]["start"]["line"], e["range"]["start"]["character"]): e for e in edits}
            edits[:] = list(unique.values())
        return {"changes": changes}

    # --- formatting and quick fixes ------------------------------------------------------------------
    def on_textDocument_formatting(self, params):
        uri = params["textDocument"]["uri"]
        text = self.docs.get(uri)
        if text is None:
            return []
        options = params.get("options") or {}
        step = " " * int(options.get("tabSize", 4)) if options.get("insertSpaces", True) else "\t"
        new = format_text(text, step)
        if new == text:
            return []
        lines = text.split("\n")
        return [{"range": {"start": {"line": 0, "character": 0},
                           "end": {"line": len(lines) - 1, "character": len(lines[-1])}}, "newText": new}]

    def on_textDocument_codeAction(self, params):
        uri = params["textDocument"]["uri"]
        text = self.docs.get(uri, "")
        lines = text.split("\n")
        index = self.index(uri)
        actions = []
        for d in (params.get("context") or {}).get("diagnostics") or []:
            m = re.match(r"(Function|Variable) '([A-Za-z_][A-Za-z0-9_]*)' is not defined", d.get("message", ""))
            if not m:
                continue
            what, name = m.groups()
            row = d["range"]["start"]["line"]
            line_text = lines[row] if row < len(lines) else ""
            if what == "Function":
                actions.append(self._create_function(uri, lines, line_text, name, d))
                actions += self._import_from(uri, lines, name, d)
            known = []
            if index is not None:
                known = list(index.locals_at(row + 1)) + list(index.functions) + list(index.constants) \
                    + list(index.globals) + list(index.structs) + list(index.enums)
            if what == "Function":
                known += list(lsp_index.builtins())
            for close in difflib.get_close_matches(name, sorted(set(known)), n=3, cutoff=0.7):
                actions.append({"title": f"Cambiar a '{close}'", "kind": "quickfix", "diagnostics": [d],
                                "edit": {"changes": {uri: [{"range": d["range"], "newText": close}]}}})
        return [a for a in actions if a]

    @staticmethod
    def _create_function(uri, lines, line_text, name, diagnostic):
        """func name(a, b...) with as many parameters as the call has, before Main (or at the end)."""
        m = re.search(r"(?<![A-Za-z0-9_.])" + re.escape(name) + r"\s*\(", line_text)
        count = 0
        if m:
            depth, i, args = 1, m.end(), ""
            while i < len(line_text) and depth:
                ch = line_text[i]
                depth += ch in "([{"
                depth -= ch in ")]}"
                if depth:
                    args += ch if depth == 1 else " "
                i += 1
            count = 0 if not args.strip() else args.count(",") + 1
        params = ", ".join(chr(ord("a") + i) for i in range(count))
        where = next((i for i, l in enumerate(lines) if re.match(r"Main\b", l)), len(lines))
        new = f"func {name}({params})\n    \nend\n\n"
        return {"title": f"Crear la función {name}({params})", "kind": "quickfix", "diagnostics": [diagnostic],
                "isPreferred": False,
                "edit": {"changes": {uri: [{"range": {"start": {"line": where, "character": 0},
                                                      "end": {"line": where, "character": 0}}, "newText": new}]}}}

    def _import_from(self, uri, lines, name, diagnostic):
        """import "file" for each file of the workspace that defines name at its top level."""
        here = uri_to_path(uri)
        out = []
        for path in self._workspace_files():
            if os.path.abspath(path) == os.path.abspath(here) or name.startswith("_"):
                continue
            compiler = DashCompiler()
            compiler.tree_cache = self.tree_cache
            try:
                program = compiler._parse_source(self.text_of(path), path)
            except Exception:
                continue
            if not any(lsp_index.dash_name(f) == name for f in list(program.functions) + list(program.native_funcs)):
                continue
            relative = os.path.relpath(path, os.path.dirname(here))
            last_import = max((i for i, l in enumerate(lines) if re.match(r"\s*import\s", l)), default=-1)
            out.append({"title": f'Importar {name} de "{relative}"', "kind": "quickfix", "diagnostics": [diagnostic],
                        "isPreferred": True,
                        "edit": {"changes": {uri: [{"range": {"start": {"line": last_import + 1, "character": 0},
                                                              "end": {"line": last_import + 1, "character": 0}},
                                                    "newText": f'import "{relative}"\n'}]}}})
        return out

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


class LspError(Exception):
    """An answer that is an error with a message for the user (a rename that cannot be done...)."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code, self.message = code, message


def _fuzzy(query, name):
    """The letters of query in name, in order (as VS Code's symbol search)."""
    i = 0
    for ch in name:
        if i < len(query) and ch == query[i]:
            i += 1
    return i == len(query)


class _NoProgram:
    """Signature help before the first analysis: only the builtins are known."""
    structs, functions = {}, {}


def main():
    out = sys.stdout.buffer
    sys.stdout = sys.stderr          # anything the compiler prints must not get into the protocol
    Server(sys.stdin.fileno(), out).run()


if __name__ == "__main__":
    main()
