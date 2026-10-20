"""Formatting of Dash code for the language server (compiler/lsp.py): the indentation of each line by
its blocks (func, if, while, for, struct, enum, Window, Main, EventLoop, On, @native, @c ... end; elif
and else one step out), and no spaces at the end of lines of code (comments keep theirs). Nothing else changes: the C between \"\"\"
stays as it is, and a line that continues an open bracket of the one above keeps its own indentation.

The trees of MUI and ReAction (mui_window_begin ... mui_window_end(), mui_hgroup_begin() ...
mui_group_end(), ra_layout_*_begin ... ra_layout_group_end()) are indented as blocks too, when the
code already did (the line after the _begin went deeper): it is a habit, not a rule of the language.
"""
import re

OPENER = re.compile(r"^(?:(?:@native(?:\s*\(\s*borrow\s*\))?\s+)?func\b|if\b|while\b|for\b|struct\b|enum\b|"
                    r"Window\b|Main\b|EventLoop\b|On\b|@c\b)")
MIDDLE = re.compile(r"^(?:elif|else)\b")
END = re.compile(r"^end\b")
ONE_LINE = re.compile(r"\bend\s*$")
TREE_BEGIN = re.compile(r"\b(?:mui_(?:window|menu|hgroup|vgroup|columns|frame|register|scroll)_begin|"
                        r"ra_layout_[hv]group_begin)\s*\(")
TREE_END = re.compile(r"^(?:mui_(?:window|group|menu)_end|ra_layout_group_end)\s*\(")


def _code(line):
    """The line without texts and comment (for brackets and the one-line "... end")."""
    out, in_text, i = [], False, 0
    while i < len(line):
        ch = line[i]
        if in_text:
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                in_text = False
        elif ch == '"':
            in_text = True
        elif ch == "#":
            break
        else:
            out.append(ch)
        i += 1
    return "".join(out).rstrip()


def _brackets(code):
    return code.count("(") + code.count("[") + code.count("{") - code.count(")") - code.count("]") - code.count("}")


def _indent(line):
    return len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip())


def format_text(text, step="    "):
    lines = text.split("\n")
    out = []
    stack = []                     # "block" (closed by end) or "tree" (closed by its _end call)
    in_native = False
    depth = 0                      # open brackets carried from the lines above
    previous = ""                  # the last line with code (for "@extern" + "func" without a body)
    hanging = False                # the line above ended with a comment: aligned comments under it stay
    for n, raw in enumerate(lines):
        stripped = raw.strip()
        if in_native:
            out.append(raw.rstrip())                     # C: exactly as it is (only end spaces)
            if '"""' in stripped:
                in_native = False
            continue
        if stripped.startswith('"""'):
            out.append(raw.rstrip())
            in_native = stripped.count('"""') == 1       # """ ... """ on one line: done
            continue
        if depth > 0:                                    # continues an open bracket: its own indentation
            out.append(raw.rstrip())
            depth = max(0, depth + _brackets(_code(stripped)))
            continue
        if not stripped:
            out.append("")
            hanging = False
            continue
        if END.match(stripped) or MIDDLE.match(stripped):
            while stack and stack[-1] == "tree":         # a tree left open inside the block
                stack.pop()
            if stack:
                stack.pop()
        elif TREE_END.match(stripped) and stack and stack[-1] == "tree":
            stack.pop()
        if stripped.startswith("#"):
            if hanging and _indent(raw) > len(step * len(stack)):
                out.append(raw)                          # goes on the comment at the end of the line above
                continue
            # a comment keeps its end as it is: test lines like "# expect-c: /* x: " mean their spaces
            out.append(step * len(stack) + raw.lstrip())
            hanging = False
            continue
        out.append(step * len(stack) + stripped)
        code = _code(stripped)
        if MIDDLE.match(stripped):
            stack.append("block")
        elif OPENER.match(stripped) and not ONE_LINE.search(code) and not previous.startswith("@extern"):
            stack.append("block")
        elif TREE_BEGIN.search(code) and _next_deeper(lines, n):
            stack.append("tree")
        previous = stripped
        depth = max(0, _brackets(code))
        hanging = code != stripped.rstrip() and "#" in stripped    # it ends with a comment
    return "\n".join(out)


def _next_deeper(lines, n):
    """Is the next line with code indented more than line n (in the text as it came)?"""
    for line in lines[n + 1:]:
        if line.strip() and not line.strip().startswith("#"):
            return _indent(line) > _indent(lines[n])
    return False
