"""
Dash Language Grammar Definition
Extensible Lark grammar for the Dash programming language.
"""

# Grammar with variables and expressions support
dash_grammar_minimal = r"""
    ?start: program
    program: (import_stmt | const_decl | global_var_decl | struct_def | interface_def | enum_def | window_def | function_def | extern_func | native_func | header_directive | link_directive | c_block | stack_directive | workbench_output_directive | catalog_directive | version_directive | main_block | comment_line)*

    // Constant declaration
    // a literal or an integer expression known when compiling (const MASCARA = 1 << 4)
    const_decl: "const" ID "=" expression

    // Global variable declaration
    global_var_decl: "var" ID ":" TYPE_NAME ("=" expression)?

    // Import statement
    import_stmt: "import" ESCAPED_STRING

    // Struct definition with optional methods
    struct_def: "struct" ID struct_impls? struct_member* "end"
    struct_impls: ":" ID ("," ID)*
    // An interface (Lorraine D43): methods that structs declaring it (struct X: Orden) have, called through
    // a table in each struct's type descriptor
    interface_def: "interface" ID (interface_method | comment_line)* "end"
    interface_method: "func" ID "(" param_list? ")" return_type?
    struct_member: struct_field | struct_method | comment_line
    // weak: the field does not hold its object (a parent pointer), so no cycle (dashweb D6)
    struct_field: WEAK? ID ":" TYPE_NAME ("=" expression)?
    WEAK: "weak"
    struct_method: "func" ID "(" param_list? ")" return_type? instruction* "end"
    // [T]: a list whose elements are T ("[String]", "[Nodo]", "[[Int]]")
    // {String: T}: a dictionary from String to T; {Int: T} from Int (Lorraine D9)
    TYPE_NAME: "Int" | "Float" | "String" | "Bool" | "Pointer" | "Func" | ID | /\[[ \t]*[\[{A-Za-z_][\[\]{}:A-Za-z0-9_ \t]*\]/ | /\{[ \t]*(?:String|Int)[ \t]*:[ \t]*[\[{A-Za-z_][\[\]{}:A-Za-z0-9_ \t]*\}/

    // Enum definition
    enum_def: "enum" ID (enum_value ","? | comment_line)* "end"
    enum_value: ID ("=" INT)?
              | ID "=" "-" INT -> enum_value_neg

    // Window definition
    window_def: "Window" ID (property | comment_line)* "end"
    property: ID value

    // Function definition with optional types
    function_def: "func" ID "(" param_list? ")" return_type? instruction* "end"
    param_list: param ("," param)*
    param: ID (":" TYPE_NAME)?
    return_type: "->" TYPE_NAME
    function_call: ID "(" arg_list? ")"
    arg_list: expression ("," expression)*

    // Lambda/anonymous function
    lambda_func: "fn" "(" param_list? ")" "->" expression
                | "fn" "(" param_list? ")" instruction* "end"

    // FFI - External function declaration
    extern_func: "@extern" "(" ESCAPED_STRING ")" "func" ID "(" param_list? ")" return_type?

    // Native C code block
    native_func: "@native" native_borrow? "func" ID "(" param_list? ")" return_type? native_body "end"
    // @native(borrow): the C only uses its arguments during the call (dashweb D26)
    native_borrow: "(" "borrow" ")"
    native_body: NATIVE_CODE
    NATIVE_CODE: /\"\"\"[\s\S]*?\"\"\"/

    // Header include directive
    header_directive: "@header" ESCAPED_STRING
    // C from outside (dashweb D10): an object or library to link, and C code at top level
    link_directive: "@link" ESCAPED_STRING
    c_block: "@c" native_body "end"
    // the stack the program needs at least, in bytes (dashweb D24)
    stack_directive: "@stack" INT
    // where the output goes when started from the Workbench ("NIL:": nowhere, no window) (dashweb D59)
    workbench_output_directive: "@workbench_output" ESCAPED_STRING
    catalog_directive: "@catalog" ESCAPED_STRING INT ESCAPED_STRING?
    version_directive: "@version" ESCAPED_STRING

    // Main block
    main_block: "Main" instruction* "end"

    // Instructions
    ?instruction: window_open
                | window_close
                | wait_cmd
                | print_cmd
                | event_loop
                | stop_cmd
                | break_stmt
                | continue_stmt
                | return_stmt
                | array_assign
                | self_member_assign
                | member_assign
                | indexed_member_assign
                | var_assign
                | local_var_decl
                | if_stmt
                | while_stmt
                | for_range_stmt
                | for_each_stmt
                | method_call_stmt
                | indexed_method_call_stmt
                | func_call_stmt
                | comment_line

    // Method call as statement (player.move(5, 0))
    // also through fields: n.hijos.push(x), self.lista.clear() (dashweb D4b)
    method_call_stmt: ID ("." ID)+ "(" arg_list? ")"
                    | "self" ("." ID)+ "(" arg_list? ")" -> self_method_call_stmt

    // a method of a list or dict element: d["k"].push(x), l[0].mover(1) (dashweb D37)
    indexed_method_call_stmt: ID ("." ID)* index_chain ("." ID)+ "(" arg_list? ")"

    // Member assignment (player.x = 10 or self.x = 10)
    member_assign: ID ("." ID)+ "=" expression
    // a field of a list element: l[0].x = 5, a.items[i].nombre = "b" (dashweb D4c)
    indexed_member_assign: ID ("." ID)* index_chain ("." ID)+ "=" expression
    self_member_assign: "self" ("." ID)+ "=" expression

    // Return statement
    return_stmt: "return" expression?

    // Function call as statement
    func_call_stmt: function_call

    // Window commands
    window_open: ID ".open"
    window_close: ID ".close"

    // I/O commands
    wait_cmd: "Wait" expression
    print_cmd: "Print" expression

    // Control flow
    stop_cmd: "Stop"
    break_stmt: BREAK
    continue_stmt: CONTINUE
    BREAK: "break"
    CONTINUE: "continue"
    if_stmt: "if" expression instruction* elif_clause* else_clause? "end"
    elif_clause: "elif" expression instruction*
    else_clause: "else" instruction*
    while_stmt: "while" expression instruction* "end"

    // For loops
    for_range_stmt: "for" ID "in" "(" expression RANGE_OP expression (STEP expression)? ")" instruction* "end"
    STEP: "step"
    for_each_stmt: "for" ID "in" expression instruction* "end"
    RANGE_OP: ".."

    // Variables (Python style - first assignment declares)
    var_assign: ID "=" expression
    // with a type, for a variable that starts empty: var actual: Nodo = nil
    local_var_decl: "var" ID ":" TYPE_NAME ("=" expression)?

    // Arrays
    // also through fields: h.reglas["k"] = v, self.l[0] = v (dashweb D5)
    array_assign: ID ("." ID)* index_chain "=" expression
                | "self" ("." ID)+ index_chain "=" expression -> self_array_assign
    index_chain: ("[" expression "]")+
    array_literal: "[" (expression ("," expression)*)? "]"
    // {"clave": valor, ...}: a dictionary with String keys (dashweb D5), or Int keys {1: valor} (D9)
    dict_literal: "{" (dict_entry ("," dict_entry)*)? "}"
    dict_entry: expression ":" expression

    // Event loop
    event_loop: "EventLoop" (event_handler | comment_line)* "end"
    ?event_handler: on_close | on_key | on_gadget | on_menu | on_click | on_timer

    on_close: "On" "Close" instruction* "end"
    on_gadget: "On" "Gadget" instruction* "end"
    on_menu: "On" "Menu" instruction* "end"
    on_key: "On" "Key" (ESCAPED_STRING | INT)? instruction* "end"
    // dashweb D27: a left click in the window (click_x(), click_y()); every N ms (a number or a variable)
    on_click: "On" "Click" instruction* "end"
    on_timer: "On" "Timer" (INT | ID) instruction* "end"

    // Expressions with precedence
    ?expression: or_expr

    ?or_expr: and_expr ("or" and_expr)*
    ?and_expr: not_test ("and" not_test)*
    ?not_test: "not" not_test -> not_expr
             | compare_expr

    ?compare_expr: bor_expr (COMP_OP bor_expr)?
    COMP_OP: "==" | "!=" | "<=" | ">=" | "<" | ">"

    // Bit operators, as in Python: | below ^ below & below the shifts, all between the
    // comparisons and + -
    ?bor_expr: bxor_expr (BOR bxor_expr)*
    ?bxor_expr: band_expr (BXOR band_expr)*
    ?band_expr: shift_expr (BAND shift_expr)*
    ?shift_expr: add_expr (SHIFT_OP add_expr)*
    BOR: "|"
    BXOR: "^"
    BAND: "&"
    SHIFT_OP.2: "<<" | ">>"

    ?add_expr: mul_expr ((ADD_OP) mul_expr)*
    ADD_OP: "+" | "-"

    ?mul_expr: unary_expr ((MUL_OP) unary_expr)*
    MUL_OP: "*" | "/" | "%"

    ?unary_expr: "-" unary_expr -> neg_expr
              | "~" unary_expr -> bnot_expr
              | primary

    ?primary: postfix_expr

    // Postfix expressions (array access, member access chains)
    postfix_expr: atom postfix_op*

    ?atom: FLOAT -> float_literal
         | INT -> number_literal
         | ESCAPED_STRING -> string_literal
         | "true" -> true_literal
         | "false" -> false_literal
         | "nil" -> nil_literal
         | "self" -> self_ref
         | array_literal
         | dict_literal
         | lambda_func
         | function_call
         | ID -> var_ref
         | "(" expression ")"

    postfix_op: "[" expression ":" expression "]" -> slice_op
              | "[" expression ":" "]" -> slice_from_op
              | "[" ":" expression "]" -> slice_to_op
              | "[" expression "]" -> index_op
              | "." ID "(" arg_list? ")" -> method_call_op
              | "." ID -> member_op
              | "(" arg_list? ")" -> call_op

    // Comments
    comment_line: COMMENT
    COMMENT: /#[^\n]*/

    // Property values
    ?value: ESCAPED_STRING | INT
          | "true" -> true_literal
          | "false" -> false_literal

    // Tokens
    ID: /[a-zA-Z_][a-zA-Z0-9_]*/
    // Float: digits on both sides of the point (so 1..10 stays a range)
    FLOAT.2: /\d+\.\d+([eE][+-]?\d+)?/
    // Decimal, hexadecimal (0xDFF000 or $DFF000) and binary (0b1010)
    INT: /0[xX][0-9a-fA-F]+|\$[0-9a-fA-F]+|0[bB][01]+|\d+/

    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""
