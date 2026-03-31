"""
Dash Language Transpiler
Transpiles .dash source files to C code for Amiga.

Pipeline: Source → Parse → AST → Analyze → Generate → C Code
"""
import sys
import os
import argparse
from dataclasses import dataclass, field
from lark import Lark
from typing import Optional, Set, List, Dict, Tuple

from compiler.grammar import dash_grammar, dash_grammar_minimal
from compiler.transformer import DashASTBuilder
from compiler.analyzer import SemanticAnalyzer, AnalysisResult
from compiler.codegen import CodeGenerator
from compiler.ast_nodes import (
    Program, FunctionDef, WindowDef, StructDef, EnumDef, ExternFunc, NativeFunc,
    ConstDecl, GlobalVarDecl
)


@dataclass
class ModuleInfo:
    """Information about a compiled module for multi-file output."""
    name: str  # Module name (e.g., "audio" from "lib/amiga/audio.dash")
    path: str  # Full path to the .dash file
    relative_path: str  # Relative path from project root
    ast: Program  # Parsed AST
    dependencies: List[str] = field(default_factory=list)  # Other modules this depends on


class DashCompiler:
    """
    Main compiler class that orchestrates the compilation pipeline.

    Stages:
    1. Parse: Convert source code to Lark parse tree
    2. Transform: Convert parse tree to Dash AST
    3. Load Imports: Recursively load imported modules
    4. Analyze: Semantic analysis and validation
    5. Generate: Convert AST to C code
    """

    def __init__(self, use_extended_grammar: bool = False, verbose: bool = False):
        self.verbose = verbose
        self.use_extended_grammar = use_extended_grammar
        grammar = dash_grammar if use_extended_grammar else dash_grammar_minimal
        self.parser = Lark(
            grammar,
            parser="lalr",
            propagate_positions=True
        )
        self._loaded_modules: Set[str] = set()  # Track loaded modules to avoid duplicates
        self._base_dir: str = ""  # Base directory for resolving imports

    def _parse_source(self, source: str) -> Program:
        """Parse source code into an AST."""
        tree = self.parser.parse(source)
        transformer = DashASTBuilder()
        return transformer.transform(tree)

    def _resolve_import_path(self, import_path: str) -> str:
        """Resolve import path relative to base directory or project root."""
        if os.path.isabs(import_path):
            return import_path

        # Search paths in order of priority:
        # 1. Relative to the current file's directory
        # 2. Relative to the project root (detected by presence of 'dash' script or compiler dir)
        # 3. Relative to current working directory

        search_paths = [self._base_dir]

        # Find project root by looking for dash script or compiler directory
        current = self._base_dir
        for _ in range(10):  # Max depth to search
            parent = os.path.dirname(current)
            if parent == current:
                break
            if os.path.exists(os.path.join(parent, 'dash')) or \
               os.path.exists(os.path.join(parent, 'compiler')):
                search_paths.append(parent)
                break
            current = parent

        # Add cwd as fallback
        cwd = os.getcwd()
        if cwd not in search_paths:
            search_paths.append(cwd)

        # Try each search path
        for base in search_paths:
            full_path = os.path.normpath(os.path.join(base, import_path))
            if os.path.exists(full_path):
                return full_path

        # Return first attempt for error message
        return os.path.normpath(os.path.join(self._base_dir, import_path))

    def _load_module(self, import_path: str) -> Program:
        """Load and parse a module file."""
        full_path = self._resolve_import_path(import_path)

        # Check for circular imports
        if full_path in self._loaded_modules:
            if self.verbose:
                print(f"  Skipping already loaded module: {import_path}", file=sys.stderr)
            return Program()  # Return empty program for already loaded modules

        self._loaded_modules.add(full_path)

        if self.verbose:
            print(f"  Loading module: {import_path}", file=sys.stderr)

        try:
            with open(full_path, "r") as f:
                source = f.read()
        except FileNotFoundError:
            raise CompilationError(f"Import not found: {import_path}", stage="import")
        except IOError as e:
            raise CompilationError(f"Error reading import {import_path}: {e}", stage="import")

        return self._parse_source(source)

    def _is_private(self, name: str) -> bool:
        """Check if a name is private (starts with underscore)."""
        return name.startswith("_")

    def _merge_modules(self, main_ast: Program) -> Program:
        """Load imports and merge public definitions into the main AST."""
        if not main_ast.imports:
            return main_ast

        if self.verbose:
            print(f"  Processing {len(main_ast.imports)} import(s)...", file=sys.stderr)

        merged_constants: List[ConstDecl] = []
        merged_global_vars: List[GlobalVarDecl] = []
        merged_functions: List[FunctionDef] = []
        merged_windows: List[WindowDef] = []
        merged_structs: List[StructDef] = []
        merged_enums: List[EnumDef] = []
        merged_extern_funcs: List[ExternFunc] = []
        merged_native_funcs: List[NativeFunc] = []

        # First, load all imports
        for import_stmt in main_ast.imports:
            module_ast = self._load_module(import_stmt.path)

            # Recursively process nested imports
            if module_ast.imports:
                module_ast = self._merge_modules(module_ast)

            # Add public constants (not starting with _)
            for const in module_ast.constants:
                if not self._is_private(const.name):
                    merged_constants.append(const)

            # Add public global variables (not starting with _)
            for gvar in module_ast.global_vars:
                if not self._is_private(gvar.name):
                    merged_global_vars.append(gvar)

            # Add public functions (not starting with _)
            for func in module_ast.functions:
                if not self._is_private(func.name):
                    merged_functions.append(func)
                elif self.verbose:
                    print(f"    Skipping private function: {func.name}", file=sys.stderr)

            # Add public windows (not starting with _)
            for window in module_ast.windows:
                if not self._is_private(window.name):
                    merged_windows.append(window)

            # Add public structs
            for struct in module_ast.structs:
                if not self._is_private(struct.name):
                    merged_structs.append(struct)

            # Add public enums
            for enum in module_ast.enums:
                if not self._is_private(enum.name):
                    merged_enums.append(enum)

            # Add extern functions
            for extern in module_ast.extern_funcs:
                if not self._is_private(extern.name):
                    merged_extern_funcs.append(extern)

            # Add native functions
            for native in module_ast.native_funcs:
                if not self._is_private(native.name):
                    merged_native_funcs.append(native)

        # Merge with main program's definitions
        # Imported items come first, then main program's items
        all_constants = merged_constants + list(main_ast.constants)
        all_global_vars = merged_global_vars + list(main_ast.global_vars)
        all_functions = merged_functions + list(main_ast.functions)
        all_windows = merged_windows + list(main_ast.windows)
        all_structs = merged_structs + list(main_ast.structs)
        all_enums = merged_enums + list(main_ast.enums)
        all_extern_funcs = merged_extern_funcs + list(main_ast.extern_funcs)
        all_native_funcs = merged_native_funcs + list(main_ast.native_funcs)

        return Program(
            imports=[],  # Imports are processed, no longer needed
            constants=all_constants,
            global_vars=all_global_vars,
            structs=all_structs,
            enums=all_enums,
            windows=all_windows,
            main=main_ast.main,
            functions=all_functions,
            extern_funcs=all_extern_funcs,
            native_funcs=all_native_funcs,
            headers=main_ast.headers
        )

    def compile(self, source: str, filename: str = "<input>") -> tuple[str, AnalysisResult]:
        """
        Compile Dash source code to C.

        Args:
            source: Dash source code
            filename: Source filename for error messages

        Returns:
            Tuple of (C code string, analysis result)

        Raises:
            CompilationError: If compilation fails
        """
        # Set base directory for import resolution
        if filename != "<input>":
            self._base_dir = os.path.dirname(os.path.abspath(filename))
        else:
            self._base_dir = os.getcwd()

        # Mark main file as loaded to prevent circular imports
        if filename != "<input>":
            self._loaded_modules.add(os.path.abspath(filename))

        # Stage 1 & 2: Parse and transform to AST
        if self.verbose:
            print("Stage 1: Parsing...", file=sys.stderr)

        try:
            ast = self._parse_source(source)
        except Exception as e:
            raise CompilationError(f"Parse error: {e}", stage="parse")

        if not isinstance(ast, Program):
            raise CompilationError(
                f"Parser returned {type(ast).__name__} instead of Program",
                stage="parse"
            )

        if self.verbose:
            print(f"  Parsed: {len(ast.windows)} windows, {len(ast.functions)} functions, "
                  f"{len(ast.imports)} imports", file=sys.stderr)

        # Stage 2.5: Load and merge imports
        if ast.imports:
            if self.verbose:
                print("Stage 1.5: Loading imports...", file=sys.stderr)
            ast = self._merge_modules(ast)
            if self.verbose:
                print(f"  After merge: {len(ast.windows)} windows, {len(ast.functions)} functions",
                      file=sys.stderr)

        # Stage 3: Semantic analysis
        if self.verbose:
            print("Stage 2: Analyzing...", file=sys.stderr)

        analyzer = SemanticAnalyzer()
        analysis = analyzer.analyze(ast)

        # Report warnings
        for warning in analysis.warnings:
            print(f"Warning: {warning}", file=sys.stderr)

        # Report errors and fail if any
        if analysis.has_errors:
            for error in analysis.errors:
                print(f"Error: {error}", file=sys.stderr)
            raise CompilationError(
                f"Semantic analysis failed with {len(analysis.errors)} error(s)",
                stage="analyze"
            )

        if self.verbose:
            print(f"  Analysis complete: {len(analysis.symbol_table)} symbols",
                  file=sys.stderr)

        # Stage 4: Code generation
        if self.verbose:
            print("Stage 3: Generating C code...", file=sys.stderr)

        generator = CodeGenerator(analysis)
        c_code = generator.generate()

        if self.verbose:
            print(f"  Generated {len(c_code)} characters of C code", file=sys.stderr)

        return c_code, analysis

    def _collect_modules(self, main_ast: Program, main_path: str) -> Dict[str, ModuleInfo]:
        """
        Collect all modules (main + imports) without merging them.
        Returns a dict of module_path -> ModuleInfo.
        """
        modules: Dict[str, ModuleInfo] = {}

        def get_module_name(path: str) -> str:
            """Extract module name from path (e.g., 'lib/amiga/audio.dash' -> 'audio')."""
            return os.path.splitext(os.path.basename(path))[0]

        def get_relative_path(full_path: str) -> str:
            """Get path relative to project root."""
            try:
                return os.path.relpath(full_path, self._project_root)
            except ValueError:
                return os.path.basename(full_path)

        def collect_recursive(ast: Program, path: str):
            """Recursively collect module and its dependencies."""
            if path in modules:
                return

            # Get dependencies from imports
            deps = []
            for imp in ast.imports:
                dep_path = self._resolve_import_path(imp.path)
                deps.append(dep_path)

            modules[path] = ModuleInfo(
                name=get_module_name(path),
                path=path,
                relative_path=get_relative_path(path),
                ast=ast,
                dependencies=deps
            )

            # Recursively load dependencies
            for imp in ast.imports:
                dep_path = self._resolve_import_path(imp.path)
                if dep_path not in modules:
                    try:
                        with open(dep_path, "r") as f:
                            source = f.read()
                        dep_ast = self._parse_source(source)
                        collect_recursive(dep_ast, dep_path)
                    except FileNotFoundError:
                        raise CompilationError(f"Import not found: {imp.path}", stage="import")

        # Start collection from main module
        collect_recursive(main_ast, main_path)
        return modules

    def compile_multifile(self, source: str, filename: str = "<input>") -> Dict[str, str]:
        """
        Compile Dash source code to multiple C files.

        Args:
            source: Dash source code
            filename: Source filename

        Returns:
            Dict mapping output filename to C code content.
            Keys are like: "main.c", "main.h", "audio.c", "audio.h", etc.

        Raises:
            CompilationError: If compilation fails
        """
        from compiler.codegen import CodeGenerator, MultiFileGenerator

        # Set base directory for import resolution
        if filename != "<input>":
            self._base_dir = os.path.dirname(os.path.abspath(filename))
            self._project_root = self._find_project_root(self._base_dir)
        else:
            self._base_dir = os.getcwd()
            self._project_root = self._base_dir

        main_path = os.path.abspath(filename) if filename != "<input>" else "<input>"

        # Stage 1: Parse main file
        if self.verbose:
            print("Stage 1: Parsing...", file=sys.stderr)

        try:
            main_ast = self._parse_source(source)
        except Exception as e:
            raise CompilationError(f"Parse error: {e}", stage="parse")

        # Stage 2: Collect all modules (don't merge)
        if self.verbose:
            print("Stage 2: Collecting modules...", file=sys.stderr)

        modules = self._collect_modules(main_ast, main_path)

        if self.verbose:
            print(f"  Found {len(modules)} module(s)", file=sys.stderr)

        # Stage 3: Create merged AST for semantic analysis
        # We still need full analysis to resolve cross-module references
        merged_ast = self._merge_modules(main_ast)

        if self.verbose:
            print("Stage 3: Analyzing...", file=sys.stderr)

        analyzer = SemanticAnalyzer()
        analysis = analyzer.analyze(merged_ast)

        # Report warnings
        for warning in analysis.warnings:
            print(f"Warning: {warning}", file=sys.stderr)

        if analysis.has_errors:
            for error in analysis.errors:
                print(f"Error: {error}", file=sys.stderr)
            raise CompilationError(
                f"Semantic analysis failed with {len(analysis.errors)} error(s)",
                stage="analyze"
            )

        # Stage 4: Generate multi-file output
        if self.verbose:
            print("Stage 4: Generating C files...", file=sys.stderr)

        generator = MultiFileGenerator(analysis, modules, main_path)
        output_files = generator.generate()

        if self.verbose:
            print(f"  Generated {len(output_files)} file(s)", file=sys.stderr)

        return output_files

    def _find_project_root(self, start_dir: str) -> str:
        """Find project root by looking for 'dash' script or 'compiler' directory."""
        current = start_dir
        for _ in range(10):
            if os.path.exists(os.path.join(current, 'dash')) or \
               os.path.exists(os.path.join(current, 'compiler')):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        return start_dir


class CompilationError(Exception):
    """Exception raised during compilation."""

    def __init__(self, message: str, stage: str = "unknown"):
        super().__init__(message)
        self.stage = stage


def transpile(source: str, filename: str = "<input>",
              extended: bool = False, verbose: bool = False) -> str:
    """
    Convenience function to transpile Dash source to C.

    Args:
        source: Dash source code
        filename: Source filename for error messages
        extended: Use extended grammar with future features
        verbose: Print compilation stages

    Returns:
        Generated C code

    Raises:
        CompilationError: If compilation fails
    """
    compiler = DashCompiler(use_extended_grammar=extended, verbose=verbose)
    c_code, _ = compiler.compile(source, filename)
    return c_code


def main():
    """Main entry point for the transpiler CLI."""
    parser = argparse.ArgumentParser(
        description="Dash Language Transpiler - Compiles .dash to C for Amiga"
    )
    parser.add_argument("input_file", help="Input Dash source file (.dash)")
    parser.add_argument("-o", "--output", default="output.c",
                        help="Output C file (.c) or directory for multifile mode")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show compilation stages")
    parser.add_argument("--extended", action="store_true",
                        help="Use extended grammar (experimental)")
    parser.add_argument("--multifile", action="store_true",
                        help="Generate multiple C files (one per module)")
    args = parser.parse_args()

    input_filename = args.input_file
    output_path = args.output

    # Read source file
    try:
        with open(input_filename, "r") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_filename}' not found", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading '{input_filename}': {e}", file=sys.stderr)
        sys.exit(1)

    # Compile
    try:
        compiler = DashCompiler(use_extended_grammar=args.extended, verbose=args.verbose)

        if args.multifile:
            # Multi-file mode: generate separate .c/.h files
            output_files = compiler.compile_multifile(source_code, filename=input_filename)

            # Determine output directory
            if output_path.endswith('.c'):
                output_dir = os.path.dirname(output_path) or '.'
            else:
                output_dir = output_path

            os.makedirs(output_dir, exist_ok=True)

            # Write all generated files
            for filename, content in output_files.items():
                filepath = os.path.join(output_dir, filename)
                with open(filepath, "w") as f:
                    f.write(content)
                if args.verbose:
                    print(f"  Wrote: {filepath}", file=sys.stderr)

            print(f"Transpiled! Generated {len(output_files)} file(s) in '{output_dir}'")
        else:
            # Single-file mode (default)
            c_output, _ = compiler.compile(source_code, filename=input_filename)

            # Write output
            with open(output_path, "w") as f:
                f.write(c_output)

            print(f"Transpiled! C code generated in '{output_path}'")

    except CompilationError as e:
        print(f"Compilation failed at {e.stage} stage: {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
