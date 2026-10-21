"""
Dash Language Semantic Analyzer
Performs semantic analysis, builds symbol table, and validates the AST.
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from enum import Enum, auto

from compiler.ast_nodes import (
    ASTNode, ASTVisitor, Program, WindowDef, MainBlock, EventLoop,
    OnCloseHandler, OnKeyHandler, OnGadgetHandler, OnMenuHandler, OnClickHandler, OnTimerHandler, WindowOpen, WindowClose, PrintStmt, WaitStmt,
    StopStmt, BreakStmt, ContinueStmt, Comment, IfStmt, WhileStmt, ForRangeStmt, ForEachStmt,
    VarDecl, VarAssign, VarRef, FunctionDef, FunctionCall, ReturnStmt,
    BinaryOp, UnaryOp, StringLiteral, NumberLiteral, BoolLiteral, MethodCall, DictLiteral,
    ArrayLiteral, ArrayAccess, ArrayAssign, ArraySlice, PropertyAccess, NilLiteral,
    StructDef, StructField, MemberAccess, MemberAssign,
    EnumDef, EnumValue, FunctionParam, ExternFunc, NativeFunc, ConstDecl,
    StructMethod, LambdaFunc, FunctionRef, SelfRef, constant_int, KEY_NAMES, FloatLiteral, GlobalVarDecl
)
from compiler.amiga_builtins import is_builtin, get_builtin


def list_elem_type(type_name: Optional[str]) -> Optional[str]:
    """Element type of a list type annotation ("[String]" -> "String"), else None."""
    if type_name and type_name.startswith("[") and type_name.endswith("]"):
        return type_name[1:-1].strip()
    return None


def dict_value_type(type_name: Optional[str]) -> Optional[str]:
    """Value type of a dictionary type annotation ("{String:Int}" -> "Int"), else None."""
    if type_name and type_name.startswith("{") and type_name.endswith("}") and ":" in type_name:
        return type_name[1:-1].split(":", 1)[1].strip()
    return None


def type_is_known(type_name: str, known) -> bool:
    """A type name, a list of one ("[Nodo]", "[[Int]]") or a dictionary ("{String:Nodo}")."""
    value = dict_value_type(type_name)
    if value is not None:
        key = type_name[1:-1].split(":", 1)[0].strip()
        return key == "String" and bool(value) and value not in ("Void", "Array") and type_is_known(value, known)
    elem = list_elem_type(type_name)
    if elem is not None:
        return bool(elem) and elem not in ("Void", "Array") and type_is_known(elem, known)
    return type_name in known



# A file without Main: a program that does nothing, or a module to import (the language server does not show it)
NO_MAIN = "el programa no tiene Main: no hace nada (un módulo para importar no lo necesita)"

class SymbolType(Enum):
    """Types of symbols in the symbol table."""
    WINDOW = auto()
    VARIABLE = auto()
    CONSTANT = auto()
    FUNCTION = auto()
    PARAMETER = auto()
    STRUCT = auto()
    ENUM = auto()
    EXTERN_FUNC = auto()
    NATIVE_FUNC = auto()


class DashType(Enum):
    """Dash language types (for future type checking)."""
    INT = auto()
    FLOAT = auto()
    FIXED = auto()   # 16.16 fixed point in a LONG
    STRING = auto()
    BOOL = auto()
    VOID = auto()
    WINDOW = auto()
    ARRAY_INT = auto()
    ARRAY_STRING = auto()
    ARRAY = auto()  # Generic array when type unknown
    DICT = auto()   # {String: T} (dashweb D5)
    FUNC = auto()  # Lambda or function pointer
    UNKNOWN = auto()


@dataclass
class Symbol:
    """Represents a symbol in the symbol table."""
    name: str
    symbol_type: SymbolType
    dash_type: DashType = DashType.UNKNOWN
    node: Optional[ASTNode] = None
    scope_level: int = 0
    is_opened: bool = False  # For windows
    is_initialized: bool = False  # For variables
    struct_name: Optional[str] = None  # Struct type of the value, when known
    elem_struct: Optional[str] = None  # For a list of structs: their struct type
    dict_value: Optional[str] = None   # For a dictionary: the type of its values ("Int", "Nodo"...)
    list_fixed: bool = False           # A list of Fixed values ([Fixed]): its elements are Fixed
    list_type: Optional[str] = None    # Its declared list type ("[String]", "[[Int]]"...), when known (D49)


@dataclass
class Scope:
    """Represents a lexical scope."""
    name: str
    level: int
    parent: Optional['Scope'] = None
    symbols: Dict[str, Symbol] = field(default_factory=dict)

    def define(self, symbol: Symbol) -> bool:
        """Define a symbol in this scope. Returns False if already defined."""
        if symbol.name in self.symbols:
            return False
        symbol.scope_level = self.level
        self.symbols[symbol.name] = symbol
        return True

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up a symbol only in this scope."""
        return self.symbols.get(name)

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol in this scope and parent scopes."""
        symbol = self.symbols.get(name)
        if symbol:
            return symbol
        if self.parent:
            return self.parent.lookup(name)
        return None


@dataclass
class AnalysisError:
    """Represents a semantic error."""
    message: str
    node: Optional[ASTNode] = None
    is_warning: bool = False

    @property
    def location(self):
        return getattr(self.node, "location", None) if self.node is not None else None

    def __str__(self):
        # file:line:column: Error: message (as gcc; editors and VS Code's problem matcher read it)
        prefix = "Warning" if self.is_warning else "Error"
        location = self.location
        if location and location.filename:
            return f"{location}: {prefix}: {self.message}"
        if location:
            return f"{prefix} at {location}: {self.message}"
        return f"{prefix}: {self.message}"


@dataclass
class AnalysisResult:
    """Result of semantic analysis."""
    program: Program
    errors: List[AnalysisError] = field(default_factory=list)
    warnings: List[AnalysisError] = field(default_factory=list)
    symbol_table: Dict[str, Symbol] = field(default_factory=dict)
    opened_windows: List[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def is_valid(self) -> bool:
        return not self.has_errors


class SemanticAnalyzer(ASTVisitor):
    """
    Performs semantic analysis on the Dash AST.

    Checks:
    - Windows are defined before being opened
    - Variables are declared before use
    - Functions are defined before being called
    - Event handlers are valid
    - Type compatibility (future)
    """

    def __init__(self):
        self.errors: List[AnalysisError] = []
        self.warnings: List[AnalysisError] = []
        self.global_scope = Scope(name="global", level=0)
        self.current_scope = self.global_scope
        self.opened_windows: List[str] = []
        self.in_event_loop = False
        self.in_function = False
        self.program: Optional[Program] = None
        self.loop_depth = 0  # while/for loops around the current statement (for break/continue)
        self.current_window: Optional[str] = None
        self.current_module: Optional[str] = None  # Module whose code is being analyzed
        self.structs: List[StructDef] = []

    def analyze(self, program: Program) -> AnalysisResult:
        """Perform semantic analysis on the program."""
        self.program = program
        self.visit(program)

        return AnalysisResult(
            program=program,
            errors=self.errors,
            warnings=self.warnings,
            symbol_table=dict(self.global_scope.symbols),
            opened_windows=self.opened_windows
        )

    def error(self, message: str, node: Optional[ASTNode] = None):
        """Record a semantic error."""
        self.errors.append(AnalysisError(message=message, node=node))

    def warning(self, message: str, node: Optional[ASTNode] = None):
        """Record a semantic warning."""
        self.warnings.append(AnalysisError(message=message, node=node, is_warning=True))

    def enter_scope(self, name: str):
        """Enter a new scope."""
        new_scope = Scope(
            name=name,
            level=self.current_scope.level + 1,
            parent=self.current_scope
        )
        self.current_scope = new_scope

    def exit_scope(self):
        """Exit the current scope."""
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    def define_symbol(self, symbol: Symbol, node: Optional[ASTNode] = None):
        """Define a symbol in the current scope."""
        if not self.current_scope.define(symbol):
            self.error(f"Symbol '{symbol.name}' is already defined in this scope", node)

    def lookup_symbol(self, name: str) -> Optional[Symbol]:
        """Look up a symbol in the current scope chain. The code of an imported module does not
        see the main program's global variables (dashweb D14): its "x = 1" is its own local."""
        symbol = self.current_scope.lookup(name)
        if (symbol is not None and getattr(self, "current_module", None) is not None
                and symbol.symbol_type == SymbolType.VARIABLE and isinstance(symbol.node, GlobalVarDecl)
                and getattr(symbol.node, "module", None) is None):
            return None
        return symbol

    # === Visitor Methods ===

    def visit_Program(self, node: Program):
        """Visit the program node."""
        self.structs = list(node.structs)

        # First pass: register all structs
        for struct in node.structs:
            symbol = Symbol(
                name=struct.name,
                symbol_type=SymbolType.STRUCT,
                dash_type=DashType.UNKNOWN,
                node=struct
            )
            self.define_symbol(symbol, struct)

        # Register all enums
        for enum in node.enums:
            symbol = Symbol(
                name=enum.name,
                symbol_type=SymbolType.ENUM,
                dash_type=DashType.INT,
                node=enum
            )
            self.define_symbol(symbol, enum)

        self._check_type_names(node)

        # Register all constants
        for const in node.constants:
            dash_type = self._infer_type(const.value)
            symbol = Symbol(
                name=const.name,
                symbol_type=SymbolType.CONSTANT,
                dash_type=dash_type,
                node=const,
                is_initialized=True
            )
            self.define_symbol(symbol, const)

        # Register all global variables
        for gvar in node.global_vars:
            dash_type = self._type_annotation_to_dash_type(gvar.var_type)
            symbol = Symbol(
                name=gvar.name,
                symbol_type=SymbolType.VARIABLE,
                dash_type=dash_type,
                node=gvar,
                is_initialized=True,  # C globals start zeroed
                struct_name=self._struct_type_name(gvar.var_type),
                elem_struct=self._list_elem_struct(gvar.var_type),
                dict_value=dict_value_type(gvar.var_type),
                list_fixed=list_elem_type(gvar.var_type) == "Fixed",
                list_type=self._list_decl(gvar.var_type)
            )
            self.define_symbol(symbol, gvar)

        # Second pass: register all windows
        for window in node.windows:
            self.visit(window)

        # Third pass: register all functions
        for func in node.functions:
            symbol = Symbol(
                name=func.name,
                symbol_type=SymbolType.FUNCTION,
                dash_type=DashType.VOID,
                node=func
            )
            self.define_symbol(symbol, func)

        # Register all extern functions
        for extern in node.extern_funcs:
            symbol = Symbol(
                name=extern.name,
                symbol_type=SymbolType.EXTERN_FUNC,
                dash_type=DashType.UNKNOWN,
                node=extern
            )
            self.define_symbol(symbol, extern)

        # Register all native functions
        for native in node.native_funcs:
            symbol = Symbol(
                name=native.name,
                symbol_type=SymbolType.NATIVE_FUNC,
                dash_type=DashType.UNKNOWN,
                node=native
            )
            self.define_symbol(symbol, native)

        # User definitions must not hide builtins: calls would still go to the builtin
        for defn in list(node.functions) + list(node.native_funcs) + list(node.structs):
            if is_builtin(defn.name):
                self.error(f"'{defn.name}' is a builtin function name and cannot be redefined", defn)

        # Analyze function and method bodies
        for func in node.functions:
            self.visit(func)
        for struct in node.structs:
            for method in struct.methods:
                self._visit_struct_method(method, struct.name)

        # Fourth pass: analyze main block
        for extra in node.extra_mains:
            self.error("Program has more than one Main block", extra)
        if node.main:
            self.visit(node.main)
        else:
            self.warning(NO_MAIN)

        # Check for unused windows
        for window in node.windows:
            symbol = self.lookup_symbol(window.name)
            if symbol and not symbol.is_opened:
                self.warning(f"Window '{window.name}' is defined but never opened", window)

    def visit_WindowDef(self, node: WindowDef):
        """Visit a window definition."""
        symbol = Symbol(
            name=node.name,
            symbol_type=SymbolType.WINDOW,
            dash_type=DashType.WINDOW,
            node=node
        )
        self.define_symbol(symbol, node)

        for prop in node.properties:
            kind = WindowDef.PROPERTY_KINDS.get(prop.name)
            value = prop.value
            if kind is None:
                known = ", ".join(WindowDef.PROPERTY_KINDS)
                self.error(f"Unknown window property '{prop.name}' (known: {known})", node)
            elif kind == "bool" and not isinstance(value, BoolLiteral):
                self.error(f"Window property '{prop.name}' takes true or false", node)
            elif kind == "int" and not isinstance(value, NumberLiteral):
                self.error(f"Window property '{prop.name}' takes a number", node)
            elif kind == "string" and not isinstance(value, StringLiteral):
                self.error(f"Window property '{prop.name}' takes a string", node)

        # Validate required properties
        if not node.get_property("title"):
            self.warning(f"Window '{node.name}' has no title, using default", node)

    def visit_MainBlock(self, node: MainBlock):
        """Visit the main block."""
        self.enter_scope("main")
        for stmt in node.body:
            self.visit(stmt)
        self.exit_scope()

    def visit_WindowOpen(self, node: WindowOpen):
        """Visit a window open statement."""
        symbol = self.lookup_symbol(node.window_name)
        if not symbol:
            self.error(f"Window '{node.window_name}' is not defined", node)
        elif symbol.symbol_type != SymbolType.WINDOW:
            self.error(f"'{node.window_name}' is not a Window", node)
        else:
            symbol.is_opened = True
            self.opened_windows.append(node.window_name)
            self.current_window = node.window_name

    def visit_WindowClose(self, node: WindowClose):
        symbol = self.lookup_symbol(node.window_name)
        if not symbol:
            self.error(f"Window '{node.window_name}' is not defined", node)
        elif symbol.symbol_type != SymbolType.WINDOW:
            self.error(f"'{node.window_name}' is not a Window", node)

    def visit_EventLoop(self, node: EventLoop):
        """Visit an event loop."""
        if not self.opened_windows:
            self.error("EventLoop requires an open window", node)
            return

        self.in_event_loop = True
        self.enter_scope("event_loop")

        has_close_handler = False
        for handler in node.handlers:
            self.visit(handler)
            if isinstance(handler, OnCloseHandler):
                has_close_handler = True

        if not has_close_handler:
            self.warning("EventLoop has no On Close handler - program may not exit properly", node)

        self.exit_scope()
        self.in_event_loop = False

    def visit_OnCloseHandler(self, node: OnCloseHandler):
        """Visit an On Close handler."""
        self.enter_scope("on_close")
        has_stop = any(isinstance(stmt, StopStmt) for stmt in node.body)
        self._visit_new_body(node.body)
        if not has_stop:
            self.warning("On Close handler has no Stop command", node)
        self.exit_scope()

    def visit_OnGadgetHandler(self, node: OnGadgetHandler):
        self.enter_scope("on_gadget")
        self._visit_new_body(node.body)
        self.exit_scope()

    def visit_OnMenuHandler(self, node: OnMenuHandler):
        self.enter_scope("on_menu")
        self._visit_new_body(node.body)
        self.exit_scope()

    def visit_OnClickHandler(self, node: OnClickHandler):
        self.enter_scope("on_click")
        self._visit_new_body(node.body)
        self.exit_scope()

    def visit_OnTimerHandler(self, node: OnTimerHandler):
        if isinstance(node.interval, str):
            self.visit(VarRef(name=node.interval, location=node.location))
        elif node.interval <= 0:
            self.error("On Timer needs a positive number of milliseconds", node)
        self.enter_scope("on_timer")
        self._visit_new_body(node.body)
        self.exit_scope()

    def visit_OnKeyHandler(self, node: OnKeyHandler):
        """Visit an On Key handler."""
        key = node.key
        if isinstance(key, str) and len(key) != 1 and key.upper() not in KEY_NAMES:
            self.error(f"Unknown key '{key}' in On Key: use one character (\"a\"), a raw code "
                       f"(0x45) or a name ({', '.join(KEY_NAMES)})", node)
        elif isinstance(key, int) and not 0 <= key <= 0x7F:
            self.error(f"Raw key code {key} out of range (0..0x7F)", node)
        self.enter_scope("on_key")
        self._visit_new_body(node.body)
        self.exit_scope()

    def visit_PrintStmt(self, node: PrintStmt):
        """Visit a print statement."""
        self.visit(node.message)

    def visit_WaitStmt(self, node: WaitStmt):
        """Visit a wait statement."""
        if isinstance(node.seconds, NumberLiteral) and node.seconds.value < 0:
            self.error("Wait time cannot be negative", node)
        self.visit(node.seconds)

    def visit_BreakStmt(self, node: BreakStmt):
        if self.loop_depth == 0:
            self.error("break can only be used inside a while or for loop", node)

    def visit_ContinueStmt(self, node: ContinueStmt):
        if self.loop_depth == 0:
            self.error("continue can only be used inside a while or for loop", node)

    def _visit_loop_body(self, body):
        self.loop_depth += 1
        for stmt in body:
            self.visit(stmt)
        self.loop_depth -= 1

    def _visit_new_body(self, body):
        """A body that starts outside any loop: function, method, lambda or
        EventLoop handler (in C a handler is a switch case, where break would
        leave the switch instead of a Dash loop)."""
        saved, self.loop_depth = self.loop_depth, 0
        for stmt in body:
            self.visit(stmt)
        self.loop_depth = saved

    def visit_StopStmt(self, node: StopStmt):
        """Visit a stop statement."""
        if not self.in_event_loop:
            self.error("Stop can only be used inside an EventLoop handler", node)

    def visit_VarDecl(self, node: VarDecl):
        """Visit a variable declaration (var name: Type = value inside a function or Main)."""
        # Analyze initial value first
        if node.initial_value:
            self.visit(node.initial_value)

        if node.var_type:
            known = self._TYPE_NAMES | {st.name for st in self.structs} | {
                e.name for e in (self.program.enums if self.program else [])}
            if not type_is_known(node.var_type, known):
                self.error(f"Unknown type '{node.var_type}' (variable '{node.name}')", node)
            dash_type = self._type_annotation_to_dash_type(node.var_type)
            if isinstance(node.initial_value, NilLiteral) and dash_type in self._NO_NIL:
                self.error(f"'{node.name}' is {node.var_type}: nil is only for structs, Arrays and Strings", node)
        else:
            dash_type = self._infer_type(node.initial_value) if node.initial_value else DashType.UNKNOWN
        symbol = Symbol(
            name=node.name,
            symbol_type=SymbolType.VARIABLE,
            dash_type=dash_type,
            node=node,
            is_initialized=True,
            struct_name=self._struct_type_name(node.var_type) if node.var_type else None,
            elem_struct=self._list_elem_struct(node.var_type),
            dict_value=dict_value_type(node.var_type),
            list_fixed=(list_elem_type(node.var_type) == "Fixed" if node.var_type
                        else self._is_fixed_list(node.initial_value)),
            list_type=(self._list_decl(node.var_type) if node.var_type
                       else self._declared_list_type(node.initial_value))
        )
        self.define_symbol(symbol, node)

    def visit_VarAssign(self, node: VarAssign):
        """Visit a variable assignment (Python style - first use declares)."""
        # First, analyze the value expression
        self.visit(node.value)

        # Check if variable already exists
        symbol = self.lookup_symbol(node.name)
        if isinstance(node.value, NilLiteral):
            if not symbol:
                self.error(f"'{node.name} = nil' does not say what '{node.name}' holds: "
                           f"declare it with a type (var {node.name}: Tipo = nil)", node)
            elif symbol.dash_type in self._NO_NIL:
                self.error(f"'{node.name}' holds a {symbol.dash_type.name.lower()}: "
                           f"nil is only for structs, Arrays and Strings", node)
            return
        if not symbol:
            # First assignment - declare the variable
            symbol = Symbol(
                name=node.name,
                symbol_type=SymbolType.VARIABLE,
                dash_type=self._infer_type(node.value),
                node=node,
                is_initialized=True,
                struct_name=self._struct_name_of(node.value),
                elem_struct=self._elem_struct_of(node.value),
                dict_value=self._dict_value_of(node.value),
                list_fixed=self._is_fixed_list(node.value),
                list_type=self._declared_list_type(node.value)
            )
            self.define_symbol(symbol, node)
        elif symbol.symbol_type in (SymbolType.FUNCTION, SymbolType.NATIVE_FUNC, SymbolType.EXTERN_FUNC):
            # a variable may hide a function with its name (one of the program in a module's code,
            # say): it is a new variable of this scope (dashweb D14)
            self.define_symbol(Symbol(
                name=node.name,
                symbol_type=SymbolType.VARIABLE,
                dash_type=self._infer_type(node.value),
                node=node,
                is_initialized=True,
                struct_name=self._struct_name_of(node.value),
                elem_struct=self._elem_struct_of(node.value),
                dict_value=self._dict_value_of(node.value),
                list_type=self._declared_list_type(node.value)
            ), node)
        elif symbol.symbol_type not in (SymbolType.VARIABLE, SymbolType.PARAMETER):
            self.error(f"Cannot assign to '{node.name}' - it's not a variable", node)
        else:
            # The C variable keeps its first type: a string cannot become a number or vice versa
            new_type = self._infer_type(node.value)
            known = (DashType.UNKNOWN,)
            if (symbol.dash_type not in known and new_type not in known
                    and (symbol.dash_type == DashType.STRING) != (new_type == DashType.STRING)):
                self.error(f"Cannot assign a {new_type.name.lower()} to '{node.name}', "
                           f"which holds a {symbol.dash_type.name.lower()}", node)
            elif symbol.dash_type == DashType.INT and new_type == DashType.FLOAT:
                self.error(f"Cannot assign a float to '{node.name}', which holds an int "
                           f"(declare it with a float: {node.name} = 0.0, or use Int())", node)
            elif symbol.dash_type == DashType.INT and new_type == DashType.FIXED:
                self.error(f"Cannot assign a Fixed to '{node.name}', which holds an int (use Int())", node)
            elif DashType.FIXED in (symbol.dash_type, new_type) and DashType.FLOAT in (symbol.dash_type, new_type):
                self.error(f"Cannot mix Fixed and Float in '{node.name}' (convert with Fixed() or Float())", node)
            symbol.is_initialized = True

    def visit_VarRef(self, node: VarRef):
        """Visit a variable reference."""
        symbol = self.lookup_symbol(node.name)
        self._check_private(node.name, symbol, node)
        if not symbol:
            self._not_defined("Variable", node.name, node)
        elif symbol.symbol_type == SymbolType.VARIABLE and not symbol.is_initialized:
            self.warning(f"Variable '{node.name}' may be used before initialization", node)

    def visit_IfStmt(self, node: IfStmt):
        """Visit an if statement."""
        self.visit(node.condition)
        self.enter_scope("if_then")
        for stmt in node.then_body:
            self.visit(stmt)
        self.exit_scope()

        if node.else_body:
            self.enter_scope("if_else")
            for stmt in node.else_body:
                self.visit(stmt)
            self.exit_scope()

    def visit_WhileStmt(self, node: WhileStmt):
        """Visit a while statement."""
        self.visit(node.condition)
        self.enter_scope("while")
        self._visit_loop_body(node.body)
        self.exit_scope()

    def visit_ForRangeStmt(self, node: ForRangeStmt):
        """Visit a for-range statement."""
        # Visit range expressions
        self.visit(node.start)
        self.visit(node.end)
        if node.step is not None:
            self.visit(node.step)
            if constant_int(node.step, self.program) == 0:
                self.error("for loop step cannot be 0", node.step)

        self.enter_scope("for_range")
        # Define loop variable
        symbol = Symbol(
            name=node.variable,
            symbol_type=SymbolType.VARIABLE,
            dash_type=DashType.INT,
            node=node,
            is_initialized=True
        )
        self.define_symbol(symbol, node)

        self._visit_loop_body(node.body)
        self.exit_scope()

    def visit_ForEachStmt(self, node: ForEachStmt):
        """Visit a for-each statement."""
        # Visit the iterable
        self.visit(node.iterable)
        if self._dict_value_of(node.iterable) is not None:
            self.error("To go through a dictionary use 'for k in d.keys()'", node)

        self.enter_scope("for_each")
        # Define loop variable (element type)
        elem = self._elem_struct_of(node.iterable)
        # what the list declares its elements are, when known: a list or dictionary inside (D49)
        decl = list_elem_type(self._declared_list_type(node.iterable))
        inner = decl if decl and (list_elem_type(decl) is not None or dict_value_type(decl) is not None) else None
        symbol = Symbol(
            name=node.variable,
            symbol_type=SymbolType.VARIABLE,
            # ints unless a list of structs, of Strings, of lists or of dictionaries
            dash_type=(DashType.UNKNOWN if elem else
                       self._type_annotation_to_dash_type(inner) if inner else
                       DashType.FIXED if self._is_fixed_list(node.iterable) else
                       DashType.STRING if self._list_kind(node.iterable) == "string" else DashType.INT),
            node=node,
            is_initialized=True,
            struct_name=elem,
            elem_struct=self._list_elem_struct(inner) if inner else None,
            dict_value=dict_value_type(inner) if inner else None,
            list_fixed=bool(inner) and list_elem_type(inner) == "Fixed",
            list_type=self._list_decl(inner)
        )
        self.define_symbol(symbol, node)

        self._visit_loop_body(node.body)
        self.exit_scope()

    def _not_defined(self, kind: str, name: str, node: ASTNode):
        """'X is not defined', or 'is private to module' when it is another module's private
        function, constant, global, struct or enum, renamed in that module (D18, D45)."""
        program = self.program
        defs = ([] if not program else list(program.functions) + list(program.native_funcs)
                + list(program.constants) + list(program.global_vars) + list(program.structs)
                + list(program.enums))
        owner = next((getattr(d, "module", None) for d in defs if getattr(d, "dash_name", None) == name), None)
        if owner:
            self.error(f"'{name}' is private to module '{os.path.basename(owner)}'", node)
        else:
            self.error(f"{kind} '{name}' is not defined", node)

    def _check_private(self, name: str, symbol: Optional[Symbol], node: ASTNode):
        """A name starting with _ defined in a module is usable only inside that module."""
        if not symbol or not name.startswith("_") or symbol.node is None:
            return
        owner = getattr(symbol.node, "module", None)
        if owner is not None and owner != self.current_module:
            self.error(f"'{name}' is private to module '{os.path.basename(owner)}'", node)

    def visit_FunctionDef(self, node: FunctionDef):
        """Visit a function definition."""
        self.current_module = getattr(node, "module", None)
        self.in_function = True
        self._returns = (node.name, node.return_type)
        self.enter_scope(f"func_{node.name}")

        # Define parameters (can be string or FunctionParam)
        for param in node.params:
            if isinstance(param, FunctionParam):
                param_name = param.name
                dash_type = self._type_annotation_to_dash_type(param.param_type)
            else:
                param_name = param
                dash_type = DashType.UNKNOWN

            symbol = Symbol(
                name=param_name,
                symbol_type=SymbolType.PARAMETER,
                dash_type=dash_type,
                is_initialized=True,
                struct_name=self._struct_type_name(param.param_type if isinstance(param, FunctionParam) else None),
                elem_struct=self._list_elem_struct(param.param_type if isinstance(param, FunctionParam) else None),
                dict_value=dict_value_type(param.param_type if isinstance(param, FunctionParam) else None),
                list_fixed=list_elem_type(param.param_type if isinstance(param, FunctionParam) else None) == "Fixed",
                list_type=self._list_decl(param.param_type if isinstance(param, FunctionParam) else None)
            )
            self.define_symbol(symbol, node)

        self._visit_new_body(node.body)

        self.exit_scope()
        self.in_function = False
        self.current_module = None
        self._returns = None

    def visit_LambdaFunc(self, node: LambdaFunc):
        """Visit a lambda. It becomes a top-level C function, so it only sees
        its parameters and global names (no captured local variables)."""
        saved_scope, saved_in_function = self.current_scope, self.in_function
        saved_returns = getattr(self, "_returns", None)
        self._returns = None
        self.current_scope = Scope(name="lambda", level=1, parent=self.global_scope)
        self.in_function = True
        for param in node.params:
            name = param.name if isinstance(param, FunctionParam) else param
            dash_type = (self._type_annotation_to_dash_type(param.param_type)
                         if isinstance(param, FunctionParam) else DashType.UNKNOWN)
            self.define_symbol(Symbol(name=name, symbol_type=SymbolType.PARAMETER,
                                      dash_type=dash_type, is_initialized=True,
                                      struct_name=self._struct_type_name(
                                          param.param_type if isinstance(param, FunctionParam) else None),
                                      elem_struct=self._list_elem_struct(
                                          param.param_type if isinstance(param, FunctionParam) else None),
                                      dict_value=dict_value_type(
                                          param.param_type if isinstance(param, FunctionParam) else None),
                                      list_fixed=list_elem_type(param.param_type if isinstance(param, FunctionParam) else None) == "Fixed",
                list_type=self._list_decl(param.param_type if isinstance(param, FunctionParam) else None)),
                               node)
        before = len(self.errors)
        self._visit_new_body(node.body if isinstance(node.body, list) else [node.body])
        for err in self.errors[before:]:
            if "is not defined" in err.message:
                err.message += " (lambdas cannot use local variables from outside)"
        self.current_scope, self.in_function = saved_scope, saved_in_function
        self._returns = saved_returns

    def _visit_struct_method(self, node: StructMethod, struct_name: Optional[str] = None):
        """Visit a struct method body; 'self' is an implicit parameter."""
        self.in_function = True
        self._returns = (f"{struct_name}.{node.name}" if struct_name else node.name, node.return_type)
        self.enter_scope(f"method_{node.name}")
        self.define_symbol(Symbol(name="self", symbol_type=SymbolType.PARAMETER, struct_name=struct_name,
                                  is_initialized=True), node)
        for param in node.params:
            name = param.name if isinstance(param, FunctionParam) else param
            dash_type = (self._type_annotation_to_dash_type(param.param_type)
                         if isinstance(param, FunctionParam) else DashType.UNKNOWN)
            self.define_symbol(Symbol(name=name, symbol_type=SymbolType.PARAMETER,
                                      dash_type=dash_type, is_initialized=True,
                                      struct_name=self._struct_type_name(
                                          param.param_type if isinstance(param, FunctionParam) else None),
                                      elem_struct=self._list_elem_struct(
                                          param.param_type if isinstance(param, FunctionParam) else None),
                                      dict_value=dict_value_type(
                                          param.param_type if isinstance(param, FunctionParam) else None),
                                      list_fixed=list_elem_type(param.param_type if isinstance(param, FunctionParam) else None) == "Fixed",
                list_type=self._list_decl(param.param_type if isinstance(param, FunctionParam) else None)),
                               node)
        self._visit_new_body(node.body)
        self.exit_scope()
        self.in_function = False

    def visit_FunctionCall(self, node: FunctionCall):
        """Visit a function call."""
        # Int(x) / Float(x) / Fixed(x): conversions; fx_*: Fixed functions
        if node.name in ("Int", "Float", "Fixed", "fx_sqrt", "fx_sin", "fx_cos"):
            if len(node.arguments) != 1:
                self.error(f"{node.name}() expects 1 argument, got {len(node.arguments)}", node)
            for arg in node.arguments:
                self.visit(arg)
                if self._infer_type(arg) == DashType.STRING and node.name != "Int":
                    self.error(f"{node.name}() converts numbers, not strings", node)
            return

        # Check if it's a builtin function
        builtin = get_builtin(node.name)
        if builtin:
            from compiler.codegen import unimplemented_builtins  # lazy: codegen imports this module
            if node.name in unimplemented_builtins():
                self.error(f"Builtin '{node.name}' is declared but not implemented yet "
                           f"(no C runtime for it)", node)
            # Validate argument count for builtin
            expected = len(builtin.params)
            actual = len(node.arguments)
            if expected != actual:
                self.error(f"Builtin '{node.name}' expects {expected} arguments, got {actual}", node)
            for arg in node.arguments:
                self.visit(arg)
            return

        symbol = self.lookup_symbol(node.name)
        self._check_private(node.name, symbol, node)
        if not symbol:
            self._not_defined("Function", node.name, node)
        elif symbol.symbol_type == SymbolType.STRUCT:
            # Struct constructor call - validate field count
            struct_node = symbol.node
            if isinstance(struct_node, StructDef):
                # Count required fields (without defaults)
                required = sum(1 for f in struct_node.fields if f.default_value is None)
                total = len(struct_node.fields)
                actual = len(node.arguments)
                if actual < required or actual > total:
                    if required == total:
                        self.error(f"Struct '{node.name}' expects {required} arguments, got {actual}", node)
                    else:
                        self.error(f"Struct '{node.name}' expects {required}-{total} arguments, got {actual}", node)
        elif symbol.symbol_type == SymbolType.EXTERN_FUNC:
            # External function call - validate argument count
            extern_node = symbol.node
            if isinstance(extern_node, ExternFunc):
                expected = len(extern_node.params)
                actual = len(node.arguments)
                if expected != actual:
                    self.error(f"Extern function '{node.name}' expects {expected} arguments, got {actual}", node)
        elif symbol.symbol_type == SymbolType.NATIVE_FUNC:
            # Native function call - validate argument count
            native_node = symbol.node
            if isinstance(native_node, NativeFunc):
                expected = len(native_node.params)
                actual = len(node.arguments)
                if expected != actual:
                    self.error(f"Native function '{node.name}' expects {expected} arguments, got {actual}", node)
        elif symbol.symbol_type in (SymbolType.VARIABLE, SymbolType.PARAMETER):
            # Calling through a function pointer (lambda or Func parameter)
            if symbol.dash_type != DashType.FUNC:
                self.error(f"'{node.name}' is not a function; a parameter that receives "
                           f"a function must be declared '{node.name}: Func'", node)
        elif symbol.symbol_type not in (SymbolType.FUNCTION, SymbolType.EXTERN_FUNC, SymbolType.NATIVE_FUNC):
            self.error(f"'{node.name}' is not a function or struct", node)
        else:
            # Check argument count for regular functions
            func_node = symbol.node
            if isinstance(func_node, FunctionDef):
                expected = len(func_node.params)
                actual = len(node.arguments)
                if expected != actual:
                    self.error(f"Function '{node.name}' expects {expected} arguments, got {actual}", node)
                if not node.is_statement and not self._returns_value(func_node):
                    self.error(f"Function '{node.name}' does not return a value", node)

        for arg in node.arguments:
            self.visit(arg)

    def visit_ReturnStmt(self, node: ReturnStmt):
        """Visit a return statement."""
        if not self.in_function:
            self.error("'return' outside of function", node)
        if node.value:
            self.visit(node.value)
        returns = getattr(self, "_returns", None)
        if returns and returns[1]:
            self._check_return(returns[0], returns[1], node)

    _NUMBER_TYPES = ("Int", "Float", "Fixed", "Bool")

    def _check_return(self, func: str, declared: str, node: ReturnStmt):
        """The value of a return against the declared return type. Only what is sure: a String
        where a number or Bool goes and back, a struct of another type, nil where it does not fit,
        a value in a Void function. (Ints are the default of some inferences, e.g. an element of
        an untyped list, so an Int is only wrong when it is a literal.)"""
        value = node.value
        where = f"'{func}' returns {declared}"
        if declared == "Void":
            if value is not None:
                self.error(f"{where}: 'return' cannot give a value", node)
            return
        if value is None or declared in ("Pointer", "Func"):
            return
        if isinstance(value, NilLiteral):
            if declared in self._NUMBER_TYPES:
                self.error(f"{where}: nil is only for structs, Arrays and Strings", node)
            return
        vtype = self._infer_type(value)
        vstruct = self._struct_name_of(value)
        literal = value.operand if isinstance(value, UnaryOp) and value.operator == "-" else value
        number_literal = isinstance(literal, (NumberLiteral, FloatLiteral, BoolLiteral))
        is_list = isinstance(value, ArrayLiteral) or vtype in (DashType.ARRAY_INT, DashType.ARRAY_STRING)
        got = None
        if declared == "String":
            if number_literal or vtype in (DashType.BOOL, DashType.FLOAT, DashType.FIXED):
                got = vtype.name.capitalize() if not number_literal else type(literal).__name__.replace("Literal", "")
            elif vstruct:
                got = vstruct
            elif is_list:
                got = "a list"
        elif declared in self._NUMBER_TYPES:
            if vtype == DashType.STRING:
                got = "String"
            elif vstruct:
                got = vstruct
            elif is_list:
                got = "a list"
        elif self._struct_type_name(declared):
            if vtype == DashType.STRING:
                got = "String"
            elif number_literal or vtype in (DashType.BOOL, DashType.FLOAT, DashType.FIXED):
                got = vtype.name.capitalize() if not number_literal else type(literal).__name__.replace("Literal", "")
            elif vstruct and vstruct != declared:
                got = vstruct
            elif is_list:
                got = "a list"
        elif list_elem_type(declared) is not None or declared == "Array" or dict_value_type(declared) is not None:
            if vtype == DashType.STRING:
                got = "String"
            elif number_literal or vtype in (DashType.BOOL, DashType.FLOAT, DashType.FIXED):
                got = vtype.name.capitalize() if not number_literal else type(literal).__name__.replace("Literal", "")
            elif vstruct:
                got = vstruct
        if got:
            self.error(f"{where}, not {got}", node)

    def visit_ArrayLiteral(self, node: ArrayLiteral):
        """Visit an array literal."""
        for element in node.elements:
            self.visit(element)
        fixed = self._is_fixed_list(node)
        for element in node.elements:
            if fixed:
                self._check_fixed_element(element)
            else:
                self._check_not_float_element(element)

    def _check_fixed_element(self, value: ASTNode):
        """What goes into a list of Fixed values: Fixed values or number literals (made Fixed)."""
        lit = value.operand if isinstance(value, UnaryOp) and value.operator == "-" else value
        if self._infer_type(value) != DashType.FIXED and not isinstance(lit, (NumberLiteral, FloatLiteral)):
            self.error("A list of Fixed values holds Fixed values (or number literals)", value)

    def _is_fixed_list(self, expr: Optional[ASTNode]) -> bool:
        """True if the expression is a list of Fixed values: a [Fixed] variable, parameter, call or
        field, a literal with a Fixed element (the rest Fixed or numbers), or a slice or + of one."""
        if expr is None:
            return False
        if isinstance(expr, VarRef):
            symbol = self.lookup_symbol(expr.name)
            return bool(symbol and symbol.list_fixed)
        if isinstance(expr, ArrayLiteral):
            return any(self._infer_type(e) == DashType.FIXED for e in expr.elements)
        if isinstance(expr, ArraySlice):
            return self._is_fixed_list(expr.array)
        if isinstance(expr, BinaryOp) and expr.operator == "+":
            return self._is_fixed_list(expr.left) or self._is_fixed_list(expr.right)
        if isinstance(expr, (FunctionCall, PropertyAccess, MemberAccess)):
            return list_elem_type(self._declared_list_type(expr)) == "Fixed"
        return False

    def _check_not_float_element(self, value: ASTNode):
        if self._infer_type(value) == DashType.FIXED:
            self.error("Arrays hold integers or strings, not Fixed values "
                       "(use a struct with Fixed fields)", value)
        if self._infer_type(value) == DashType.FLOAT:
            self.error("Arrays hold integers or strings, not Float values "
                       "(use a struct with Float fields, or scale to integers)", value)

    def visit_ArrayAccess(self, node: ArrayAccess):
        """Visit an array access."""
        self.visit(node.array)
        self.visit(node.index)
        if self._dict_value_of(node.array) is not None and self._infer_type(node.index) == DashType.INT:
            self.error("Dictionary keys are Strings", node)
        if getattr(node, "default", None) is not None:          # d.get(k, default) (D65)
            self.visit(node.default)
            value = self._dict_value_of(node.array)
            got = self._infer_type(node.default)
            want = {"Int": DashType.INT, "String": DashType.STRING, "Bool": DashType.BOOL}.get(value)
            if want is None:
                if not isinstance(node.default, NilLiteral):
                    self.error(f"get() on a dictionary of {value}: the default can only be nil "
                               f"(use has() for another one)", node.default)
            elif got not in (want, DashType.UNKNOWN) and not (want == DashType.BOOL and got == DashType.INT):
                self.error(f"get(): the default must be {value}, like the dictionary's values", node.default)

    def visit_DictLiteral(self, node: DictLiteral):
        """{"clave": valor}: String keys, values of one type."""
        for key, value in zip(node.keys, node.values):
            self.visit(key)
            self.visit(value)
            if self._infer_type(key) not in (DashType.STRING, DashType.UNKNOWN):
                self.error("Dictionary keys are Strings", key)
            self._check_not_float_element(value)

    def visit_ArrayAssign(self, node: ArrayAssign):
        """Visit an array assignment."""
        self.visit(node.array)
        self.visit(node.index)
        self.visit(node.value)
        if self._is_fixed_list(node.array):
            self._check_fixed_element(node.value)
        else:
            self._check_not_float_element(node.value)
        if self._dict_value_of(node.array) is not None and self._infer_type(node.index) == DashType.INT:
            self.error("Dictionary keys are Strings", node)

    def visit_PropertyAccess(self, node: PropertyAccess):
        """Visit a property access."""
        self.visit(node.object)
        # .length, or a field of some struct (the object's struct type is not tracked here)
        known = node.property == "length" or any(
            struct.get_field(node.property) for struct in self.structs)
        if not known:
            self.warning(f"Unknown property '{node.property}'", node)

    def visit_MemberAccess(self, node: MemberAccess):
        """Visit a member access (player.x or Direction.UP)."""
        # Check if it's an enum value access
        symbol = self.lookup_symbol(node.object_name)
        if symbol and symbol.symbol_type == SymbolType.ENUM:
            # Validate enum value exists
            enum_node = symbol.node
            if isinstance(enum_node, EnumDef):
                if not enum_node.get_value(node.member):
                    self.error(f"Enum '{node.object_name}' has no value '{node.member}'", node)
            return

        # Check if the object variable exists
        if not symbol:
            self._not_defined("Variable", node.object_name, node)
            return

        # Win.width/height/left/top/title: current size, position and title of a window
        if symbol.symbol_type == SymbolType.WINDOW:
            if node.member not in ("width", "height", "left", "top", "title",
                                   "inner_left", "inner_top", "inner_width", "inner_height"):
                self.error(f"Window '{node.object_name}' has no readable property '{node.member}' "
                           f"(width, height, left, top, title, inner_left, inner_top, inner_width, "
                           f"inner_height)", node)
            return

        # For array.length, allow it
        if node.member == "length":
            return

        # For struct members, validate the member exists
        # We need to track the type of the variable to know if it's a struct
        # For now, we'll allow any member access and let codegen handle it

    def visit_MemberAssign(self, node: MemberAssign):
        """Visit a member assignment (player.x = 10, a.b.c = 10)."""
        # Check if the object variable exists
        symbol = self.lookup_symbol(node.object_name)
        if not symbol:
            self._not_defined("Variable", node.object_name, node)
            return

        if node.target is not None:
            # a.b.c = x: every step before the last one must be a struct field
            self.visit(node.target)
            owner = self._struct_name_of(node.target)
            if owner is None:
                self.error(f"Cannot assign '{self._chain_text(node)}': "
                           f"'{self._chain_text(node, last=False)}' is not a known struct "
                           f"(give the variable or parameter a struct type)", node)
        else:
            owner = symbol.struct_name
        struct = self.program.get_struct(owner) if (owner and self.program) else None
        if struct and not struct.get_field(node.member):
            self.error(f"Struct '{owner}' has no field '{node.member}'", node)

        # Visit the value being assigned
        self.visit(node.value)

    def _chain_text(self, node: MemberAssign, last: bool = True) -> str:
        """Source text of the assigned chain: a.b.c (or a.b without the last member)."""
        def text(expr):
            if isinstance(expr, MemberAccess):
                return f"{expr.object_name}.{expr.member}"
            if isinstance(expr, PropertyAccess):
                return f"{text(expr.object)}.{expr.property}"
            return "self" if isinstance(expr, SelfRef) else getattr(expr, "name", "?")
        owner = text(node.target) if node.target is not None else node.object_name
        return f"{owner}.{node.member}" if last else owner

    def _return_values(self, stmts):
        """Values of the return statements in a body (nested blocks included)."""
        for stmt in stmts or []:
            if isinstance(stmt, ReturnStmt) and stmt.value is not None:
                yield stmt.value
            for attr in ("then_body", "else_body", "body"):
                nested = getattr(stmt, attr, None)
                if isinstance(nested, list):
                    yield from self._return_values(nested)

    def _dict_value_of(self, expr: Optional[ASTNode]) -> Optional[str]:
        """Type of the values ("Int", "String", "Nodo", "[Int]"...) if expr is a dictionary."""
        if isinstance(expr, DictLiteral):
            if not expr.values:
                return "Int"
            first = expr.values[0]
            struct = self._struct_name_of(first)
            if struct:
                return struct
            if isinstance(first, ArrayLiteral):
                return "Array"
            return "String" if self._infer_type(first) == DashType.STRING else "Int"
        if isinstance(expr, VarRef):
            symbol = self.lookup_symbol(expr.name)
            return symbol.dict_value if symbol else None
        if isinstance(expr, ArrayAccess):
            # a value of a dictionary of dictionaries, or an element of a list of them: d[k], l[i]
            outer = self._dict_value_of(expr.array)
            if outer is not None:
                return dict_value_type(outer)
            return dict_value_type(list_elem_type(self._declared_list_type(expr.array)))
        if isinstance(expr, (FunctionCall, MethodCall, PropertyAccess, MemberAccess)) and self.program:
            type_name = None
            if isinstance(expr, (FunctionCall, MethodCall)):
                type_name = self._call_type(expr)
            else:
                if isinstance(expr, MemberAccess):
                    owner, member = self._struct_name_of(VarRef(name=expr.object_name)), expr.member
                else:
                    owner, member = self._struct_name_of(expr.object), expr.property
                struct = self.program.get_struct(owner) if owner else None
                field = struct.get_field(member) if struct else None
                type_name = field.field_type if field else None
            return dict_value_type(type_name)
        return None

    def _list_elem_struct(self, type_name: Optional[str]) -> Optional[str]:
        """For a list type "[Nodo]", the struct of its elements (dashweb D4a)."""
        return self._struct_type_name(list_elem_type(type_name))

    def _struct_type_name(self, type_name: Optional[str]) -> Optional[str]:
        """The type annotation itself when it names a struct."""
        if type_name and self.program and self.program.get_struct(type_name):
            return type_name
        return None

    def _list_kind(self, expr: ASTNode) -> Optional[str]:
        """What a list expression holds: "int", "string", "struct:Name", "list", "any"
        (empty or unknown), "fixed" (a list of Fixed), or None if expr is not a list."""
        if self._is_fixed_list(expr):
            return "fixed"
        if isinstance(expr, MethodCall) and expr.method == "keys" and self._dict_value_of(expr.object) is not None:
            return "string"
        if isinstance(expr, ArraySlice):
            return self._list_kind(expr.array)
        if isinstance(expr, BinaryOp) and expr.operator == "+":
            kinds = [self._list_kind(expr.left), self._list_kind(expr.right)]
            if None in kinds:
                return None
            known = [k for k in kinds if k != "any"]
            return known[0] if known else "any"
        if isinstance(expr, ArrayLiteral):
            if not expr.elements:
                return "any"
            struct = self._elem_struct_of(expr)
            if struct:
                return f"struct:{struct}"
            if all(isinstance(e, ArrayLiteral) for e in expr.elements):
                return "list"
            types = {self._infer_type(e) for e in expr.elements}
            if types == {DashType.STRING}:
                return "string"
            if types <= {DashType.INT, DashType.BOOL}:
                return "int"
            return "any"
        if isinstance(expr, VarRef):
            symbol = self.lookup_symbol(expr.name)
            if not symbol:
                return None
            if symbol.elem_struct:
                return f"struct:{symbol.elem_struct}"
            return {DashType.ARRAY_INT: "int", DashType.ARRAY_STRING: "string",
                    DashType.ARRAY: "any"}.get(symbol.dash_type)
        declared = self._declared_list_type(expr)
        if declared:
            elem = list_elem_type(declared)
            if self._struct_type_name(elem):
                return f"struct:{elem}"
            return {"Int": "int", "String": "string"}.get(elem, "list" if list_elem_type(elem) else "any")
        if isinstance(expr, FunctionCall) and self.program:
            func = self.program.get_function(expr.name)
            if func and func.return_type == "Array":
                return "any"
        if isinstance(expr, (PropertyAccess, MemberAccess)) and self.program:
            if isinstance(expr, MemberAccess):
                owner, member = self._struct_name_of(VarRef(name=expr.object_name)), expr.member
            else:
                owner, member = self._struct_name_of(expr.object), expr.property
            struct = self.program.get_struct(owner) if owner else None
            field = struct.get_field(member) if struct else None
            if field and field.field_type == "Array":
                return "any"
        return None

    def _declared_list_type(self, expr: ASTNode) -> Optional[str]:
        """The "[T]" type a call or a struct field declares for its list, if any."""
        if not self.program:
            return None
        type_name = None
        if isinstance(expr, FunctionCall) and get_builtin(expr.name) and get_builtin(expr.name).list_of:
            return f"[{get_builtin(expr.name).list_of}]"
        if isinstance(expr, VarRef):
            symbol = self.lookup_symbol(expr.name)
            return symbol.list_type if symbol else None
        if isinstance(expr, ArrayAccess):   # an element of a list of lists
            inner = list_elem_type(self._declared_list_type(expr.array))
            return inner if list_elem_type(inner) is not None else None
        if isinstance(expr, (FunctionCall, MethodCall)):
            type_name = self._call_type(expr)
        elif isinstance(expr, (PropertyAccess, MemberAccess)):
            if isinstance(expr, MemberAccess):
                owner, member = self._struct_name_of(VarRef(name=expr.object_name)), expr.member
            else:
                owner, member = self._struct_name_of(expr.object), expr.property
            struct = self.program.get_struct(owner) if owner else None
            field = struct.get_field(member) if struct else None
            type_name = field.field_type if field else None
        return type_name if list_elem_type(type_name) is not None else None

    @staticmethod
    def _list_decl(type_name: Optional[str]) -> Optional[str]:
        """type_name if it is a list type ("[T]"), else None."""
        return type_name if type_name and list_elem_type(type_name) is not None else None

    def _call_type(self, expr: ASTNode) -> Optional[str]:
        """The return type a call declares: a function, @native, @extern or a struct's method (D49)."""
        if not self.program:
            return None
        if isinstance(expr, FunctionCall):
            func = self.program.get_function(expr.name) or next(
                (f for f in list(self.program.native_funcs) + list(self.program.extern_funcs)
                 if f.name == expr.name), None)
            return func.return_type if func else None
        if isinstance(expr, MethodCall):
            owner = self._struct_name_of(expr.object)
            struct = self.program.get_struct(owner) if owner else None
            method = struct.get_method(expr.method) if struct else None
            return method.return_type if method else None
        return None

    @staticmethod
    def _kind_text(kind: str) -> str:
        return {"int": "Ints", "string": "Strings", "list": "lists", "fixed": "Fixed values"}.get(
            kind, kind.split(":")[-1])

    def _elem_struct_of(self, expr: Optional[ASTNode]) -> Optional[str]:
        """Struct type of the elements of a list expression, when all are one struct."""
        if isinstance(expr, BinaryOp) and expr.operator == "+":
            return self._elem_struct_of(expr.left) or self._elem_struct_of(expr.right)
        declared = self._declared_list_type(expr)
        if declared:
            return self._list_elem_struct(declared)
        if isinstance(expr, ArrayLiteral) and expr.elements:
            names = {self._struct_name_of(e) for e in expr.elements if not isinstance(e, NilLiteral)}
            return names.pop() if len(names) == 1 else None
        if isinstance(expr, ArraySlice):
            expr = expr.array
        if isinstance(expr, VarRef):
            symbol = self.lookup_symbol(expr.name)
            return symbol.elem_struct if symbol else None
        return None

    def _struct_name_of(self, expr: Optional[ASTNode]) -> Optional[str]:
        """Struct type of the value an expression yields, if known at compile time."""
        prog = self.program
        if prog is None or expr is None:
            return None
        if isinstance(expr, VarRef):
            symbol = self.lookup_symbol(expr.name)
            return symbol.struct_name if symbol else None
        if isinstance(expr, SelfRef):
            symbol = self.lookup_symbol("self")
            return symbol.struct_name if symbol else None
        if isinstance(expr, FunctionCall):
            if prog.get_struct(expr.name):
                return expr.name
            func = prog.get_function(expr.name)
            if not func:
                return None
            if func.return_type:
                return self._struct_type_name(func.return_type)
            # untyped: the struct a "return Struct(...)" in its body builds
            for value in self._return_values(func.body):
                if isinstance(value, FunctionCall) and prog.get_struct(value.name):
                    return value.name
            return None
        if isinstance(expr, ArrayAccess):
            value = self._dict_value_of(expr.array)
            if value is not None:
                return self._struct_type_name(value)
            return self._elem_struct_of(expr.array)
        if isinstance(expr, MethodCall) and expr.method == "pop" and self._list_kind(expr.object):
            return self._elem_struct_of(expr.object)
        if isinstance(expr, MemberAccess):
            owner = self._struct_name_of(VarRef(name=expr.object_name))
            member = expr.member
        elif isinstance(expr, PropertyAccess):
            owner = self._struct_name_of(expr.object)
            member = expr.property
        else:
            return None
        struct = prog.get_struct(owner) if owner else None
        field = struct.get_field(member) if struct else None
        return self._struct_type_name(field.field_type) if field else None

    def visit_BinaryOp(self, node: BinaryOp):
        """Visit a binary operation."""
        self.visit(node.left)
        self.visit(node.right)
        left, right = self._infer_type(node.left), self._infer_type(node.right)
        if node.operator == "%" and DashType.FLOAT in (left, right):
            self.error("% needs integers; use Int() to convert a Float", node)
        if node.operator in self._BIT_OPS:
            for side in (left, right):
                if side in (DashType.FLOAT, DashType.FIXED, DashType.STRING) or side in self._LIST_TYPES:
                    self.error(f"'{node.operator}' works on integers, not {self._type_text(side)} "
                               f"(Int() converts a Float or a Fixed)", node)
                    break
        if DashType.FIXED in (left, right) and DashType.FLOAT in (left, right):
            self.error("Cannot mix Fixed and Float (convert with Fixed() or Float())", node)
        if node.operator == "+":
            lk, rk = self._list_kind(node.left), self._list_kind(node.right)
            if (lk is None) != (rk is None):
                self.error("A list can only be added to another list", node)
            elif lk and rk and "any" not in (lk, rk) and lk != rk:
                self.error(f"Cannot add a list of {self._kind_text(lk)} to a list of {self._kind_text(rk)}", node)

    _BIT_OPS = ("&", "|", "^", "<<", ">>")
    _LIST_TYPES = (DashType.ARRAY, DashType.ARRAY_INT, DashType.ARRAY_STRING, DashType.DICT)

    @staticmethod
    def _type_text(t: DashType) -> str:
        return {DashType.FLOAT: "Float", DashType.FIXED: "Fixed", DashType.STRING: "Strings"}.get(t, "lists")

    def visit_UnaryOp(self, node: UnaryOp):
        """Visit a unary operation."""
        self.visit(node.operand)
        if node.operator == "~":
            t = self._infer_type(node.operand)
            if t in (DashType.FLOAT, DashType.FIXED, DashType.STRING) or t in self._LIST_TYPES:
                self.error(f"'~' works on integers, not {self._type_text(t)} "
                           f"(Int() converts a Float or a Fixed)", node)

    def visit_Comment(self, node: Comment):
        """Visit a comment (no-op)."""
        pass

    def visit_StringLiteral(self, node: StringLiteral):
        """Visit a string literal."""
        pass

    def visit_NumberLiteral(self, node: NumberLiteral):
        """Visit a number literal."""
        pass

    def visit_BoolLiteral(self, node: BoolLiteral):
        """Visit a boolean literal."""
        pass

    def visit_NilLiteral(self, node: NilLiteral):
        """nil: C NULL."""
        pass

    _LIST_METHODS = {"push": 1, "pop": 0, "insert": 2, "remove": 1, "clear": 0}

    def _dict_get(self, node) -> bool:
        """d.get(k, default) of a dictionary (dashweb D65) becomes d[k] with a default: the node turns into an
        ArrayAccess (its class changed in place), so all that knows d[k] (its type, its ownership, its C) knows
        it too, and the code generator looks the key up once. True if it did."""
        if not (isinstance(node, MethodCall) and node.method == "get" and len(node.arguments) == 2 and
                self._dict_value_of(node.object) is not None):
            return False
        obj, key, default = node.object, node.arguments[0], node.arguments[1]
        node.__class__ = ArrayAccess
        for name in ("object", "method", "arguments"):
            node.__dict__.pop(name, None)
        node.array, node.index, node.default = obj, key, default
        return True

    def visit_MethodCall(self, node: MethodCall):
        """Methods of lists (dashweb D4b): push, pop, insert, remove, clear. Struct methods are
        checked by the code generator as before."""
        if self._dict_get(node):
            self.visit(node)                     # as d[k], with its default
            return
        if self._dict_value_of(node.object) is not None:
            self.visit(node.object)
            for arg in node.arguments:
                self.visit(arg)
            wanted = {"has": 1, "remove": 1, "keys": 0, "clear": 0, "get": 2}.get(node.method)
            if wanted is None:
                self.error(f"Dictionaries have no method '{node.method}' (they have get, has, remove, keys "
                           f"and clear)", node)
            elif len(node.arguments) != wanted:
                self.error(f"{node.method}() on a dictionary takes {wanted} argument(s), "
                           f"got {len(node.arguments)}", node)
            return
        kind = self._list_kind(node.object)
        if kind is None or self._struct_name_of(node.object):
            return
        self.visit(node.object)
        for arg in node.arguments:
            self.visit(arg)
        wanted = self._LIST_METHODS.get(node.method)
        if wanted is None:
            self.error(f"Lists have no method '{node.method}' (they have push, pop, insert, remove "
                       f"and clear)", node)
            return
        if len(node.arguments) != wanted:
            self.error(f"{node.method}() on a list takes {wanted} argument(s), got {len(node.arguments)}", node)
            return
        if node.method in ("push", "insert") and self._is_fixed_list(node.object):
            self._check_fixed_element(node.arguments[-1])
            return
        if node.method in ("push", "insert") and kind not in ("any", "list"):
            value = node.arguments[-1]
            vtype = self._infer_type(value)
            struct = self._struct_name_of(value)
            wrong = ((kind == "int" and (vtype == DashType.STRING or struct))
                     or (kind == "string" and vtype == DashType.INT)
                     or (kind.startswith("struct:") and (vtype in (DashType.INT, DashType.STRING)
                                                         or (struct and struct != kind[7:]))))
            if wrong:
                self.error(f"Cannot {node.method} that into a list of {self._kind_text(kind)}", node)

    def generic_visit(self, node: ASTNode):
        """Default visitor - just traverse children if possible."""
        pass

    # === Helper Methods ===

    def _infer_type(self, node: ASTNode) -> DashType:
        """Infer the type of an expression."""
        self._dict_get(node)                     # d.get(k, default) is d[k] (D65)
        if isinstance(node, StringLiteral):
            return DashType.STRING
        elif isinstance(node, NumberLiteral):
            return DashType.INT
        elif isinstance(node, FloatLiteral):
            return DashType.FLOAT
        elif isinstance(node, BinaryOp):
            left, right = self._infer_type(node.left), self._infer_type(node.right)
            if node.operator == "+" and DashType.STRING in (left, right):
                return DashType.STRING
            if node.operator == "+" and self._list_kind(node.left) is not None:
                kind = self._list_kind(node)
                return {"int": DashType.ARRAY_INT, "string": DashType.ARRAY_STRING}.get(kind, DashType.ARRAY)
            if node.operator in ("&", "|", "^", "<<", ">>"):
                return DashType.INT
            if node.operator in ("+", "-", "*", "/", "%"):
                if DashType.FLOAT in (left, right):
                    return DashType.FLOAT
                if DashType.FIXED in (left, right):
                    return DashType.FIXED
                if left == right == DashType.INT:
                    return DashType.INT
            return DashType.UNKNOWN
        elif isinstance(node, UnaryOp) and node.operator == "-":
            return self._infer_type(node.operand)
        elif isinstance(node, UnaryOp) and node.operator == "~":
            return DashType.INT
        elif isinstance(node, FunctionCall) and node.name in ("Int", "Float"):
            return DashType.FLOAT if node.name == "Float" else DashType.INT
        elif isinstance(node, FunctionCall) and node.name in ("Fixed", "fx_sqrt", "fx_sin", "fx_cos"):
            return DashType.FIXED
        elif isinstance(node, FunctionCall) and self.program and self.program.get_function(node.name):
            func = self.program.get_function(node.name)
            if func.return_type in ("Int", "Float", "Fixed", "String", "Bool") or \
                    list_elem_type(func.return_type) is not None or dict_value_type(func.return_type) is not None:
                return self._type_annotation_to_dash_type(func.return_type)
        elif isinstance(node, FunctionCall) and get_builtin(node.name) and get_builtin(node.name).list_of:
            return self._type_annotation_to_dash_type(f"[{get_builtin(node.name).list_of}]")
        elif isinstance(node, BoolLiteral):
            return DashType.BOOL
        elif isinstance(node, VarRef):
            symbol = self.lookup_symbol(node.name)
            if symbol and symbol.symbol_type == SymbolType.FUNCTION:
                return DashType.FUNC             # g = doble: the function as a value
            if symbol:
                return symbol.dash_type
        elif isinstance(node, ArrayLiteral):
            if node.elements:
                elem_type = self._infer_type(node.elements[0])
                if elem_type == DashType.INT:
                    return DashType.ARRAY_INT
                elif elem_type == DashType.STRING:
                    return DashType.ARRAY_STRING
            return DashType.ARRAY
        elif isinstance(node, DictLiteral):
            return DashType.DICT
        elif isinstance(node, ArrayAccess) and self._is_fixed_list(node.array):
            return DashType.FIXED
        elif isinstance(node, ArrayAccess) and self._dict_value_of(node.array) is not None:
            value = self._dict_value_of(node.array)
            return {"Int": DashType.INT, "String": DashType.STRING, "Bool": DashType.BOOL}.get(value, DashType.UNKNOWN)
        elif isinstance(node, ArrayAccess):
            # Access returns the element type: a list of Strings gives Strings, a
            # list of structs a struct, a String a character, anything else an Int
            if isinstance(node.array, VarRef):
                symbol = self.lookup_symbol(node.array.name)
                if symbol and symbol.dash_type == DashType.ARRAY_STRING:
                    return DashType.STRING
                if symbol and (symbol.elem_struct or symbol.dash_type == DashType.STRING):
                    return DashType.UNKNOWN
            elem = list_elem_type(self._declared_list_type(node.array))
            if list_elem_type(elem) is not None:   # an element of a list of lists (D49)
                return self._type_annotation_to_dash_type(elem)
            if elem == "String":
                return DashType.STRING
            if elem is not None and elem != "Int":
                return DashType.UNKNOWN
            return DashType.INT
        elif isinstance(node, PropertyAccess) and node.property == "length":
            return DashType.INT
        elif isinstance(node, (PropertyAccess, MemberAccess)):
            # a struct field: its declared type (Int, Float, Fixed, String, Bool)
            if isinstance(node, MemberAccess):
                owner, member = self._struct_name_of(VarRef(name=node.object_name)), node.member
            else:
                owner, member = self._struct_name_of(node.object), node.property
            struct = self.program.get_struct(owner) if (owner and self.program) else None
            field = struct.get_field(member) if struct else None
            if field and field.field_type in ("Int", "Float", "Fixed", "String", "Bool"):
                return self._type_annotation_to_dash_type(field.field_type)
        elif isinstance(node, (LambdaFunc, FunctionRef)):
            return DashType.FUNC
        elif isinstance(node, (MethodCall, FunctionCall)) and (
                list_elem_type(self._call_type(node)) is not None or dict_value_type(self._call_type(node)) is not None):
            return self._type_annotation_to_dash_type(self._call_type(node))   # a list or dictionary (D49)
        elif isinstance(node, MethodCall) and node.method == "pop":
            if self._is_fixed_list(node.object):
                return DashType.FIXED
            kind = self._list_kind(node.object)
            if kind == "string":
                return DashType.STRING
            if kind == "int":
                return DashType.INT
        return DashType.UNKNOWN

    def _returns_value(self, func: FunctionDef) -> bool:
        """True if the function can return a value."""
        if func.return_type:
            return func.return_type != "Void"

        def search(stmts):
            for stmt in stmts:
                if isinstance(stmt, ReturnStmt) and stmt.value is not None:
                    return True
                for attr in ("then_body", "else_body", "body"):
                    nested = getattr(stmt, attr, None)
                    if isinstance(nested, list) and search(nested):
                        return True
            return False

        return search(func.body)

    _TYPE_NAMES = {"Int", "Float", "Fixed", "String", "Bool", "Pointer", "Void", "Func", "Array"}
    _NO_NIL = (DashType.INT, DashType.FLOAT, DashType.FIXED, DashType.BOOL)

    def _check_type_names(self, program: Program):
        """Every type annotation names a type: an unknown name used to compile as
        Int silently (an Array field then kept its lists until exit)."""
        known = self._TYPE_NAMES | {s.name for s in program.structs} | {e.name for e in program.enums}

        def check(type_name, where):
            if type_name and not type_is_known(type_name, known):
                self.error(f"Unknown type '{type_name}' ({where}); types are "
                           f"{', '.join(sorted(self._TYPE_NAMES))}, or a struct or enum name", where_node)

        def params(node, what):
            for p in node.params:
                if not isinstance(p, str):
                    check(p.param_type, f"parameter '{p.name}' of {what}")

        for where_node in program.global_vars:
            check(where_node.var_type, f"global '{where_node.name}'")
        for where_node in list(program.functions) + list(program.native_funcs) + list(program.extern_funcs):
            params(where_node, f"'{where_node.name}'")
            check(where_node.return_type, f"return of '{where_node.name}'")
        for struct in program.structs:
            for where_node in struct.fields:
                check(where_node.field_type, f"field '{where_node.name}' of '{struct.name}'")
                t = where_node.field_type
                if where_node.weak and not (program.get_struct(t) or list_elem_type(t) is not None
                                            or dict_value_type(t) is not None or t == "Array"):
                    self.error(f"weak is for fields that hold a struct, a list or a dictionary "
                               f"('{where_node.name}' of '{struct.name}' is {t})", where_node)
            for where_node in struct.methods:
                params(where_node, f"'{struct.name}.{where_node.name}'")
                check(where_node.return_type, f"return of '{struct.name}.{where_node.name}'")

    def _type_annotation_to_dash_type(self, type_name: Optional[str]) -> DashType:
        """Convert a type annotation string to a DashType."""
        if not type_name:
            return DashType.UNKNOWN
        if dict_value_type(type_name) is not None:
            return DashType.DICT
        elem = list_elem_type(type_name)
        if elem is not None:
            return {"Int": DashType.ARRAY_INT, "String": DashType.ARRAY_STRING}.get(elem, DashType.ARRAY)
        type_map = {
            "Int": DashType.INT,
            "Float": DashType.FLOAT,
            "Fixed": DashType.FIXED,
            "String": DashType.STRING,
            "Bool": DashType.BOOL,
            "Pointer": DashType.UNKNOWN,
            "Void": DashType.VOID,
            "Func": DashType.FUNC,
            "Array": DashType.ARRAY_INT,
        }
        return type_map.get(type_name, DashType.UNKNOWN)


def analyze(program: Program) -> AnalysisResult:
    """Convenience function to analyze a program."""
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(program)
