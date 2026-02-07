import ast
import hashlib
from typing import List, Dict


def normalize_python_ast(node: ast.AST) -> str:
    """Нормализует AST, заменяя имена переменных и литералы на обобщённые токены"""

    class Normalizer(ast.NodeTransformer):
        def __init__(self):
            self.var_id = 0

        def visit_Name(self, node):
            if isinstance(node.ctx, (ast.Load, ast.Store)):
                node.id = f"__var{self.var_id}__"
                self.var_id += 1
            return node

        def visit_Constant(self, node):
            if isinstance(node.value, str):
                node.value = "__str__"
            elif isinstance(node.value, (int, float)):
                node.value = "__num__"
            elif node.value is None:
                node.value = "__none__"
            return node

    normalized = Normalizer().visit(node)
    ast.fix_missing_locations(normalized)
    return ast.unparse(normalized)


def extract_python_entities(file_path: str) -> List[Dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    entities = []

    def walk(node, name_parts: List[str]):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = "function"
            name = node.name
            # Для вложенных функций добавляем <locals>
            if name_parts:
                full_parts = name_parts + ["<locals>", name]
            else:
                full_parts = [name]
            full_name = ".".join(full_parts)

        elif isinstance(node, ast.ClassDef):
            kind = "class"
            name = node.name
            full_parts = name_parts + [name] if name_parts else [name]
            full_name = ".".join(full_parts)

        else:
            # Обходим дочерние узлы без изменения имени
            for child in ast.iter_child_nodes(node):
                walk(child, name_parts)
            return

        # Сохраняем сущность
        normalized = normalize_python_ast(node)
        ast_hash = hashlib.sha256(normalized.encode("utf-8")).digest()

        entities.append(
            {
                "kind": kind,
                "full_name": full_name,
                "simple_name": name,
                "ast_hash": ast_hash,
            }
        )

        # Рекурсивно обходим тело с обновлённым путём
        new_parts = name_parts + [name]
        for child in node.body:
            walk(child, new_parts)

    walk(tree, [])
    return entities
