"""
Dash Language Parser/Transformer
Converts Lark parse tree to Dash AST nodes.
"""
from lark import Transformer, Token, Tree
from typing import List, Any, Optional

from compiler.ast_nodes import (
    Program, WindowDef, WindowProperty, MainBlock, EventLoop,
    OnCloseHandler, OnKeyHandler, WindowOpen, PrintStmt, WaitStmt,
    StopStmt, Comment, IfStmt, WhileStmt, ForRangeStmt, ForEachStmt,
    VarDecl, VarAssign, VarRef, FunctionDef, FunctionCall, MethodCall,
    ReturnStmt, BinaryOp, UnaryOp, StringLiteral, NumberLiteral, BoolLiteral,
    SourceLocation, ArrayLiteral, ArrayAccess, ArrayAssign, ArraySlice,
    PropertyAccess, ImportStmt, ConstDecl, GlobalVarDecl, StructDef, StructField, StructMethod,
    SelfRef, MemberAccess, MemberAssign, EnumDef, EnumValue, FunctionParam,
    ExternFunc, NativeFunc, LambdaFunc, FunctionRef
)


class DashASTBuilder(Transformer):
    """
    Transforms Lark parse tree into Dash AST nodes.

    This is a clean transformer that only builds the AST,
    without any code generation logic.
    """

    def __init__(self):
        super().__init__()
        self._imports: List[ImportStmt] = []
        self._constants: List[ConstDecl] = []
        self._global_vars: List[GlobalVarDecl] = []
        self._structs: List[StructDef] = []
        self._enums: List[EnumDef] = []
        self._windows: List[WindowDef] = []
        self._functions: List[FunctionDef] = []
        self._extern_funcs: List[ExternFunc] = []
        self._native_funcs: List[NativeFunc] = []
        self._headers: List[str] = []

    def _get_location(self, token_or_tree) -> Optional[SourceLocation]:
        """Extract source location from a token or tree."""
        if isinstance(token_or_tree, Token):
            return SourceLocation(
                line=token_or_tree.line,
                column=token_or_tree.column
            )
        elif isinstance(token_or_tree, Tree) and token_or_tree.meta:
            return SourceLocation(
                line=token_or_tree.meta.line,
                column=token_or_tree.meta.column
            )
        return None

    # === Program Structure ===

    def program(self, items) -> Program:
        """Build the program node."""
        main_block = None
        for item in items:
            if isinstance(item, MainBlock):
                main_block = item
        return Program(
            imports=self._imports,
            constants=self._constants,
            global_vars=self._global_vars,
            structs=self._structs,
            enums=self._enums,
            windows=self._windows,
            main=main_block,
            functions=self._functions,
            extern_funcs=self._extern_funcs,
            native_funcs=self._native_funcs,
            headers=self._headers
        )

    def import_stmt(self, items) -> ImportStmt:
        """Build an import statement node."""
        path_token = items[0]
        # Remove quotes from the path
        path = path_token.value[1:-1] if isinstance(path_token, Token) else str(path_token)
        import_node = ImportStmt(path=path, location=self._get_location(path_token))
        self._imports.append(import_node)
        return import_node

    # === Constants ===

    def const_decl(self, items) -> ConstDecl:
        """Build a constant declaration node."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        value = items[1]
        const_node = ConstDecl(name=name, value=value, location=self._get_location(items[0]))
        self._constants.append(const_node)
        return const_node

    def const_int(self, items) -> NumberLiteral:
        """Build a number literal for constant."""
        return NumberLiteral(value=int(items[0].value))

    def const_string(self, items) -> StringLiteral:
        """Build a string literal for constant."""
        return StringLiteral(value=items[0].value)

    def const_true(self, items) -> BoolLiteral:
        """Build a true literal for constant."""
        return BoolLiteral(value=True)

    def const_false(self, items) -> BoolLiteral:
        """Build a false literal for constant."""
        return BoolLiteral(value=False)

    # === Global Variables ===

    def global_var_decl(self, items) -> GlobalVarDecl:
        """Build a global variable declaration node."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        var_type = items[1].value if isinstance(items[1], Token) else str(items[1])
        initial_value = items[2] if len(items) > 2 else None
        node = GlobalVarDecl(
            name=name,
            var_type=var_type,
            initial_value=initial_value,
            location=self._get_location(items[0])
        )
        self._global_vars.append(node)
        return node

    # === Struct Definition ===

    def struct_def(self, items) -> str:
        """Build a struct definition node with fields and methods."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        fields = [item for item in items[1:] if isinstance(item, StructField)]
        methods = [item for item in items[1:] if isinstance(item, StructMethod)]
        struct = StructDef(
            name=name,
            fields=fields,
            methods=methods,
            location=self._get_location(items[0])
        )
        self._structs.append(struct)
        return ""  # Return empty string to not include in program items

    def struct_member(self, items):
        """Pass through struct member (field or method)."""
        return items[0] if items else None

    def struct_field(self, items) -> StructField:
        """Build a struct field node."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        field_type = items[1].value if isinstance(items[1], Token) else str(items[1])
        default_value = None
        # Check for default value (items after name and type)
        for item in items[2:]:
            if isinstance(item, (NumberLiteral, StringLiteral, BoolLiteral)):
                default_value = item
                break
            elif not isinstance(item, Token):
                default_value = item
                break
        return StructField(
            name=name,
            field_type=field_type,
            default_value=default_value,
            location=self._get_location(items[0])
        )

    def struct_method(self, items) -> StructMethod:
        """Build a struct method node."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        params = []
        body = []
        return_type = None

        for item in items[1:]:
            if isinstance(item, list):
                # Could be param_list or body statements
                if item and (isinstance(item[0], FunctionParam) or isinstance(item[0], str)):
                    params = item
                else:
                    body.extend(self._flatten_statements(item))
            elif isinstance(item, str) and item not in ('', None):
                return_type = item
            elif item is not None and not isinstance(item, Token) and item != "":
                body.append(item)

        return StructMethod(
            name=name,
            params=params,
            body=body,
            return_type=return_type,
            location=self._get_location(items[0])
        )

    def self_ref(self, items) -> SelfRef:
        """Build a self reference node."""
        return SelfRef()

    # === Enum Definition ===

    def enum_def(self, items) -> str:
        """Build an enum definition node."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        values = [item for item in items[1:] if isinstance(item, EnumValue)]
        enum = EnumDef(
            name=name,
            values=values,
            location=self._get_location(items[0])
        )
        self._enums.append(enum)
        return ""

    def enum_value(self, items) -> EnumValue:
        """Build an enum value node."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        value = None
        if len(items) > 1 and isinstance(items[1], Token):
            value = int(items[1].value)
        return EnumValue(name=name, value=value, location=self._get_location(items[0]))

    # === FFI - External Functions ===

    def extern_func(self, items) -> str:
        """Build an extern function declaration node."""
        library = items[0].value[1:-1] if isinstance(items[0], Token) else str(items[0])
        name = items[1].value if isinstance(items[1], Token) else str(items[1])
        params = []
        return_type = None

        for item in items[2:]:
            if isinstance(item, list):
                params = item
            elif isinstance(item, str) and item not in ('', None):
                return_type = item

        extern = ExternFunc(
            library=library,
            name=name,
            params=params,
            return_type=return_type,
            location=self._get_location(items[0])
        )
        self._extern_funcs.append(extern)
        return ""

    # === Native Functions (inline C code) ===

    def native_func(self, items) -> str:
        """Build a native function with inline C code."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        params = []
        return_type = None
        c_code = ""

        for item in items[1:]:
            if isinstance(item, list):
                params = item
            elif isinstance(item, str):
                if item.startswith('"""') or '\n' in item:
                    c_code = item
                elif item not in ('', None):
                    return_type = item

        native = NativeFunc(
            name=name,
            params=params,
            return_type=return_type,
            c_code=c_code,
            location=self._get_location(items[0])
        )
        self._native_funcs.append(native)
        return ""

    def native_body(self, items) -> str:
        """Extract the C code from triple-quoted string."""
        code = items[0].value if isinstance(items[0], Token) else str(items[0])
        # Remove triple quotes
        if code.startswith('"""') and code.endswith('"""'):
            code = code[3:-3]
        return code

    def header_directive(self, items) -> str:
        """Process @header directive - add custom C include/declaration."""
        header = items[0].value if isinstance(items[0], Token) else str(items[0])
        # Remove quotes
        if header.startswith('"') and header.endswith('"'):
            header = header[1:-1]
        self._headers.append(header)
        return ""

    def param(self, items) -> FunctionParam:
        """Build a function parameter with optional type."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        param_type = None
        if len(items) > 1:
            param_type = items[1].value if isinstance(items[1], Token) else str(items[1])
        return FunctionParam(name=name, param_type=param_type)

    def return_type(self, items) -> str:
        """Process return type annotation."""
        return items[0].value if isinstance(items[0], Token) else str(items[0])

    def main_block(self, items) -> MainBlock:
        """Build the main block node."""
        body = self._flatten_statements(items)
        return MainBlock(body=body)

    def block_body(self, items) -> List:
        """Process a block body into a list of statements."""
        return self._flatten_statements(items)

    # === Window Definition ===

    def window_def(self, items) -> str:
        """Build a window definition node."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        properties = []

        for item in items[1:]:
            if isinstance(item, WindowProperty):
                properties.append(item)
            elif isinstance(item, list):
                properties.extend(p for p in item if isinstance(p, WindowProperty))

        window = WindowDef(
            name=name,
            properties=properties,
            location=self._get_location(items[0])
        )
        self._windows.append(window)
        return ""  # Return empty string to not include in program items

    def window_body(self, items) -> List[WindowProperty]:
        """Process window body properties."""
        return [item for item in items if isinstance(item, WindowProperty)]

    def window_property(self, items) -> WindowProperty:
        """Build a window property node."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        value = items[1]
        return WindowProperty(name=name, value=value)

    def property(self, items) -> WindowProperty:
        """Build a property node (legacy grammar support)."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        value = items[1]
        # Convert raw tokens to AST nodes
        if isinstance(value, Token):
            if value.type == 'ESCAPED_STRING':
                value = StringLiteral(value=value.value)
            elif value.type in ('NUMBER', 'INT'):
                value = NumberLiteral(value=int(value.value))
        return WindowProperty(name=name, value=value)

    # === Statements ===

    def instruction(self, items):
        """Handle instruction (legacy grammar)."""
        return items[0] if items else None

    def statement(self, items):
        """Handle statement."""
        return items[0] if items else None

    def simple_stmt(self, items):
        """Handle simple statement."""
        return items[0] if items else None

    def compound_stmt(self, items):
        """Handle compound statement."""
        return items[0] if items else None

    def window_open(self, items) -> WindowOpen:
        """Build a window open node."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        return WindowOpen(
            window_name=name,
            location=self._get_location(items[0])
        )

    def print_stmt(self, items) -> PrintStmt:
        """Build a print statement node."""
        message = items[0]
        if not isinstance(message, StringLiteral):
            message = StringLiteral(value=str(message))
        return PrintStmt(message=message)

    def print_cmd(self, items) -> PrintStmt:
        """Build a print command node (legacy grammar)."""
        value = items[0]
        if isinstance(value, Token):
            if value.type == 'ESCAPED_STRING':
                message = StringLiteral(value=value.value)
            else:
                # Variable or other token - convert to VarRef
                message = VarRef(name=value.value)
        else:
            # Already an AST node (VarRef, BinaryOp, etc.) - use as-is
            message = value
        return PrintStmt(message=message)

    def wait_stmt(self, items) -> WaitStmt:
        """Build a wait statement node."""
        seconds = items[0]
        if not isinstance(seconds, NumberLiteral):
            seconds = NumberLiteral(value=int(seconds))
        return WaitStmt(seconds=seconds)

    def wait_cmd(self, items) -> WaitStmt:
        """Build a wait command node (legacy grammar)."""
        value = items[0]
        if isinstance(value, Token):
            seconds = NumberLiteral(value=int(value.value))
        elif isinstance(value, NumberLiteral):
            seconds = value
        else:
            seconds = NumberLiteral(value=int(value))
        return WaitStmt(seconds=seconds)

    def stop_stmt(self, items) -> StopStmt:
        """Build a stop statement node."""
        return StopStmt()

    def stop_cmd(self, items) -> StopStmt:
        """Build a stop command node (legacy grammar)."""
        return StopStmt()

    def return_stmt(self, items) -> ReturnStmt:
        """Build a return statement node."""
        value = items[0] if items else None
        return ReturnStmt(value=value)

    # === Event Loop ===

    def event_loop(self, items) -> EventLoop:
        """Build an event loop node."""
        handlers = [item for item in items if isinstance(item, (OnCloseHandler, OnKeyHandler))]
        return EventLoop(handlers=handlers)

    def event_handler(self, items):
        """Handle event handler wrapper."""
        return items[0] if items else None

    def on_close(self, items) -> OnCloseHandler:
        """Build an On Close handler node."""
        body = self._flatten_statements(items)
        return OnCloseHandler(body=body)

    def on_key(self, items) -> OnKeyHandler:
        """Build an On Key handler node."""
        key = items[0].value if isinstance(items[0], Token) else str(items[0])
        body = self._flatten_statements(items[1:])
        return OnKeyHandler(key=key, body=body)

    # === Control Flow ===

    def if_stmt(self, items) -> IfStmt:
        """Build an if statement node."""
        condition = items[0]
        then_body = []
        else_body = []

        # Collect then body (everything until else_clause or end)
        for item in items[1:]:
            if isinstance(item, list):
                # This is the else clause body
                else_body = item
            elif item is not None and not isinstance(item, Token):
                then_body.append(item)

        return IfStmt(
            condition=condition,
            then_body=then_body,
            else_body=else_body
        )

    def else_clause(self, items) -> List:
        """Process else clause - return list of statements."""
        return self._flatten_statements(items)

    def while_stmt(self, items) -> WhileStmt:
        """Build a while statement node."""
        condition = items[0]
        body = []
        for item in items[1:]:
            if item is not None and not isinstance(item, Token):
                body.append(item)
        return WhileStmt(condition=condition, body=body)

    def for_stmt(self, items) -> ForRangeStmt:
        """Build a for statement node (legacy - range only)."""
        var_name = items[0].value if isinstance(items[0], Token) else str(items[0])
        start = items[1]
        end = items[2]
        body = self._flatten_statements(items[3:])
        return ForRangeStmt(variable=var_name, start=start, end=end, body=body)

    def for_range_stmt(self, items) -> ForRangeStmt:
        """Build a for-range statement: for i in (start..end)."""
        var_name = items[0].value if isinstance(items[0], Token) else str(items[0])
        # Filter out RANGE_OP token
        filtered = [i for i in items[1:] if not (isinstance(i, Token) and i.type == 'RANGE_OP')]
        start = filtered[0]
        end = filtered[1]
        body = self._flatten_statements(filtered[2:])
        return ForRangeStmt(variable=var_name, start=start, end=end, body=body)

    def for_each_stmt(self, items) -> ForEachStmt:
        """Build a for-each statement: for item in array."""
        var_name = items[0].value if isinstance(items[0], Token) else str(items[0])
        iterable_name = items[1].value if isinstance(items[1], Token) else str(items[1])
        body = self._flatten_statements(items[2:])
        return ForEachStmt(variable=var_name, iterable=VarRef(name=iterable_name), body=body)

    def range_expr(self, items):
        """Handle range expression - return start and end."""
        return items  # Will be unpacked by for_stmt

    # === Variables ===

    def var_decl(self, items) -> VarDecl:
        """Build a variable declaration node."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        initial_value = items[1] if len(items) > 1 else None
        return VarDecl(name=name, initial_value=initial_value)

    def var_assign(self, items) -> VarAssign:
        """Build a variable assignment node (also serves as declaration)."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        value = items[1]
        # Convert raw tokens to AST nodes if needed
        if isinstance(value, Token):
            if value.type in ('NUMBER', 'INT'):
                value = NumberLiteral(value=int(value.value))
            elif value.type == 'ESCAPED_STRING':
                value = StringLiteral(value=value.value)
        return VarAssign(name=name, value=value)

    def var_ref(self, items) -> VarRef:
        """Build a variable reference node."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        return VarRef(name=name)

    def expr_stmt(self, items):
        """Handle expression statement."""
        return items[0] if items else None

    # === Functions ===

    def function_def(self, items) -> str:
        """Build a function definition node."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        params = []
        body = []
        return_type = None

        for item in items[1:]:
            if isinstance(item, list):
                # This is the param_list (list of FunctionParam or strings)
                if item and (isinstance(item[0], FunctionParam) or isinstance(item[0], str)):
                    params = item
                else:
                    # Body as list (from extended grammar)
                    body.extend(self._flatten_statements(item))
            elif isinstance(item, str) and item not in ('', None):
                # Return type
                return_type = item
            elif item is not None and not isinstance(item, Token) and item != "":
                # Individual statement (from minimal grammar)
                body.append(item)

        func = FunctionDef(name=name, params=params, body=body, return_type=return_type)
        self._functions.append(func)
        return ""

    def param_list(self, items) -> List:
        """Process parameter list - returns FunctionParam or string."""
        result = []
        for item in items:
            if isinstance(item, FunctionParam):
                result.append(item)
            elif isinstance(item, Token):
                result.append(item.value)
            elif isinstance(item, str):
                result.append(item)
        return result

    def function_call(self, items) -> FunctionCall:
        """Build a function call node."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        arguments = items[1] if len(items) > 1 and isinstance(items[1], list) else []
        return FunctionCall(name=name, arguments=arguments)

    def arg_list(self, items) -> List:
        """Process argument list."""
        return list(items)

    def lambda_func(self, items) -> LambdaFunc:
        """Build a lambda/anonymous function node."""
        params = []
        body = []
        is_expression = False

        for item in items:
            if isinstance(item, list):
                # This could be param_list or body statements
                if item and (isinstance(item[0], FunctionParam) or isinstance(item[0], str)):
                    params = item
                else:
                    body = item
            elif item is not None and not isinstance(item, Token):
                # Single expression body (arrow function style)
                if not isinstance(item, list):
                    body = item
                    is_expression = True

        return LambdaFunc(params=params, body=body, is_expression=is_expression)

    def func_call_stmt(self, items) -> FunctionCall:
        """Handle function call as statement."""
        return items[0] if items else None

    def method_call_stmt(self, items) -> MethodCall:
        """Handle method call as statement (player.move(5, 0))."""
        obj_name = items[0].value if isinstance(items[0], Token) else str(items[0])
        method_name = items[1].value if isinstance(items[1], Token) else str(items[1])
        args = items[2] if len(items) > 2 and isinstance(items[2], list) else []
        return MethodCall(object=VarRef(name=obj_name), method=method_name, arguments=args)

    # === Arrays ===

    def array_literal(self, items) -> ArrayLiteral:
        """Build an array literal node."""
        elements = list(items) if items else []
        return ArrayLiteral(elements=elements)

    def postfix_expr(self, items):
        """Build a postfix expression (handles array[i][j], obj.x.y, method calls, and slices)."""
        if len(items) == 1:
            return items[0]

        # First item is the base atom
        result = items[0]

        # Apply each postfix operation
        for op in items[1:]:
            if isinstance(op, tuple):
                op_type = op[0]
                if op_type == 'index':
                    result = ArrayAccess(array=result, index=op[1])
                elif op_type == 'slice':
                    result = ArraySlice(array=result, start=op[1], end=op[2])
                elif op_type == 'slice_from':
                    result = ArraySlice(array=result, start=op[1], end=None)
                elif op_type == 'slice_to':
                    result = ArraySlice(array=result, start=None, end=op[1])
                elif op_type == 'member':
                    # Convert to MemberAccess - need object_name as string
                    if isinstance(result, VarRef):
                        result = MemberAccess(object_name=result.name, member=op[1])
                    else:
                        # For chained access like arr[0].length, use PropertyAccess
                        result = PropertyAccess(object=result, property=op[1])
                elif op_type == 'method_call':
                    # Method call like player.move(5, 0)
                    result = MethodCall(object=result, method=op[1], arguments=op[2])
                elif op_type == 'call':
                    # Function call on result (e.g., for lambdas or function references)
                    if isinstance(result, VarRef):
                        # Variable being called as function
                        result = FunctionCall(name=result.name, arguments=op[1])
                    else:
                        # For now, treat as method call with empty method
                        result = MethodCall(object=result, method="__call__", arguments=op[1])

        return result

    def index_op(self, items):
        """Handle index operation [expr]."""
        return ('index', items[0])

    def slice_op(self, items):
        """Handle slice operation [start:end]."""
        return ('slice', items[0], items[1])

    def slice_from_op(self, items):
        """Handle slice operation [start:]."""
        return ('slice_from', items[0])

    def slice_to_op(self, items):
        """Handle slice operation [:end]."""
        return ('slice_to', items[0])

    def member_op(self, items):
        """Handle member operation .name."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        return ('member', name)

    def method_call_op(self, items):
        """Handle method call operation .name(args)."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        args = items[1] if len(items) > 1 and isinstance(items[1], list) else []
        return ('method_call', name, args)

    def call_op(self, items):
        """Handle function call operation (args)."""
        args = items[0] if items and isinstance(items[0], list) else []
        return ('call', args)

    def index_chain(self, items):
        """Build list of indices for array access."""
        return list(items)

    def array_assign(self, items):
        """Build an array assignment node (supports matrix[i][j] = value)."""
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        indices = items[1]  # List of indices from index_chain
        value = items[2]

        # Build nested ArrayAccess for the target
        result = VarRef(name=name)
        for idx in indices[:-1]:  # All but last index
            result = ArrayAccess(array=result, index=idx)

        # Return ArrayAssign with the innermost target
        return ArrayAssign(array=result, index=indices[-1], value=value)

    def member_assign(self, items) -> MemberAssign:
        """Build a member assignment node (player.x = 10)."""
        obj_name = items[0].value if isinstance(items[0], Token) else str(items[0])
        member = items[1].value if isinstance(items[1], Token) else str(items[1])
        value = items[2]
        return MemberAssign(object_name=obj_name, member=member, value=value)

    def self_member_assign(self, items) -> MemberAssign:
        """Build a self member assignment node (self.x = 10)."""
        member = items[0].value if isinstance(items[0], Token) else str(items[0])
        value = items[1]
        return MemberAssign(object_name="self", member=member, value=value)

    # === Expressions ===

    def or_expr(self, items):
        """Build OR expression."""
        return self._build_binary_chain(items, "or")

    def and_expr(self, items):
        """Build AND expression."""
        return self._build_binary_chain(items, "and")

    def compare_expr(self, items):
        """Build comparison expression."""
        if len(items) == 1:
            return items[0]
        # items = [left, COMP_OP, right]
        left = items[0]
        op = items[1].value if isinstance(items[1], Token) else str(items[1])
        right = items[2]
        return BinaryOp(left=left, operator=op, right=right)

    def not_op(self, items) -> UnaryOp:
        """Build NOT expression."""
        return UnaryOp(operator="not", operand=items[0])

    def not_expr(self, items) -> UnaryOp:
        """Build NOT expression (alias)."""
        return UnaryOp(operator="not", operand=items[0])

    def comparison(self, items):
        """Build comparison expression."""
        if len(items) == 1:
            return items[0]
        # Handle chained comparisons
        result = items[0]
        i = 1
        while i < len(items):
            op = items[i]
            right = items[i + 1]
            result = BinaryOp(left=result, operator=op, right=right)
            i += 2
        return result

    def eq(self, items): return "=="
    def neq(self, items): return "!="
    def lt(self, items): return "<"
    def gt(self, items): return ">"
    def lte(self, items): return "<="
    def gte(self, items): return ">="

    def add_expr(self, items):
        """Build addition/subtraction expression."""
        if len(items) == 1:
            return items[0]
        return self._build_binary_chain_with_ops(items)

    def mul_expr(self, items):
        """Build multiplication/division expression."""
        if len(items) == 1:
            return items[0]
        return self._build_binary_chain_with_ops(items)

    def neg(self, items) -> UnaryOp:
        """Build negation expression."""
        return UnaryOp(operator="-", operand=items[0])

    def neg_expr(self, items) -> UnaryOp:
        """Build negation expression (alias)."""
        return UnaryOp(operator="-", operand=items[0])

    def _build_binary_chain(self, items, default_op):
        """Build a chain of binary operations with a default operator."""
        if len(items) == 1:
            return items[0]

        result = items[0]
        i = 1
        while i < len(items):
            if isinstance(items[i], str):
                op = items[i]
                right = items[i + 1]
                i += 2
            else:
                op = default_op
                right = items[i]
                i += 1
            result = BinaryOp(left=result, operator=op, right=right)
        return result

    def _build_binary_chain_with_ops(self, items):
        """Build a chain of binary operations where operators are in the items."""
        if len(items) == 1:
            return items[0]

        result = items[0]
        i = 1
        while i < len(items):
            op_token = items[i]
            op = op_token.value if isinstance(op_token, Token) else str(op_token)
            right = items[i + 1]
            result = BinaryOp(left=result, operator=op, right=right)
            i += 2
        return result

    # === Literals ===

    def string_literal(self, items):
        """Build a string literal node, handling interpolation."""
        value = items[0].value if isinstance(items[0], Token) else str(items[0])

        # Check for interpolation: "Hello #{name}!"
        if '#{' in value and '}' in value:
            return self._parse_interpolated_string(value)

        return StringLiteral(value=value)

    def _parse_interpolated_string(self, value: str):
        """Parse an interpolated string into concatenation operations."""
        import re

        # Remove surrounding quotes
        if value.startswith('"') and value.endswith('"'):
            content = value[1:-1]
        else:
            content = value

        # Find all #{...} patterns
        pattern = r'#\{([^}]+)\}'
        parts = []
        last_end = 0

        for match in re.finditer(pattern, content):
            # Add text before the interpolation
            if match.start() > last_end:
                text = content[last_end:match.start()]
                parts.append(StringLiteral(value=f'"{text}"'))

            # Add the variable reference
            var_name = match.group(1).strip()
            parts.append(VarRef(name=var_name))

            last_end = match.end()

        # Add remaining text after last interpolation
        if last_end < len(content):
            text = content[last_end:]
            parts.append(StringLiteral(value=f'"{text}"'))

        # Build concatenation chain
        if len(parts) == 1:
            return parts[0]

        result = parts[0]
        for part in parts[1:]:
            result = BinaryOp(left=result, operator="+", right=part)

        return result

    def number_literal(self, items) -> NumberLiteral:
        """Build a number literal node."""
        value = items[0].value if isinstance(items[0], Token) else str(items[0])
        return NumberLiteral(value=int(value))

    def true_lit(self, items) -> BoolLiteral:
        """Build a true literal node."""
        return BoolLiteral(value=True)

    def false_lit(self, items) -> BoolLiteral:
        """Build a false literal node."""
        return BoolLiteral(value=False)

    def true_literal(self, items) -> BoolLiteral:
        """Build a true literal node (alias)."""
        return BoolLiteral(value=True)

    def false_literal(self, items) -> BoolLiteral:
        """Build a false literal node (alias)."""
        return BoolLiteral(value=False)

    # Value handlers (for window properties)
    def string_value(self, items) -> StringLiteral:
        """Handle string value."""
        value = items[0].value if isinstance(items[0], Token) else str(items[0])
        return StringLiteral(value=value)

    def number_value(self, items) -> NumberLiteral:
        """Handle number value."""
        value = items[0].value if isinstance(items[0], Token) else str(items[0])
        return NumberLiteral(value=int(value))

    def bool_true(self, items) -> BoolLiteral:
        """Handle true value."""
        return BoolLiteral(value=True)

    def bool_false(self, items) -> BoolLiteral:
        """Handle false value."""
        return BoolLiteral(value=False)

    def value(self, items):
        """Handle generic value (legacy grammar)."""
        if isinstance(items[0], Token):
            if items[0].type == 'ESCAPED_STRING':
                return StringLiteral(value=items[0].value)
            elif items[0].type in ('NUMBER', 'INT'):
                return NumberLiteral(value=int(items[0].value))
        return items[0]

    # === Comments ===

    def comment_line(self, items) -> Comment:
        """Build a comment node."""
        text = items[0].value if isinstance(items[0], Token) else str(items[0])
        return Comment(text=text)

    # === Helpers ===

    def _flatten_statements(self, items) -> List:
        """Flatten and filter a list of statements."""
        result = []
        for item in items:
            if item is None or item == "":
                continue
            if isinstance(item, list):
                result.extend(self._flatten_statements(item))
            elif isinstance(item, Token):
                continue  # Skip tokens
            elif isinstance(item, str) and not item.strip():
                continue  # Skip empty strings
            else:
                result.append(item)
        return result


# Alias for backward compatibility
DashCodeGenerator = DashASTBuilder
