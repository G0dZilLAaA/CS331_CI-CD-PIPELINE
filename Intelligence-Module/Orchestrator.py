"""
Pipeline Orchestrator
Coordinates Stage0 → Stage1 → Stage2

Two modes:
    - Legacy single-file: run_pipeline() (reads from disk, backward compat)
    - Batch CI/CD mode:   run_pipeline_batch(file_list) (source code provided by dev team)
"""

from Stage0.Stage0_Compile import file_reader, infer_language, compile_test
from Stage1.Pipeline.Stage1_pipeline import run_stage1
from Stage2.Pipeline.validation_pipeline import run_stage2
from cost_modes import get_mode
from Stage1.config import apply_mode_overrides
import json
import os


class Pipeline_Orchestrator:
    def __init__(self, file_path: str = None, user_context: str = None, mode: str = None):
        self.file_path = file_path
        self.user_context = user_context
        self.mode_config = get_mode(mode)
        self.source_code = None
        self.stage0_output = None
        self.stage1_output = None
        self.stage2_output = None

    # ──────────────────────────────────────────────
    # Legacy single-file mode (backward compat)
    # ──────────────────────────────────────────────

    def load_source(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.source_code = f.read()

    def run_stage_0(self):
        self.stage0_output = file_reader(self.file_path)
        return self.stage0_output

    def run_stage_1(self, user_context=None):
        self.stage1_output = run_stage1(self.stage0_output, self.source_code, user_context=user_context)
        return self.stage1_output

    def run_stage_2(self):
        self.stage2_output = run_stage2(
            self.stage1_output,
            max_mutants=self.mode_config.get("max_mutants")
        )
        return self.stage2_output

    def run_pipeline(self):
        """Legacy single-file pipeline. Reads from self.file_path."""
        apply_mode_overrides(self.mode_config)

        self.load_source()

        stage0_result = self.run_stage_0()

        if stage0_result["status"] != "PASS":
            return {
                "pipeline_status": "STOPPED_AT_STAGE_0",
                "stage0": stage0_result,
                "stage1": None,
                "stage2": None
            }

        stage1_result = self.run_stage_1(user_context=self.user_context)
        stage2_result = self.run_stage_2()

        return {
            "pipeline_status": "STAGE_2_COMPLETE",
            "stage0": stage0_result,
            "stage1": stage1_result,
            "stage2": stage2_result
        }

    # ──────────────────────────────────────────────
    # Batch CI/CD mode (primary entry point)
    # ──────────────────────────────────────────────

    def run_pipeline_batch(self, file_list: list):
        """
        Run the pipeline for a batch of files from a git event trigger.

        Args:
            file_list: list of dicts, each with:
                - "file_path": str (required — for identification)
                - "source_code": str (required — raw source content)
                - "language": str (optional — inferred from file_path extension if absent)
                - "diff": dict (optional — diff metadata for future use)

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
            source_code = file_entry["source_code"]
            language = file_entry.get("language")
            diff = file_entry.get("diff")

            print(f"\n{'=' * 60}")
            print(f"PIPELINE — {file_path}")
            print(f"{'=' * 60}")

            # Infer language if not provided
            if language is None:
                try:
                    _, ext = os.path.splitext(file_path)
                    language = infer_language(ext)
                except ValueError:
                    results.append({
                        "file_path": file_path,
                        "pipeline_status": "SKIPPED",
                        "error": f"Unsupported file extension: {file_path}",
                        "stage0": None,
                        "stage1": None,
                        "stage2": None
                    })
                    skipped += 1
                    continue

            file_result = self.run_single_file(file_path, source_code, language, diff)
            results.append(file_result)

            if file_result["pipeline_status"] == "STOPPED_AT_STAGE_0":
                failed_stage0 += 1
            elif file_result["pipeline_status"] == "STAGE_2_COMPLETE":
                completed += 1
                passed += 1
            elif file_result["pipeline_status"] == "SKIPPED":
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

        Args:
            file_path: path string (for identification/logging)
            source_code: raw source code string (mandatory)
            language: resolved language string
            diff: optional diff metadata (reserved for future use)

        Returns:
            per-file result dict
        """
        # Stage 0
        stage0_result = compile_test(source_code, language)

        if stage0_result["status"] != "PASS":
            return {
                "file_path": file_path,
                "language": language,
                "pipeline_status": "STOPPED_AT_STAGE_0",
                "stage0": stage0_result,
                "stage1": None,
                "stage2": None
            }

        # Stage 1
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

        # Stage 2
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

        return {
            "file_path": file_path,
            "language": language,
            "pipeline_status": "STAGE_2_COMPLETE",
            "stage0": stage0_result,
            "stage1": stage1_result,
            "stage2": stage2_result
        }


if __name__ == "__main__":

    # ── Legacy single-file mode ──
    # file_path = r"C:\Users\hp\Desktop\Leet Code\Optimised and Learnings\23 - Merge k sorted Lists.py"
    # pipeline = Pipeline_Orchestrator(file_path)
    # result = pipeline.run_pipeline()

    # ── Batch CI/CD mode ──
    pipeline = Pipeline_Orchestrator(mode=None)
    batch_input = [
        {
            "file_path": "src/solution.py",
            "source_code": "class Solution:\n    def twoSum(self, nums, target):\n        d = {}\n        for i, n in enumerate(nums):\n            if target - n in d:\n                return [d[target-n], i]\n            d[n] = i\n",
        },
        # {
        #     "file_path": "src/utils.js",
        #     "source_code": "function add(a, b) { return a + b; }\nmodule.exports = { add };",
        #     "language": "javascript"
        # },
    ]

    result = pipeline.run_pipeline_batch(batch_input)

    print("\n" + "=" * 60)
    print("BATCH PIPELINE RESULT")
    print("=" * 60)

    print(f"\nBatch Status: {result['pipeline_status']}")
    print(f"Total Files: {result['total_files']}")
    print(f"Completed: {result['completed']}")
    print(f"Failed Stage 0: {result['failed_stage0']}")
    print(f"Skipped: {result['skipped']}")

    for file_result in result["results"]:
        print(f"\n{'-' * 40}")
        print(f"File: {file_result.get('file_path')}")
        print(f"Language: {file_result.get('language')}")
        print(f"Status: {file_result.get('pipeline_status')}")

        if file_result.get('error'):
            print(f"Error: {file_result['error']}")

        if file_result.get('stage1'):
            s1 = file_result['stage1']
            print(f"Coverage — Line: {s1['coverage']['line']:.2%}, Branch: {s1['coverage']['branch']:.2%}")
            print(f"Bugs — Exceptions: {len(s1['bugs']['exceptions'])}, "
                  f"Failures: {len(s1['bugs']['failures'])}, "
                  f"Incorrect: {len(s1['bugs']['incorrect_outputs'])}")

        if file_result.get('stage2') and file_result['stage2'].get('mutation_testing'):
            mt = file_result['stage2']['mutation_testing']
            print(f"Mutation Score: {mt.get('mutation_score', 0):.2%}")