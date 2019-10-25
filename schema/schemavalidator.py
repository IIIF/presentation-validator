#!/usr/bin/python

from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError, SchemaError
import json
import sys

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

def validate(data, version, url):
    if version == '3.0':
        with open('schema/iiif_3_0.json') as json_file:
            try:
                schema = json.load(json_file)
            except ValueError as err:
                print ('Failed to load JSON due to: {}'.format(err))
                raise

    try:
        validator = Draft7Validator(schema)
        results = validator.iter_errors(json.loads(data))
    except SchemaError as err:    
        print('Problem with the supplied schema:\n')
        print(err)
        raise

    okay = 0
    errors = sorted(results, key=lambda e: e.path)
    error = ''
    errorsJson = []
    if errors:
        print('Validation Failed')
        errorCount = 1
        for err in errors:
            error += 'Error {} of {}.\n Message: {}'.format(errorCount, len(errors), err.message)
            detail = ''
            if 'title' in err.schema:
                detail = err.schema['title']
                print (' Test message: {}'.format(detail))
            description = ''    
            if 'description' in err.schema:
                description = err.schema['description']
                print (' Test description: {}'.format(description))
            print('\n Path for error: {}'.format(printPath(err.path, err.message)))
            context = err.instance
            print (json.dumps(err.instance, indent=4))
            if isinstance(context, dict):
                for key in context:
                    print('****')
                    print(key)
                    print('****')
                    if isinstance(context[key], list): 
                        context[key] = '[ ... ]'
                    elif isinstance(context[key], dict):
                        context[key] = '{ ... }'
            errorsJson.append({
                'title': 'Error {} of {}.\n Message: {}'.format(errorCount, len(errors), err.message),
                'detail': detail,
                'description': description,
                'path': printPath(err.path, err.message),
                'context': context
        
            })
            print (json.dumps(err.instance, indent=4))
            errorCount += 1

        # Return:
       # infojson = {
      #      'received': data,
     #       'okay': okay,
    #        'warnings': warnings,
   #         'error': str(err),
  #          'url': url
 #        }

        okay = 0
    else:
        print ('Passed Validation!')
        okay = 1

    return {
        'received': data,
        'okay': okay,
        'warnings': [],
        'error': error,
        'errorList': errorsJson,
        'url': url
    }

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print ('Usage:\n\t{} manifest schema'.format(sys.argv[0]))
        exit(-1)
    with open(sys.argv[1]) as json_file:
        print ('Loading: {}'.format(sys.argv[1])) 
        try:
            iiif_json = json.load(json_file)
        except ValueError as err:
            print ('Failed to load JSON due to: {}'.format(err))
            exit(-1)

    with open(sys.argv[2]) as schema_file:
        print ('Loading schema: {}\n'.format(sys.argv[2])) 
        try:
            schema = json.load(schema_file)
        except ValueError as err:
            print ('Failed to load schema due to JSON error: {}'.format(err))
            exit(-1)

    try:
        validator = Draft7Validator(schema)
        results = validator.iter_errors(iiif_json)
    except SchemaError as err:    
        print('Problem with the supplied schema:\n')
        print(err)

    errors = sorted(results, key=lambda e: e.path)
    if errors:
        print('Validation Failed')
        errorCount = 1
        for err in errors:
            print('Error {} of {}.\n Message: {}'.format(errorCount, len(errors), err.message))
            if 'title' in err.schema:
                print (' Test message: {}'.format(err.schema['title']))
            if 'description' in err.schema:
                print (' Test description: {}'.format(err.schema['description']))
            print('\n Path for error: {}'.format(printPath(err.path, err.message)))
            context = err.instance
            for key in context:
                if isinstance(context[key], list): 
                    context[key] = '[ ... ]'
                elif isinstance(context[key], dict):
                    context[key] = '{ ... }'

            print (json.dumps(err.instance, indent=4))
            errorCount += 1

        # Return:
       # infojson = {
      #      'received': data,
     #       'okay': okay,
    #        'warnings': warnings,
   #         'error': str(err),
  #          'url': url
 #        }

    else:
        print ('Passed Validation!')
