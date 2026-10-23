#!/usr/bin/env python3
"""Generate editor/vscode/syntaxes/dash.tmLanguage.json (the colours of VS Code) from the compiler:
the keywords of compiler/grammar.py, the type names of the analyzer and every builtin of
compiler/amiga_builtins.py, so the editor never lags behind the language.

Usage:
    python3 tools/gen_tmgrammar.py          # write the grammar
    python3 tools/gen_tmgrammar.py --check  # exit 1 if it is out of date (tests/run_tests.py runs this)

A new keyword in grammar.py must be given a colour in KEYWORDS below, or this script stops.
"""
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from compiler.grammar import dash_grammar_minimal as DASH_GRAMMAR  # noqa: E402
from compiler.amiga_builtins import get_all_builtins  # noqa: E402
from compiler.analyzer import SemanticAnalyzer  # noqa: E402

OUTPUT = PROJECT_ROOT / "editor" / "vscode" / "syntaxes" / "dash.tmLanguage.json"

# Every word the grammar uses as a literal, by colour (TextMate scope without ".dash")
KEYWORDS = {
    "keyword.control": ["if", "elif", "else", "while", "for", "in", "step", "return", "break", "continue", "end"],
    "keyword.other": ["import", "Main", "EventLoop", "On", "Print", "Wait", "Stop"],
    "keyword.other.event": ["Close", "Key", "Gadget", "Menu", "Click", "Timer"],
    "keyword.operator.logical": ["and", "or", "not"],
    "storage.type": ["func", "fn", "struct", "enum", "Window"],
    "storage.modifier": ["const", "var", "weak", "borrow"],
    "constant.language": ["true", "false", "nil"],
    "variable.language.self": ["self"],
    "keyword.other.directive": ["@native", "@extern", "@header", "@link", "@c", "@stack", "@workbench_output", "@catalog"],
}
LIST_METHODS = ["push", "pop", "insert", "remove", "clear", "has", "keys"]
IDENT = r"[A-Za-z_][A-Za-z0-9_]*"


def grammar_words():
    """The identifier-like literals of the Lark grammar (comments left out)."""
    text = "\n".join(line.split("//", 1)[0] for line in DASH_GRAMMAR.splitlines())
    return set(re.findall(r'"(@?[A-Za-z_][A-Za-z0-9_]*)"', text))


def words(kind):
    return KEYWORDS[kind]


def alternation(names):
    # longest first, so a name that starts another is not taken for it
    return "|".join(re.escape(n) for n in sorted(set(names), key=lambda n: (-len(n), n)))


def build():
    known = {w for ws in KEYWORDS.values() for w in ws}
    types = sorted(SemanticAnalyzer._TYPE_NAMES)
    missing = sorted(grammar_words() - known - set(types))
    if missing:
        sys.exit(f"gen_tmgrammar: give a colour to these words of compiler/grammar.py in KEYWORDS: {missing}")
    builtins = sorted(get_all_builtins())
    type_alt = alternation(types)
    word = lambda kind: {"match": r"\b(?:" + alternation(words(kind)) + r")\b", "name": kind + ".dash"}

    repository = {
        "comment": {"match": r"#(?!\{).*$", "name": "comment.line.number-sign.dash"},
        "native-block": {
            "begin": '"""', "end": '"""', "name": "meta.embedded.block.c.dash", "contentName": "source.c",
            "patterns": [{"include": "source.c"}],
        },
        "string": {
            "begin": '"', "end": '"', "name": "string.quoted.double.dash",
            "patterns": [
                {"match": r"\\(?:[\\\"nrt0]|[0-7]{1,3}|x[0-9A-Fa-f]{2})", "name": "constant.character.escape.dash"},
                {
                    # "#{expression}" (any expression since dashweb's interpolation with expressions)
                    # quotes inside are written \" ; a "#{" never closed stays text (the string's " ends it)
                    "begin": r"#\{", "end": r"\}|(?=\")", "name": "meta.interpolation.dash",
                    "beginCaptures": {"0": {"name": "punctuation.section.interpolation.begin.dash"}},
                    "endCaptures": {"0": {"name": "punctuation.section.interpolation.end.dash"}},
                    "contentName": "source.dash",
                    "patterns": [{"begin": r'\\"', "end": r'\\"', "name": "string.quoted.double.dash"}]
                                + [{"include": "#" + k} for k in ("number", "builtin", "member", "keyword", "type",
                                                                   "constant", "call", "operator")]
                                + [{"match": IDENT, "name": "variable.other.dash"}],
                },
            ],
        },
        "directive": {
            "patterns": [
                {"match": r"(@native)\s*(\()\s*(borrow)\s*(\))",
                 "captures": {"1": {"name": "keyword.other.directive.dash"},
                              "3": {"name": "storage.modifier.dash"}}},
                {"match": r"(?:" + alternation(words("keyword.other.directive")) + r")\b",
                 "name": "keyword.other.directive.dash"},
            ]
        },
        "type": {
            "patterns": [
                {"match": r"\b(?:" + type_alt + r")\b", "name": "support.type.dash"},
                # after ":" or "->": a struct or enum of the program
                {"match": r"(?<=:|->)\s*\b(?!(?:" + type_alt + r")\b)([A-Z][A-Za-z0-9_]*)\b",
                 "captures": {"1": {"name": "entity.name.type.dash"}}},
            ]
        },
        "declaration": {
            "patterns": [
                {"match": r"\b(func)\s+(" + IDENT + r")",
                 "captures": {"1": {"name": "storage.type.function.dash"}, "2": {"name": "entity.name.function.dash"}}},
                {"match": r"\b(struct|enum|Window)\s+(" + IDENT + r")",
                 "captures": {"1": {"name": "storage.type.dash"}, "2": {"name": "entity.name.type.dash"}}},
                {"match": r"\b(const)\s+(" + IDENT + r")",
                 "captures": {"1": {"name": "storage.modifier.dash"}, "2": {"name": "variable.other.constant.dash"}}},
                {"match": r"\b(var)\s+(" + IDENT + r")",
                 "captures": {"1": {"name": "storage.modifier.dash"}, "2": {"name": "variable.other.dash"}}},
                {"match": r"\b(On)\s+(Close|Key|Gadget|Menu|Click|Timer)\b",
                 "captures": {"1": {"name": "keyword.other.dash"}, "2": {"name": "keyword.other.event.dash"}}},
                # a parameter or a field: "name: Type"
                {"match": r"\b(" + IDENT + r")\s*(?=:\s*[\[{A-Za-z_])",
                 "captures": {"1": {"name": "variable.parameter.dash"}}},
            ]
        },
        "window-block": {
            # Window Name / property value ... / end: the properties are names of their own
            "begin": r"^\s*(Window)\s+(" + IDENT + r")",
            "beginCaptures": {"1": {"name": "storage.type.dash"}, "2": {"name": "entity.name.type.dash"}},
            "end": r"^\s*(end)\b",
            "endCaptures": {"1": {"name": "keyword.control.dash"}},
            "name": "meta.window.dash",
            "patterns": [
                {"include": "#comment"},
                {"match": r"^\s*(" + IDENT + r")\b", "captures": {"1": {"name": "support.type.property-name.dash"}}},
                {"include": "#expression"},
            ],
        },
        "keyword": {
            "patterns": [word("keyword.control"), word("keyword.other"), word("keyword.operator.logical"),
                         word("storage.type"), word("storage.modifier")]
        },
        "constant": {
            "patterns": [word("constant.language"), word("variable.language.self"),
                         {"match": r"\b[A-Z][A-Z0-9_]*[A-Z0-9]\b", "name": "variable.other.constant.dash"}]
        },
        "number": {
            "patterns": [
                {"match": r"\b0[xX][0-9A-Fa-f]+\b", "name": "constant.numeric.hex.dash"},
                {"match": r"\b0[bB][01]+\b", "name": "constant.numeric.binary.dash"},
                {"match": r"\b[0-9]+\.[0-9]+\b", "name": "constant.numeric.float.dash"},
                {"match": r"\b[0-9]+\b", "name": "constant.numeric.integer.dash"},
            ]
        },
        "builtin": {
            # every builtin of compiler/amiga_builtins.py (a call)
            "match": r"\b(?:" + alternation(builtins) + r")\b(?=\s*\()",
            "name": "support.function.builtin.dash",
        },
        "member": {
            "patterns": [
                {"match": r"(\.)(" + alternation(LIST_METHODS) + r")\b(?=\s*\()",
                 "captures": {"2": {"name": "support.function.method.dash"}}},
                {"match": r"(\.)(length)\b", "captures": {"2": {"name": "support.variable.property.dash"}}},
                {"match": r"\b(" + IDENT + r")(\.)(open|close)\b(?!\s*\()",
                 "captures": {"3": {"name": "support.function.window.dash"}}},
                {"match": r"(\.)(" + IDENT + r")(?=\s*\()", "captures": {"2": {"name": "entity.name.function.method.dash"}}},
                {"match": r"(\.)(" + IDENT + r")\b", "captures": {"2": {"name": "variable.other.property.dash"}}},
            ]
        },
        "call": {
            "patterns": [
                # Struct(...) builds one
                {"match": r"\b[A-Z][A-Za-z0-9_]*(?=\s*\()", "name": "entity.name.type.constructor.dash"},
                {"match": r"\b" + IDENT + r"(?=\s*\()", "name": "entity.name.function.call.dash"},
            ]
        },
        "operator": {
            "patterns": [
                {"match": r"->", "name": "punctuation.separator.return-type.dash"},
                {"match": r"\.\.", "name": "keyword.operator.range.dash"},
                {"match": r"==|!=|<=|>=|<<|>>|[-+*/%<>=&|^~]", "name": "keyword.operator.dash"},
            ]
        },
        "expression": {
            "patterns": [{"include": "#" + k} for k in
                         ("comment", "string", "number", "builtin", "member", "keyword", "type", "constant",
                          "call", "operator")]
        },
    }
    order = ("comment", "native-block", "string", "directive", "window-block", "declaration", "builtin", "member",
             "keyword", "type", "constant", "number", "call", "operator")
    return {
        "$schema": "https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json",
        "name": "Dash",
        "scopeName": "source.dash",
        "comment": "Generated by tools/gen_tmgrammar.py from the compiler: do not edit by hand.",
        "patterns": [{"include": "#" + k} for k in order],
        "repository": repository,
    }


def main():
    text = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        if not OUTPUT.exists() or OUTPUT.read_text() != text:
            print(f"{OUTPUT.relative_to(PROJECT_ROOT)} is out of date: run python3 tools/gen_tmgrammar.py")
            sys.exit(1)
        return
    OUTPUT.write_text(text)
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
