"""`.dashui` files (MUI windows made with the visual editor) as Dash source.

`import "ventana.dashui"` in a Dash program: the compiler reads the JSON and compiles
the Dash code made here, a module like any other. For each window: a struct with a
field per named object (plus `window`) and a function `<Name>_create()` that builds it
with the mui_ builtins and returns the struct. Format: docs/MUI_EDITOR.md.
"""

import json
import re

VERSION = 1

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_NAME_RULE = "letters without accents, digits and _, not starting with a digit"


# words of "On Click", "On Key"...: names like any other where they are not after On
_EVENT_WORDS = {"Click", "Close", "Gadget", "Key", "Menu", "On", "Timer"}


def reserved():
    """Words of the language (the editor's media/model.js has the same list): an object or window called "end"
    broke the code made here"""
    from compiler import lsp_index
    return {w for w in lsp_index.keywords() if not w.startswith("@")} - _EVENT_WORDS


def _check_name(name, what, where):
    if not isinstance(name, str) or not _IDENT.match(name):
        raise DashUIError(f"{where}: bad {what} name {name!r} ({_NAME_RULE})")
    if name in reserved():
        raise DashUIError(f"{where}: {what} name {name!r} is a word of the language")


def _int(value, what, where):
    """A whole number of the file ("event": "uno" ended in a Python error)"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise DashUIError(f"{where}: {what} must be a whole number, not {value!r}")
    return value

# type -> (builtin, positional properties with defaults) for leaf objects
_LEAVES = {
    "text": ("mui_text", [("text", "")]),
    "label": ("mui_label", [("text", "")]),
    "button": ("mui_button", [("label", "")]),
    "string": ("mui_string", [("text", ""), ("max", 80)]),
    "checkbox": ("mui_checkbox", [("checked", False)]),
    "cycle": ("mui_cycle", [("options", "")]),
    "slider": ("mui_slider", [("min", 0), ("max", 100), ("value", 0)]),
    "gauge": ("mui_gauge", [("max", 100)]),
    "list": ("mui_list", []),
    "canvas": ("mui_canvas", [("min_width", 64), ("min_height", 32)]),
    "scrollbar": ("mui_scrollbar", [("vertical", True)]),
    "image": ("mui_image", [("file", "")]),
    "image_button": ("mui_image_button", [("file", "")]),
    "space": ("mui_space", []),
    "balance": ("mui_balance", []),
}

# type -> (builtin, positional properties) for groups (children inside, mui_group_end after)
_GROUPS = {
    "vgroup": ("mui_vgroup_begin", []),
    "hgroup": ("mui_hgroup_begin", []),
    "frame": ("mui_frame_begin", [("title", ""), ("horizontal", False)]),
    "columns": ("mui_columns_begin", [("columns", 2)]),
    "tabs": ("mui_register_begin", [("titles", "")]),
    "scroll": ("mui_scroll_begin", []),
}

# event property -> builtin that connects it
_EVENTS = {"event": "mui_on_press", "change": "mui_on_change", "ack": "mui_on_ack", "double": "mui_on_double"}


class DashUIError(Exception):
    pass


# the text a "tr": number goes with (dashweb D71); {"field": number} gives each text its own
_MAIN_TEXT = {"text": "text", "label": "text", "button": "label", "string": "text", "cycle": "options",
              "frame": "title", "tabs": "titles", "window": "title", "menu": "title", "item": "label"}


def _tr_ids(node: dict, kind: str, where: str) -> dict:
    """{field: catalog number} of a node, a window, a menu or a menu item"""
    tr = node.get("tr")
    if tr is None:
        return {}
    if isinstance(tr, bool) or not isinstance(tr, (int, dict)):
        raise DashUIError(f"{where}: \"tr\" must be a number or {{\"field\": number}}, not {tr!r}")
    if isinstance(tr, int):
        if kind not in _MAIN_TEXT:
            raise DashUIError(f"{where}: a {kind!r} has no text for \"tr\"")
        return {_MAIN_TEXT[kind]: tr}
    for field, number in tr.items():
        _int(number, f'"tr" of {field!r}', where)
    return tr


def _text(node: dict, field: str, default, ids: dict) -> str:
    """A property of the file as Dash: a text with a catalog number goes through tr (dashweb D71)"""
    value = _value(node.get(field, default))
    return f"tr({ids[field]}, {value})" if field in ids and isinstance(node.get(field, default), str) else value


def dash_string(text) -> str:
    """A Dash string literal (escapes that the Dash lexer and C both take)."""
    out = []
    for ch in str(text):
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "#":
            out.append("#")
        elif ord(ch) < 32 or ord(ch) == 127:
            out.append("\\%03o" % ord(ch))   # \33 (ESC) for MUI text codes
        else:
            out.append(ch)
    s = "".join(out)
    if "#{" in s:   # would be interpolation in Dash
        raise DashUIError("text with '#{' is not allowed (it would be read as interpolation): " + repr(text))
    return '"' + s + '"'


def _value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return dash_string(v)
    raise DashUIError(f"unsupported value {v!r}")


class _Window:
    def __init__(self, win: dict, where: str):
        self.win = win
        self.where = where
        self.lines = []        # body of <Name>_create
        self.fields = []       # named objects, in order
        self.after = []        # events and settings, after mui_window_end
        self.auto = 0

    def var_for(self, node: dict, needs_var: bool) -> str:
        name = node.get("name")
        if name:
            if name == "window":
                raise DashUIError(f"{self.where}: object name 'window' is the window's own")
            _check_name(name, "object", self.where)
            if name in self.fields:
                raise DashUIError(f"{self.where}: object name {name!r} used twice")
            self.fields.append(name)
            # a local of its own: the object's name alone would be a global of the program or of a module that
            # has it (Dash functions see and change globals), which the window would overwrite (dashweb D72)
            return f"_ui_{name}"
        if needs_var:
            self.auto += 1
            return f"_ui{self.auto}"
        return ""

    def node(self, node: dict, depth: int):
        if not isinstance(node, dict) or "type" not in node:
            raise DashUIError(f"{self.where}: object without 'type': {node!r}")
        kind = node["type"]
        indent = "    " * depth
        settings = [k for k in ("weight", "disabled", "hidden", "help") if k in node]
        events = [k for k in _EVENTS if k in node]
        if kind in _GROUPS:
            builtin, props = _GROUPS[kind]
        elif kind in _LEAVES:
            builtin, props = _LEAVES[kind]
        else:
            raise DashUIError(f"{self.where}: unknown object type {kind!r}")
        ids = _tr_ids(node, kind, self.where)
        args = ", ".join(_text(node, p, default, ids) for p, default in props)
        var = self.var_for(node, bool(settings or events))
        call = f"{builtin}({args})"
        self.lines.append(f"{indent}{var} = {call}" if var else f"{indent}{call}")
        for k in events:
            self.after.append(f"    {_EVENTS[k]}({var}, {_int(node[k], repr(k), self.where)})")
        if "weight" in node:
            self.after.append(f"    mui_weight({var}, {_int(node['weight'], 'weight', self.where)})")
        if node.get("disabled"):
            self.after.append(f"    mui_set_enabled({var}, false)")
        if node.get("hidden"):
            self.after.append(f"    mui_set_visible({var}, false)")
        if node.get("help"):
            self.after.append(f"    mui_help({var}, {_text(node, 'help', '', ids)})")
        if kind in _GROUPS:
            for child in node.get("children", []):
                self.node(child, depth + 1)
            self.lines.append(f"{indent}mui_group_end()")
        elif node.get("children"):
            raise DashUIError(f"{self.where}: a {kind!r} cannot have children")

    def generate(self) -> str:
        win = self.win
        name = win.get("name")
        _check_name(name, "window", self.where)
        win_id = _int(win.get("id", 0), "id", self.where)
        title = _text(win, "title", name, _tr_ids(win, "window", self.where))
        self.lines.append(f"    _window = mui_window_begin({title}, {win_id})")
        for menu in win.get("menus", []):
            title = _text(menu, "title", "", _tr_ids(menu, "menu", self.where))
            self.lines.append(f"        mui_menu_begin({title})")
            for item in menu.get("items", []):
                if item.get("separator"):
                    self.lines.append("            mui_menu_separator()")
                else:
                    label = _text(item, "label", "", _tr_ids(item, "item", self.where))
                    self.lines.append(f"            mui_menu_item({label}, "
                                      f"{dash_string(item.get('key', ''))}, {_int(item.get('event', 0), 'a menu event', self.where)})")
            self.lines.append("        mui_menu_end()")
        root = win.get("root")
        if root:
            # the window's own group is vertical: a root vgroup goes straight into it
            if root.get("type") == "vgroup" and not root.get("name") and \
                    not any(k in root for k in ("weight", "disabled", "hidden", "help")):
                for child in root.get("children", []):
                    self.node(child, 2)
            else:
                self.node(root, 2)
        self.lines.append("    mui_window_end()")
        if "close" in win:
            self.after.append(f"    mui_on_close(_window, {_int(win['close'], 'close', self.where)})")
        if "size" in win:
            # [width, height] in percent of the visible screen, when it opens (dashweb D38)
            size = win["size"]
            if not (isinstance(size, list) and len(size) == 2 and all(isinstance(v, int) for v in size)):
                raise DashUIError(f"{self.where}: \"size\" is [width, height] in percent")
            self.after.append(f"    mui_window_size(_window, {size[0]}, {size[1]})")
        fields = ["window"] + self.fields
        struct = [f"struct {name}"] + [f"    {f}: Int" for f in fields] + ["end", ""]
        func = ([f"func {name}_create() -> {name}"] + self.lines + self.after +
                [f"    return {name}(_window" + "".join(f", _ui_{f}" for f in self.fields) + ")", "end", ""])
        return "\n".join(struct + func)


def generate(source: str, filename: str = "<dashui>") -> str:
    """Dash source for the windows of a .dashui file (JSON text)."""
    try:
        data = json.loads(source)
    except json.JSONDecodeError as e:
        raise DashUIError(f"{filename}: not valid JSON: {e}")
    if not isinstance(data, dict) or data.get("dashui") != VERSION:
        raise DashUIError(f"{filename}: not a version {VERSION} .dashui file (\"dashui\": {VERSION})")
    out = [f"# Made from {filename} (MUI windows, docs/MUI_EDITOR.md)", ""]
    names = set()
    for i, win in enumerate(data.get("windows", [])):
        where = f"{filename}: window {i + 1}"
        if not isinstance(win, dict):
            raise DashUIError(f"{where}: not an object")
        if win.get("name") in names:
            raise DashUIError(f"{where}: window name {win.get('name')!r} used twice")
        names.add(win.get("name"))
        out.append(_Window(win, where).generate())
    return "\n".join(out)
