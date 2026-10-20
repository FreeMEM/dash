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
