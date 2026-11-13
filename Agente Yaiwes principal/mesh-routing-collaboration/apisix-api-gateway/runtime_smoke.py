#!/usr/bin/env python3
from adapter import version

if __name__ == "__main__":
    out = version()
    assert out["ok"] is True
    assert "3.18.0" in (out["stdout"] + out["stderr"])
    print("APISIX_RUNTIME_VERSION_PASS")
