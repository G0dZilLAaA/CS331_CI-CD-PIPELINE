#Stage 0: Compilation Errors Test
def file_reader(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        return compile_test(code)

    except Exception as e:
        return {
            "status": "FAIL",
            "error": str(e)
        }

def compile_test(code: str):
    try:
        compiled = compile(code, "<submitted_code>", "exec")
        return {
            "stage": 0,
            "status": "PASS",
            "check_type": "compile_only",
            "language": "python",
            "executed": False,
            "error": None
        }

    except Exception as e:
        return {
            "status": "FAIL",
            "error_type" : type(e).__name__,
            "error": str(e)
        }

result = file_reader("Sample code 1.py")
print(result)
