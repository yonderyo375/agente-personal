"""Calculadora segura para expresiones matemáticas."""
import ast
import math
import operator

ALLOWED_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg,
}

def _safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.n
    elif isinstance(node, ast.BinOp):
        op = ALLOWED_OPS.get(type(node.op))
        if not op:
            raise ValueError(f"Operador no permitido: {node.op}")
        return op(_safe_eval(node.left), _safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp):
        op = ALLOWED_OPS.get(type(node.op))
        if not op:
            raise ValueError("Operador unario no permitido")
        return op(_safe_eval(node.operand))
    elif isinstance(node, ast.Call):
        func_name = node.func.id if isinstance(node.func, ast.Name) else None
        allowed_funcs = {"sqrt": math.sqrt, "abs": abs, "round": round,
                         "sin": math.sin, "cos": math.cos, "tan": math.tan,
                         "log": math.log, "log10": math.log10, "pi": math.pi}
        if func_name in allowed_funcs:
            args = [_safe_eval(a) for a in node.args]
            return allowed_funcs[func_name](*args)
    raise ValueError(f"Expresión no permitida: {ast.dump(node)}")

def calculate(expression: str) -> str:
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error calculando '{expression}': {e}"
