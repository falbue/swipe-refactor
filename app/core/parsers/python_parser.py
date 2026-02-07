import ast
import hashlib
from typing import Dict, List, Optional, Tuple


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


def _iter_python_entities(tree: ast.AST):
    """Итератор по сущностям Python (классы/функции) с полными именами"""

    def walk(node, name_parts: List[str]):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = "function"
            name = node.name
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
            for child in ast.iter_child_nodes(node):
                yield from walk(child, name_parts)
            return

        yield {
            "kind": kind,
            "full_name": full_name,
            "simple_name": name,
            "node": node,
        }

        new_parts = name_parts + [name]
        for child in node.body:
            yield from walk(child, new_parts)

    yield from walk(tree, [])


def _split_full_name(full_name: str) -> Tuple[str, int]:
    """Разделяет имя сущности и индекс при наличии суффикса #N"""
    if "#" in full_name:
        base, suffix = full_name.rsplit("#", 1)
        if suffix.isdigit():
            return base, int(suffix)
    return full_name, 1


def extract_python_entities(file_path: str) -> List[Dict]:
    """Извлекает сущности из файла и возвращает их метаданные с хэшом AST"""
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    entities = []
    for entity in _iter_python_entities(tree):
        normalized = normalize_python_ast(entity["node"])
        ast_hash = hashlib.sha256(normalized.encode("utf-8")).digest()
        entities.append(
            {
                "kind": entity["kind"],
                "full_name": entity["full_name"],
                "simple_name": entity["simple_name"],
                "ast_hash": ast_hash,
            }
        )
    return entities


def find_python_entity_block(
    file_path: str, kind: Optional[str], full_name: str
) -> Dict:
    """Находит блок кода сущности по имени/типу и возвращает его диапазон и текст"""
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"Syntax error in file: {file_path}") from exc

    target_name, target_index = _split_full_name(full_name)
    seen = 0
    target_node = None
    target_kind = None

    for entity in _iter_python_entities(tree):
        if entity["full_name"] != target_name:
            continue
        if kind and entity["kind"] != kind:
            continue
        seen += 1
        if seen == target_index:
            target_node = entity["node"]
            target_kind = entity["kind"]
            break

    if not target_node:
        raise ValueError(f"Entity not found: {full_name}")

    start_line = getattr(target_node, "lineno", None)
    end_line = getattr(target_node, "end_lineno", None)
    code = ast.get_source_segment(source, target_node)

    if code is None and start_line is not None:
        lines = source.splitlines()
        if end_line is None:
            end_line = start_line
        code = "\n".join(lines[start_line - 1 : end_line])

    if code is None or start_line is None:
        raise ValueError(f"Unable to extract code for: {full_name}")

    return {
        "kind": target_kind,
        "full_name": full_name,
        "start_line": start_line,
        "end_line": end_line or start_line,
        "code": code,
    }
