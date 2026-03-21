import sys
import json
from presentation_validator.model import ErrorDetail
from presentation_validator.v3.schemavalidator import create_snippet

ignore = ["target", "lookAt", "range","structures","first","last","start","source"]
# create a method where you pass in a manifest and it checks to see if the id is unique
# if it is not unique, then it should raise a validation error  
def check(manifest):

    duplicates = []
    ids = []
    checkNode(manifest, ids, duplicates) 

    if len(duplicates) > 0:
        return duplicates
    else:
        return None    

def checkNode(node, ids=[], duplicates=[], path = ""):
    if type(node) != dict:
        return 

    for key, value in node.items():
        if key == 'id':
            if type(value) != str:
                raise ValueError(f"Id must be a string: {value}")
            if value in ids:
                duplicates.append(ErrorDetail(
                    f"Duplicate id found",
                    "The id field must be unique",
                    f"Duplicate id: {value}",
                    path + "/" + key,
                    create_snippet(node),
                    None
                ))
            ids.append(value)
        else:
            # Don't look further in fields that point to other resources
            if key in ignore:
                continue

            if type(value) == list:
                count = 0
                for item in value:
                    checkNode(item, ids, duplicates, path + "/" + key + "[" + str(count) + "]")
                    count += 1

            elif type(value) != str:
                checkNode(value, ids, duplicates, path + "/" + key)    

def main():
    # pass in manifest by command line argument
    # load json from file
    with open(sys.argv[1], 'r') as f:
        manifest = json.load(f)

    check(manifest)                

if __name__ == '__main__':
    main()