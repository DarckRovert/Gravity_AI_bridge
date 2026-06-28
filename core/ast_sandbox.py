import ast
import logging

log = logging.getLogger("gravity.ast_sandbox")

# Lista de módulos peligrosos que podrían permitir RCE, escape del sandbox o robo de info
BANNED_MODULES = {
    "os", "sys", "subprocess", "shutil", "socket", "pty", "pathlib", 
    "threading", "multiprocessing", "importlib", "ctypes", "builtins"
}

# Lista de built-ins peligrosos que permiten inyección o manipulación del runtime
BANNED_BUILTINS = {
    "eval", "exec", "compile", "open", "__import__", "getattr", "setattr", "delattr",
    "globals", "locals", "vars", "dir"
}

class SecurityASTVisitor(ast.NodeVisitor):
    def __init__(self):
        self.is_safe = True
        self.reason = ""

    def fail(self, reason: str):
        self.is_safe = False
        self.reason = reason

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            base_module = alias.name.split('.')[0]
            if base_module in BANNED_MODULES:
                self.fail(f"Uso de módulo prohibido: {base_module}")
                return
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_module = node.module.split('.')[0]
            if base_module in BANNED_MODULES:
                self.fail(f"Uso de módulo prohibido: {base_module}")
                return
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in BANNED_BUILTINS:
                self.fail(f"Uso de built-in prohibido: {node.func.id}()")
                return
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in BANNED_BUILTINS:
                self.fail(f"Uso de atributo prohibido: .{node.func.attr}()")
                return
        self.generic_visit(node)

def is_code_safe(code: str) -> tuple[bool, str]:
    """
    Analiza estáticamente un código fuente en Python buscando operaciones peligrosas.
    Retorna (True, "") si es seguro, o (False, razon) si contiene operaciones prohibidas.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Error de sintaxis en el código: {e}"

    visitor = SecurityASTVisitor()
    visitor.visit(tree)

    return visitor.is_safe, visitor.reason
