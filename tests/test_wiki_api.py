import os

import pytest
import requests


def _probe_fastapi_zim_files() -> tuple[bool, str]:
    base_url = os.getenv("WIKI_API_URL", "http://127.0.0.1:8080")
    try:
        response = requests.get(f"{base_url}/zim-files", timeout=5)
    except requests.RequestException as exc:
        return False, f"FastAPI server not available: {exc}"

    if response.status_code == 503:
        return False, "WikiSearchAPI not initialized"

    if response.status_code != 200:
        return False, f"Unexpected status: {response.status_code}"

    data = response.json()
    if "zim_files" not in data:
        return False, "Missing zim_files in response"
    if not isinstance(data["zim_files"], list):
        return False, "zim_files is not a list"
    if not data["zim_files"]:
        return False, "No ZIM files loaded"

    return True, "ok"


def test_fastapi_zim_files() -> None:
    ok, message = _probe_fastapi_zim_files()
    if not ok:
        pytest.skip(message)


if __name__ == "__main__":
    ok, message = _probe_fastapi_zim_files()
    if ok:
        print("FastAPI /zim-files check passed.")
    else:
        print(f"FastAPI /zim-files check skipped: {message}")
