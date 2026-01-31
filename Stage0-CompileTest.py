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
        exec(compiled, {})
        return {
            "status": "PASS",
            "error": None
        }
    except Exception as e:
        return {
            "status": "FAIL",
            "error": str(e)
        }

result = file_reader("Sample code 1.py")
print(result)
