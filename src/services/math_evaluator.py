"""Math Notes service for Mis Apuntes.

Evaluates mathematical expressions and variable assignments in real-time
as typed in notes (macOS Sequoia Math Notes feature). Uses safe AST parsing.
"""

import ast
import math
import operator
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


class MathEvaluator:
    """Safe AST-based math evaluator supporting arithmetic, math functions, and variables."""

    def __init__(self) -> None:
        self.allowed_operators: Dict[type, Callable[..., Any]] = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        self.allowed_functions: Dict[str, Any] = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "pi": math.pi,
            "e": math.e,
        }

    def _eval_ast_node(
        self, node: ast.AST, variables: Dict[str, Union[int, float]]
    ) -> Union[int, float]:
        """Recursively evaluates an AST node securely."""
        if isinstance(node, ast.Expression):
            return self._eval_ast_node(node.body, variables)

        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return (
                float(node.value) if isinstance(node.value, float) else int(node.value)
            )

        if isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]
            if node.id in self.allowed_functions and isinstance(
                self.allowed_functions[node.id], (int, float)
            ):
                val = self.allowed_functions[node.id]
                return float(val) if isinstance(val, float) else int(val)
            raise ValueError(f"Variable no definida: {node.id}")

        if isinstance(node, ast.UnaryOp):
            un_op_cls = type(node.op)
            if un_op_cls in self.allowed_operators:
                operand = self._eval_ast_node(node.operand, variables)
                res_un = self.allowed_operators[un_op_cls](operand)
                return float(res_un) if isinstance(res_un, float) else int(res_un)
            raise ValueError("Operador unario no soportado")

        if isinstance(node, ast.BinOp):
            bin_op_cls = type(node.op)
            if bin_op_cls in self.allowed_operators:
                left = self._eval_ast_node(node.left, variables)
                right = self._eval_ast_node(node.right, variables)
                res_bin = self.allowed_operators[bin_op_cls](left, right)
                return float(res_bin) if isinstance(res_bin, float) else int(res_bin)
            raise ValueError("Operador binario no soportado")

        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Name)
                and node.func.id in self.allowed_functions
            ):
                func = self.allowed_functions[node.func.id]
                if callable(func):
                    args = [self._eval_ast_node(arg, variables) for arg in node.args]
                    res_call = func(*args)
                    return (
                        float(res_call)
                        if isinstance(res_call, float)
                        else int(res_call)
                    )
            raise ValueError("Función no permitida")

        raise ValueError("Expresión no soportada")

    def evaluate_expr(
        self, expr_str: str, variables: Optional[Dict[str, Union[int, float]]] = None
    ) -> Optional[Union[int, float]]:
        """Evaluates a math expression string safely."""
        if variables is None:
            variables = {}

        cleaned_expr = expr_str.replace("^", "**").strip()
        if not cleaned_expr:
            return None

        try:
            parsed = ast.parse(cleaned_expr, mode="eval")
            res = self._eval_ast_node(parsed, variables)
            if isinstance(res, float) and res.is_integer():
                return int(res)
            return round(res, 4) if isinstance(res, float) else res
        except Exception:
            return None

    def process_note_text(self, text: str) -> Tuple[str, bool]:
        """Scans lines for variable assignments and equations ending with '=', evaluating them."""
        lines = text.splitlines()
        modified = False
        variables: Dict[str, Union[int, float]] = {}

        new_lines: List[str] = []
        for line in lines:
            stripped = line.strip()

            assign_match = re.match(
                r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^=]+)$", stripped
            )
            if assign_match:
                var_name, var_expr = assign_match.groups()
                val = self.evaluate_expr(var_expr, variables)
                if val is not None:
                    variables[var_name] = val

            if stripped.endswith("=") and not stripped.endswith("=="):
                expr_part = stripped[:-1].strip()

                if "=" in expr_part:
                    var_target, math_expr = expr_part.split("=", 1)
                    var_target = var_target.strip()
                    val = self.evaluate_expr(math_expr.strip(), variables)
                    if val is not None:
                        if var_target:
                            variables[var_target] = val
                        line = f"{line} {val}"
                        modified = True
                else:
                    val = self.evaluate_expr(expr_part, variables)
                    if val is not None:
                        line = f"{line} {val}"
                        modified = True

            new_lines.append(line)

        return "\n".join(new_lines), modified
