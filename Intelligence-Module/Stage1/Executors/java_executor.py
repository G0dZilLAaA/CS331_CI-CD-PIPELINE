"""
Java Executor — compiles via javac, runs via java subprocess.

Coverage: approximate (all executable lines on success).
Future: jacoco instrumentation for precise coverage.
"""

import subprocess
import tempfile
import os
import re
import json
import time
from Stage1.config import TEST_TIMEOUT
from Stage1.Executors.executor_base import ExecutorBase


class JavaExecutor(ExecutorBase):

    def execute_callable(self, source_code, tests):
        results = []
        all_executed_lines = set()

        for ind, test in enumerate(tests):
            method_name = test.get("method_name")
            test_input = test.get("input", [])

            wrapper = self.build_callable_wrapper(source_code, method_name, test_input)
            result = self.compile_and_run(wrapper)
            result["test_id"] = ind

            per_test_lines = result.pop("executed_lines", set())
            all_executed_lines.update(per_test_lines)
            result["per_test_executed_lines"] = per_test_lines
            results.append(result)

        return results, all_executed_lines

    def execute_stdin(self, source_code, tests):
        results = []
        all_executed_lines = set()

        for ind, test in enumerate(tests):
            fake_input = test.get("input", "")

            result = self.compile_and_run(source_code, stdin_input=fake_input)
            result["test_id"] = ind

            per_test_lines = result.pop("executed_lines", set())
            all_executed_lines.update(per_test_lines)
            result["per_test_executed_lines"] = per_test_lines
            results.append(result)

        return results, all_executed_lines

    def execute_script(self, source_code):
        result = self.compile_and_run(source_code)
        result["test_id"] = 0

        per_test_lines = result.pop("executed_lines", set())
        result["per_test_executed_lines"] = per_test_lines

        return [result], per_test_lines

    def build_callable_wrapper(self, source_code, method_name, test_input):
        """
        Build a Java wrapper that instantiates Solution class,
        calls the method, and prints JSON output.
        """
        # Serialize args as Java literals (simplified)
        args_str = ", ".join(self.java_literal(arg) for arg in test_input)

        # Extract the class body (remove public class declaration wrapper if needed)
        wrapper = f"""
{source_code}

class TestHarness {{
    public static void main(String[] args) {{
        try {{
            Solution instance = new Solution();
            Object result = instance.{method_name}({args_str});
            System.out.println(result);
        }} catch (Exception e) {{
            System.err.println("__EXCEPTION__:" + e.getMessage());
            System.exit(1);
        }}
    }}
}}
"""
        return wrapper

    def java_literal(self, value):
        """Convert a Python value to a Java literal string (best effort)."""
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, float):
            return str(value)
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, list):
            inner = ", ".join(self.java_literal(v) for v in value)
            return f"new int[]{{{inner}}}"
        else:
            return str(value)

    def compile_and_run(self, code, stdin_input=None):
        """Compile Java source, then run the resulting class."""
        tmp_dir = None
        start = time.time()

        try:
            tmp_dir = tempfile.mkdtemp()

            # Extract class name from source
            class_name = self.extract_main_class(code)
            if not class_name:
                class_name = "TestHarness"

            src_path = os.path.join(tmp_dir, f"{class_name}.java")
            with open(src_path, 'w', encoding='utf-8') as f:
                f.write(code)

            # Compile
            compile_proc = subprocess.run(
                ["javac", src_path],
                capture_output=True, text=True,
                timeout=TEST_TIMEOUT, cwd=tmp_dir
            )

            if compile_proc.returncode != 0:
                return {
                    "status": "exception",
                    "output": None,
                    "error": f"Compilation failed: {compile_proc.stderr.strip()}",
                    "runtime": time.time() - start,
                    "executed_lines": set(),
                    "called_operations": []
                }

            # Run
            run_proc = subprocess.run(
                ["java", "-cp", tmp_dir, class_name],
                input=stdin_input,
                capture_output=True, text=True,
                timeout=TEST_TIMEOUT
            )

            runtime = time.time() - start

            if run_proc.returncode != 0:
                stderr = run_proc.stderr.strip()
                if "__EXCEPTION__:" in stderr:
                    error_msg = stderr.split("__EXCEPTION__:")[-1].strip()
                    return {
                        "status": "exception",
                        "output": None,
                        "error": error_msg,
                        "runtime": runtime,
                        "executed_lines": set(),
                        "called_operations": []
                    }
                return {
                    "status": "crash",
                    "output": None,
                    "error": stderr,
                    "runtime": runtime,
                    "executed_lines": set(),
                    "called_operations": []
                }

            stdout = run_proc.stdout.strip()

            # Try parsing output
            output = stdout
            try:
                output = json.loads(stdout)
            except (json.JSONDecodeError, ValueError):
                pass

            executed_lines = self.approximate_coverage(code)

            return {
                "status": "success",
                "output": output,
                "error": None,
                "runtime": runtime,
                "executed_lines": executed_lines,
                "called_operations": []
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "output": None,
                "error": f"Execution exceeded {TEST_TIMEOUT} seconds",
                "runtime": time.time() - start,
                "executed_lines": set(),
                "called_operations": []
            }

        except Exception as e:
            return {
                "status": "crash",
                "output": None,
                "error": str(e),
                "runtime": time.time() - start,
                "executed_lines": set(),
                "called_operations": []
            }

        finally:
            if tmp_dir and os.path.exists(tmp_dir):
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def extract_main_class(self, code):
        """Extract the class name that contains main() or first public class."""
        # Look for class with main
        match = re.search(r'class\s+(\w+)\s*\{[^}]*public\s+static\s+void\s+main', code, re.DOTALL)
        if match:
            return match.group(1)
        # Fallback: first public class
        match = re.search(r'public\s+class\s+(\w+)', code)
        if match:
            return match.group(1)
        # Fallback: any class
        match = re.search(r'class\s+(\w+)', code)
        if match:
            return match.group(1)
        return None

    def approximate_coverage(self, code):
        lines = set()
        in_block_comment = False
        for i, line in enumerate(code.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("/*"):
                in_block_comment = True
            if in_block_comment:
                if "*/" in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith("//"):
                continue
            lines.add(i)
        return lines