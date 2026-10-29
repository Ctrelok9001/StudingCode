import sys
import subprocess
import time


def execute_python_code(code: str, stdin_data: str = "", timeout: float = 3.0) -> dict:

    start_time = time.perf_counter()
    try:
        process = subprocess.Popen(
            [sys.executable, "-I", "-s", "-c", code],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        stdout, stderr = process.communicate(input=stdin_data, timeout=timeout)
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        if process.returncode != 0:
            if "SyntaxError" in stderr or "IndentationError" in stderr:
                return {
                    "success": False,
                    "status": "syntax_error",
                    "stdout": stdout,
                    "stderr": stderr,
                    "duration_ms": duration_ms,
                    "message": "Синтаксическая ошибка в коде"
                }
            return {
                "success": False,
                "status": "runtime_error",
                "stdout": stdout,
                "stderr": stderr,
                "duration_ms": duration_ms,
                "message": "Ошибка во время выполнения (Runtime Error)"
            }

        return {
            "success": True,
            "status": "ok",
            "stdout": stdout,
            "stderr": stderr,
            "duration_ms": duration_ms,
            "message": "Код успешно выполнен"
        }

    except subprocess.TimeoutExpired:
        process.kill()
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "success": False,
            "status": "timeout",
            "stdout": "",
            "stderr": f"Превышен лимит времени выполнения ({timeout} сек.)",
            "duration_ms": duration_ms,
            "message": "Time Limit Exceeded"
        }
    except Exception as e:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "success": False,
            "status": "runtime_error",
            "stdout": "",
            "stderr": str(e),
            "duration_ms": duration_ms,
            "message": f"Системная ошибка: {e}"
        }


def normalize_output(text: str) -> str:
    lines = [line.rstrip() for line in text.strip().splitlines()]
    return "\n".join(lines)


def run_test_cases(code: str, test_cases) -> dict:

    results = []
    tests_passed = 0
    total_time_ms = 0
    overall_status = "accepted"
    first_error_msg = ""

    for index, test in enumerate(test_cases, 1):
        input_data = test.input_data or ""
        expected = normalize_output(test.expected_output or "")

        exec_res = execute_python_code(code, stdin_data=input_data)
        total_time_ms += exec_res["duration_ms"]

        if not exec_res["success"]:
            overall_status = exec_res["status"]
            first_error_msg = exec_res["stderr"] or exec_res["message"]
            results.append({
                "index": index,
                "is_hidden": test.is_hidden,
                "passed": False,
                "status": exec_res["status"],
                "input": "" if test.is_hidden else input_data,
                "expected": "" if test.is_hidden else expected,
                "actual": "" if test.is_hidden else exec_res["stdout"],
                "error": exec_res["stderr"],
                "duration_ms": exec_res["duration_ms"]
            })
            break

        actual = normalize_output(exec_res["stdout"])
        if actual == expected:
            tests_passed += 1
            results.append({
                "index": index,
                "is_hidden": test.is_hidden,
                "passed": True,
                "status": "ok",
                "input": "" if test.is_hidden else input_data,
                "expected": "" if test.is_hidden else expected,
                "actual": "" if test.is_hidden else actual,
                "error": "",
                "duration_ms": exec_res["duration_ms"]
            })
        else:
            overall_status = "wrong_answer"
            first_error_msg = f"Тест #{index}: Несовпадение вывода"
            results.append({
                "index": index,
                "is_hidden": test.is_hidden,
                "passed": False,
                "status": "wrong_answer",
                "input": "" if test.is_hidden else input_data,
                "expected": "" if test.is_hidden else expected,
                "actual": "" if test.is_hidden else actual,
                "error": "Вывод не совпадает с ожидаемым",
                "duration_ms": exec_res["duration_ms"]
            })
            break

    total_tests = len(test_cases)
    if tests_passed == total_tests and total_tests > 0:
        overall_status = "accepted"

    return {
        "status": overall_status,
        "tests_passed": tests_passed,
        "total_tests": total_tests,
        "duration_ms": total_time_ms,
        "error_message": first_error_msg,
        "test_results": results
    }
