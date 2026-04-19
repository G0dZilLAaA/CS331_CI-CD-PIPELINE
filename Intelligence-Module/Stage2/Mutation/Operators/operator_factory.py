"""
Operator Factory — returns the correct operator set for a language.

Usage:
    from Stage2.Mutation.Operators.operator_factory import get_operators
    operators = get_operators("javascript")
"""

from Stage2.Mutation.Operators.python_operators import ACTIVE_OPERATORS as ACTIVE_OPERATORS_PY
from Stage2.Mutation.Operators.js_ts_operators import ACTIVE_OPERATORS_JS
from Stage2.Mutation.Operators.java_operators import ACTIVE_OPERATORS_JAVA
from Stage2.Mutation.Operators.c_cpp_operators import ACTIVE_OPERATORS_C


def get_operators(language: str):
    """
    Returns list of active mutation operator instances for the given language.

    Args:
        language: one of "python", "javascript", "typescript", "java", "c", "cpp"

    Returns:
        list of operator instances

    Raises:
        ValueError: if language is not supported
    """
    if language == "python":
        return ACTIVE_OPERATORS_PY

    elif language in ("javascript", "typescript"):
        return ACTIVE_OPERATORS_JS

    elif language == "java":
        return ACTIVE_OPERATORS_JAVA

    elif language in ("c", "cpp"):
        return ACTIVE_OPERATORS_C

    else:
        raise ValueError(f"No mutation operators available for language: {language}")