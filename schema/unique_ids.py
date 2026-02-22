import sys
import json

ignore = ["target", "lookAt", "range","structures","first","last","start"]
# create a method where you pass in a manifest and it checks to see if the id is unique
# if it is not unique, then it should raise a validation error  
def check(manifest):

    duplicates = []
    ids = []
    print ("Looking at manifest")
    checkNode(manifest, ids, duplicates) 

    if len(duplicates) > 0:
        raise ValueError(f"Duplicate ids: {duplicates}")

def checkNode(node, ids=[], duplicates=[]):
    if type(node) != dict:
        return 

    for key, value in node.items():
        if key == 'id':
            if type(value) != str:
                raise ValueError(f"Id must be a string: {value}")
            if value in ids:
                duplicates.append(value)
            ids.append(value)
        else:
            # Don't look further in fields that point to other resources
            if key in ignore:
                continue

            if type(value) == list:
                for item in value:
                    checkNode(item, ids, duplicates)

            elif type(value) != str:
                checkNode(value, ids, duplicates)    

def main():
    # pass in manifest by command line argument
    # load json from file
    with open(sys.argv[1], 'r') as f:
        manifest = json.load(f)

    check(manifest)                

if __name__ == '__main__':
    main()