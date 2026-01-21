from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import urljoin, urlparse
from pathlib import PurePosixPath

from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

def iter_refs(node: Any, path: str = "#") -> Iterable[Tuple[str, str]]:
    """
    Yield ($ref_value, json_pointer_path_in_schema) for every $ref in a schema tree.
    """
    #print (f"Travesring {node}")
    if isinstance(node, dict):
        if "$ref" in node and isinstance(node["$ref"], str):
            yield node["$ref"], path + "/$ref"
        for k, v in node.items():
            yield from iter_refs(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from iter_refs(v, f"{path}/{i}")


def build_registry_from_dir(schema_dir: str | Path) -> Tuple[Registry, Dict[str, Dict[str, Any]]]:
    """
    Load all *.json schemas under schema_dir into a referencing.Registry.

    Each resource is keyed by:
      - its $id, if present, else
      - a file:// URI for its absolute path.
    """
    schema_dir = Path(schema_dir)
    registry = Registry()
    by_uri: Dict[str, Dict[str, Any]] = {}

    for path in schema_dir.rglob("*.json"):
        with path.open("r", encoding="utf-8") as f:
            schema = json.load(f)

        print (f"Loading {path.name}")
        uri = schema.get("$id")
        if not uri:
            uri = path.resolve().as_uri()  # file:///.../schema.json

        resource = Resource.from_contents(schema)
        registry = registry.with_resource(uri, resource)
        if uri in by_uri:
            raise Exception(f"Duplicate schema ID {uri} found in {path.name}")

        by_uri[uri] = schema

    return registry, by_uri


def find_missing_refs_in_dir(schema_dir: str | Path) -> List[Dict[str, str]]:
    """
    Returns a list of unresolved $refs across all schemas in schema_dir.
    """
    registry, schemas = build_registry_from_dir(schema_dir)
    missing: List[Dict[str, str]] = []
    for base_uri, schema in schemas.items():
        resolver = registry.resolver(base_uri=base_uri)

        for ref, where in iter_refs(schema):
            # Make relative refs absolute against the schema's base URI
            target = urljoin(base_uri, ref)

            try:
                resolver.lookup(target)
            except Unresolvable:
                missing.append(
                    {
                        "schema": base_uri,
                        "ref": ref,
                        "where": where,
                        "resolved_target": target,
                    }
                )

    return missing


if __name__ == "__main__":
    problems = find_missing_refs_in_dir(Path(__file__).resolve().parent)
    if problems:
        print("\nMissing/unresolvable $refs:")
        for p in problems:
            print(f"- In {p['schema'].split("/")[-1]}:\n at {p['where']}: {p['ref']}  (→ {p['resolved_target']})\n")
        raise SystemExit(2)
    else:
        print("All $refs resolved.")