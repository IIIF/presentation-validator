#!/usr/bin/python

from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError, SchemaError, best_match, relevance
import json
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

def printPath(pathObj, fields):
    path = ''
    for item in pathObj:
        if isinstance(item, int):
            path += u'[{}]'.format(item)
        else:
            path += u'/'    
            path += item

    path += '/[{}]'.format(fields)
    return path    

def validate(data, version, url=None):
    if version == '3.0':
        with open('schema/iiif_3_0.json') as json_file:
            try:
                schema = json.load(json_file)
            except ValueError as err:
                print ('Failed to load JSON due to: {}'.format(err))
                raise

    error = ''
    errorsJson = []
    try:
        validator = Draft7Validator(schema)
        validator.validate(json.loads(data))
        print ('Passed Validation!')
        okay = 1
    except SchemaError as err:    
        print('Problem with the supplied schema:\n')
        print(err)
        raise
    except ValidationError as err:    
        results = validator.iter_errors(json.loads(data))

        okay = 0
        #print (best_match(results))
        errors = sorted(results, key=relevance)
        #errors = [best_match(results)]
        errorCount = 1
        for err in errors:
            detail = ''
            if err and 'title' in err.schema:
                detail = err.schema['title']
            description = ''    
            if 'description' in err.schema:
                detail += ' ' + err.schema['description']
            context = err.instance
            if isinstance(context, dict):
                for key in context:
                    if isinstance(context[key], list): 
                        context[key] = '[ ... ]'
                    elif isinstance(context[key], dict):
                        context[key] = '{ ... }'

            #print (json.dumps(err.schema,indent=2))
            errorsJson.append({
                'title': 'Error {} of {}.\n Message: {}'.format(errorCount, len(errors), err.message),
                'detail': detail,
                'description': description,
                'path': printPath(err.path, err.message),
                'context': context,
                'error': err
    
            })
            errorCount +=1 

    return {
        'okay': okay,
        'warnings': [],
        'error': error,
        'errorList': errorsJson,
        'url': url
    }

def json_path(absolute_path):
    path = '$'
    for elem in absolute_path:
        if isinstance(elem, int):
            path += '[' + str(elem) + ']'
        else:
            path += '.' + elem
    return path    

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print ('Usage:\n\t{} manifest'.format(sys.argv[0]))
        exit(-1)
    with open(sys.argv[1]) as json_file:
        print ('Loading: {}'.format(sys.argv[1])) 
        try:
            iiif_json = json.load(json_file)
        except ValueError as err:
            print ('Failed to load JSON due to: {}'.format(err))
            exit(-1)

    result = validate(json.dumps(iiif_json), '3.0', sys.argv[1])
    for error in result['errorList']:
        print ("Message: {}".format(error['title']))
        print (" **")
        print (" Validator: {}".format(error['error'].validator))
        print (" Relative Schema Path: {}".format(error['error'].relative_schema_path))
        print (" Schema Path: {}".format(error['error'].absolute_schema_path))
        print (" Relative_path: {}".format(error['error'].relative_path))
        print (" Absolute_path: {}".format(error['error'].absolute_path))
        print (" Json_path: {}".format(json_path(error['error'].absolute_path)))
        print (" Instance: {}".format(error['error'].instance))
        print (" Context: {}".format(error['error'].context))
        print (" Full: {}".format(error['error']))

