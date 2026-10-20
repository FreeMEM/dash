"""./dash --debug: the C says which line of Dash each line comes from (#line), so gdb, its breakpoints
and its steps speak in .dash lines (the debugger of the VS Code extension, docs/IDE_LOOP.md).

The code generator (DASH_DEBUG_LINES=1) leaves a mark before each statement and at the end of
each function, method and Main:

    /*@dash-line 12 "/home/x/prog.dash"*/
    ... C of that statement (one line or several) ...
    /*@dash-noline*/

and apply() turns them into #line directives: every line of C after a mark gets the mark's line
(a statement that takes several lines of C is still one line of Dash: a step does not stop in the
middle), and after a noline the numbers go back to the real lines of the C file, so the runtime
and the C of @native stay as they are.
"""
import re

MARK = re.compile(r'^\s*/\*@dash-line (\d+) "((?:[^"\\]|\\.)*)"\*/\s*$')
NOLINE = "/*@dash-noline*/"


def mark(line, filename):
    """The mark of a statement at this line of this file (absolute path)."""
    escaped = filename.replace("\\", "\\\\").replace('"', '\\"')
    return f'/*@dash-line {line} "{escaped}"*/\n'


def apply(code, c_filename):
    """The C with its marks turned into #line directives (c_filename: the name of the C file itself,
    for the lines that are not Dash's)."""
    c_name = c_filename.replace("\\", "\\\\").replace('"', '\\"')
    out = []
    current = None                                  # (line, "file") of the statement being written
    for line in code.split("\n"):
        m = MARK.match(line)
        if m:
            current = (m.group(1), m.group(2))
            continue
        if line.strip() == NOLINE:
            if current is not None:
                current = None
                out.append(f'#line {len(out) + 2} "{c_name}"')   # the next line is the C file's own again
            continue
        if current is not None and line.strip() and not line.lstrip().startswith("#"):
            out.append(f'#line {current[0]} "{current[1]}"')
        out.append(line)
    return "\n".join(out)


def strip(code):
    """The C without the marks (when they are not wanted)."""
    return "\n".join(l for l in code.split("\n") if not MARK.match(l) and l.strip() != NOLINE)
