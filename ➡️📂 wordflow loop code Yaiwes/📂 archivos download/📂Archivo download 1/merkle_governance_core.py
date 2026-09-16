import hashlib
import json
import os
import re
from typing import Dict, List, Optional, Tuple

class MerkleTree:
    """Árbol de Merkle individual para una rama del sistema."""
    def __init__(self, branch_name: str):
        self.branch_name = branch_name
        self.leaves: List[str] = []
        self.tree: List[List[str]] = []

    def add_leaf(self, data: str) -> str:
        """Añade un nodo hoja mediante hash SHA-256."""
        leaf_hash = hashlib.sha256(data.encode('utf-8')).hexdigest()
        self.leaves.append(leaf_hash)
        self._build_tree()
        return leaf_hash

    def _build_tree(self) -> None:
        if not self.leaves:
            self.tree = [[]]
            return
        
        current_level = self.leaves
        self.tree = [current_level]
        
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = hashlib.sha256((left + right).encode('utf-8')).hexdigest()
                next_level.append(combined)
            self.tree.append(next_level)
            current_level = next_level

    def get_root(self) -> str:
        if not self.leaves:
            return hashlib.sha256(self.branch_name.encode('utf-8')).hexdigest()
        return self.tree[-1][0]


class MerkleForest:
    """Bosque de Merkle con 5 ramas independientes y raíz global."""
    BRANCHES = ["core", "extensions", "plugins", "transient", "logs"]

    def __init__(self):
        self.trees: Dict[str, MerkleTree] = {
            branch: MerkleTree(branch) for branch in self.BRANCHES
        }

    def register_artifact(str_data: str, branch: str) -> Tuple[str, str]:
        """Somete un artefacto a una rama específica y devuelve su hash y la raíz del bosque."""
        if branch not in self.BRANCHES:
            raise ValueError(f"Rama inválida '{branch}'. Debe ser una de: {self.BRANCHES}")
        
        leaf_hash = self.trees[branch].add_leaf(str_data)
        global_root = self.get_global_root()
        return leaf_hash, global_root

    def get_global_root(self) -> str:
        """Calcula la raíz global determinista combinando las 5 raíces."""
        combined_roots = "".join([self.trees[b].get_root() for b in self.BRANCHES])
        return hashlib.sha256(combined_roots.encode('utf-8')).hexdigest()


class GovernanceGate:
    """Guardián de Gobernanza para controlar el acceso e inmutabilidad de /core/."""
    def __init__(self, merkle_forest: MerkleForest):
        self.forest = merkle_forest

    def evaluate_ingestion(self, file_path: str, code_content: str, human_override: bool = False) -> Dict:
        """
        [Determinista 90%] Evalúa la ruta y contenido para proteger el núcleo inmutable.
        [LLM 10%] Permite pasar metadatos de intención semántica cuando no son ruta exacta.
        """
        normalized_path = os.path.normpath(file_path).replace("\\", "/")
        is_core = normalized_path.startswith("core/") or "/core/" in normalized_path

        # Regla estricta determinista: Inmutabilidad de /core/
        if is_core and not human_override:
            return {
                "status": "REJECTED_CORE_PROTECTION",
                "reason": "Intento de modificación en /core/ sin anulación humana explícita.",
                "target_branch": "core",
                "merkle_proof": None
            }

        # Asignación determinista de rama
        if is_core:
            target_branch = "core"
        elif normalized_path.startswith("plugins/"):
            target_branch = "plugins"
        elif normalized_path.startswith("extensions/"):
            target_branch = "extensions"
        else:
            target_branch = "transient"

        # Registro criptográfico inmediato en la rama correspondiente
        leaf_hash = self.forest.trees[target_branch].add_leaf(code_content)
        global_root = self.forest.get_global_root()

        return {
            "status": "ALLOWED",
            "file_path": normalized_path,
            "target_branch": target_branch,
            "artifact_hash": leaf_hash,
            "global_merkle_root": global_root,
            "intent_metadata": self._extract_llm_intent_metadata(code_content) # 10% LLM extraction fallback
        }

    def _extract_llm_intent_metadata(self, code_content: str) -> Dict[str, str]:
        """[10% LLM] Extracción ligera determinista de docstrings/intenciones del módulo."""
        docstring_match = re.search(r'"""(.*?)"""', code_content, re.DOTALL)
        intent = docstring_match.group(1).strip() if docstring_match else "Sin documentación explícita."
        return {"doc_intent": intent[:200]}


# Ejemplo de ejecución rápida
if __name__ == "__main__":
    forest = MerkleForest()
    gate = GovernanceGate(forest)

    # Intento 1: Modificación directa no autorizada en /core/
    res1 = gate.evaluate_ingestion("core/engine.py", "def init(): pass")
    print("Test 1 (Core no autorizado):", res1["status"])

    # Intento 2: Ingesta válida en plugin
    res2 = gate.evaluate_ingestion("plugins/custom_tool.py", '"""Plugin para procesamiento"""\ndef run(): return 42')
    print("Test 2 (Plugin autorizado):", res2["status"], "| Global Root:", res2["global_merkle_root"][:10])