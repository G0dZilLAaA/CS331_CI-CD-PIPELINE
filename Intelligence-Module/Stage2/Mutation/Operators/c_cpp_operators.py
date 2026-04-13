"""
C/C++ Mutation Operators — tree-sitter + string surgery.

Same mutation concepts, C/C++-specific node types.
"""

from Stage2.Mutation.Operators.ts_operator_base import TS_Operator_Base


RELATIONAL_SWAPS = {
    "<":  ["<=", ">", ">="],
    "<=": ["<", ">", ">="],
    ">":  [">=", "<", "<="],
    ">=": [">", "<", "<="],
    "==": ["!="],
    "!=": ["=="],
}

ARITHMETIC_SWAPS = {
    "+": ["-"],
    "-": ["+"],
    "*": ["/"],
    "/": ["*"],
    "%": ["*"],
}


class C_Relational_Swap(TS_Operator_Base):
    name = "relational_swap"
    description = "Swaps relational comparison operators (C/C++)"

    def find_targets(self, tree, source_bytes):
        targets = []
        for node in self._walk(tree.root_node):
            if node.type == "binary_expression":
                for child in node.children:
                    text = self._node_text(child, source_bytes)
                    if text in RELATIONAL_SWAPS:
                        for swap_to in RELATIONAL_SWAPS[text]:
                            targets.append({
                                "start_byte": child.start_byte,
                                "end_byte": child.end_byte,
                                "original": text,
                                "replacement": swap_to,
                                "line": child.start_point[0] + 1
                            })
        return targets

    def apply(self, source_bytes, target):
        return self._replace_bytes(
            source_bytes, target["start_byte"], target["end_byte"], target["replacement"]
        )

    def describe_mutation(self, target):
        return f"Line {target['line']}: Changed {target['original']} to {target['replacement']}"


class C_Arithmetic_Swap(TS_Operator_Base):
    name = "arithmetic_swap"
    description = "Swaps arithmetic operators (C/C++)"

    def find_targets(self, tree, source_bytes):
        targets = []
        for node in self._walk(tree.root_node):
            if node.type == "binary_expression":
                for child in node.children:
                    text = self._node_text(child, source_bytes)
                    if text in ARITHMETIC_SWAPS:
                        for swap_to in ARITHMETIC_SWAPS[text]:
                            targets.append({
                                "start_byte": child.start_byte,
                                "end_byte": child.end_byte,
                                "original": text,
                                "replacement": swap_to,
                                "line": child.start_point[0] + 1
                            })
        return targets

    def apply(self, source_bytes, target):
        return self._replace_bytes(
            source_bytes, target["start_byte"], target["end_byte"], target["replacement"]
        )

    def describe_mutation(self, target):
        return f"Line {target['line']}: Changed {target['original']} to {target['replacement']}"


class C_Conditional_Negate(TS_Operator_Base):
    name = "conditional_negate"
    description = "Negates if-statement conditions (C/C++)"

    def find_targets(self, tree, source_bytes):
        targets = []
        for node in self._walk(tree.root_node):
            if node.type == "if_statement":
                for child in node.children:
                    if child.type == "parenthesized_expression":
                        inner = self._node_text(child, source_bytes)
                        targets.append({
                            "start_byte": child.start_byte,
                            "end_byte": child.end_byte,
                            "original": inner,
                            "replacement": f"(!{inner})" if not inner.startswith("(!") else inner[2:-1],
                            "line": child.start_point[0] + 1
                        })
        return targets

    def apply(self, source_bytes, target):
        return self._replace_bytes(
            source_bytes, target["start_byte"], target["end_byte"], target["replacement"]
        )

    def describe_mutation(self, target):
        return f"Line {target['line']}: Negated if-condition"


class C_Boundary_Mutate(TS_Operator_Base):
    name = "boundary_mutate"
    description = "Shifts integer constants by ±1 (C/C++)"

    def find_targets(self, tree, source_bytes):
        targets = []
        for node in self._walk(tree.root_node):
            if node.type == "number_literal":
                text = self._node_text(node, source_bytes)
                try:
                    value = int(text)
                except ValueError:
                    continue

                targets.append({
                    "start_byte": node.start_byte,
                    "end_byte": node.end_byte,
                    "original_value": value,
                    "mutated_value": value + 1,
                    "line": node.start_point[0] + 1
                })
                targets.append({
                    "start_byte": node.start_byte,
                    "end_byte": node.end_byte,
                    "original_value": value,
                    "mutated_value": value - 1,
                    "line": node.start_point[0] + 1
                })
        return targets

    def apply(self, source_bytes, target):
        return self._replace_bytes(
            source_bytes, target["start_byte"], target["end_byte"], str(target["mutated_value"])
        )

    def describe_mutation(self, target):
        return f"Line {target['line']}: Changed {target['original_value']} to {target['mutated_value']}"


class C_Return_Mutate(TS_Operator_Base):
    name = "return_mutate"
    description = "Replaces return values with 0 (C/C++)"

    def find_targets(self, tree, source_bytes):
        targets = []
        for node in self._walk(tree.root_node):
            if node.type == "return_statement":
                children = [c for c in node.children if c.type not in ("return", ";")]
                if children:
                    val_node = children[0]
                    text = self._node_text(val_node, source_bytes)
                    if text != "0":
                        targets.append({
                            "start_byte": val_node.start_byte,
                            "end_byte": val_node.end_byte,
                            "original": text,
                            "line": node.start_point[0] + 1
                        })
        return targets

    def apply(self, source_bytes, target):
        return self._replace_bytes(
            source_bytes, target["start_byte"], target["end_byte"], "0"
        )

    def describe_mutation(self, target):
        return f"Line {target['line']}: Changed return value to 0"


ACTIVE_OPERATORS_C = [
    C_Relational_Swap(),
    C_Arithmetic_Swap(),
    C_Conditional_Negate(),
    C_Boundary_Mutate(),
    C_Return_Mutate(),
]