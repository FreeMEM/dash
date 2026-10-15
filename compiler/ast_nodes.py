"""
Dash Language AST Node Definitions
Provides a clean, typed representation of the program structure.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Union, Any
from enum import Enum, auto


class NodeType(Enum):
    """Types of AST nodes for visitor pattern."""
    PROGRAM = auto()
    WINDOW_DEF = auto()
    MAIN_BLOCK = auto()
    EVENT_LOOP = auto()
    ON_CLOSE = auto()
    ON_KEY = auto()
    WINDOW_OPEN = auto()
    PRINT = auto()
    WAIT = auto()
    STOP = auto()
    COMMENT = auto()
    # Future nodes
    IF_STMT = auto()
    WHILE_STMT = auto()
    FOR_STMT = auto()
    VAR_DECL = auto()
    VAR_ASSIGN = auto()
    VAR_REF = auto()
    BINARY_OP = auto()
    UNARY_OP = auto()
    LITERAL = auto()
    FUNCTION_DEF = auto()
    FUNCTION_CALL = auto()
    RETURN_STMT = auto()
    ARRAY_LITERAL = auto()
    ARRAY_ACCESS = auto()
    ARRAY_ASSIGN = auto()
    PROPERTY_ACCESS = auto()


@dataclass
class SourceLocation:
    """Tracks source code location for error reporting."""
    line: int
    column: int
    filename: str = ""

    def __str__(self):
        if self.filename:
            return f"{self.filename}:{self.line}:{self.column}"
        return f"line {self.line}, column {self.column}"


@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    # Note: location must be defined in subclasses with default=None
    # to avoid dataclass inheritance issues

    def accept(self, visitor):
        """Visitor pattern support."""
        method_name = f"visit_{self.__class__.__name__}"
        visitor_method = getattr(visitor, method_name, visitor.generic_visit)
        return visitor_method(self)


# === Literal Values ===

@dataclass
class StringLiteral(ASTNode):
    """String literal value."""
    value: str  # Already includes quotes from parser
    location: Optional[SourceLocation] = None

    @property
    def unquoted(self) -> str:
        """Returns the string without surrounding quotes."""
        if self.value.startswith('"') and self.value.endswith('"'):
            return self.value[1:-1]
        return self.value


@dataclass
class NumberLiteral(ASTNode):
    """Numeric literal value."""
    value: int
    location: Optional[SourceLocation] = None

    @classmethod
    def from_string(cls, s: str, location=None):
        return cls(value=int(s), location=location)


@dataclass
class NilLiteral(ASTNode):
    """nil: no struct, list or String (C NULL)."""
    location: Optional[SourceLocation] = None


@dataclass
class BoolLiteral(ASTNode):
    """Boolean literal value."""
    value: bool
    location: Optional[SourceLocation] = None


# === Window Definition ===

@dataclass
class WindowProperty(ASTNode):
    """A single window property (e.g., title "Hello")."""
    name: str
    value: Union[StringLiteral, NumberLiteral]
    location: Optional[SourceLocation] = None


@dataclass
class WindowDef(ASTNode):
    """Window definition block."""

    # Property name -> kind of value it takes
    PROPERTY_KINDS = {
        "title": "string",
        "width": "int", "height": "int", "left": "int", "top": "int",
        "closegadget": "bool", "dragbar": "bool", "depthgadget": "bool",
        "sizegadget": "bool", "borderless": "bool", "activate": "bool",
    }

    name: str
    properties: List[WindowProperty] = field(default_factory=list)
    location: Optional[SourceLocation] = None

    def get_property(self, name: str, default=None):
        """Get a property value by name."""
        for prop in self.properties:
            if prop.name == name:
                return prop.value
        return default

    @property
    def title(self) -> str:
        prop = self.get_property("title")
        if prop and isinstance(prop, StringLiteral):
            return prop.value
        return '"Dash Window"'

    @property
    def width(self) -> int:
        prop = self.get_property("width")
        if prop and isinstance(prop, NumberLiteral):
            return prop.value
        return 320

    @property
    def height(self) -> int:
        prop = self.get_property("height")
        if prop and isinstance(prop, NumberLiteral):
            return prop.value
        return 200


# === Instructions ===

@dataclass
class PrintStmt(ASTNode):
    """Print command."""
    message: ASTNode  # Can be StringLiteral, VarRef, or any expression
    location: Optional[SourceLocation] = None


@dataclass
class WaitStmt(ASTNode):
    """Wait command (in seconds)."""
    seconds: NumberLiteral
    location: Optional[SourceLocation] = None


@dataclass
class StopStmt(ASTNode):
    """Stop command to exit event loop."""
    location: Optional[SourceLocation] = None


@dataclass
class BreakStmt(ASTNode):
    """break: leave the innermost while/for loop."""
    location: Optional[SourceLocation] = None


@dataclass
class ContinueStmt(ASTNode):
    """continue: jump to the next iteration of the innermost while/for loop."""
    location: Optional[SourceLocation] = None


@dataclass
class WindowOpen(ASTNode):
    """Window.open command."""
    window_name: str
    location: Optional[SourceLocation] = None


@dataclass
class WindowClose(ASTNode):
    """Window.close command."""
    window_name: str
    location: Optional[SourceLocation] = None


@dataclass
class Comment(ASTNode):
    """Comment line (preserved for documentation)."""
    text: str
    location: Optional[SourceLocation] = None


# === Event Handlers ===

@dataclass
class OnCloseHandler(ASTNode):
    """Handler for window close event."""
    body: List[ASTNode] = field(default_factory=list)
    location: Optional[SourceLocation] = None


@dataclass
class OnMenuHandler(ASTNode):
    """On Menu: an item of the menu_title/menu_item menus was chosen (menu_id() tells which)."""
    body: List[ASTNode] = field(default_factory=list)
    location: Optional[SourceLocation] = None


@dataclass
class OnGadgetHandler(ASTNode):
    """On Gadget: a gadget made with button_create/slider_create... was used
    (gadget_id() tells which)."""
    body: List[ASTNode] = field(default_factory=list)
    location: Optional[SourceLocation] = None


@dataclass
class OnKeyHandler(ASTNode):
    """On Key handler: any key (key None), one character ('"a"'), a key name
    ('"ESC"', see KEY_NAMES) or a raw key code (int)."""
    key: Optional[Union[str, int]] = None
    body: List[ASTNode] = field(default_factory=list)
    location: Optional[SourceLocation] = None


# On Key "NAME": Amiga raw key codes (the same on every keymap)
KEY_NAMES = {
    "SPACE": 0x40, "BACKSPACE": 0x41, "TAB": 0x42, "ENTER": 0x43, "RETURN": 0x44,
    "ESC": 0x45, "DEL": 0x46, "HELP": 0x5F,
    "UP": 0x4C, "DOWN": 0x4D, "RIGHT": 0x4E, "LEFT": 0x4F,
    **{f"F{n}": 0x4F + n for n in range(1, 11)},
}


@dataclass
class EventLoop(ASTNode):
    """Event loop block."""
    handlers: List[Union[OnCloseHandler, OnKeyHandler]] = field(default_factory=list)
    location: Optional[SourceLocation] = None

    def get_handler(self, handler_type):
        """Get a specific handler by type."""
        for handler in self.handlers:
            if isinstance(handler, handler_type):
                return handler
        return None


# === Control Flow (Future) ===

@dataclass
class IfStmt(ASTNode):
    """If statement (future)."""
    condition: ASTNode
    then_body: List[ASTNode] = field(default_factory=list)
    else_body: List[ASTNode] = field(default_factory=list)
    location: Optional[SourceLocation] = None


@dataclass
class WhileStmt(ASTNode):
    """While loop (future)."""
    condition: ASTNode
    body: List[ASTNode] = field(default_factory=list)
    location: Optional[SourceLocation] = None


@dataclass
class ForRangeStmt(ASTNode):
    """For loop over a range: for i in (start..end) or (start..end step n)."""
    variable: str
    start: ASTNode  # Start expression
    end: ASTNode    # End expression
    body: List[ASTNode] = field(default_factory=list)
    location: Optional[SourceLocation] = None
    step: Optional[ASTNode] = None  # None: 1, or -1 when both limits are constants and start > end


@dataclass
class ForEachStmt(ASTNode):
    """For loop over an array: for item in array."""
    variable: str
    iterable: ASTNode  # Array to iterate over
    body: List[ASTNode] = field(default_factory=list)
    location: Optional[SourceLocation] = None


# Keep ForStmt as alias for backwards compatibility
ForStmt = ForRangeStmt


# === Variables (Future) ===

@dataclass
class VarDecl(ASTNode):
    """Variable declaration (future)."""
    name: str
    var_type: Optional[str] = None
    initial_value: Optional[ASTNode] = None
    location: Optional[SourceLocation] = None


@dataclass
class VarAssign(ASTNode):
    """Variable assignment (future)."""
    name: str
    value: ASTNode
    location: Optional[SourceLocation] = None


@dataclass
class VarRef(ASTNode):
    """Variable reference (future)."""
    name: str
    location: Optional[SourceLocation] = None


# === Expressions (Future) ===

@dataclass
class BinaryOp(ASTNode):
    """Binary operation (future)."""
    left: ASTNode
    operator: str
    right: ASTNode
    location: Optional[SourceLocation] = None


@dataclass
class FloatLiteral(ASTNode):
    """Float literal: 1.5, 2.0e3 (C float: 32-bit, software floating point on 68000)."""
    value: float
    location: Optional[SourceLocation] = None


@dataclass
class UnaryOp(ASTNode):
    """Unary operation (future)."""
    operator: str
    operand: ASTNode
    location: Optional[SourceLocation] = None


# === Functions ===

@dataclass
class FunctionDef(ASTNode):
    """Function definition."""
    name: str
    params: List[Union[str, 'FunctionParam']] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)
    return_type: Optional[str] = None
    location: Optional[SourceLocation] = None

    def get_param_names(self) -> List[str]:
        """Get list of parameter names."""
        names = []
        for p in self.params:
            if isinstance(p, str):
                names.append(p)
            else:
                names.append(p.name)
        return names


@dataclass
class FunctionCall(ASTNode):
    """Function call."""
    name: str
    arguments: List[ASTNode] = field(default_factory=list)
    location: Optional[SourceLocation] = None
    is_statement: bool = False  # Called for its effect; the result is discarded


@dataclass
class DictLiteral(ASTNode):
    """{"clave": valor, ...} (dashweb D5)."""
    keys: List[ASTNode] = field(default_factory=list)
    values: List[ASTNode] = field(default_factory=list)
    location: Optional[SourceLocation] = None


@dataclass
class MethodCall(ASTNode):
    """Method call on an object (player.move(5, 0))."""
    object: ASTNode  # The object on which method is called
    method: str  # Method name
    arguments: List[ASTNode] = field(default_factory=list)
    location: Optional[SourceLocation] = None


@dataclass
class LambdaFunc(ASTNode):
    """Lambda/anonymous function expression."""
    params: List[Union[str, 'FunctionParam']] = field(default_factory=list)
    body: Union[ASTNode, List[ASTNode]] = field(default_factory=list)
    is_expression: bool = False  # True if body is a single expression
    location: Optional[SourceLocation] = None


@dataclass
class FunctionRef(ASTNode):
    """Reference to a named function (for passing as value)."""
    name: str
    location: Optional[SourceLocation] = None


@dataclass
class ReturnStmt(ASTNode):
    """Return statement."""
    value: Optional[ASTNode] = None  # None means return without value
    location: Optional[SourceLocation] = None


# === Arrays ===

@dataclass
class ArrayLiteral(ASTNode):
    """Array literal like [1, 2, 3]."""
    elements: List[ASTNode] = field(default_factory=list)
    location: Optional[SourceLocation] = None


@dataclass
class ArrayAccess(ASTNode):
    """Array element access like arr[i]."""
    array: ASTNode  # The array being accessed (usually VarRef)
    index: ASTNode  # The index expression
    location: Optional[SourceLocation] = None


@dataclass
class ArrayAssign(ASTNode):
    """Array element assignment like arr[i] = value."""
    array: ASTNode  # The array being modified
    index: ASTNode  # The index expression
    value: ASTNode  # The value to assign
    location: Optional[SourceLocation] = None


@dataclass
class ArraySlice(ASTNode):
    """Array slicing like arr[start:end]."""
    array: ASTNode  # The array being sliced
    start: Optional[ASTNode]  # Start index (None means from beginning)
    end: Optional[ASTNode]  # End index (None means to end)
    location: Optional[SourceLocation] = None


@dataclass
class PropertyAccess(ASTNode):
    """Property access like arr.length."""
    object: ASTNode  # The object being accessed
    property: str    # The property name
    location: Optional[SourceLocation] = None


# === Structs ===

@dataclass
class StructField(ASTNode):
    """A field in a struct definition."""
    name: str
    field_type: str  # "Int", "String", "Bool"
    default_value: Optional[ASTNode] = None
    location: Optional[SourceLocation] = None


@dataclass
class StructMethod(ASTNode):
    """A method in a struct definition."""
    name: str
    params: List[Union[str, 'FunctionParam']] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)
    return_type: Optional[str] = None
    location: Optional[SourceLocation] = None


@dataclass
class SelfRef(ASTNode):
    """Reference to 'self' in a struct method."""
    location: Optional[SourceLocation] = None


@dataclass
class StructDef(ASTNode):
    """Struct definition with optional methods."""
    name: str
    fields: List['StructField'] = field(default_factory=list)
    methods: List['StructMethod'] = field(default_factory=list)
    location: Optional[SourceLocation] = None

    def get_field(self, name: str) -> Optional['StructField']:
        """Get a field by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def get_method(self, name: str) -> Optional['StructMethod']:
        """Get a method by name."""
        for m in self.methods:
            if m.name == name:
                return m
        return None


@dataclass
class MemberAccess(ASTNode):
    """Member access like player.x or arr.length."""
    object_name: str  # The object/variable name
    member: str       # The member/property name
    location: Optional[SourceLocation] = None


@dataclass
class MemberAssign(ASTNode):
    """Member assignment like player.x = 10 or a.b.c = 10."""
    object_name: str  # The object being modified (root variable, or "self")
    member: str       # The member name
    value: ASTNode    # The value to assign
    location: Optional[SourceLocation] = None
    # Expression of the struct that owns 'member' when the chain is longer
    # than one step (a.b.c = x: target is a.b); None for player.x = 10
    target: Optional[ASTNode] = None


# === Enums ===

@dataclass
class EnumValue(ASTNode):
    """A value in an enum definition."""
    name: str
    value: Optional[int] = None  # Explicit value or None for auto
    location: Optional[SourceLocation] = None


@dataclass
class EnumDef(ASTNode):
    """Enum definition."""
    name: str
    values: List['EnumValue'] = field(default_factory=list)
    location: Optional[SourceLocation] = None

    def get_value(self, name: str) -> Optional['EnumValue']:
        """Get an enum value by name."""
        for v in self.values:
            if v.name == name:
                return v
        return None

    def get_numeric_value(self, name: str) -> Optional[int]:
        """Get the numeric value of an enum constant."""
        current = 0
        for v in self.values:
            if v.value is not None:
                current = v.value
            if v.name == name:
                return current
            current += 1
        return None


# === FFI ===

@dataclass
class FunctionParam(ASTNode):
    """Function parameter with optional type."""
    name: str
    param_type: Optional[str] = None  # None means inferred
    location: Optional[SourceLocation] = None


@dataclass
class ExternFunc(ASTNode):
    """External function declaration for FFI."""
    library: str  # e.g., "graphics.library"
    name: str
    params: List['FunctionParam'] = field(default_factory=list)
    return_type: Optional[str] = None
    location: Optional[SourceLocation] = None


@dataclass
class NativeFunc(ASTNode):
    """Function with inline C code body."""
    name: str
    params: List['FunctionParam'] = field(default_factory=list)
    return_type: Optional[str] = None
    c_code: str = ""  # Raw C code
    location: Optional[SourceLocation] = None


# === Program Structure ===

@dataclass
class ImportStmt(ASTNode):
    """Import statement for loading other modules."""
    path: str  # Path to the module file (without quotes)
    location: Optional[SourceLocation] = None


@dataclass
class ConstDecl(ASTNode):
    """Constant declaration (const NAME = value)."""
    name: str
    value: Union[NumberLiteral, StringLiteral, BoolLiteral]
    location: Optional[SourceLocation] = None


@dataclass
class GlobalVarDecl(ASTNode):
    """Global variable declaration (var NAME: TYPE = value)."""
    name: str
    var_type: str
    initial_value: Optional[ASTNode] = None
    location: Optional[SourceLocation] = None


@dataclass
class MainBlock(ASTNode):
    """Main block containing program instructions."""
    body: List[ASTNode] = field(default_factory=list)
    location: Optional[SourceLocation] = None


@dataclass
class Program(ASTNode):
    """Root node representing the entire program."""
    imports: List[ImportStmt] = field(default_factory=list)
    constants: List['ConstDecl'] = field(default_factory=list)
    global_vars: List['GlobalVarDecl'] = field(default_factory=list)
    structs: List[StructDef] = field(default_factory=list)
    enums: List['EnumDef'] = field(default_factory=list)
    windows: List[WindowDef] = field(default_factory=list)
    main: Optional[MainBlock] = None
    functions: List[FunctionDef] = field(default_factory=list)
    extern_funcs: List['ExternFunc'] = field(default_factory=list)
    native_funcs: List['NativeFunc'] = field(default_factory=list)
    headers: List[str] = field(default_factory=list)
    extra_mains: List[MainBlock] = field(default_factory=list)  # Duplicate Main blocks (an error)
    location: Optional[SourceLocation] = None

    def get_window(self, name: str) -> Optional[WindowDef]:
        """Get a window definition by name."""
        for window in self.windows:
            if window.name == name:
                return window
        return None

    def get_function(self, name: str) -> Optional[FunctionDef]:
        """Get a function definition by name."""
        for func in self.functions:
            if func.name == name:
                return func
        return None

    def get_struct(self, name: str) -> Optional[StructDef]:
        """Get a struct definition by name."""
        for struct in self.structs:
            if struct.name == name:
                return struct
        return None

    def get_enum(self, name: str) -> Optional['EnumDef']:
        """Get an enum definition by name."""
        for enum in self.enums:
            if enum.name == name:
                return enum
        return None

    def get_extern_func(self, name: str) -> Optional['ExternFunc']:
        """Get an extern function by name."""
        for ef in self.extern_funcs:
            if ef.name == name:
                return ef
        return None

    def get_constant(self, name: str) -> Optional['ConstDecl']:
        """Get a constant by name."""
        for const in self.constants:
            if const.name == name:
                return const
        return None


# === Visitor Pattern Base ===

class ASTVisitor:
    """Base class for AST visitors."""

    def visit(self, node: ASTNode):
        """Visit a node."""
        return node.accept(self)

    def generic_visit(self, node: ASTNode):
        """Default visitor for unhandled nodes."""
        raise NotImplementedError(f"No visitor for {node.__class__.__name__}")

    def visit_children(self, nodes: List[ASTNode]):
        """Visit a list of child nodes."""
        results = []
        for node in nodes:
            if isinstance(node, ASTNode):
                results.append(self.visit(node))
        return results


def constant_int(node: Optional[ASTNode], program: Optional['Program'] = None) -> Optional[int]:
    """Integer value of a node known at compile time: a number literal, its
    negation, or an integer const. None when it is only known at run time."""
    if isinstance(node, NumberLiteral):
        return node.value
    if isinstance(node, UnaryOp) and node.operator == "-":
        inner = constant_int(node.operand, program)
        return -inner if inner is not None else None
    if isinstance(node, VarRef) and program is not None:
        const = program.get_constant(node.name)
        if const is not None and isinstance(const.value, NumberLiteral):
            return const.value.value
    return None
