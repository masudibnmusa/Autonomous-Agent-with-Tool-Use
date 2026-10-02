"""Safe arithmetic evaluator (no eval)."""
import ast
import math
import operator

from app.tools.base_tool import BaseTool, ToolError

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.USub: operator.neg, ast.UAdd: operator.pos}
_FUNCS = {
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10, "exp": math.exp,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "abs": abs, "round": round, "min": min, "max": max,
}
_CONSTS = {"pi": math.pi, "e": math.e}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name) and node.id in _CONSTS:
        return _CONSTS[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ToolError("Exponent too large.")
        return _BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS:
        return _FUNCS[node.func.id](*[_eval(a) for a in node.args])
    raise ToolError("Unsupported expression.")


class CalculatorTool(BaseTool):
    name = "calculator"
    description = (
        "Evaluate a math expression exactly. Supports + - * / // % **, parentheses, "
        "sqrt, log, log10, exp, sin, cos, tan, abs, round, min, max, and constants pi, e."
    )
    input_schema = {
        "type": "object",
        "properties": {"expression": {"type": "string", "description": "e.g. '(12.5 * 4) / 3'"}},
        "required": ["expression"],
    }

    def run(self, expression: str) -> str:
        try:
            tree = ast.parse(expression, mode="eval")
            return str(_eval(tree))
        except ToolError:
            raise
        except ZeroDivisionError:
            raise ToolError("Division by zero.")
        except (SyntaxError, ValueError, TypeError, OverflowError) as e:
            raise ToolError(f"Could not evaluate expression: {e}")