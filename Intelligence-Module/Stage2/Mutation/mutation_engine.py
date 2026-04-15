"""
Mutation Engine for Stage-2 (Layer 3)

Takes source code and generates N mutated versions using
language-specific operators.

Two mutation paths:
    Python:     ast.parse → operator mutates tree → ast.unparse
    Non-Python: tree-sitter parse → operator finds byte targets → string surgery

Each mutant has exactly ONE change from the original code.

Output per mutant:
    {
        "id": int,
        "operator": str,
        "line": int,
        "description": str,
        "source_code": str (the mutated source)
    }
"""

import ast
import random
import subprocess
import tempfile
import os

from Stage2.Mutation.Operators.operator_factory import get_operators


MAX_MUTANTS = 15
VALIDATE_MUTANTS = True
COMPILE_TIMEOUT = 3


class Mutation_Engine:
    def __init__(self, operators=None, max_mutants=None, language="python"):
        """
        Args:
            operators: list of operator instances (auto-resolved from language if None)
            max_mutants: cap on mutant count
            language: target language for parsing + validation
        """
        self.language = language
        self.operators = operators or get_operators(language)
        self.max_mutants = max_mutants or MAX_MUTANTS

    def generate_mutants(self, source_code, language=None):
        """
        Generates mutated versions of the source code.

        Args:
            source_code: the original source code string
            language: override language (uses self.language if None)

        Returns:
            list of mutant dicts
        """
        lang = language or self.language

        # Re-resolve operators if language was overridden
        if lang != self.language:
            self.operators = get_operators(lang)
            self.language = lang

        if lang == "python":
            return self._generate_python(source_code)
        else:
            return self._generate_treesitter(source_code, lang)

    # ── Python Path (ast-based) ──

    def _generate_python(self, source_code):
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            print(f"    [Mutation Engine] Failed to parse Python source: {e}")
            return []

        all_targets = []
        for operator in self.operators:
            targets = operator.find_targets(tree)
            for target in targets:
                all_targets.append({
                    "operator": operator,
                    "target": target
                })

        if not all_targets:
            print("    [Mutation Engine] No mutation targets found")
            return []

        print(f"    [Mutation Engine] Found {len(all_targets)} possible mutations")

        selected = self.select_targets(all_targets) if len(all_targets) > self.max_mutants else all_targets

        mutants = []
        mutant_id = 0

        for entry in selected:
            operator = entry["operator"]
            target = entry["target"]

            mutant_tree = operator.apply(tree, target)
            if mutant_tree is None:
                continue

            try:
                mutant_code = ast.unparse(mutant_tree)
            except Exception as e:
                print(f"    [Mutation Engine] Unparse failed: {e}")
                continue

            if VALIDATE_MUTANTS and not self._validate_python(mutant_code):
                continue

            mutants.append({
                "id": mutant_id,
                "operator": operator.name,
                "line": target.get("line"),
                "description": operator.describe_mutation(target),
                "source_code": mutant_code
            })
            mutant_id += 1

        print(f"    [Mutation Engine] Generated {len(mutants)} valid mutants")
        return mutants

    # ── Tree-sitter Path (string surgery) ──

    def _generate_treesitter(self, source_code, language):
        tree, source_bytes = self._parse_treesitter(source_code, language)
        if tree is None:
            print(f"    [Mutation Engine] Failed to parse {language} source")
            return []

        all_targets = []
        for operator in self.operators:
            targets = operator.find_targets(tree, source_bytes)
            for target in targets:
                all_targets.append({
                    "operator": operator,
                    "target": target
                })

        if not all_targets:
            print("    [Mutation Engine] No mutation targets found")
            return []

        print(f"    [Mutation Engine] Found {len(all_targets)} possible mutations")

        selected = self.select_targets(all_targets) if len(all_targets) > self.max_mutants else all_targets

        mutants = []
        mutant_id = 0

        for entry in selected:
            operator = entry["operator"]
            target = entry["target"]

            mutant_code = operator.apply(source_bytes, target)
            if mutant_code is None:
                continue

            if VALIDATE_MUTANTS and not self._validate_compiled(mutant_code, language):
                continue

            mutants.append({
                "id": mutant_id,
                "operator": operator.name,
                "line": target.get("line"),
                "description": operator.describe_mutation(target),
                "source_code": mutant_code
            })
            mutant_id += 1

        print(f"    [Mutation Engine] Generated {len(mutants)} valid mutants")
        return mutants

    def _parse_treesitter(self, source_code, language):
        """Parse source using tree-sitter, return (tree, source_bytes)."""
        try:
            from tree_sitter import Language, Parser

            if language in ("javascript", "typescript"):
                if language == "typescript":
                    import tree_sitter_typescript as ts_lang
                    lang = Language(ts_lang.language_typescript())
                else:
                    import tree_sitter_javascript as ts_lang
                    lang = Language(ts_lang.language())
            elif language == "java":
                import tree_sitter_java as ts_lang
                lang = Language(ts_lang.language())
            elif language in ("c", "cpp"):
                import tree_sitter_c as ts_lang
                lang = Language(ts_lang.language())
            else:
                print(f"    [Mutation Engine] No tree-sitter grammar for {language}")
                return None, None

            parser = Parser()
            parser.language = lang
            source_bytes = source_code.encode("utf-8")
            tree = parser.parse(source_bytes)

            if tree and tree.root_node:
                return tree, source_bytes
            return None, None

        except Exception as e:
            print(f"    [Mutation Engine] Tree-sitter parse error: {e}")
            return None, None

    # ── Validation ──

    def _validate_python(self, source_code):
        try:
            compile(source_code, "<mutant>", "exec")
            return True
        except SyntaxError:
            return False

    def _validate_compiled(self, source_code, language):
        """Validate mutant compiles for non-Python languages."""
        suffix_map = {
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "c": ".c",
            "cpp": ".cpp"
        }
        compiler_map = {
            "javascript": ["node", "--check"],
            "typescript": ["tsc", "--noEmit", "--allowJs", "--esModuleInterop"],
            "java": ["javac"],
            "c": ["gcc", "-fsyntax-only"],
            "cpp": ["g++", "-fsyntax-only"]
        }

        suffix = suffix_map.get(language)
        compiler_cmd = compiler_map.get(language)

        if not suffix or not compiler_cmd:
            return True  # Can't validate, assume valid

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix=suffix,
                                             delete=False, encoding='utf-8') as tmp:
                tmp.write(source_code)
                tmp_path = tmp.name

            subprocess.run(
                compiler_cmd + [tmp_path],
                check=True,
                capture_output=True,
                text=True,
                timeout=COMPILE_TIMEOUT
            )
            return True

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

        except Exception:
            return True  # Can't validate, assume valid

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    # ── Target Selection (unchanged) ──

    def select_targets(self, all_targets):
        by_operator = {}
        for entry in all_targets:
            name = entry["operator"].name
            if name not in by_operator:
                by_operator[name] = []
            by_operator[name].append(entry)

        num_operators = len(by_operator)
        per_operator = self.max_mutants // num_operators
        remainder = self.max_mutants % num_operators

        selected = []
        leftover_budget = 0

        for name, targets in by_operator.items():
            budget = per_operator + (1 if remainder > 0 else 0)
            remainder = max(0, remainder - 1)
            budget += leftover_budget
            leftover_budget = 0

            if len(targets) <= budget:
                selected.extend(targets)
                leftover_budget = budget - len(targets)
            else:
                selected.extend(random.sample(targets, budget))

        return selected[:self.max_mutants]

    # ── Placeholders ──

    def detect_equivalent_mutants(self, original_code, mutant_code):
        raise NotImplementedError

    def generate_higher_order_mutants(self, source_code, order=2):
        raise NotImplementedError