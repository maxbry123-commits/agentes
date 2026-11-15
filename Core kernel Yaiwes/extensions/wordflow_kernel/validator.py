import ast
import compileall
from pathlib import Path


class Validator:
    def validate_python_tree(self, root):
        root = Path(root)
        errors = []
        for p in root.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            try:
                ast.parse(p.read_text(encoding="utf-8"))
            except Exception as e:
                errors.append({"path": str(p), "error": str(e)})
        return {"status": "PASS" if not errors else "FAIL", "errors": errors}

    def compile_tree(self, root):
        ok = compileall.compile_dir(str(root), quiet=1)
        return {"status": "PASS" if ok else "FAIL"}
