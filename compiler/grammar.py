"""
Dash Language Grammar Definition
Extensible Lark grammar for the Dash programming language.
"""

dash_grammar = r"""
    // ===========================================
    // PROGRAM STRUCTURE
    // ===========================================
    ?start: program
    program: (window_def | function_def | comment_line)* main_block? comment_line*

    // ===========================================
    // WINDOW DEFINITION
    // ===========================================
    window_def: "Window" ID window_body "end"
    window_body: window_property*
    window_property: WINDOW_PROP_NAME value
    WINDOW_PROP_NAME: "title" | "width" | "height" | "left" | "top"
                    | "closegadget" | "dragbar" | "depthgadget" | "sizegadget"

    // ===========================================
    // MAIN BLOCK
    // ===========================================
    main_block: "Main" block_body "end"
    block_body: statement*

    // ===========================================
    // STATEMENTS
    // ===========================================
    ?statement: simple_stmt
              | compound_stmt
              | comment_line

    // Simple statements (single line)
    ?simple_stmt: window_open
                | print_stmt
                | wait_stmt
                | stop_stmt
                | return_stmt
                | var_decl
                | var_assign
                | expr_stmt

    // Compound statements (blocks)
    ?compound_stmt: event_loop
                  | if_stmt
                  | while_stmt
                  | for_stmt

    // ===========================================
    // WINDOW COMMANDS
    // ===========================================
    window_open: ID ".open"
    window_close: ID ".close"

    // ===========================================
    // I/O COMMANDS
    // ===========================================
    print_stmt: "Print" expression
    wait_stmt: "Wait" expression

    // ===========================================
    // CONTROL FLOW
    // ===========================================
    stop_stmt: "Stop"
    return_stmt: "return" expression?

    if_stmt: "if" expression block_body else_clause? "end"
    else_clause: "else" block_body

    while_stmt: "while" expression block_body "end"

    for_stmt: "for" ID "in" range_expr block_body "end"
    range_expr: "(" expression ".." expression ")"

    // ===========================================
    // EVENT LOOP
    // ===========================================
    event_loop: "EventLoop" (event_handler | comment_line)* "end"

    ?event_handler: on_close
                  | on_key
                  | on_gadget

    on_close: "On" "Close" block_body "end"
    on_key: "On" "Key" "(" ESCAPED_STRING ")" block_body "end"
    on_gadget: "On" "Gadget" "(" expression ")" block_body "end"

    // ===========================================
    // VARIABLES
    // ===========================================
    var_decl: "let" ID "=" expression
    var_assign: ID "=" expression

    // ===========================================
    // FUNCTIONS (FUTURE)
    // ===========================================
    function_def: "func" ID "(" param_list? ")" block_body "end"
    param_list: ID ("," ID)*
    function_call: ID "(" arg_list? ")"
    arg_list: expression ("," expression)*

    // ===========================================
    // EXPRESSIONS
    // ===========================================
    ?expression: or_expr

    ?or_expr: and_expr ("or" and_expr)*
    ?and_expr: not_expr ("and" not_expr)*
    ?not_expr: "not" not_expr -> not_op
             | comparison

    ?comparison: add_expr (comp_op add_expr)*
    ?comp_op: "==" -> eq
            | "!=" -> neq
            | "<"  -> lt
            | ">"  -> gt
            | "<=" -> lte
            | ">=" -> gte

    ?add_expr: mul_expr (("+"|"-") mul_expr)*
    ?mul_expr: unary_expr (("*"|"/"|"%") unary_expr)*
    ?unary_expr: "-" unary_expr -> neg
              | primary

    ?primary: literal
            | var_ref
            | function_call
            | "(" expression ")"

    var_ref: ID
    expr_stmt: expression

    // ===========================================
    // LITERALS
    // ===========================================
    ?literal: string_literal
            | number_literal
            | bool_literal

    string_literal: ESCAPED_STRING
    number_literal: NUMBER
    bool_literal: "true" -> true_lit
                | "false" -> false_lit

    // ===========================================
    // VALUES (for properties)
    // ===========================================
    ?value: ESCAPED_STRING -> string_value
          | NUMBER -> number_value
          | "true" -> bool_true
          | "false" -> bool_false

    // ===========================================
    // COMMENTS
    // ===========================================
    comment_line: COMMENT
    COMMENT: /#[^\n]*/

    // ===========================================
    // TOKENS
    // ===========================================
    ID: /[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.ESCAPED_STRING
    %import common.NUMBER
    %import common.WS
    %import common.NEWLINE

    %ignore WS
    %ignore NEWLINE
"""

# Grammar with variables and expressions support
dash_grammar_minimal = r"""
    ?start: program
    program: (import_stmt | const_decl | global_var_decl | struct_def | enum_def | window_def | function_def | extern_func | native_func | header_directive | main_block | comment_line)*

    // Constant declaration
    const_decl: "const" ID "=" const_value
    ?const_value: INT -> const_int
                | ESCAPED_STRING -> const_string
                | "true" -> const_true
                | "false" -> const_false

    // Global variable declaration
    global_var_decl: "var" ID ":" TYPE_NAME ("=" expression)?

    // Import statement
    import_stmt: "import" ESCAPED_STRING

    // Struct definition with optional methods
    struct_def: "struct" ID struct_member* "end"
    struct_member: struct_field | struct_method
    struct_field: ID ":" TYPE_NAME ("=" expression)?
    struct_method: "func" ID "(" param_list? ")" return_type? instruction* "end"
    TYPE_NAME: "Int" | "String" | "Bool" | "Pointer" | "Func" | ID

    // Enum definition
    enum_def: "enum" ID enum_value* "end"
    enum_value: ID ("=" INT)?

    // Window definition
    window_def: "Window" ID property* "end"
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
    native_func: "@native" "func" ID "(" param_list? ")" return_type? native_body "end"
    native_body: NATIVE_CODE
    NATIVE_CODE: /\"\"\"[\s\S]*?\"\"\"/

    // Header include directive
    header_directive: "@header" ESCAPED_STRING

    // Main block
    main_block: "Main" instruction* "end"

    // Instructions
    ?instruction: window_open
                | wait_cmd
                | print_cmd
                | event_loop
                | stop_cmd
                | return_stmt
                | array_assign
                | self_member_assign
                | member_assign
                | var_assign
                | if_stmt
                | while_stmt
                | for_range_stmt
                | for_each_stmt
                | method_call_stmt
                | func_call_stmt
                | comment_line

    // Method call as statement (player.move(5, 0))
    method_call_stmt: ID "." ID "(" arg_list? ")"

    // Member assignment (player.x = 10 or self.x = 10)
    member_assign: ID "." ID "=" expression
    self_member_assign: "self" "." ID "=" expression

    // Return statement
    return_stmt: "return" expression?

    // Function call as statement
    func_call_stmt: function_call

    // Window commands
    window_open: ID ".open"

    // I/O commands
    wait_cmd: "Wait" expression
    print_cmd: "Print" expression

    // Control flow
    stop_cmd: "Stop"
    if_stmt: "if" expression instruction* else_clause? "end"
    else_clause: "else" instruction*
    while_stmt: "while" expression instruction* "end"

    // For loops
    for_range_stmt: "for" ID "in" "(" expression RANGE_OP expression ")" instruction* "end"
    for_each_stmt: "for" ID "in" ID instruction* "end"
    RANGE_OP: ".."

    // Variables (Python style - first assignment declares)
    var_assign: ID "=" expression

    // Arrays
    array_assign: ID index_chain "=" expression
    index_chain: ("[" expression "]")+
    array_literal: "[" (expression ("," expression)*)? "]"

    // Event loop
    event_loop: "EventLoop" (event_handler | comment_line)* "end"
    ?event_handler: on_close

    on_close: "On" "Close" instruction* "end"

    // Expressions with precedence
    ?expression: or_expr

    ?or_expr: and_expr ("or" and_expr)*
    ?and_expr: compare_expr ("and" compare_expr)*

    ?compare_expr: add_expr (COMP_OP add_expr)?
    COMP_OP: "==" | "!=" | "<=" | ">=" | "<" | ">"

    ?add_expr: mul_expr ((ADD_OP) mul_expr)*
    ADD_OP: "+" | "-"

    ?mul_expr: unary_expr ((MUL_OP) unary_expr)*
    MUL_OP: "*" | "/" | "%"

    ?unary_expr: "not" unary_expr -> not_expr
              | "-" unary_expr -> neg_expr
              | primary

    ?primary: postfix_expr

    // Postfix expressions (array access, member access chains)
    postfix_expr: atom postfix_op*

    ?atom: INT -> number_literal
         | ESCAPED_STRING -> string_literal
         | "true" -> true_literal
         | "false" -> false_literal
         | "self" -> self_ref
         | array_literal
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

    // Tokens
    ID: /[a-zA-Z_][a-zA-Z0-9_]*/
    INT: /\d+/

    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""
