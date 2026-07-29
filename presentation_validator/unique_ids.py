import sys
import json
from typing import List, Set, Tuple
from presentation_validator.model import ErrorDetail
from presentation_validator.v3.schemavalidator import create_snippet

IGNORE: Set[str] = {
    "target",
    "lookAt",
    "range",
    "structures",
    "first",
    "last",
    "start",
    "source",
    "body",
    "scope",
}
MAX_DEPTH: int = 1000


class MaxDepthExceeded(Exception):
    pass


def check(manifest) -> List[ErrorDetail]:
    """
    Checks that all values associated with the key 'id' are globally unique.

    Args:
        manifest: the root JSON dict

    Returns:
        A generator of ErrorDetail objects for each duplicate ID found.
        The generator is empty if no duplicates are found.

    Raises:
        MaxDepthExceeded: If MAX_DEPTH is exceeded in the search.
    """
    seen_ids = []
    # stores tuples of (search depth, path, node)
    stack: List[Tuple[int, str, dict]] = [(0, "", manifest)]
    while stack:
        depth, path, node = stack.pop()
        if depth > MAX_DEPTH:
            raise MaxDepthExceeded(f"Max search depth {MAX_DEPTH} exceeded at {node}")
        for key, value in filter(lambda x: x[0] not in IGNORE, node.items()):
            if key == "id":
                if value in seen_ids:
                    yield ErrorDetail(
                        f"Duplicate id found",
                        "The id field must be unique",
                        f"Duplicate id: {value}",
                        path + "/" + key,
                        create_snippet(node),
                        None,
                    )
                seen_ids.append(value)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    # only dicts can contain IDs
                    if isinstance(item, dict):
                        stack.append((depth + 1, f"{path}/{key}[{i}]", item))


def main():
    # pass in manifest by command line argument
    # load json from file
    with open(sys.argv[1], "r") as f:
        manifest = json.load(f)

    errors = check(manifest)
    for err in errors:
        print(err)


if __name__ == "__main__":
    main()
