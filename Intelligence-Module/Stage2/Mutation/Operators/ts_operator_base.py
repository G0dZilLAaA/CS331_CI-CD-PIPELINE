"""
Tree-Sitter Mutation Operator Base

All non-Python operators use tree-sitter for AST parsing
and string surgery for mutation (tree-sitter trees are immutable).

Mutation approach:
    1. Parse source → tree
    2. Walk tree to find target nodes
    3. Replace target node's source text using byte offsets
    4. Return mutated source string

This avoids needing an unparser — we work directly on the source string.
"""


class TS_Operator_Base:
    name = "base"
    description = "base tree-sitter operator"

    def find_targets(self, tree, source_bytes):
        """
        Find all mutable targets in the tree.

        Args:
            tree: tree-sitter tree object
            source_bytes: source code as bytes

        Returns:
            list of target dicts, each must contain:
                - "start_byte": int
                - "end_byte": int
                - "line": int (1-indexed)
                - operator-specific fields
        """
        raise NotImplementedError

    def apply(self, source_bytes, target):
        """
        Apply mutation by string surgery.

        Args:
            source_bytes: original source as bytes
            target: target dict from find_targets

        Returns:
            mutated source as string, or None if failed
        """
        raise NotImplementedError

    def describe_mutation(self, target):
        raise NotImplementedError

    def replace_bytes(self, source_bytes, start, end, replacement):
        """Replace a byte range in source with replacement string."""
        return (source_bytes[:start] + replacement.encode("utf-8") + source_bytes[end:]).decode("utf-8")

    def walk(self, node):
        """Yield all nodes via DFS."""
        yield node
        for child in node.children:
            yield from self.walk(child)

    def node_text(self, node, source_bytes):
        """Get source text for a node."""
        return source_bytes[node.start_byte:node.end_byte].decode("utf-8")