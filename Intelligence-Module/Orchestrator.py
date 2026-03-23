"""
Pipeline Orchestrator
Coordinates Stage0 → Stage1
"""

from Stage0.Stage0_Compile import file_reader
from Stage1.Pipeline.Stage1_pipeline import run_stage1
import json
import os


class Pipeline_Orchestrator:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.source_code = None
        self.stage0_output = None
        self.stage1_output = None

    def load_source(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.source_code = f.read()

    def run_stage_0(self):
        self.stage0_output = file_reader(self.file_path)
        return self.stage0_output

    def run_stage_1(self):
        self.stage1_output = run_stage1(self.stage0_output, self.source_code)
        return self.stage1_output

    def run_pipeline(self):
        # Load source code
        self.load_source()

        # Run Stage0
        stage0_result = self.run_stage_0()

        # Gate
        if stage0_result["status"] != "PASS":
            return {
                "pipeline_status": "STOPPED_AT_STAGE_0",
                "stage0": stage0_result,
                "stage1": None
            }

        # Run Stage1
        stage1_result = self.run_stage_1()


        return {
            "pipeline_status": "STAGE_1_COMPLETE",
            "stage0": stage0_result,
            "stage1": stage1_result
        }

if __name__ == "__main__":
    #file_path = r"C:\Users\hp\Desktop\IIIT Guwahati\CS\CS331(SE LAB)\Stage1\Tests\LC Tests.py"
    # file_path = r"C:\Users\hp\Desktop\IIIT Guwahati\CS\CS 201 (Algorithm)\Mid Sem Algo\Q2.cpp"
    file_path = r"C:\Users\hp\Desktop\Leet Code\Optimised and Learnings\4 - Median of Two Sorted arrays_alt sol.py"
    #file_path = r"./Stage1/Tests/Test5.py"

    pipeline = Pipeline_Orchestrator(file_path)
    result = pipeline.run_pipeline()


    print("\n" + "=" * 60)
    print("PIPELINE RESULT")
    print("=" * 60)

    print(f"\nPipeline Status: {result['pipeline_status']}")

    print("\n" + "-" * 40)
    print("STAGE 0 — Compilation Check")
    print("-" * 40)
    print(json.dumps(result['stage0'], indent=2, default=str))

    if result.get('stage1'):
        print("\n" + "-" * 40)
        print("STAGE 1 — Semantic Analysis & Testing")
        print("-" * 40)

        stage1 = result['stage1']

        print(f"\n  Language: {stage1['language']}")
        print(f"  Execution Model: {stage1['execution_model']}")

        print("\n  Structural Features:")
        print(json.dumps(stage1['structural_features'], indent=4, default=str))

        print("\n  Coverage:")
        print(f"    Line:   {stage1['coverage']['line']}")
        print(f"    Branch: {stage1['coverage']['branch']}")

        print(f"\n  Bugs Summary:")
        print(f"    Exceptions:       {len(stage1['bugs']['exceptions'])}")
        print(f"    Failures:         {len(stage1['bugs']['failures'])}")
        print(f"    Incorrect Outputs: {len(stage1['bugs']['incorrect_outputs'])}")

        print(f"\n  Tests Executed: {len(stage1['executed_tests'])}")

        # All generated test cases
        test_cases = stage1.get('generated_test_cases', [])
        print(f"\n  Generated Tests Cases: {len(test_cases)}")
        print(f"\n  Tests Case Details:")
        for i, test in enumerate(test_cases):
            print(f"    Tests {i + 1}:")
            print(f"      Strategy: {test.get('strategy')}")
            print(f"      Method:   {test.get('method_name')}")
            print(f"      Input:    {test.get('input')}")
            print(f"      Expected: {test.get('expected_output')}")
            print(f"      Mode:     {test.get('comparison_mode')}")

        # Bug details — at most 3
        all_bugs = []
        for bug in stage1['bugs']['exceptions']:
            bug['type'] = 'exception'
            all_bugs.append(bug)
        for bug in stage1['bugs']['failures']:
            bug['type'] = 'failure'
            all_bugs.append(bug)
        for bug in stage1['bugs']['incorrect_outputs']:
            bug['type'] = 'incorrect_output'
            all_bugs.append(bug)

        if all_bugs:
            print(f"\n  Bug Details (showing {min(3, len(all_bugs))} of {len(all_bugs)}):")
            for i, bug in enumerate(all_bugs[:3]):
                print(f"    Bug {i + 1}:")
                print(f"      Type:     {bug.get('type')}")
                print(f"      Strategy: {bug.get('strategy', 'N/A')}")
                print(f"      Input:    {bug.get('input', 'N/A')}")
                if bug.get('type') == 'incorrect_output':
                    print(f"      Expected: {bug.get('expected', 'N/A')}")
                    print(f"      Actual:   {bug.get('actual', 'N/A')}")
                else:
                    print(f"      Error:    {bug.get('error', 'N/A')}")

        # Bug summary by strategy
        print(f"\n  Bug Summary by Strategy:")
        strategy_counts = {}
        for bug in all_bugs:
            strategy = bug.get('strategy', 'unknown')
            if strategy not in strategy_counts:
                strategy_counts[strategy] = 0
            strategy_counts[strategy] += 1

        for strategy, count in strategy_counts.items():
            print(f"    {strategy}: {count} bugs")

        # Bug summary by type
        print(f"\n  Bug Summary by Type:")
        print(f"    Exceptions:        {len(stage1['bugs']['exceptions'])}")
        print(f"    Failures:          {len(stage1['bugs']['failures'])}")
        print(f"    Incorrect Outputs: {len(stage1['bugs']['incorrect_outputs'])}")
        print(f"    Total:             {len(all_bugs)}")

        # Save test cases and bugs to temp file
        import tempfile

        if result.get('stage1'):
            save_data = {
                "generated_test_cases": result["stage1"].get("generated_test_cases", []),
                "bugs": result["stage1"]["bugs"]
            }

            output_filename = "Test_Cases.json"
            output_path = r"Stage1/Tests"

            full_path = os.path.join(output_path, output_filename)

            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, default=str)

            print(f"\n  Results saved to: {output_path}")

    print("\n\n\n",result)
