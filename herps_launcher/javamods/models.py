"""Typed contracts for the pinned port-pack JSON artifacts, not stdout.

These types deliberately make no compatibility decision. In particular, the
backend's ``works`` verdict is retained as evidence, never as a tested result.
Unknown JSON fields and omitted optional fields survive in independent raw
copies so an exported report can retain the original evidence.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


class SchemaError(ValueError):
    """The tool artifact does not match the audited serialization contract."""


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str


def _object(value: Any, path: str) -> dict:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        raise SchemaError(f"{path}: expected an object with string keys")
    return value


def _required(value: dict, key: str, path: str) -> Any:
    if key not in value:
        raise SchemaError(f"{path}.{key}: missing required field")
    return value[key]


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise SchemaError(f"{path}: expected a string")
    return value


def _strings(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise SchemaError(f"{path}: expected an array of strings")
    return [_string(item, f"{path}[{i}]") for i, item in enumerate(value)]


def _count(value: Any, path: str) -> int:
    # bool subclasses int in Python, but is not a JSON integer count.
    if type(value) is not int or value < 0:
        raise SchemaError(f"{path}: expected a nonnegative integer")
    return value


def _field(value: dict, key: str, path: str, parser=_string):
    return parser(_required(value, key, path), f"{path}.{key}")


def _enum(value: Any, path: str, allowed: tuple[str, ...]) -> str:
    result = _string(value, path)
    if result not in allowed:
        raise SchemaError(f"{path}: expected one of {', '.join(repr(v) for v in allowed)}")
    return result


@dataclass(frozen=True)
class CodeEvidence:
    classes: int
    features: dict[str, int]
    events: list[str]
    examples: dict[str, list[str]]
    raw: dict

    @classmethod
    def parse(cls, value: Any, path: str = "check.code") -> CodeEvidence:
        value = _object(value, path)
        features = _object(_required(value, "features", path), f"{path}.features")
        examples = _object(_required(value, "examples", path), f"{path}.examples")
        return cls(
            _field(value, "classes", path, _count),
            {key: _count(count, f"{path}.features.{key}") for key, count in features.items()},
            _field(value, "events", path, _strings),
            {key: _strings(items, f"{path}.examples.{key}") for key, items in examples.items()},
            deepcopy(value),
        )


@dataclass(frozen=True)
class CheckResult:
    mod_id: str
    name: str
    version: str
    loader: str
    license: str
    verdict: str
    summary: str
    ports: list[str]
    skipped: list[str]
    depends: list[str]
    namespaces: list[str]
    code: CodeEvidence
    raw: dict

    @classmethod
    def parse(cls, value: Any) -> CheckResult:
        path = "check"
        value = _object(value, path)
        return cls(
            _field(value, "mod_id", path),
            _field(value, "name", path),
            _field(value, "version", path),
            _enum(_required(value, "loader", path), f"{path}.loader",
                  ("neoforge", "forge", "fabric", "quilt", "")),
            _field(value, "license", path),
            _enum(_required(value, "verdict", path), f"{path}.verdict", ("works", "partly", "no")),
            _field(value, "summary", path),
            _field(value, "ports", path, _strings),
            _field(value, "skipped", path, _strings),
            _field(value, "depends", path, _strings),
            _field(value, "namespaces", path, _strings),
            CodeEvidence.parse(_required(value, "code", path)),
            deepcopy(value),
        )


@dataclass(frozen=True)
class Census:
    blockstates: int
    item_models: int
    recipes: int
    loot_tables: int
    tags: int
    worldgen: int
    structures: int
    languages: int
    textures: int
    sounds: int
    classes: int
    mixin_configs: int
    raw: dict

    @classmethod
    def parse(cls, value: Any, path: str = "inventory.info.census") -> Census:
        value = _object(value, path)
        fields = ("blockstates", "item_models", "recipes", "loot_tables", "tags", "worldgen",
                  "structures", "languages", "textures", "sounds", "classes", "mixin_configs")
        return cls(*[_field(value, key, path, _count) for key in fields], deepcopy(value))


@dataclass(frozen=True)
class JarInfo:
    mod_id: str
    name: str
    version: str
    license: str
    depends: list[str]
    census: Census
    raw: dict

    @classmethod
    def parse(cls, value: Any, path: str = "inventory.info") -> JarInfo:
        value = _object(value, path)
        return cls(
            *[_field(value, key, path) for key in ("mod_id", "name", "version", "license")],
            _field(value, "depends", path, _strings),
            Census.parse(_required(value, "census", path), f"{path}.census"),
            deepcopy(value),
        )


@dataclass(frozen=True)
class InventoryRecord:
    key: str
    name: str
    version: str
    path: str
    class_: str
    tier: str
    confidence: str
    source: str
    license: str
    client: str
    server: str
    depends: list[str]
    layer: int
    categories: list[str]
    missing: list[str]
    jar: str | None
    info: JarInfo | None
    raw: dict

    @classmethod
    def parse(cls, value: Any, path: str = "inventory") -> InventoryRecord:
        value = _object(value, path)
        return cls(
            *[_field(value, key, path) for key in
              ("key", "name", "version", "path", "class", "tier", "confidence", "source", "license", "client", "server")],
            _field(value, "depends", path, _strings),
            _field(value, "layer", path, _count),
            _strings(value["categories"], f"{path}.categories") if "categories" in value else [],
            _strings(value["missing"], f"{path}.missing") if "missing" in value else [],
            _string(value["jar"], f"{path}.jar") if "jar" in value else None,
            JarInfo.parse(value["info"], f"{path}.info") if "info" in value else None,
            deepcopy(value),
        )


@dataclass(frozen=True)
class CoverageRow:
    key: str
    name: str
    class_: str
    tier: str
    license: str
    license_kind: str
    status: str
    reason: str
    raw: dict

    @classmethod
    def parse(cls, value: Any, path: str = "coverage") -> CoverageRow:
        value = _object(value, path)
        return cls(
            *[_field(value, key, path) for key in ("key", "name", "class", "tier", "license", "license_kind")],
            _enum(_required(value, "status", path), f"{path}.status",
                  ("ported", "partial", "not-yet", "not-needed")),
            _field(value, "reason", path),
            deepcopy(value),
        )


def _records(value: Any, path: str, model) -> list:
    if not isinstance(value, list):
        raise SchemaError(f"{path}: expected an array of records")
    records = [model.parse(item, f"{path}[{i}]") for i, item in enumerate(value)]
    seen = set()
    for record in records:
        if record.key in seen:
            raise SchemaError(f"{path}: duplicate record key {record.key!r}")
        seen.add(record.key)
    return records


def parse_inventory(value: Any) -> list[InventoryRecord]:
    return _records(value, "inventory", InventoryRecord)


def parse_coverage(value: Any) -> list[CoverageRow]:
    return _records(value, "coverage", CoverageRow)
