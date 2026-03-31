"""
Dash Language Compiler Package

A transpiler that converts Dash source code to C for Amiga.
"""
__version__ = "2.0.0"
__all__ = ["DashCompiler", "transpile", "CompilationError"]

def __getattr__(name):
    """Lazy import to avoid circular imports when running as module."""
    if name in ("DashCompiler", "transpile", "CompilationError"):
        from compiler.main import DashCompiler, transpile, CompilationError
        globals()["DashCompiler"] = DashCompiler
        globals()["transpile"] = transpile
        globals()["CompilationError"] = CompilationError
        return globals()[name]
    raise AttributeError(f"module 'compiler' has no attribute {name!r}")
