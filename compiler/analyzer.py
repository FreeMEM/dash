"""
Dash Language Semantic Analyzer
Performs semantic analysis, builds symbol table, and validates the AST.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from enum import Enum, auto

from compiler.ast_nodes import (
    ASTNode, ASTVisitor, Program, WindowDef, MainBlock, EventLoop,
    OnCloseHandler, OnKeyHandler, WindowOpen, PrintStmt, WaitStmt,
    StopStmt, Comment, IfStmt, WhileStmt, ForRangeStmt, ForEachStmt,
    VarDecl, VarAssign, VarRef, FunctionDef, FunctionCall, ReturnStmt,
    BinaryOp, UnaryOp, StringLiteral, NumberLiteral, BoolLiteral,
    ArrayLiteral, ArrayAccess, ArrayAssign, PropertyAccess,
    StructDef, StructField, MemberAccess, MemberAssign,
    EnumDef, EnumValue, FunctionParam, ExternFunc, NativeFunc, ConstDecl
)
from compiler.amiga_builtins import is_builtin, get_builtin


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
    STRING = auto()
    BOOL = auto()
    VOID = auto()
    WINDOW = auto()
    ARRAY_INT = auto()
    ARRAY_STRING = auto()
    ARRAY = auto()  # Generic array when type unknown
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

    def __str__(self):
        prefix = "Warning" if self.is_warning else "Error"
        location = ""
        if self.node and self.node.location:
            location = f" at {self.node.location}"
        return f"{prefix}{location}: {self.message}"


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
        self.current_window: Optional[str] = None

    def analyze(self, program: Program) -> AnalysisResult:
        """Perform semantic analysis on the program."""
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
        """Look up a symbol in the current scope chain."""
        return self.current_scope.lookup(name)

    # === Visitor Methods ===

    def visit_Program(self, node: Program):
        """Visit the program node."""
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
                is_initialized=(gvar.initial_value is not None)
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

        # Fourth pass: analyze main block
        if node.main:
            self.visit(node.main)
        else:
            self.warning("Program has no Main block")

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
        has_stop = False
        for stmt in node.body:
            self.visit(stmt)
            if isinstance(stmt, StopStmt):
                has_stop = True
        if not has_stop:
            self.warning("On Close handler has no Stop command", node)
        self.exit_scope()

    def visit_OnKeyHandler(self, node: OnKeyHandler):
        """Visit an On Key handler."""
        self.enter_scope("on_key")
        for stmt in node.body:
            self.visit(stmt)
        self.exit_scope()

    def visit_PrintStmt(self, node: PrintStmt):
        """Visit a print statement."""
        pass  # Always valid with a string

    def visit_WaitStmt(self, node: WaitStmt):
        """Visit a wait statement."""
        if isinstance(node.seconds, NumberLiteral) and node.seconds.value < 0:
            self.error("Wait time cannot be negative", node)

    def visit_StopStmt(self, node: StopStmt):
        """Visit a stop statement."""
        if not self.in_event_loop:
            self.warning("Stop used outside of EventLoop has no effect", node)

    def visit_VarDecl(self, node: VarDecl):
        """Visit a variable declaration."""
        # Analyze initial value first
        if node.initial_value:
            self.visit(node.initial_value)

        symbol = Symbol(
            name=node.name,
            symbol_type=SymbolType.VARIABLE,
            dash_type=self._infer_type(node.initial_value) if node.initial_value else DashType.UNKNOWN,
            node=node,
            is_initialized=node.initial_value is not None
        )
        self.define_symbol(symbol, node)

    def visit_VarAssign(self, node: VarAssign):
        """Visit a variable assignment (Python style - first use declares)."""
        # First, analyze the value expression
        self.visit(node.value)

        # Check if variable already exists
        symbol = self.lookup_symbol(node.name)
        if not symbol:
            # First assignment - declare the variable
            symbol = Symbol(
                name=node.name,
                symbol_type=SymbolType.VARIABLE,
                dash_type=self._infer_type(node.value),
                node=node,
                is_initialized=True
            )
            self.define_symbol(symbol, node)
        elif symbol.symbol_type != SymbolType.VARIABLE:
            self.error(f"Cannot assign to '{node.name}' - it's not a variable", node)
        else:
            symbol.is_initialized = True

    def visit_VarRef(self, node: VarRef):
        """Visit a variable reference."""
        symbol = self.lookup_symbol(node.name)
        if not symbol:
            self.error(f"Variable '{node.name}' is not defined", node)
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
        for stmt in node.body:
            self.visit(stmt)
        self.exit_scope()

    def visit_ForRangeStmt(self, node: ForRangeStmt):
        """Visit a for-range statement."""
        # Visit range expressions
        self.visit(node.start)
        self.visit(node.end)

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

        for stmt in node.body:
            self.visit(stmt)
        self.exit_scope()

    def visit_ForEachStmt(self, node: ForEachStmt):
        """Visit a for-each statement."""
        # Visit the iterable
        self.visit(node.iterable)

        self.enter_scope("for_each")
        # Define loop variable (element type)
        symbol = Symbol(
            name=node.variable,
            symbol_type=SymbolType.VARIABLE,
            dash_type=DashType.INT,  # Assume array of ints for now
            node=node,
            is_initialized=True
        )
        self.define_symbol(symbol, node)

        for stmt in node.body:
            self.visit(stmt)
        self.exit_scope()

    def visit_FunctionDef(self, node: FunctionDef):
        """Visit a function definition."""
        self.in_function = True
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
                is_initialized=True
            )
            self.define_symbol(symbol, node)

        for stmt in node.body:
            self.visit(stmt)

        self.exit_scope()
        self.in_function = False

    def visit_FunctionCall(self, node: FunctionCall):
        """Visit a function call."""
        # Check if it's a builtin function
        builtin = get_builtin(node.name)
        if builtin:
            # Validate argument count for builtin
            expected = len(builtin.params)
            actual = len(node.arguments)
            if expected != actual:
                self.error(f"Builtin '{node.name}' expects {expected} arguments, got {actual}", node)
            for arg in node.arguments:
                self.visit(arg)
            return

        symbol = self.lookup_symbol(node.name)
        if not symbol:
            self.error(f"Function '{node.name}' is not defined", node)
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

        for arg in node.arguments:
            self.visit(arg)

    def visit_ReturnStmt(self, node: ReturnStmt):
        """Visit a return statement."""
        if not self.in_function:
            self.error("'return' outside of function", node)
        if node.value:
            self.visit(node.value)

    def visit_ArrayLiteral(self, node: ArrayLiteral):
        """Visit an array literal."""
        for element in node.elements:
            self.visit(element)

    def visit_ArrayAccess(self, node: ArrayAccess):
        """Visit an array access."""
        self.visit(node.array)
        self.visit(node.index)

    def visit_ArrayAssign(self, node: ArrayAssign):
        """Visit an array assignment."""
        self.visit(node.array)
        self.visit(node.index)
        self.visit(node.value)

    def visit_PropertyAccess(self, node: PropertyAccess):
        """Visit a property access."""
        self.visit(node.object)
        # For now, only .length is supported
        if node.property != "length":
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
            self.error(f"Variable '{node.object_name}' is not defined", node)
            return

        # For array.length, allow it
        if node.member == "length":
            return

        # For struct members, validate the member exists
        # We need to track the type of the variable to know if it's a struct
        # For now, we'll allow any member access and let codegen handle it

    def visit_MemberAssign(self, node: MemberAssign):
        """Visit a member assignment (player.x = 10)."""
        # Check if the object variable exists
        symbol = self.lookup_symbol(node.object_name)
        if not symbol:
            self.error(f"Variable '{node.object_name}' is not defined", node)
            return

        # Visit the value being assigned
        self.visit(node.value)

    def visit_BinaryOp(self, node: BinaryOp):
        """Visit a binary operation."""
        self.visit(node.left)
        self.visit(node.right)

    def visit_UnaryOp(self, node: UnaryOp):
        """Visit a unary operation."""
        self.visit(node.operand)

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

    def generic_visit(self, node: ASTNode):
        """Default visitor - just traverse children if possible."""
        pass

    # === Helper Methods ===

    def _infer_type(self, node: ASTNode) -> DashType:
        """Infer the type of an expression."""
        if isinstance(node, StringLiteral):
            return DashType.STRING
        elif isinstance(node, NumberLiteral):
            return DashType.INT
        elif isinstance(node, BoolLiteral):
            return DashType.BOOL
        elif isinstance(node, VarRef):
            symbol = self.lookup_symbol(node.name)
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
        elif isinstance(node, ArrayAccess):
            # Access returns the element type
            return DashType.INT  # For now assume int arrays
        elif isinstance(node, PropertyAccess):
            if node.property == "length":
                return DashType.INT
        return DashType.UNKNOWN

    def _type_annotation_to_dash_type(self, type_name: Optional[str]) -> DashType:
        """Convert a type annotation string to a DashType."""
        if not type_name:
            return DashType.UNKNOWN
        type_map = {
            "Int": DashType.INT,
            "String": DashType.STRING,
            "Bool": DashType.BOOL,
            "Pointer": DashType.UNKNOWN,
            "Void": DashType.VOID,
        }
        return type_map.get(type_name, DashType.UNKNOWN)


def analyze(program: Program) -> AnalysisResult:
    """Convenience function to analyze a program."""
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(program)
