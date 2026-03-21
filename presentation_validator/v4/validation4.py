from ast import main
from pathlib import Path
import json
import sys
from presentation_validator.model import ValidationResult
from presentation_validator.v3.schemavalidator import convertValidationError
from presentation_validator.v4.unique_ids import check

from jsonschema import Draft202012Validator
from jsonschema.exceptions import relevance
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

SCHEMA_DIR = Path("schema/v4")
BASE_URI = "https://iiif.io/api/presentation/4.0/schema"

def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def validate(instance):
    # Read all JSON documents in the SCHEMA_DIR and store them in schemas
    schemas = {}
    
    # Iterate through all JSON files in the schema directory
    for json_file in SCHEMA_DIR.glob("*.json"):
        try:
            schema_content = load_schema(json_file)
            # Use the filename as a URI-like key for consistency
            uri = f"{BASE_URI}/{json_file.name}"
            schemas[uri] = schema_content
            #print(f"Loaded schema: {json_file.name}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Failed to load schema from {json_file}: {e}")

    registry = Registry().with_resources(
        (uri, Resource.from_contents(schema, default_specification=DRAFT202012))
        for uri, schema in schemas.items()
    )

    main = schemas[f"{BASE_URI}/main.json"]
    validator = Draft202012Validator(main, registry=registry)

    result = ValidationResult()

    results = validator.iter_errors(instance)
    errors = sorted(results, key=relevance)

    if errors:
        result.passed = False
        errorCount = 1
        # Now create some useful messsages to pass on
        for err in errors:
            result.errorList.append(convertValidationError(err, errorCount, len(errors)))
            
            errorCount += 1
    else:
        result.passed = True

    duplicate_ids = check(instance)
    if duplicate_ids:
        result.passed = False

        # Add all of the examples of duplicated ids
        result.errorList.extend(duplicate_ids)
    
    return result

def main():
    # Check if command line argument is provided
    if len(sys.argv) < 2:
        print("Usage: python validation4.py <json_file>")
        sys.exit(1)
    
    # Get filename from first command line argument
    filename = sys.argv[1]
    
    try:
        # Read the JSON file and store in instance
        with open(filename, 'r', encoding='utf-8') as f:
            instance = json.load(f)
        print(f"Checking: {filename}")
        
        # Validate the instance
        validate(instance)
        
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{filename}': {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()