"""
Cost Modes Configuration

Defines three pipeline execution presets: fast, balanced, thorough.
Each mode sets four parameters that control cost/accuracy tradeoff:

    max_iterations:     Agent loop iterations in Stage 1 (controls test generation depth)
    max_tests_per_call: Tests generated per LLM call in Stage 1
    gemini_model:       LLM model identifier for all LLM calls
    max_mutants:        Mutant count for Stage 2 mutation testing

Usage:
    from cost_modes import get_mode
    config = get_mode("balanced")
    # config["max_iterations"] → value

Future:
    Values to be derived from a formula based on code structural
    features using Clopper-Pearson (mutants) and Musa Logarithmic
    Model (iterations). Currently placeholder values.
"""


MODES = {
    "fast": {
        "max_iterations": None,        # TODO: fill
        "max_tests_per_call": None,    # TODO: fill
        "gemini_model": None,          # TODO: fill
        "max_mutants": None,           # TODO: fill
    },
    "balanced": {
        "max_iterations": None,        # TODO: fill
        "max_tests_per_call": None,    # TODO: fill
        "gemini_model": None,          # TODO: fill
        "max_mutants": None,           # TODO: fill
    },
    "thorough": {
        "max_iterations": None,        # TODO: fill
        "max_tests_per_call": None,    # TODO: fill
        "gemini_model": None,          # TODO: fill
        "max_mutants": None,           # TODO: fill
    },
}

DEFAULT_MODE = "balanced"

def get_mode(mode_name=None):
    """
    Returns the config dict for the given mode.

    Args:
        mode_name: "fast", "balanced", or "thorough"
                   Defaults to DEFAULT_MODE if None.

    Returns:
        dict with max_iterations, max_tests_per_call, gemini_model, max_mutants

    Raises:
        ValueError if mode_name is not recognized
    """
    if mode_name is None:
        mode_name = DEFAULT_MODE

    mode_name = mode_name.lower()

    if mode_name not in MODES:
        raise ValueError(
            f"Unknown mode '{mode_name}'. Choose from: {list(MODES.keys())}"
        )

    return MODES[mode_name]