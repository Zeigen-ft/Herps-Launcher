"""Supplement port-pack's lossy census with passive, bounded safety evidence.

This is a preflight, not a Java loader, decompiler, or replacement porter.
Method attributes (including Code) are skipped, never interpreted or executed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import struct
import tomllib
import zipfile

from herps_launcher.core import GAME, archive, digest
from .models import Diagnostic


@dataclass
class JarMetadata:
    mod_id: str = ""
    name: str = ""
    version: str = ""
    loader: str = ""
    license: str = ""
    required_dependencies: dict[str, str | list[str]] = field(default_factory=dict)
    mixins: tuple[str, ...] = ()
    access_changes: tuple[str, ...] = ()
    class_count: int = 0
    unreadable_classes: tuple[str, ...] = ()
    diagnostics: list[Diagnostic] = field(default_factory=list)
    raw: dict = field(default_factory=dict)
    sha256: str = ""


def _text(value, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    return value


def _constraint(value) -> str | list[str]:
    if isinstance(value, str) and value.strip():
        return value
    if isinstance(value, list) and value and all(isinstance(v, str) and v.strip() for v in value):
        return value
    raise ValueError("Dependency constraints must be strings or nonempty lists of strings")


def _manifest(data: bytes) -> dict[str, str]:
    # Unfold continuation lines specified by the JAR manifest format.
    unfolded = re.sub(r"\r?\n ", "", data.decode("utf-8"))
    return {key.lower(): value.strip() for line in unfolded.splitlines()
            if ":" in line for key, value in [line.split(":", 1)]}


def _class_metadata_readable(data: bytes) -> bool:
    """Validate structure and reference kinds, skipping every attribute body.

    Deliberately limited to class-file versions through Java 25, the pinned
    preparer's major version. Newer/preview formats require separate evidence.
    """
    cursor = 0

    def take(n):
        nonlocal cursor
        if n < 0 or cursor + n > len(data):
            raise ValueError("truncated class")
        value = data[cursor:cursor + n]
        cursor += n
        return value

    def u2():
        return int.from_bytes(take(2), "big")

    try:
        if take(4) != b"\xca\xfe\xba\xbe":
            return False
        minor, major = u2(), u2()
        if not 45 <= major <= 69 or minor == 65535 or (major >= 56 and minor != 0):
            return False
        count = u2()
        if count < 2:
            return False
        pool = [None] * count
        index = 1
        while index < count:
            tag = take(1)[0]
            if tag == 1:
                # Modified UTF-8 is not ordinary UTF-8. Keep bytes: structural
                # validation needs no string decoding or interpretation.
                value = take(u2())
            elif tag in (3, 4):
                value = take(4)
            elif tag in (5, 6):
                value = take(8)
            elif tag in (7, 8, 16, 19, 20):
                value = u2()
            elif tag in (9, 10, 11, 12, 17, 18):
                value = (u2(), u2())
            elif tag == 15:
                value = (take(1)[0], u2())
            else:
                return False
            pool[index] = (tag, value)
            if tag in (5, 6):
                index += 1
                if index >= count:
                    return False
            index += 1

        def ref(index, tags):
            if not 0 < index < count or pool[index] is None or pool[index][0] not in tags:
                raise ValueError("invalid constant-pool reference")

        for entry in pool[1:]:
            if entry is None:
                continue
            tag, value = entry
            if tag in (7, 8, 16, 19, 20):
                ref(value, (1,))
            elif tag in (9, 10, 11):
                ref(value[0], (7,))
                ref(value[1], (12,))
            elif tag == 12:
                ref(value[0], (1,))
                ref(value[1], (1,))
            elif tag in (17, 18):
                ref(value[1], (12,))
            elif tag == 15:
                if not 1 <= value[0] <= 9:
                    return False
                ref(value[1], (9, 10, 11))

        def attributes():
            for _ in range(u2()):
                ref(u2(), (1,))
                take(int.from_bytes(take(4), "big"))

        u2()  # access_flags
        ref(u2(), (7,))
        super_class = u2()
        if super_class:
            ref(super_class, (7,))
        for _ in range(u2()):
            ref(u2(), (7,))
        for _ in range(2):  # fields, then methods
            for _ in range(u2()):
                u2()
                ref(u2(), (1,))
                ref(u2(), (1,))
                attributes()
        attributes()
        return cursor == len(data)
    except (ValueError, IndexError, struct.error):
        return False


def inspect_jar(path: Path) -> JarMetadata:
    result = JarMetadata()
    try:
        result.sha256 = digest(path)
        files = archive(path)
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as error:
        result.diagnostics.append(Diagnostic("insufficient_evidence", f"Cannot inspect JAR: {error}"))
        return result
    result.raw["archive_entries"] = sorted(files)
    manifest = {}
    try:
        if "META-INF/MANIFEST.MF" in files:
            manifest = _manifest(files["META-INF/MANIFEST.MF"])
            result.raw["manifest"] = manifest
        metadata_keys = [key for key in ("fabric.mod.json", "META-INF/neoforge.mods.toml", "META-INF/mods.toml") if key in files]
        if len(metadata_keys) != 1:
            raise ValueError("Expected exactly one Fabric, Forge, or NeoForge metadata file")
        key = metadata_keys[0]
        result.raw["metadata_text"] = {key: files[key].decode("utf-8", errors="replace")}

        def unique_pairs(pairs):
            values = {}
            for name, value in pairs:
                if name in values:
                    raise ValueError(f"Duplicate JSON key: {name}")
                values[name] = value
            return values

        metadata = json.loads(files[key], object_pairs_hook=unique_pairs) if key.endswith(".json") else tomllib.loads(files[key].decode("utf-8"))
        result.raw[key] = metadata
        if not isinstance(metadata, dict):
            raise ValueError("Mod metadata must be an object")
        mixins = []
        if key == "fabric.mod.json":
            result.loader = "fabric"
            result.mod_id = _text(metadata.get("id"), "id")
            result.version = _text(metadata.get("version"), "version")
            result.name = _text(metadata.get("name", result.mod_id), "name")
            licence = metadata.get("license", "")
            if isinstance(licence, list) and all(isinstance(item, str) for item in licence):
                licence = " OR ".join(licence)
            result.license = _text(licence, "license")
            dependencies = metadata.get("depends", {})
            if not isinstance(dependencies, dict):
                raise ValueError("depends must be an object")
            result.required_dependencies = {_text(dep, "dependency id"): _constraint(value) for dep, value in dependencies.items()}
            declared = metadata.get("mixins", [])
            if not isinstance(declared, list):
                raise ValueError("mixins must be a list")
            for item in declared:
                mixins.append(_text(item.get("config") if isinstance(item, dict) else item, "mixin config"))
            if metadata.get("accessWidener"):
                result.access_changes += (_text(metadata["accessWidener"], "accessWidener"),)
            if metadata.get("jars"):
                result.diagnostics.append(Diagnostic("unsupported_feature", "Nested JAR dependencies are not resolved by passive preflight"))
            if metadata.get("entrypoints"):
                result.diagnostics.append(Diagnostic("unsupported_feature", "Declared Fabric Java entrypoints cannot run without a working Java bridge"))
        else:
            result.loader = "neoforge" if "neoforge" in key else "forge"
            mods = metadata.get("mods", [])
            if not isinstance(mods, list) or not mods or not all(isinstance(item, dict) for item in mods):
                raise ValueError("mods must be a nonempty table array")
            if len(mods) != 1:
                result.diagnostics.append(Diagnostic("insufficient_evidence", "Multiple mod records in one JAR need separate evidence"))
            mod = mods[0]
            result.mod_id = _text(mod.get("modId"), "modId")
            result.name = _text(mod.get("displayName", result.mod_id), "displayName")
            result.version = _text(mod.get("version"), "version")
            if result.version == "${file.jarVersion}":
                result.version = manifest.get("implementation-version", "")
            result.license = _text(metadata.get("license", ""), "license")
            dependencies = metadata.get("dependencies", {})
            if not isinstance(dependencies, dict):
                raise ValueError("dependencies must be a table")
            declared = dependencies.get(result.mod_id, [])
            if not isinstance(declared, list):
                raise ValueError("dependencies must be table arrays")
            for item in declared:
                if not isinstance(item, dict):
                    raise ValueError("Dependency entry must be a table")
                mandatory = item.get("mandatory", True)
                if not isinstance(mandatory, bool):
                    raise ValueError("mandatory must be boolean")
                dependency_type = item.get("type", "required" if mandatory else "optional")
                if dependency_type not in ("required", "optional", "incompatible", "discouraged"):
                    raise ValueError("Unknown dependency type")
                if dependency_type in ("incompatible", "discouraged"):
                    result.diagnostics.append(Diagnostic("insufficient_evidence", "Negative dependency constraints need separate compatibility evidence"))
                if dependency_type == "required":
                    dep = _text(item.get("modId"), "dependency modId")
                    if dep in result.required_dependencies:
                        raise ValueError(f"Duplicate required dependency: {dep}")
                    result.required_dependencies[dep] = _constraint(item.get("versionRange", "*"))
            if metadata.get("loaderVersion"):
                result.required_dependencies["javafml"] = _constraint(metadata["loaderVersion"])
            declared = metadata.get("mixins", [])
            if not isinstance(declared, list):
                raise ValueError("mixins must be a table array")
            for item in declared:
                mixins.append(_text(item.get("config") if isinstance(item, dict) else item, "mixin config"))
            # NeoForge permits an explicit list in addition to the conventional file.
            for item in metadata.get("accessTransformers", []):
                result.access_changes += (_text(item.get("file") if isinstance(item, dict) else item, "access transformer"),)
        if manifest.get("mixinconfigs"):
            mixins.extend(config.strip() for config in manifest["mixinconfigs"].split(",") if config.strip())
        result.mixins = tuple(sorted(set(mixins)))
        if not re.fullmatch(r"[a-z][a-z0-9_\-]{0,127}", result.mod_id) or not result.version or "${" in result.version:
            raise ValueError("Missing, unresolved, or invalid mod identity/version")
        if manifest.get("fmlat"):
            result.access_changes += tuple("META-INF/" + part.strip() for part in manifest["fmlat"].split() if part.strip())
        if "META-INF/accesstransformer.cfg" in files:
            result.access_changes += ("META-INF/accesstransformer.cfg",)
        if any(name.endswith(".jar") for name in files):
            result.diagnostics.append(Diagnostic("unsupported_feature", "Embedded JARs require separate dependency and class evidence"))
        if "META-INF/coremods.json" in files or any(manifest.get(key) for key in ("fmlcoreplugin", "premain-class", "agent-class", "launcher-agent-class")):
            result.diagnostics.append(Diagnostic("unsupported_feature", "Coremods or Java agents require unsupported executable loader hooks"))
    except (ValueError, TypeError, UnicodeError) as error:
        result.diagnostics.append(Diagnostic("insufficient_evidence", f"Incomplete or malformed mod metadata: {error}"))
    result.class_count = sum(name.endswith(".class") for name in files)
    result.unreadable_classes = tuple(name for name, data in files.items() if name.endswith(".class") and not _class_metadata_readable(data))
    if result.unreadable_classes:
        result.diagnostics.append(Diagnostic("unreadable_classes", "Unreadable, truncated, preview, or unsupported class metadata: " + ", ".join(result.unreadable_classes)))
    if result.mixins:
        result.diagnostics.append(Diagnostic("required_mixins", "Mixin declarations require Java hooks unavailable in Horizon: " + ", ".join(result.mixins)))
    result.access_changes = tuple(sorted(set(result.access_changes)))
    if result.access_changes:
        result.diagnostics.append(Diagnostic("unsupported_feature", "Access wideners/transformers require unsupported Java access changes: " + ", ".join(result.access_changes)))
    return result


def version_matches(version: str, constraint: str | list[str]) -> bool | None:
    """Conservative subset of Fabric/Maven numeric constraints; None = unknown.

    No attempt is made to normalize snapshots, prereleases or arbitrary loader
    syntax. Unsupported expressions remain evidence gaps, never successful.
    """
    if isinstance(constraint, list):
        results = [version_matches(version, part) for part in constraint]
        return True if True in results else (None if None in results else False)
    constraint = constraint.strip()
    if constraint in ("*", ""):
        return True
    if "||" in constraint:
        return version_matches(version, constraint.split("||"))
    if not re.fullmatch(r"\d+(?:\.\d+)*", version):
        return None

    def numbers(value):
        return tuple(map(int, value.split(".")))

    def compare(value):
        a, b = numbers(version), numbers(value)
        size = max(len(a), len(b))
        a, b = a + (0,) * (size - len(a)), b + (0,) * (size - len(b))
        return (a > b) - (a < b)

    interval = re.fullmatch(r"([\[(])\s*(\d+(?:\.\d+)*)?\s*,\s*(\d+(?:\.\d+)*)?\s*([\])])", constraint)
    if interval:
        left, lower, upper, right = interval.groups()
        return (lower is None or compare(lower) >= (0 if left == "[" else 1)) and (upper is None or compare(upper) <= (0 if right == "]" else -1))
    exact = re.fullmatch(r"\[(\d+(?:\.\d+)*)\]", constraint)
    if exact:
        return compare(exact[1]) == 0
    wildcard = re.fullmatch(r"(\d+(?:\.\d+)*)\.(?:\*|x|X)", constraint)
    if wildcard:
        prefix = numbers(wildcard[1])
        return numbers(version)[:len(prefix)] == prefix
    tokens = re.findall(r"(?:>=|<=|>|<|=)?\s*\d+(?:\.\d+)*", constraint)
    if not tokens or re.sub(r"\s+", "", "".join(tokens)) != re.sub(r"\s+", "", constraint):
        return None
    results = []
    for token in tokens:
        operator, number = re.fullmatch(r"(>=|<=|>|<|=)?\s*(\d+(?:\.\d+)*)", token).groups()
        difference = compare(number)
        results.append({None: difference == 0, "=": difference == 0, ">": difference > 0,
                        ">=": difference >= 0, "<": difference < 0, "<=": difference <= 0}[operator])
    return all(results)


def assess_dependencies(metadata: JarMetadata, available: dict[str, JarMetadata], minecraft: str = GAME) -> list[Diagnostic]:
    diagnostics = []
    for dep, constraint in metadata.required_dependencies.items():
        if dep in ("fabricloader", "fabric-loader", "forge", "neoforge", "quilt_loader", "quiltloader", "quilt-loader", "java", "javafml"):
            diagnostics.append(Diagnostic("unsupported_feature", f"Required Java runtime/loader {dep} ({constraint}) has no working Java bridge"))
            continue
        if dep == "minecraft":
            version = minecraft
        elif dep in available:
            version = available[dep].version
            if available[dep].diagnostics:
                diagnostics.append(Diagnostic("insufficient_evidence", f"Dependency {dep} has incomplete or unsupported metadata"))
        else:
            diagnostics.append(Diagnostic("missing_dependency", f"Required dependency {dep} ({constraint}) is absent from user-provided files"))
            continue
        matches = version_matches(version, constraint)
        if matches is False:
            diagnostics.append(Diagnostic("version_mismatch", f"{dep} version {version} does not satisfy {constraint}"))
        elif matches is None:
            diagnostics.append(Diagnostic("insufficient_evidence", f"Cannot establish whether {dep} version {version} satisfies {constraint}"))
    if "minecraft" not in metadata.required_dependencies:
        diagnostics.append(Diagnostic("insufficient_evidence", "No required Minecraft version constraint was provided"))
    return diagnostics
