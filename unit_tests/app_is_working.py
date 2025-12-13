"""
Comprehensive pre-run health checks and light stress tests for the project.

This script avoids hitting external APIs by mocking where reasonable,
so you can verify local environment readiness and basic logic quickly.

Run:
    python unit_tests/app_is_working.py
"""

import os
import sys
import time
import importlib
from typing import List, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError

OK = "OK"
WARN = "WARN"
FAIL = "FAIL"


def _print_result(name: str, status: str, detail: str = "") -> None:
    icon = {OK: "✓", WARN: "⚠", FAIL: "✗"}.get(status, "•")
    msg = f"{icon} {name}: {status}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def check_python_version(min_major: int = 3, min_minor: int = 10) -> Tuple[str, str]:
    v = sys.version_info
    if (v.major, v.minor) >= (min_major, min_minor):
        return OK, f"Python {v.major}.{v.minor}"
    return FAIL, f"Found {v.major}.{v.minor}, require >= {min_major}.{min_minor}"


def check_requirements_installed(packages: List[str]) -> Tuple[str, str]:
    missing = []
    for pkg in packages:
        try:
            importlib.import_module(pkg)
        except Exception:
            missing.append(pkg)
    if not missing:
        return OK, "All required packages import successfully"
    return FAIL, f"Missing packages: {', '.join(missing)}"


def check_env_vars(vars_to_check: List[str]) -> Tuple[str, str]:
    missing = [v for v in vars_to_check if not os.getenv(v)]
    if not missing:
        return OK, "All expected env vars present"
    return WARN, f"Missing env vars: {', '.join(missing)}"


def check_streamlit_import() -> Tuple[str, str]:
    try:
        import streamlit  # noqa: F401
        return OK, "streamlit import succeeded"
    except Exception as e:
        return FAIL, f"streamlit import failed: {e}"


def check_langchain_imports() -> Tuple[str, str]:
    try:
        import langchain_core  # noqa: F401
        import langchain_community  # noqa: F401
        # Optional providers
        optional_missing = []
        try:
            import langchain_openai  # noqa: F401
        except Exception:
            optional_missing.append("langchain_openai")
        try:
            import langchain_ollama  # noqa: F401
        except Exception:
            optional_missing.append("langchain_ollama")
        if optional_missing:
            return WARN, f"Optional providers missing: {', '.join(optional_missing)}"
        return OK, "LangChain core + providers import succeeded"
    except Exception as e:
        return FAIL, f"LangChain imports failed: {e}"


def check_ollama_server(base_url: str = None) -> Tuple[str, str]:
    base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        req = Request(f"{base_url}/api/tags", headers={"Accept": "application/json"})
        with urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                return OK, f"Ollama reachable at {base_url}"
            return WARN, f"Ollama responded with status {resp.status}"
    except URLError as e:
        return WARN, f"Ollama not reachable at {base_url}: {e.reason}"
    except Exception as e:
        return WARN, f"Ollama check error: {e}"


# Light stress tests that do not call external APIs
class DummyLLM:
    """A minimal stand-in for an LLM that echoes input size."""

    def __init__(self):
        self.temperature = 0

    def invoke(self, payload):
        text = str(payload)
        return {
            "messages": [
                {"type": "ai", "content": f"len={len(text)}"}
            ]
        }


def stress_long_inputs(iterations: int = 3, size: int = 100_000) -> Tuple[str, str]:
    llm = DummyLLM()
    try:
        for i in range(iterations):
            s = ("A" * size) + str(i)
            res = llm.invoke({"prompt": s})
            if "messages" not in res:
                return FAIL, "DummyLLM returned unexpected structure"
        return OK, f"Processed {iterations} long inputs of ~{size} chars"
    except MemoryError:
        return FAIL, "MemoryError during long input stress"
    except Exception as e:
        return FAIL, f"Error during long input stress: {e}"


def stress_repeat_calls(iterations: int = 1000) -> Tuple[str, str]:
    llm = DummyLLM()
    try:
        start = time.time()
        for i in range(iterations):
            _ = llm.invoke({"prompt": f"ping {i}"})
        dur = time.time() - start
        return OK, f"{iterations} calls completed in {dur:.2f}s"
    except Exception as e:
        return FAIL, f"Error during repeat calls stress: {e}"


def main() -> int:
    checks = []

    # Core environment
    checks.append(("Python Version", *check_python_version()))
    checks.append(("Requirements", *check_requirements_installed([
        "streamlit",
        "dotenv",
        "langchain_core",
        "langchain_community",
    ])))

    # Secrets presence (optional; WARN if missing)
    checks.append(("Env Vars", *check_env_vars([
        "OPENAI_API_KEY",
        "TAVILY_API_KEY",
    ])))

    # Imports
    checks.append(("Streamlit Import", *check_streamlit_import()))
    checks.append(("LangChain Imports", *check_langchain_imports()))

    # Local services
    checks.append(("Ollama Server", *check_ollama_server()))

    # Stress (local-only)
    checks.append(("Stress Long Inputs", *stress_long_inputs()))
    checks.append(("Stress Repeat Calls", *stress_repeat_calls()))

    # Print results
    failures = 0
    warnings = 0
    print("\n=== Pre-run Health Check ===")
    for name, status, detail in checks:
        _print_result(name, status, detail)
        if status == FAIL:
            failures += 1
        elif status == WARN:
            warnings += 1

    print("\nSummary:")
    print(f"Failures: {failures}")
    print(f"Warnings: {warnings}")

    # Return non-zero on failure to integrate with CI
    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
