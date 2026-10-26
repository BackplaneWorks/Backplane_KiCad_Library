#!/usr/bin/env python
"""
Miscellaneous tools that are on itself unrelated footprints/3d
"""

import ast
import string
from dataclasses import asdict, is_dataclass
from typing import Any


def eval_ast_node(node, context: dict) -> Any:
    if isinstance(node, ast.Name):
        return context[node.id]
    elif isinstance(node, ast.Attribute):
        value = eval_ast_node(node.value, context)
        return getattr(value, node.attr)
    elif isinstance(node, ast.Subscript):
        value = eval_ast_node(node.value, context)
        key = (
            eval_ast_node(node.slice, context)
            if isinstance(node.slice, ast.Index)
            else eval_ast_node(node.slice.value, context)
        )
        return value[key]
    elif isinstance(node, ast.Call):
        func = eval_ast_node(node.func, context)
        args = [eval_ast_node(arg, context) for arg in node.args]
        kwargs = {kw.arg: eval_ast_node(kw.value, context) for kw in node.keywords}
        return func(*args, **kwargs)
    elif isinstance(node, ast.BinOp):
        left = eval_ast_node(node.left, context)
        right = eval_ast_node(node.right, context)
        return eval_binop(node.op, left, right)
    elif isinstance(node, ast.Constant):
        return node.value
    else:
        raise ValueError(f"Unsupported expression node: {ast.dump(node)}")


def eval_binop(op, left, right):
    if isinstance(op, ast.Add):
        return left + right
    elif isinstance(op, ast.Sub):
        return left - right
    elif isinstance(op, ast.Mult):
        return left * right
    elif isinstance(op, ast.Div):
        return left / right
    elif isinstance(op, ast.FloorDiv):
        return left // right
    elif isinstance(op, ast.Mod):
        return left % right
    elif isinstance(op, ast.Pow):
        return left**right
    else:
        raise ValueError(f"Unsupported binary operator: {type(op)}")


def formatString(obj: Any, strformat: str) -> str:
    """
    Format a formatted string using an object (dataclass or class),
    supporting method calls in placeholders like {field.lower()}.
    """
    if is_dataclass(obj):
        context = asdict(obj)
    elif hasattr(obj, "__dict__"):
        context = vars(obj)
    else:
        raise TypeError("Object must be a dataclass or class instance")
    strdata = string.Formatter().parse(strformat)
    result_parts = []

    for literal_text, field_expr, format_spec, conversion in strdata:
        result_parts.append(literal_text)
        if field_expr:
            # value = evaluate_field_expr(field_expr, context)
            try:
                node = ast.parse(field_expr, mode="eval").body
                value = eval_ast_node(node, context)
            except Exception as e:
                raise ValueError(f"Failed to evaluate expression '{field_expr}': {e}")

            # Handle conversions like !s, !r, !a
            if conversion == "s":
                value = str(value)
            elif conversion == "r":
                value = repr(value)
            elif conversion == "a":
                value = ascii(value)

            # Apply format spec (like :.2f)
            if format_spec:
                value = format(value, format_spec)

            result_parts.append(str(value))

    return "".join(result_parts)
