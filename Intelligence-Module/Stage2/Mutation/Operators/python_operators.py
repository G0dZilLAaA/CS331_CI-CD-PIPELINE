"""
Python Mutation Operators — ast-based.

Moved from mutant_operators.py.
All operators and ACTIVE_OPERATORS list preserved exactly.
"""

import ast
import copy


class Base_Mutant_Operator:
    name = "base"
    description = "base operator"

    def find_targets(self, tree):
        raise NotImplementedError

    def apply(self, tree, target):
        raise NotImplementedError

    def describe_mutation(self, target):
        raise NotImplementedError


OP_NAMES = {
    ast.Lt: "<", ast.LtE: "<=",
    ast.Gt: ">", ast.GtE: ">=",
    ast.Eq: "==", ast.NotEq: "!=",
    ast.Add: "+", ast.Sub: "-",
    ast.Mult: "*", ast.Div: "/",
    ast.FloorDiv: "//", ast.Mod: "%",
}


RELATIONAL_SWAPS = {
    ast.Lt:    [ast.LtE, ast.Gt, ast.GtE],
    ast.LtE:   [ast.Lt, ast.Gt, ast.GtE],
    ast.Gt:    [ast.GtE, ast.Lt, ast.LtE],
    ast.GtE:   [ast.Gt, ast.Lt, ast.LtE],
    ast.Eq:    [ast.NotEq],
    ast.NotEq: [ast.Eq],
}


class Relational_Swap(Base_Mutant_Operator):
    name = "relational_swap"
    description = "Swaps relational comparison operators"

    def find_targets(self, tree):
        targets = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                for i, op in enumerate(node.ops):
                    if type(op) in RELATIONAL_SWAPS:
                        for swap_to in RELATIONAL_SWAPS[type(op)]:
                            targets.append({
                                "node": node,
                                "op_index": i,
                                "original_op": type(op),
                                "mutated_op": swap_to,
                                "line": node.lineno
                            })
        return targets

    def apply(self, tree, target):
        mutant_tree = copy.deepcopy(tree)
        for node in ast.walk(mutant_tree):
            if isinstance(node, ast.Compare) and node.lineno == target["line"]:
                if target["op_index"] < len(node.ops):
                    if type(node.ops[target["op_index"]]) == target["original_op"]:
                        node.ops[target["op_index"]] = target["mutated_op"]()
                        return mutant_tree
        return None

    def describe_mutation(self, target):
        orig = OP_NAMES.get(target["original_op"], "?")
        mutated = OP_NAMES.get(target["mutated_op"], "?")
        return f"Line {target['line']}: Changed {orig} to {mutated}"


ARITHMETIC_SWAPS = {
    ast.Add:      [ast.Sub],
    ast.Sub:      [ast.Add],
    ast.Mult:     [ast.Div],
    ast.Div:      [ast.Mult],
    ast.FloorDiv: [ast.Mod],
    ast.Mod:      [ast.FloorDiv],
}


class Arithmetic_Swap(Base_Mutant_Operator):
    name = "arithmetic_swap"
    description = "Swaps arithmetic operators"

    def find_targets(self, tree):
        targets = []
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                if type(node.op) in ARITHMETIC_SWAPS:
                    for swap_to in ARITHMETIC_SWAPS[type(node.op)]:
                        targets.append({
                            "node": node,
                            "original_op": type(node.op),
                            "mutated_op": swap_to,
                            "line": node.lineno
                        })
        return targets

    def apply(self, tree, target):
        mutant_tree = copy.deepcopy(tree)
        for node in ast.walk(mutant_tree):
            if isinstance(node, ast.BinOp) and node.lineno == target["line"]:
                if type(node.op) == target["original_op"]:
                    node.op = target["mutated_op"]()
                    return mutant_tree
        return None

    def describe_mutation(self, target):
        orig = OP_NAMES.get(target["original_op"], "?")
        mutated = OP_NAMES.get(target["mutated_op"], "?")
        return f"Line {target['line']}: Changed {orig} to {mutated}"


class Conditional_Negate(Base_Mutant_Operator):
    name = "conditional_negate"
    description = "Negates if-statement conditions"

    def find_targets(self, tree):
        targets = []
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                targets.append({"node": node, "line": node.lineno})
        return targets

    def apply(self, tree, target):
        mutant_tree = copy.deepcopy(tree)
        for node in ast.walk(mutant_tree):
            if isinstance(node, ast.If) and node.lineno == target["line"]:
                node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
                ast.fix_missing_locations(mutant_tree)
                return mutant_tree
        return None

    def describe_mutation(self, target):
        return f"Line {target['line']}: Negated if-condition"


class Boundary_Mutate(Base_Mutant_Operator):
    name = "boundary_mutate"
    description = "Shifts integer constants by ±1"

    def find_targets(self, tree):
        targets = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, int):
                targets.append({
                    "node": node,
                    "original_value": node.value,
                    "mutated_value": node.value + 1,
                    "line": node.lineno
                })
                targets.append({
                    "node": node,
                    "original_value": node.value,
                    "mutated_value": node.value - 1,
                    "line": node.lineno
                })
        return targets

    def apply(self, tree, target):
        mutant_tree = copy.deepcopy(tree)
        for node in ast.walk(mutant_tree):
            if (isinstance(node, ast.Constant)
                    and isinstance(node.value, int)
                    and node.lineno == target["line"]
                    and node.value == target["original_value"]):
                node.value = target["mutated_value"]
                return mutant_tree
        return None

    def describe_mutation(self, target):
        return (
            f"Line {target['line']}: "
            f"Changed {target['original_value']} to {target['mutated_value']}"
        )


class Return_Mutate(Base_Mutant_Operator):
    name = "return_mutate"
    description = "Replaces return values with None"

    def find_targets(self, tree):
        targets = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Return) and node.value is not None:
                targets.append({"node": node, "line": node.lineno})
        return targets

    def apply(self, tree, target):
        mutant_tree = copy.deepcopy(tree)
        for node in ast.walk(mutant_tree):
            if isinstance(node, ast.Return) and node.lineno == target["line"]:
                if node.value is not None:
                    node.value = ast.Constant(value=None)
                    ast.fix_missing_locations(mutant_tree)
                    return mutant_tree
        return None

    def describe_mutation(self, target):
        return f"Line {target['line']}: Changed return value to None"


ACTIVE_OPERATORS = [
    Relational_Swap(),
    Arithmetic_Swap(),
    Conditional_Negate(),
    Boundary_Mutate(),
    Return_Mutate(),
]