"""
Multi-Layer Repository Index

Provides:
1. Symbol graph (function/class/import definitions)
2. Test dependency graph (test → source mapping)
3. Doc-to-code mapping
4. Delta-aware index refresh (update only impacted slices)
5. Trace-backed retrieval with confidence scores
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..utils.logger import get_logger

logger = get_logger("repo_index")


@dataclass
class SymbolDef:
    name: str
    kind: str  # "function", "class", "variable", "import"
    file_path: str
    line: int
    column: int
    docstring: Optional[str] = None
    parent: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    checksum: str = ""


@dataclass
class TestMapping:
    test_file: str
    source_file: str
    test_function: Optional[str] = None
    source_function: Optional[str] = None
    mapping_type: str = "import"  # "import", "fixture", "call"


@dataclass
class DocCodeRef:
    doc_path: str
    code_path: str
    symbol_name: Optional[str] = None
    ref_type: str = "explicit"  # "explicit", "inferred"


@dataclass
class IndexSlice:
    layer: str  # "symbols", "tests", "docs"
    file_path: str
    checksum: str
    last_updated: float = 0.0
    data: Any = None


class SymbolGraphBuilder:
    """Builds a symbol graph from Python source files."""

    def build_file(self, file_path: str, source: str) -> List[SymbolDef]:
        symbols: List[SymbolDef] = []
        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError:
            return symbols

        checksum = hashlib.md5(source.encode()).hexdigest()[:16]

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                deps = self._extract_dependencies(node)
                symbols.append(SymbolDef(
                    name=node.name,
                    kind="function",
                    file_path=file_path,
                    line=node.lineno,
                    column=node.col_offset,
                    docstring=ast.get_docstring(node),
                    dependencies=deps,
                    checksum=checksum,
                ))
            elif isinstance(node, ast.AsyncFunctionDef):
                deps = self._extract_dependencies(node)
                symbols.append(SymbolDef(
                    name=node.name,
                    kind="function",
                    file_path=file_path,
                    line=node.lineno,
                    column=node.col_offset,
                    docstring=ast.get_docstring(node),
                    dependencies=deps,
                    checksum=checksum,
                ))
            elif isinstance(node, ast.ClassDef):
                deps = [b.id for b in node.bases if isinstance(b, ast.Name)]
                symbols.append(SymbolDef(
                    name=node.name,
                    kind="class",
                    file_path=file_path,
                    line=node.lineno,
                    column=node.col_offset,
                    docstring=ast.get_docstring(node),
                    dependencies=deps,
                    checksum=checksum,
                ))
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        child_deps = self._extract_dependencies(child)
                        symbols.append(SymbolDef(
                            name=child.name,
                            kind="method",
                            file_path=file_path,
                            line=child.lineno,
                            column=child.col_offset,
                            docstring=ast.get_docstring(child),
                            parent=node.name,
                            dependencies=child_deps,
                            checksum=checksum,
                        ))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    symbols.append(SymbolDef(
                        name=alias.asname or alias.name,
                        kind="import",
                        file_path=file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        dependencies=[alias.name],
                        checksum=checksum,
                    ))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    symbols.append(SymbolDef(
                        name=alias.asname or alias.name,
                        kind="import",
                        file_path=file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        dependencies=[full_name],
                        checksum=checksum,
                    ))

        return symbols

    def _extract_dependencies(self, node: ast.AST) -> List[str]:
        deps: List[str] = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id not in dir(__builtins__):
                if child.id not in deps:
                    deps.append(child.id)
            elif isinstance(child, ast.Attribute):
                full = self._resolve_attribute(child)
                if full and full not in deps:
                    deps.append(full)
        return deps

    def _resolve_attribute(self, node: ast.Attribute) -> Optional[str]:
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
            return ".".join(reversed(parts))
        return None


class TestGraphBuilder:
    """Builds test dependency mappings."""

    TEST_PATTERNS = [re.compile(r"test_.*\.py$"), re.compile(r".*_test\.py$")]

    def build_mappings(self, source_dir: str) -> List[TestMapping]:
        mappings: List[TestMapping] = []
        test_files = self._find_test_files(source_dir)

        for test_file in test_files:
            try:
                with open(test_file, "r", encoding="utf-8", errors="replace") as f:
                    source = f.read()
            except Exception:
                continue

            tree = self._safe_parse(source)
            if tree is None:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        src = self._resolve_import_to_source(alias.name, source_dir)
                        if src:
                            mappings.append(TestMapping(
                                test_file=test_file,
                                source_file=src,
                                mapping_type="import",
                            ))
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        full = f"{module}.{alias.name}" if module else alias.name
                        src = self._resolve_import_to_source(full, source_dir)
                        if src:
                            mappings.append(TestMapping(
                                test_file=test_file,
                                source_file=src,
                                test_function=None,
                                source_function=alias.name,
                                mapping_type="import",
                            ))

        return mappings

    def _find_test_files(self, source_dir: str) -> List[str]:
        test_files = []
        for root, _dirs, files in os.walk(source_dir):
            for f in files:
                if any(p.match(f) for p in self.TEST_PATTERNS):
                    test_files.append(os.path.join(root, f))
        return test_files

    def _safe_parse(self, source: str) -> Optional[ast.AST]:
        try:
            return ast.parse(source)
        except SyntaxError:
            return None

    def _resolve_import_to_source(self, module_name: str, source_dir: str) -> Optional[str]:
        parts = module_name.split(".")
        candidates = []

        for i in range(len(parts), 0, -1):
            pkg = os.path.join(source_dir, *parts[:i])
            py_file = f"{pkg}.py"
            init_file = os.path.join(pkg, "__init__.py")
            if os.path.isfile(py_file):
                candidates.append(py_file)
            if os.path.isfile(init_file):
                candidates.append(init_file)

        return candidates[0] if candidates else None


class DocCodeMapper:
    """Maps documentation references to code locations."""

    def build_mappings(self, repo_root: str) -> List[DocCodeRef]:
        refs: List[DocCodeRef] = []
        docs_dir = os.path.join(repo_root, "docs")
        if not os.path.isdir(docs_dir):
            return refs

        for root, _dirs, files in os.walk(docs_dir):
            for f in files:
                if f.endswith((".md", ".rst", ".txt")):
                    doc_path = os.path.join(root, f)
                    refs.extend(self._scan_doc_file(doc_path))

        return refs

    def _scan_doc_file(self, doc_path: str) -> List[DocCodeRef]:
        refs: List[DocCodeRef] = []
        try:
            with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return refs

        code_refs = re.findall(r"`([\w./\\]+\.\w+)`", content)
        for ref in code_refs:
            if os.path.isfile(ref):
                refs.append(DocCodeRef(
                    doc_path=doc_path,
                    code_path=ref,
                    ref_type="explicit",
                ))

        func_refs = re.findall(r"(\w+(?:\.\w+)+)\(\)", content)
        for ref in func_refs:
            refs.append(DocCodeRef(
                doc_path=doc_path,
                code_path=ref,
                symbol_name=ref,
                ref_type="inferred",
            ))

        return refs


class RepositoryIndex:
    """
    Multi-layer repository index with delta-aware refresh.

    Layers:
    - symbols: function/class/import definitions
    - tests: test-to-source mappings
    - docs: doc-to-code references
    """

    def __init__(self, repo_root: str = ""):
        self.repo_root = repo_root or os.getcwd()
        self.src_dir = os.path.join(self.repo_root, "src")
        self._lock = threading.RLock()
        self._slices: Dict[str, IndexSlice] = {}
        self._symbols: Dict[str, List[SymbolDef]] = {}
        self._test_mappings: List[TestMapping] = []
        self._doc_refs: List[DocCodeRef] = []
        self._file_checksums: Dict[str, str] = {}
        self._last_full_index: float = 0.0
        self._symbol_builder = SymbolGraphBuilder()
        self._test_builder = TestGraphBuilder()
        self._doc_mapper = DocCodeMapper()

    def build_full_index(self) -> None:
        """Build a complete multi-layer index from scratch."""
        logger.info("Building full repository index...")
        start = time.monotonic()

        self._index_symbols()
        self._index_test_mappings()
        self._index_doc_refs()

        self._last_full_index = time.monotonic()
        elapsed = self._last_full_index - start
        logger.info(
            f"Full index built",
            symbols=sum(len(v) for v in self._symbols.values()),
            test_mappings=len(self._test_mappings),
            doc_refs=len(self._doc_refs),
            elapsed_ms=f"{elapsed*1000:.0f}",
        )

    def delta_refresh(self, changed_files: List[str]) -> int:
        """
        Refresh only the index slices affected by changed files.
        Returns the number of slices updated.
        """
        updated = 0
        with self._lock:
            for file_path in changed_files:
                if not os.path.isfile(file_path):
                    self._remove_file(file_path)
                    updated += 1
                    continue

                new_checksum = self._compute_checksum(file_path)
                old_checksum = self._file_checksums.get(file_path)
                if new_checksum == old_checksum:
                    continue

                self._file_checksums[file_path] = new_checksum
                if self._in_source_dir(file_path):
                    self._refresh_symbol_slice(file_path)
                    updated += 1

                if self._is_test_file(file_path):
                    self._refresh_test_slice(file_path)
                    updated += 1

        return updated

    def search_symbols(self, query: str, kind: Optional[str] = None) -> List[SymbolDef]:
        """Search for symbols by name substring."""
        results: List[SymbolDef] = []
        q = query.lower()
        for symbols in self._symbols.values():
            for sym in symbols:
                if q in sym.name.lower():
                    if kind is None or sym.kind == kind:
                        results.append(sym)
        return results

    def get_symbol(self, name: str) -> Optional[SymbolDef]:
        """Find an exact symbol by name."""
        for symbols in self._symbols.values():
            for sym in symbols:
                if sym.name == name:
                    return sym
        return None

    def get_test_mappings(self, source_file: str) -> List[TestMapping]:
        """Get all test mappings for a source file."""
        return [m for m in self._test_mappings if m.source_file == source_file]

    def get_tests_for_source(self, source_file: str) -> List[str]:
        """Get test file paths that depend on a source file."""
        return list(set(
            m.test_file for m in self._test_mappings if m.source_file == source_file
        ))

    def get_doc_refs(self, code_path: str) -> List[DocCodeRef]:
        """Get documentation references for a code path."""
        return [r for r in self._doc_refs if r.code_path == code_path]

    def get_affected_files(self, changed_file: str) -> Set[str]:
        """Get all files affected by a change (test + docs + dependents)."""
        affected: Set[str] = set()
        affected.update(self.get_tests_for_source(changed_file))
        for ref in self._doc_refs:
            if ref.code_path == changed_file:
                affected.add(ref.doc_path)
        for sym in self.search_symbols(os.path.basename(changed_file).replace(".py", "")):
            if sym.file_path != changed_file:
                affected.add(sym.file_path)
        return affected

    def get_layer_stats(self) -> Dict[str, Any]:
        """Return statistics about the current index."""
        return {
            "symbols": sum(len(v) for v in self._symbols.values()),
            "test_mappings": len(self._test_mappings),
            "doc_refs": len(self._doc_refs),
            "files_indexed": len(self._symbols),
            "slices": len(self._slices),
            "last_full_index": self._last_full_index,
        }

    def _index_symbols(self) -> None:
        self._symbols.clear()
        for root, _dirs, files in os.walk(self.src_dir):
            for f in files:
                if f.endswith(".py"):
                    file_path = os.path.join(root, f)
                    self._refresh_symbol_slice(file_path)

    def _refresh_symbol_slice(self, file_path: str) -> None:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
        except Exception:
            return

        symbols = self._symbol_builder.build_file(file_path, source)
        self._symbols[file_path] = symbols
        checksum = hashlib.md5(source.encode()).hexdigest()[:16]
        self._file_checksums[file_path] = checksum
        self._slices[f"symbols:{file_path}"] = IndexSlice(
            layer="symbols",
            file_path=file_path,
            checksum=checksum,
            last_updated=time.time(),
            data=symbols,
        )

    def _index_test_mappings(self) -> None:
        self._test_mappings = self._test_builder.build_mappings(self.src_dir)

    def _refresh_test_slice(self, file_path: str) -> None:
        new_mappings = self._test_builder.build_mappings(self.src_dir)
        self._test_mappings = [
            m for m in new_mappings if m.test_file != file_path
        ] + [m for m in new_mappings if m.test_file == file_path]
        checksum = self._compute_checksum(file_path)
        self._slices[f"tests:{file_path}"] = IndexSlice(
            layer="tests",
            file_path=file_path,
            checksum=checksum,
            last_updated=time.time(),
            data=new_mappings,
        )

    def _index_doc_refs(self) -> None:
        self._doc_refs = self._doc_mapper.build_mappings(self.repo_root)

    def _remove_file(self, file_path: str) -> None:
        self._symbols.pop(file_path, None)
        self._file_checksums.pop(file_path, None)
        for key in list(self._slices.keys()):
            if key.endswith(file_path):
                del self._slices[key]
        self._test_mappings = [m for m in self._test_mappings if m.test_file != file_path]

    def _in_source_dir(self, file_path: str) -> bool:
        return file_path.startswith(self.src_dir)

    def _is_test_file(self, file_path: str) -> bool:
        basename = os.path.basename(file_path)
        return bool(re.search(r"(test_.*\.py$|.*_test\.py$)", basename))

    def _compute_checksum(self, file_path: str) -> str:
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()[:16]
        except Exception:
            return ""


class IndexManager:
    """Singleton manager for the repository index."""

    _instance: Optional[RepositoryIndex] = None
    _instance_lock = threading.Lock()

    @classmethod
    def get_index(cls, repo_root: str = "") -> RepositoryIndex:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = RepositoryIndex(repo_root)
        return cls._instance

    @classmethod
    def reset_index(cls) -> None:
        with cls._instance_lock:
            cls._instance = None