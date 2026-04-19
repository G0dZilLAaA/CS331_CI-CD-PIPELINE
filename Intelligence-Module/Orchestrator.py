"""
Pipeline Orchestrator
Coordinates Stage0 → Stage1 → Stage2

Batch CI/CD mode entry point: run_pipeline_batch(file_list)

file_entry format:
    {
        "file_path": str,           # required — used for identification & language inference
        "source_code": str          # optional — if absent, read from disk (local dev fallback)
    }
"""

from Stage0.Stage0_Compile import infer_language, compile_test
from Stage1.Pipeline.Stage1_pipeline import run_stage1
from Stage2.Pipeline.validation_pipeline import run_stage2
from cost_modes import get_mode
from Stage1.config import apply_mode_overrides
import os
import json


class Pipeline_Orchestrator:
    def __init__(self, user_context: str = None, mode: str = None, output_path: str = None):
        self.user_context = user_context
        self.mode_config = get_mode(mode)
        self.output_path = output_path  # None = don't save; str = directory to save artifacts

    # ──────────────────────────────────────────────
    # Source resolver
    # ──────────────────────────────────────────────

    @staticmethod
    def resolve_source(file_entry: dict) -> str:
        if "source_code" in file_entry:
            return file_entry["source_code"]
        with open(file_entry["file_path"], "r", encoding="utf-8") as f:
            return f.read()

    # ──────────────────────────────────────────────
    # Artifact saver
    # ──────────────────────────────────────────────

    def save_artifacts(self, file_path: str, file_result: dict):
        """
        Saves per-stage JSON artifacts under self.output_path.

        Naming convention (derived from source file stem + language):
            <stem>_<lang>_bugs.json
            <stem>_<lang>_test_cases.json
            <stem>_<lang>_summary.json
            <stem>_<lang>_analysis.json
        """
        if not self.output_path:
            return

        os.makedirs(self.output_path, exist_ok=True)
        stem = os.path.splitext(os.path.basename(file_path))[0]
        lang = file_result.get("language", "unknown")
        prefix = f"{stem}_{lang}"

        artifacts = {}

        # Bugs (Stage 2 post-filtering)
        if file_result.get("stage2"):
            artifacts[f"{prefix}_bugs.json"] = file_result["stage2"].get("bugs", {})

        # Test cases (Stage 2 post-filtering)
        if file_result.get("stage2"):
            artifacts[f"{prefix}_test_cases.json"] = file_result["stage2"].get("tests", {})

        # Summary — condensed single-file overview
        if file_result.get("stage0"):
            s0 = file_result["stage0"]
            s1 = file_result.get("stage1")
            s2 = file_result.get("stage2")

            summary = {
                "stage0": {
                    "status": s0.get("status"),
                    "language": s0.get("language"),
                    "error_count": s0.get("total_errors"),
                    "errors": s0.get("errors", []),
                },
            }

            if s1:
                sf = s1.get("structural_features", {})
                cov = s1.get("coverage", {})
                summary["stage1"] = {
                    "execution_model": s1.get("execution_model"),
                    "structural_features": {
                        "function_count": sf.get("function_count"),
                        "class_count": sf.get("class_count"),
                        "loop_count": sf.get("loop_count"),
                        "max_nesting_depth": sf.get("max_nesting_depth"),
                        "cyclomatic_complexity": sf.get("cyclomatic_complexity"),
                        "recursiondetected": sf.get("recursiondetected"),
                        "branching_factor": sf.get("branching_factor"),
                    },
                    "coverage": {
                        "line": cov.get("line"),
                        "branch": cov.get("branch"),
                    },
                }

            if s2:
                s2_bugs = s2.get("bugs", {})
                s2_summ = s2_bugs.get("summary", {})
                s2_tests = s2.get("tests", {})
                s2_mutation = s2.get("mutation_testing", {})
                summary["stage2"] = {
                    "confirmed_bugs": s2_summ.get("confirmed_count", 0),
                    "inconclusive": s2_summ.get("inconclusive_count", 0),
                    "hallucinations_removed": s2_summ.get("hallucinated_count", 0),
                    "valid_test_cases": s2_tests.get("total_valid", 0),
                    "mutation_score": s2_mutation.get("mutation_score") if s2_mutation else None,
                }

            artifacts[f"{prefix}_summary.json"] = summary

        # Analysis — combined Stage 0 + Stage 1 detailed data
        analysis = {}
        if file_result.get("stage0"):
            analysis["compilation"] = file_result["stage0"]
        if file_result.get("stage1"):
            s1 = file_result["stage1"]
            analysis["semantic_analysis"] = {
                "language": s1.get("language"),
                "execution_model": s1.get("execution_model"),
                "structural_features": s1.get("structural_features", {}),
                "coverage": s1.get("coverage", {}),
            }
        if analysis:
            artifacts[f"{prefix}_analysis.json"] = analysis

        for filename, payload in artifacts.items():
            out_path = os.path.join(self.output_path, filename)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
            print(f"    [Orchestrator] Saved → {out_path}")

    # ──────────────────────────────────────────────
    # Batch CI/CD mode
    # ──────────────────────────────────────────────

    def run_pipeline_batch(self, file_list: list):
        """
        Run the pipeline for a batch of files from a git event trigger.

        Args:
            file_list: list of file_entry dicts
                - "file_path": str   (required)
                - "source_code": str (optional — inlined by CI webhook; falls back to disk)

        Returns:
            {
                "pipeline_status": "BATCH_COMPLETE",
                "total_files": int,
                "passed": int,
                "failed_stage0": int,
                "completed": int,
                "skipped": int,
                "results": [per-file result dicts]
            }
        """
        apply_mode_overrides(self.mode_config)

        results = []
        passed = 0
        failed_stage0 = 0
        completed = 0
        skipped = 0

        for file_entry in file_list:
            file_path = file_entry["file_path"]

            print(f"\n{'=' * 60}")
            print(f"PIPELINE — {file_path}")
            print(f"{'=' * 60}")

            # Resolve source
            try:
                source_code = self.resolve_source(file_entry)
            except Exception as e:
                results.append({
                    "file_path": file_path,
                    "pipeline_status": "SKIPPED",
                    "error": f"Could not read source: {e}",
                    "stage0": None, "stage1": None, "stage2": None
                })
                skipped += 1
                continue

            # Infer language from extension
            try:
                _, ext = os.path.splitext(file_path)
                language = infer_language(ext)
            except ValueError:
                results.append({
                    "file_path": file_path,
                    "pipeline_status": "SKIPPED",
                    "error": f"Unsupported file extension: {file_path}",
                    "stage0": None, "stage1": None, "stage2": None
                })
                skipped += 1
                continue

            file_result = self.run_single_file(file_path, source_code, language)
            results.append(file_result)

            status = file_result["pipeline_status"]
            if status == "STOPPED_AT_STAGE_0":
                failed_stage0 += 1
            elif status == "STAGE_2_COMPLETE":
                completed += 1
                passed += 1
                self.save_artifacts(file_path, file_result)
            elif status == "SKIPPED":
                skipped += 1

        return {
            "pipeline_status": "BATCH_COMPLETE",
            "total_files": len(file_list),
            "passed": passed,
            "failed_stage0": failed_stage0,
            "completed": completed,
            "skipped": skipped,
            "results": results
        }

    def run_single_file(self, file_path, source_code, language, diff=None):
        """
        Run full pipeline for a single file.
        Orchestrator owns all console output (SoC).
        """
        # ── Stage 0 ──
        stage0_result = compile_test(source_code, language)

        print(f"\n{'─' * 60}")
        print(f"STAGE 0 — Compilation Check")
        print(f"{'─' * 60}")
        print(f"    Status   : {stage0_result['status']}")
        print(f"    Language : {stage0_result['language']}")
        print(f"    Errors   : {stage0_result['total_errors']}")
        if stage0_result["status"] == "FAIL":
            for i, err in enumerate(stage0_result.get("errors", [])):
                print(f"      [{i + 1}] {err.get('error_type', 'Unknown')}: {err.get('error', '')}")

        if stage0_result["status"] != "PASS":
            return {
                "file_path": file_path,
                "language": language,
                "pipeline_status": "STOPPED_AT_STAGE_0",
                "stage0": stage0_result,
                "stage1": None,
                "stage2": None
            }

        # ── Stage 1 ──
        try:
            stage1_result = run_stage1(
                stage0_result, source_code,
                user_context=self.user_context
            )
        except Exception as e:
            return {
                "file_path": file_path,
                "language": language,
                "pipeline_status": "FAILED_AT_STAGE_1",
                "stage0": stage0_result,
                "stage1": None,
                "stage2": None,
                "error": str(e)
            }

        # Print Stage 1 output
        print(f"\n{'─' * 60}")
        print(f"STAGE 1 — Semantic Analysis & Test Generation")
        print(f"{'─' * 60}")

        print(f"\n  [Semantic Analysis]")
        print(f"    Language        : {stage1_result.get('language')}")
        print(f"    Execution model : {stage1_result.get('execution_model')}")

        sf = stage1_result.get("structural_features") or {}
        if sf:
            print(f"    Functions       : {sf.get('function_count', 'N/A')}")
            print(f"    Classes         : {sf.get('class_count', 'N/A')}")
            print(f"    Loops           : {sf.get('loop_count', 'N/A')}")
            print(f"    Max nesting     : {sf.get('max_nesting_depth', 'N/A')}")
            print(f"    Cyclomatic comp.: {sf.get('cyclomatic_complexity', 'N/A')}")
            print(f"    Recursion       : {'Yes' if sf.get('recursiondetected') else 'No'}")
            print(f"    Branching factor: {sf.get('branching_factor', 'N/A')}")

        cov = stage1_result.get("coverage", {})
        bugs = stage1_result.get("bugs", {})
        print(f"\n  [Test Generation]")
        print(f"    Tests generated  : {len(stage1_result.get('generated_test_cases', []))}")
        print(f"    Tests executed   : {len(stage1_result.get('executed_tests', []))}")
        print(f"    Line coverage    : {cov.get('line', 0):.2%}")
        print(f"    Branch coverage  : {cov.get('branch', 0):.2%}")
        print(f"    Exceptions       : {len(bugs.get('exceptions', []))}")
        print(f"    Failures         : {len(bugs.get('failures', []))}")
        print(f"    Incorrect outputs: {len(bugs.get('incorrect_outputs', []))}")

        # ── Stage 2 ──
        try:
            stage2_result = run_stage2(
                stage1_result,
                max_mutants=self.mode_config.get("max_mutants")
            )
        except Exception as e:
            return {
                "file_path": file_path,
                "language": language,
                "pipeline_status": "FAILED_AT_STAGE_2",
                "stage0": stage0_result,
                "stage1": stage1_result,
                "stage2": None,
                "error": str(e)
            }

        # Print Stage 2 output
        print(f"\n{'─' * 60}")
        print(f"STAGE 2 — Validation Pipeline")
        print(f"{'─' * 60}")

        s2_bugs = stage2_result.get("bugs", {})
        s2_summary = s2_bugs.get("summary", {})
        s2_tests = stage2_result.get("tests", {})
        s2_mutation = stage2_result.get("mutation_testing", {})

        print(f"\n  [Signal Filter]")
        print(f"    Incoming bugs    : {s2_summary.get('total_incoming', 0)}")
        print(f"    After filtering  : {s2_summary.get('total_after_filtering', 0)}")
        print(f"    Hallucinations   : {s2_summary.get('hallucinated_count', 0)}")

        print(f"\n  [Mutation Testing]")
        if s2_mutation:
            print(f"    Total mutants    : {s2_mutation.get('total_mutants', 0)}")
            print(f"    Killed           : {s2_mutation.get('killed', 0)}")
            print(f"    Survived         : {s2_mutation.get('survived', 0)}")
            print(f"    Mutation score   : {s2_mutation.get('mutation_score', 0):.2%}")
        else:
            print(f"    No mutants generated")

        print(f"\n  [Final Report]")
        print(f"    Confirmed bugs   : {s2_summary.get('confirmed_count', 0)}")
        print(f"    Inconclusive     : {s2_summary.get('inconclusive_count', 0)}")
        print(f"    Valid test cases  : {s2_tests.get('total_valid', 0)}")
        print(f"    Coverage-only     : {len(s2_tests.get('coverage_only_tests', []))}")

        return {
            "file_path": file_path,
            "language": language,
            "pipeline_status": "STAGE_2_COMPLETE",
            "stage0": stage0_result,
            "stage1": stage1_result,
            "stage2": stage2_result
        }


if __name__ == "__main__":

    pipeline = Pipeline_Orchestrator(
        mode=None,
        output_path=r"C:\Users\hp\Desktop\IIIT Guwahati\CS\CS331(SE LAB)\pipeline_output"
    )

    batch_input = [
        {"file_path": r"C:\Users\hp\Desktop\Leet Code\Optimised and Learnings\23 - Merge k sorted Lists.py"}
        ,{"file_path": r"C:\Users\hp\Desktop\IIIT Guwahati\CS\CS331(SE LAB)\Test.cpp"},
        {"file_path": r"C:\Users\hp\Desktop\IIIT Guwahati\CS\CS331(SE LAB)\Test.c"},
        {"file_path": r"C:\Users\hp\Desktop\IIIT Guwahati\CS\CS331(SE LAB)\Test.js"}
    ]

    result = pipeline.run_pipeline_batch(batch_input)

    print("\n" + "=" * 60)
    print("BATCH PIPELINE RESULT")
    print("=" * 60)
    print(f"\nBatch Status : {result['pipeline_status']}")
    print(f"Total Files  : {result['total_files']}")
    print(f"Completed    : {result['completed']}")
    print(f"Failed Stg0  : {result['failed_stage0']}")
    print(f"Skipped      : {result['skipped']}")

    for file_result in result["results"]:
        print(f"\n{'-' * 40}")
        print(f"File    : {file_result.get('file_path')}")
        print(f"Language: {file_result.get('language')}")
        print(f"Status  : {file_result.get('pipeline_status')}")

        if file_result.get("error"):
            print(f"Error   : {file_result['error']}")

        if file_result.get("stage1"):
            s1 = file_result["stage1"]
            print(f"Coverage — Line: {s1['coverage']['line']:.2%}, Branch: {s1['coverage']['branch']:.2%}")
            print(f"Bugs — Exceptions: {len(s1['bugs']['exceptions'])}, "
                  f"Failures: {len(s1['bugs']['failures'])}, "
                  f"Incorrect: {len(s1['bugs']['incorrect_outputs'])}")

        if file_result.get("stage2") and file_result["stage2"].get("mutation_testing"):
            mt = file_result["stage2"]["mutation_testing"]
            print(f"Mutation Score: {mt.get('mutation_score', 0):.2%}")