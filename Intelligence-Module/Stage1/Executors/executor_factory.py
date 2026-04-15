"""
Executor Factory — dispatches to the correct executor based on language.

Usage:
    from Stage1.Executors.executor_factory import get_executor
    executor = get_executor("javascript")
    results, coverage = executor.run(source_code, tests, execution_model)
"""

from Stage1.Executors.python_executor import PythonExecutor
from Stage1.Executors.js_ts_executor import JSTSExecutor
from Stage1.Executors.java_executor import JavaExecutor
from Stage1.Executors.c_cpp_executor import CCppExecutor


def get_executor(language: str):
    """
    Returns the appropriate executor instance for the given language.

    Args:
        language: one of "python", "javascript", "typescript", "java", "c", "cpp"

    Returns:
        ExecutorBase subclass instance

    Raises:
        ValueError: if language is not supported
    """
    if language == "python":
        return PythonExecutor()

    elif language == "javascript":
        return JSTSExecutor("javascript")

    elif language == "typescript":
        return JSTSExecutor("typescript")

    elif language == "java":
        return JavaExecutor()

    elif language in ("c", "cpp"):
        return CCppExecutor(language)

    else:
        raise ValueError(f"No executor available for language: {language}")