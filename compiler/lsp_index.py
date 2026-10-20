"""What the language server knows of a program (compiler/lsp.py): its symbols, what is visible at a
line, the type of a name, the members of a type, the builtins. Plain functions over the AST of the
last analysis that worked (while typing, the text often does not parse: the last good one is used).

Lines and columns here are 1-based, as the compiler's SourceLocation.
"""
import re
from dataclasses import fields, is_dataclass

from compiler import ast_nodes as A
from compiler.amiga_builtins import get_all_builtins
from compiler.analyzer import SemanticAnalyzer
from compiler.grammar import dash_grammar_minimal

TYPE_NAMES = sorted(SemanticAnalyzer._TYPE_NAMES)
LIST_MEMBERS = [("push", "push(valor)", "Añade al final"), ("pop", "pop()", "Quita y devuelve el último"),
                ("insert", "insert(i, valor)", "Inserta en la posición i"),
                ("remove", "remove(i)", "Quita el de la posición i"), ("clear", "clear()", "Vacía la lista")]
DICT_MEMBERS = [("has", "has(clave)", "true si tiene esa clave"), ("keys", "keys()", "Lista de las claves"),
                ("remove", "remove(clave)", "Quita esa clave"), ("clear", "clear()", "Vacía el diccionario")]
C_TO_DASH = {"LONG": "Int", "ULONG": "Int", "WORD": "Int", "UWORD": "Int", "BYTE": "Int", "UBYTE": "Int",
             "int": "Int", "STRPTR": "String", "BOOL": "Bool", "void": "Void", "APTR": "Pointer",
             "float": "Float", "FLOAT": "Float", "DashFixed": "Fixed"}


def keywords():
    """The words of the grammar (if, while, Main, @native...), from compiler/grammar.py."""
    text = "\n".join(line.split("//", 1)[0] for line in dash_grammar_minimal.splitlines())
    words = set(re.findall(r'"(@?[A-Za-z_][A-Za-z0-9_]*)"', text)) - set(TYPE_NAMES)
    return sorted(words)


def builtin_signature(b):
    params = ", ".join(b.params)
    ret = C_TO_DASH.get(b.return_type, b.return_type)
    return f"{b.name}({params})" + (f" -> {ret}" if ret and ret != "Void" else "")


def builtins():
    return get_all_builtins()


def dash_name(node):
    """A private function of a module is renamed (_f -> _f_m1_mod): the name the code uses."""
    return getattr(node, "dash_name", None) or node.name


def _line(node):
    loc = getattr(node, "location", None)
    return loc.line if loc else 0


def _file(node):
    loc = getattr(node, "location", None)
    return loc.filename if loc else ""


def type_text(t):
    return t if t else ""


def function_signature(f, name=None):
    params = ", ".join(p.name + (f": {p.param_type}" if getattr(p, "param_type", None) else "")
                       for p in (f.params or []))
    ret = getattr(f, "return_type", None)
    return f"{name or dash_name(f)}({params})" + (f" -> {ret}" if ret and ret != "Void" else "")


class Index:
    """The symbols of an analyzed program (merged with its modules), seen from the file path."""

    def __init__(self, program, path):
        self.program = program
        self.path = path
        self.structs = {s.name: s for s in program.structs}
        self.enums = {e.name: e for e in program.enums}
        self.windows = {w.name: w for w in program.windows}
        self.functions = {}
        for f in list(program.functions) + list(program.native_funcs) + list(program.extern_funcs):
            name = dash_name(f)
            module = getattr(f, "module", None)
            if name.startswith("_") and module and module != path:
                continue                                  # private to another module
            self.functions[name] = f
        self.constants = {c.name: c for c in program.constants}
        self.globals = {g.name: g for g in program.global_vars}

    # --- where the cursor is ---------------------------------------------------------------------
    def bodies(self):
        """The blocks of this file that hold code, with their first line: functions, methods, Main."""
        out = []
        for f in self.program.functions:
            if _file(f) == self.path:
                out.append((f, None))
        for s in self.program.structs:
            for m in s.methods or []:
                if _file(m) == self.path:
                    out.append((m, s))
        if self.program.main is not None and _file(self.program.main) in (self.path, ""):
            out.append((self.program.main, None))
        return sorted(out, key=lambda b: _line(b[0]))

    def body_at(self, line):
        """The function, method or Main that holds this line (the last one starting before it)."""
        found = (None, None)
        for body, struct in self.bodies():
            if _line(body) and _line(body) <= line:
                found = (body, struct)
        return found

    def locals_at(self, line):
        """name -> (node, type) of the parameters and variables seen at this line."""
        body, struct = self.body_at(line)
        seen = {}
        if body is None:
            return seen
        if struct is not None:
            seen["self"] = (struct, struct.name)
        for p in getattr(body, "params", None) or []:
            seen[p.name] = (p, getattr(p, "param_type", None))
        for node in _walk(getattr(body, "body", None) or []):
            if _line(node) > line:
                continue
            if isinstance(node, (A.VarAssign, A.VarDecl)) and isinstance(node.name, str):
                if node.name not in seen:
                    seen[node.name] = (node, getattr(node, "var_type", None) or self.infer(node.value if isinstance(node, A.VarAssign) else node.initial_value, seen))
            elif isinstance(node, A.ForRangeStmt):
                seen.setdefault(node.variable, (node, "Int"))
            elif isinstance(node, A.ForEachStmt):
                seen.setdefault(node.variable, (node, self._element_type(self.infer(node.iterable, seen))))
        return seen

    # --- types -----------------------------------------------------------------------------------
    def infer(self, value, scope=None):
        """The type of an expression, when it can be told without the analyzer: a constructor, a
        literal, a call with a return type, a name already known."""
        if value is None:
            return None
        if isinstance(value, A.StringLiteral):
            return "String"
        if isinstance(value, (A.NumberLiteral,)):
            return "Int"
        if isinstance(value, A.FloatLiteral):
            return "Float"
        if isinstance(value, A.BoolLiteral):
            return "Bool"
        if isinstance(value, A.ArrayLiteral):
            inner = self.infer(value.elements[0], scope) if value.elements else None
            return f"[{inner}]" if inner else "Array"
        if isinstance(value, A.DictLiteral):
            inner = self.infer(value.values[0], scope) if value.values else None
            return "{String: " + (inner or "Int") + "}"
        if isinstance(value, A.FunctionCall):
            if value.name in self.structs:
                return value.name
            f = self.functions.get(value.name)
            if f is not None:
                return getattr(f, "return_type", None)
            b = builtins().get(value.name)
            if b is not None:
                return C_TO_DASH.get(b.return_type)
        if isinstance(value, A.VarRef):
            return self.type_of(value.name, scope)
        return None

    def type_of(self, name, scope=None):
        if scope and name in scope:
            return scope[name][1]
        if name in self.globals:
            return self.globals[name].var_type
        if name in self.constants:
            return self.infer(self.constants[name].value)
        if name in self.enums:
            return "enum " + name
        if name in self.windows:
            return "Window"
        if name in self.structs:
            return "struct " + name
        return None

    @staticmethod
    def _element_type(t):
        if t and t.startswith("[") and t.endswith("]"):
            return t[1:-1].strip()
        return None

    def chain_type(self, chain, line):
        """The type of a.b.c at this line (None if it cannot be told)."""
        parts = chain.split(".")
        scope = self.locals_at(line)
        t = self.type_of(parts[0], scope)
        for part in parts[1:]:
            s = self.structs.get(t)
            if s is None:
                return None
            field = next((f for f in s.fields if f.name == part), None)
            if field is None:
                return None
            t = field.field_type
        return t

    def members(self, t):
        """(name, kind, detail, documentation) of what goes after "x." for a type."""
        if not t:
            return []
        if t in self.structs:
            s = self.structs[t]
            out = [(f.name, "field", f"{f.name}: {f.field_type}", "") for f in s.fields]
            out += [(m.name, "method", function_signature(m), "") for m in s.methods or []]
            return out
        if t.startswith("enum "):
            e = self.enums.get(t[5:])
            return [(v.name, "enum", f"{e.name}.{v.name}", "") for v in (e.values if e else [])]
        if t.startswith("[") or t == "Array":
            return [(n, "method", d, doc) for n, d, doc in LIST_MEMBERS] + [("length", "property", "length: Int", "")]
        if t.startswith("{"):
            return [(n, "method", d, doc) for n, d, doc in DICT_MEMBERS] + [("length", "property", "length: Int", "")]
        if t == "String":
            return [("length", "property", "length: Int", "Número de caracteres")]
        if t == "Window":
            return [("open", "method", "open", "Abre la ventana"), ("close", "method", "close", "La cierra")]
        return []

    # --- what a name is ---------------------------------------------------------------------------
    def resolve(self, chain, name, line):
        """What `name` is at this line (with `chain.` before it, a member): (kind, node, detail) with kind
        local, function, struct, enum, window, const, global, field, method, enum-value, builtin,
        list-method or type; or None."""
        if chain:
            t = self.chain_type(chain, line)
            s = self.structs.get(t)
            if s is not None:
                for f in s.fields:
                    if f.name == name:
                        return "field", f, f"{s.name}.{f.name}: {f.field_type}"
                for m in s.methods or []:
                    if m.name == name:
                        return "method", m, function_signature(m, f"{s.name}.{m.name}")
            if t and t.startswith("enum "):
                e = self.enums.get(t[5:])
                for v in (e.values if e else []):
                    if v.name == name:
                        return "enum-value", v, f"{e.name}.{v.name}" + (f" = {v.value}" if v.value is not None else "")
            for n, detail, doc in LIST_MEMBERS + DICT_MEMBERS + [("length", "length: Int", "Número de elementos")]:
                if n == name:
                    return "list-method", None, detail + ("\n\n" + doc if doc else "")
            return None
        scope = self.locals_at(line)
        if name in scope:
            node, t = scope[name]
            if name == "self":
                return "local", None, f"self: {t}"
            return "local", node, f"{name}: {t}" if t else name
        if name in self.functions:
            f = self.functions[name]
            return "function", f, function_signature(f, name)
        if name in self.structs:
            st = self.structs[name]
            return "struct", st, "struct " + name + "\n" + "\n".join(f"    {f.name}: {f.field_type}" for f in st.fields)
        if name in self.enums:
            e = self.enums[name]
            return "enum", e, "enum " + name + " " + ", ".join(v.name for v in e.values)
        if name in self.windows:
            return "window", self.windows[name], "Window " + name
        if name in self.constants:
            return "const", self.constants[name], "const " + name
        if name in self.globals:
            g = self.globals[name]
            return "global", g, f"var {name}: {g.var_type}"
        b = builtins().get(name)
        if b is not None:
            return "builtin", b, builtin_signature(b) + ("\n\n" + b.description if b.description else "")
        if name in TYPE_NAMES:
            return "type", None, name
        return None

    def files(self):
        """The files of the program: this one and every module it brought."""
        out = {self.path}
        for group in (self.program.functions, self.program.native_funcs, self.program.extern_funcs,
                      self.program.structs, self.program.enums, self.program.constants,
                      self.program.global_vars, self.program.windows):
            for node in group:
                if _file(node):
                    out.add(_file(node))
        return out

    def body_range(self, line):
        """(first, last) lines of the function, method or Main that holds this line (last: None = end)."""
        body, _ = self.body_at(line)
        if body is None:
            return None
        starts = sorted(_line(b) for b, _ in self.bodies())
        later = [l for l in starts if l > _line(body)]
        top = [_line(n) for group in (self.program.functions, self.program.structs, self.program.enums,
                                      self.program.constants, self.program.global_vars, self.program.windows)
               for n in group if _file(n) == self.path and _line(n) > _line(body)]
        ends = later + top
        return _line(body), (min(ends) - 1 if ends else None)

    # --- calls -----------------------------------------------------------------------------------
    def signature_of(self, callee, line):
        """(label, [parameter labels], documentation) of what is called as callee ("f" or "a.metodo")."""
        if "." in callee:
            chain, _, method = callee.rpartition(".")
            s = self.structs.get(self.chain_type(chain, line))
            m = next((m for m in (s.methods if s else []) or [] if m.name == method), None)
            if m is not None:
                return function_signature(m), [_param_label(p) for p in m.params or []], ""
            for name, detail, doc in LIST_MEMBERS + DICT_MEMBERS:
                if name == method:
                    inside = detail[detail.index("(") + 1:-1]
                    return detail, [p.strip() for p in inside.split(",") if p.strip()], doc
            return None
        b = builtins().get(callee)
        if b is not None:
            return builtin_signature(b), list(b.params), b.description or ""
        f = self.functions.get(callee)
        if f is not None:
            return function_signature(f), [_param_label(p) for p in f.params or []], ""
        s = self.structs.get(callee)
        if s is not None:
            params = [f"{f.name}: {f.field_type}" for f in s.fields]
            return f"{s.name}({', '.join(params)})", params, "Construye un " + s.name
        return None


def _param_label(p):
    return p.name + (f": {p.param_type}" if getattr(p, "param_type", None) else "")


def _walk(nodes):
    """Every statement and expression node under these, depth first."""
    stack = list(reversed(nodes if isinstance(nodes, list) else [nodes]))
    seen = set()
    while stack:
        node = stack.pop()
        if isinstance(node, list):
            stack.extend(reversed(node))
            continue
        if not is_dataclass(node) or isinstance(node, (type, A.SourceLocation)) or id(node) in seen:
            continue
        seen.add(id(node))
        yield node
        for f in fields(node):
            value = getattr(node, f.name, None)
            if isinstance(value, list) or (is_dataclass(value) and not isinstance(value, type)):
                stack.append(value)


def call_at(text_before):
    """(callee, index of the argument) of the call the cursor is inside, from the text before it
    (strings and nested calls taken into account), or None."""
    depth, commas, i, in_string = 0, 0, len(text_before) - 1, False
    while i >= 0:
        ch = text_before[i]
        if ch == '"' and (i == 0 or text_before[i - 1] != "\\"):
            in_string = not in_string
        elif not in_string:
            if ch in ")]}":
                depth += 1
            elif ch in "([{":
                if depth == 0:
                    if ch != "(":
                        return None
                    m = re.search(r"([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s*$", text_before[:i])
                    return (m.group(1), commas) if m else None
                depth -= 1
            elif ch == "," and depth == 0:
                commas += 1
            elif ch == "\n" and depth == 0 and commas == 0 and i < len(text_before) - 1:
                pass
        i -= 1
    return None


def word_at(line_text, character):
    """(chain, name, start, end) of the identifier under the cursor (0-based character): chain is
    what comes before it with dots ("a.b" in "a.b.c"), "" if nothing; None if not on a name."""
    for m in re.finditer(r"@?[A-Za-z_][A-Za-z0-9_]*", line_text):
        if m.start() <= character <= m.end():
            chain = ""
            before = line_text[:m.start()]
            c = re.search(r"([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.$", before)
            if c:
                chain = c.group(1)
            return chain, m.group(0), m.start(), m.end()
    return None


def code_spans(line_text):
    """The parts of a line that are code: not inside a text (except #{...}) nor a comment."""
    spans, i, start, in_text, depth = [], 0, 0, False, 0
    while i < len(line_text):
        ch = line_text[i]
        if not in_text:
            if ch == "#":
                spans.append((start, i))
                return spans
            if ch == '"':
                spans.append((start, i))
                in_text = True
        else:
            if ch == "\\":
                i += 2
                continue
            if line_text.startswith("#{", i):
                start, depth = i + 2, 1
                i += 2
                while i < len(line_text) and depth:
                    if line_text[i] == "{":
                        depth += 1
                    elif line_text[i] == "}":
                        depth -= 1
                    i += 1
                spans.append((start, i - 1))
                continue
            if ch == '"':
                in_text = False
                start = i + 1
        i += 1
    if not in_text:
        spans.append((start, len(line_text)))
    return spans


def occurrences(text, name, member=False, first_line=1, last_line=None):
    """(line, start, end) of each use of name in the code of text (1-based lines, 0-based
    characters); member: only after a dot; else not after one. Inside the lines asked."""
    out = []
    pattern = re.compile(r"(?<![A-Za-z0-9_@])" + re.escape(name) + r"(?![A-Za-z0-9_])")
    lines = text.split("\n")
    in_native = False
    for number, line_text in enumerate(lines, start=1):
        if line_text.strip().startswith('"""'):
            in_native = not in_native
            continue
        if in_native or number < first_line or (last_line is not None and number > last_line):
            continue
        for a, b in code_spans(line_text):
            for m in pattern.finditer(line_text, a, b):
                dotted = m.start() > 0 and line_text[m.start() - 1] == "."
                if dotted == member:
                    out.append((number, m.start(), m.end()))
    return out

