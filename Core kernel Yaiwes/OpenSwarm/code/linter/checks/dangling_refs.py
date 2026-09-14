"""Every cross-entity id field on a backend pydantic model must say what it points at.

OpenSwarm stores entities as JSON records that reference each other with bare strings
(``Workflow.edit_agent_session_id``, ``Output.workspace_id``, ``CardPosition.session_id``). The
type says ``str``, so nothing tells a reader the referent may be gone, and a reader that forgets
renders a blank instead of a designed empty state. Measured on real data: 0 of 5 workflow chat
pointers resolved, and 8 of 10 app workspaces had no record at all.

The rule: a field named ``*_id`` / ``*_ids`` on a class that inherits from pydantic ``BaseModel``
must be declared in ``backend/config/entity_references.py``, which names the entity it points at
and the store that resolves it. A model's own primary key is spelled ``id`` and so never matches.
Pre-existing fields are grandfathered per FIELD (not per file) in the ``dangling-refs`` exception
list, keyed ``<path>::<Model>.<field>``, so a new field in an old model is still caught.

The registry is checked back: an entry for a field that no longer exists is an error, and so is a
store whose lookup function has been renamed away. A registry nobody verifies is a registry that
rots.

Scoped to ``backend/`` Python, like checks/classes.py. One AST pass, no imports of backend code
(CI lints with a bare interpreter that has no pydantic).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from . import CheckError, is_excepted, is_excluded, is_lintignored

RULE = "dangling-refs"
REGISTRY_REL = "backend/config/entity_references.py"
REFERENCES_NAME = "CROSS_ENTITY_REFERENCES"
STORES_NAME = "ENTITY_STORES"
KIND_ENUM_NAME = "EntityKind"

# (dotted module, model name, field name)
FieldKey = Tuple[str, str, str]


def p_dotted(rel: str) -> str:
    """``backend/apps/foo/models.py`` -> ``backend.apps.foo.models``."""
    parts = list(Path(rel).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def p_const_str(node: Optional[ast.AST]) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def p_attr_name(node: Optional[ast.AST]) -> Optional[str]:
    """``EntityKind.SESSION`` -> ``SESSION``."""
    return node.attr if isinstance(node, ast.Attribute) else None


def p_base_names(node: ast.ClassDef) -> List[str]:
    names: List[str] = []
    for base in node.bases:
        target: ast.AST = base.value if isinstance(base, ast.Subscript) else base
        if isinstance(target, ast.Name):
            names.append(target.id)
        elif isinstance(target, ast.Attribute):
            names.append(target.attr)
    return names


def p_is_class_var(node: ast.AnnAssign) -> bool:
    annotation: ast.AST = node.annotation
    if isinstance(annotation, ast.Subscript):
        annotation = annotation.value
    if isinstance(annotation, ast.Name):
        return annotation.id == "ClassVar"
    return isinstance(annotation, ast.Attribute) and annotation.attr == "ClassVar"


class BackendIndex:
    """Everything one AST pass over ``backend/`` needs to hand the rest of the check."""

    def __init__(self) -> None:
        self.bases: Dict[str, List[str]] = {}
        self.top_level: Dict[str, Set[str]] = {}
        # (rel path, dotted module, model, field, lineno, col)
        self.id_fields: List[Tuple[str, str, str, str, int, int]] = []
        self.p_model_cache: Dict[str, bool] = {}

    def is_model(self, name: str, seen: Optional[Set[str]] = None) -> bool:
        if name == "BaseModel":
            return True
        cached = self.p_model_cache.get(name)
        if cached is not None:
            return cached
        seen = seen if seen is not None else set()
        if name in seen:
            return False
        seen.add(name)
        result = any(self.is_model(b, seen) for b in self.bases.get(name, []))
        self.p_model_cache[name] = result
        return result


def p_index_file(index: BackendIndex, tree: ast.Module, rel: str) -> None:
    module = p_dotted(rel)
    names: Set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    index.top_level[module] = names

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        index.bases.setdefault(node.name, []).extend(p_base_names(node))
        for stmt in node.body:
            if not isinstance(stmt, ast.AnnAssign) or not isinstance(stmt.target, ast.Name):
                continue
            field = stmt.target.id
            if not (field.endswith("_id") or field.endswith("_ids")) or p_is_class_var(stmt):
                continue
            index.id_fields.append((rel, module, node.name, field, stmt.lineno, stmt.col_offset))


class Registry:
    """The parsed contents of entity_references.py, as data."""

    def __init__(self) -> None:
        self.kinds: Set[str] = set()
        self.stores: Dict[str, Tuple[str, str, int]] = {}
        self.references: Dict[FieldKey, Tuple[str, int]] = {}


def p_list_literal(tree: ast.Module, name: str) -> Optional[List[ast.expr]]:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets: List[ast.expr] = list(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        if any(isinstance(t, ast.Name) and t.id == name for t in targets):
            return list(node.value.elts) if isinstance(node.value, ast.List) else None
    return None


def p_parse_registry(path: Path) -> Registry:
    try:
        tree = ast.parse(path.read_text(), filename=REGISTRY_REL)
    except (OSError, SyntaxError) as exc:
        raise CheckError(f"cannot read the reference registry at {REGISTRY_REL}: {exc}") from exc

    registry = Registry()
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == KIND_ENUM_NAME:
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    registry.kinds.update(t.id for t in stmt.targets if isinstance(t, ast.Name))

    stores = p_list_literal(tree, STORES_NAME)
    references = p_list_literal(tree, REFERENCES_NAME)
    if stores is None or references is None:
        raise CheckError(f"{REGISTRY_REL} must assign {STORES_NAME} and {REFERENCES_NAME} to list literals")

    for element in stores:
        if not isinstance(element, ast.Call):
            continue
        kw = {k.arg: k.value for k in element.keywords if k.arg}
        kind = p_attr_name(kw.get("kind"))
        module = p_const_str(kw.get("module"))
        lookup = p_const_str(kw.get("lookup"))
        if kind and module and lookup:
            registry.stores[kind] = (module, lookup, element.lineno)

    for element in references:
        if not isinstance(element, ast.Call):
            continue
        kw = {k.arg: k.value for k in element.keywords if k.arg}
        module = p_const_str(kw.get("module"))
        model = p_const_str(kw.get("model"))
        field = p_const_str(kw.get("field"))
        target = p_attr_name(kw.get("target"))
        if module and model and field and target:
            registry.references[(module, model, field)] = (target, element.lineno)
    return registry


def p_registry_error(lineno: int, message: str) -> str:
    return f"{REGISTRY_REL}:{lineno}:1: error: [{RULE}] {message}"


def p_check_registry(registry: Registry, index: BackendIndex) -> List[str]:
    """Fail loudly when the registry has drifted from the code it describes."""
    errors: List[str] = []
    for kind, (module, lookup, lineno) in sorted(registry.stores.items()):
        if kind not in registry.kinds:
            errors.append(p_registry_error(lineno, f"store kind '{kind}' is not a member of {KIND_ENUM_NAME}"))
        elif lookup not in index.top_level.get(module, set()):
            errors.append(p_registry_error(lineno, f"store for '{kind}' points at {module}.{lookup}, which no longer exists"))

    declared = {(module, model, field) for _, module, model, field, _, _ in index.id_fields}
    for (module, model, field), (target, lineno) in sorted(registry.references.items()):
        if target not in registry.stores:
            errors.append(p_registry_error(lineno, f"'{model}.{field}' targets '{target}', which has no {STORES_NAME} row"))
        if (module, model, field) not in declared:
            errors.append(p_registry_error(lineno, f"'{model}.{field}' in {module} matches no field on a backend model; it was renamed or removed"))
    return errors


def run_dangling_refs_check(
    root: Path,
    exceptions: Dict[str, List[str]],
    excludes: List[str],
    ignores: Optional[Dict[Path, Set[str]]] = None,
) -> List[str]:
    """Flag ``*_id`` / ``*_ids`` fields on backend models that declare no target entity."""
    backend = root / "backend"
    if not backend.is_dir():
        return []

    index = BackendIndex()
    for pyfile in sorted(backend.rglob("*.py")):
        if is_excluded(pyfile, root, excludes):
            continue
        # Forward slashes even on Windows, so the config's exception globs match there too.
        rel = pyfile.relative_to(root).as_posix()
        try:
            tree = ast.parse(pyfile.read_text(), filename=rel)
        except (OSError, SyntaxError):
            continue
        p_index_file(index, tree, rel)

    registry = p_parse_registry(root / REGISTRY_REL)
    errors = p_check_registry(registry, index)

    for rel, module, model, field, lineno, col in index.id_fields:
        if not index.is_model(model):
            continue
        if (module, model, field) in registry.references:
            continue
        if is_excepted(f"{rel}::{model}.{field}", RULE, exceptions):
            continue
        if ignores and is_lintignored(root / rel, root, RULE, ignores):
            continue
        errors.append(
            f"{rel}:{lineno}:{col + 1}: error: [{RULE}] cross-entity id field "
            f"'{model}.{field}' declares no target entity; add an EntityReference for it in "
            f"{REGISTRY_REL}, or grandfather '{rel}::{model}.{field}' in the dangling-refs exceptions"
        )
    return errors
