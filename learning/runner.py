import sys
import os
import ast
import subprocess
import time


FORBIDDEN_MODULES = {
    "os", "subprocess", "shutil", "socket", "urllib", "requests",
    "http", "ftplib", "smtplib", "telnetlib", "pty", "commands",
    "multiprocessing", "threading", "ctypes", "winreg", "msvcrt",
    "posix", "pwd", "spwd", "grp", "crypt", "termios", "resource",
    "importlib", "pickle", "shelve", "marshal", "webbrowser",
    "tempfile", "platform"
}

FORBIDDEN_FUNCTIONS = {
    "eval", "exec", "__import__", "compile"
}


def analyze_code_safety(code: str) -> tuple[bool, str]:
    try:
        tree = ast.parse(code)
    except (SyntaxError, IndentationError):
        return True, ""

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split('.')[0]
                if root_pkg in FORBIDDEN_MODULES:
                    return False, f"Импорт модуля '{alias.name}' заблокирован системой безопасности."
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split('.')[0]
                if root_pkg in FORBIDDEN_MODULES:
                    return False, f"Импорт из модуля '{node.module}' заблокирован системой безопасности."
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_FUNCTIONS:
                    return False, f"Вызов функции '{node.func.id}()' заблокирован системой безопасности."
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in ("system", "popen", "spawn", "fork", "execv", "execve"):
                    return False, f"Вызов системного метода '{node.func.attr}()' заблокирован."
    return True, ""


def format_python_code(code: str) -> tuple[bool, str]:
    if not code or not code.strip():
        return True, ""
    try:
        tree = ast.parse(code)
        formatted = ast.unparse(tree)
        return True, formatted
    except Exception as e:
        return False, str(e)


def decode_output(raw_bytes: bytes) -> str:
    if not raw_bytes:
        return ""
    for enc in ("utf-8", "cp1251", "cp866"):
        try:
            return raw_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("utf-8", errors="replace")


def execute_python_code(code: str, stdin_data: str = "", timeout: float = 3.0) -> dict:
    is_safe, security_msg = analyze_code_safety(code)
    if not is_safe:
        return {
            "success": False,
            "status": "security_error",
            "stdout": "",
            "stderr": security_msg,
            "duration_ms": 0,
            "message": security_msg
        }

    start_time = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    try:
        process = subprocess.Popen(
            [sys.executable, "-X", "utf8", "-I", "-s", "-c", code],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        stdin_bytes = stdin_data.encode("utf-8") if isinstance(stdin_data, str) else stdin_data
        stdout_bytes, stderr_bytes = process.communicate(input=stdin_bytes, timeout=timeout)
        stdout = decode_output(stdout_bytes)
        stderr = decode_output(stderr_bytes)
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
