#!/usr/local/bin/python3

from jsonschema import Draft7Validator, RefResolver
from jsonschema.exceptions import ValidationError, SchemaError, best_match, relevance
from jsonpath_rw import jsonpath, parse
import json
import sys
import re

class IIIFErrorParser(object):
    """
        This class tries to clean up json schema validation errors to remove
        errors that are misleading. Particularly ones where part of the error is related
        to a part of the schema with a different type. This occurs when you use `oneOf` and
        the validation then doesn't know if its valid or not so gives misleading errors. To clean this up
        this classes dismisses validation errors related to collections and annotation lists if the type is a Manifest.

        To initalise:

        errorParser = IIIFErrorParser(schema, iiif_json)

        where:
            schema: the schema as a JSON object
            iiif_json: the IIIF asset which failed validation

        then test if the error is related to the type of the IIIF asset:

        if errorParser.isValid(validationError.absolute_schema_path, validationError.absolute_path):
    """

    def __init__(self, schema, iiif_asset):
        """
            Intialize the IIIFErrorParse. Parameters:
                schema: the schema as a JSON object
                iiif_json: the IIIF asset which failed validation
        """
        self.schema = schema
        self.iiif_asset = iiif_asset
        self.resolver = RefResolver.from_schema(self.schema)

    def isValid(self, error_path, IIIFJsonPath):
        """
            This checks wheather the passed error path is valid for this iiif_json
            If the type doesn't match in the hirearchy then this error can
            be dismissed as misleading. 

            Arguments:
                error_path (list of strings and ints): the path to the schema error 
                            e.g. [u'allOf', 1, u'oneOf', 2, u'allOf', 1, u'properties', u'type', u'pattern']
                            from validation_error.absolute_schema_path
                IIIFJsonPath (list of strings and ints): the path to the validation error
                            in the IIIF Json file. e.g.  [u'items', 0, u'items', 0, u'items', 0, u'body']
                            from validation_error.absolute_path
        """
        return self.parse(error_path, self.schema, self.iiif_asset, IIIFJsonPath)
        
    def diagnoseWhichOneOf(self, error_path, IIIFJsonPath):
        """
            Given a schema error that ends in oneOf the current json schema library 
            will check all possibilities in oneOf and return validation error messages for each one
            This method will identify the real oneOf that causes the error by checking the type of 
            each oneOf possibility and returning only the one that matches. 

            Arguments:
                error_path: list of strings and ints which are the path to the error in the schema
                            generated from validation_error.absolute_schema_path

                IIIF Json Path: list of strings and ints which gives the path to the failing part of the 
                                IIIF data. Generated from validation_error.absolute_path
        """

        # convert the IIIF path from a list to an actual JSON object containing only
        # the JSON which has failed.
        path = parse(self.pathToJsonPath(IIIFJsonPath))
        iiifJsonPart = path.find(self.iiif_asset)[0].value

        # Extract only the part of the schema that has failed and in practice will
        # be a list of the oneOf possibilities. Also add all references in the schema
        # so these resolve
        schema_part = self.addReferences(self.getSchemaPortion(error_path))
        valid_errors = []            
        oneOfIndex = 0
        # For each of the oneOf possibilities in the current part of the schema
        for possibility in schema_part:
            try:
                # run through a validator passing the IIIF data snippet
                # and the json schema snippet 
                validator = Draft7Validator(possibility)
                results = validator.iter_errors(iiifJsonPart)
            except SchemaError as err:    
                print('Problem with the supplied schema:\n')
                print(err)
                raise

            # One of the oneOf possibilities is a reference to another part of the schema
            # this won't bother the validator but will complicate the diagnoise so replace
            # it with the actual schema json (and copy all references)
            if isinstance(possibility, dict) and "$ref" in possibility:
                tmpClas = possibility['classes']
                tmpType = possibility['types']
                possibility = self.resolver.resolve(possibility['$ref'])[1]
                possibility['classes'] = tmpClas
                possibility['types'] = tmpType

            # This oneOf possiblity failed validation
            if results:
                addErrors = True
                store_errs = []
                for err in results:
                    # For each of the reported errors check the types with the IIIF data to see if its relevant
                    # if one error in this oneOf possibility group is not relevant then none a relevant so discard
                    if not self.parse(list(err.absolute_schema_path), possibility, iiifJsonPart, list(err.absolute_path)):
                        addErrors = False
                    else:    
                        # if this oneOf possiblity is still relevant add it to the list and check
                        # its not another oneOf error
                        if addErrors:
                            # if error is also a oneOf then diagnoise again
                            #print ('Schema path: {} error path: {}'.format(err.absolute_schema_path, error_path))
                            if err.absolute_schema_path[-1] == 'oneOf' and err.absolute_schema_path != error_path and 'rights' not in err.absolute_schema_path:
                                error_path.append(oneOfIndex) # this is is related to one of the original oneOfs at index oneOfIndex
                                error_path.extend(err.absolute_schema_path) # but we found another oneOf test at this location
                                result = (self.diagnoseWhichOneOf(error_path, IIIFJsonPath)) # so recursivly discovery real error

                                if isinstance(result, ValidationError):    
                                    store_errs.append(result)
                                else:
                                    store_errs.extend(result)

                        #print ('would add: {} by addErrors is {}'.format(err.message, addErrors))
                            else:
                                store_errs.append(err)
                # if All errors are relevant to the current type add them to the list        
                if addErrors:
                    valid_errors += store_errs
            oneOfIndex += 1            

        if valid_errors:
            # this may hide errors as we are only selecting the first one but better to get one to work on and then can re-run
            # Also need to convert back the error paths to the full path
            error_path.reverse()
            IIIFJsonPath.reverse()
            for error in valid_errors:
                error.absolute_schema_path.extendleft(error_path)
                error.absolute_path.extendleft(IIIFJsonPath)
            #    print ('Err {}, path {}'.format(error.message, error.path))
            return valid_errors
        else:
            # Failed to find the source of the error so most likely its a problem with the type
            # and it didn't match any of the possible oneOf types

            path = parse(self.pathToJsonPath(IIIFJsonPath))
            instance = path.find(self.iiif_asset)[0].value
            IIIFJsonPath.append('type')
            #print (IIIFJsonPath)
            return ValidationError(message='Failed to find out which oneOf test matched your data. This is likely due to an issue with the type and it not being valid value at this level. SchemaPath: {}'.format(self.pathToJsonPath(error_path)),
                                    path=[], schema_path=error_path, schema=self.getSchemaPortion(error_path), instance=instance) 



    def pathToJsonPath(self, pathAsList):
        """
            Convert a json path as a list of keys and indexes to a json path

            Arguments:
                pathAsList e.g. [u'items', 0, u'items', 0, u'items', 0, u'body']
        """
        jsonPath = "$"
        for item in pathAsList:
            if isinstance(item, int):
                jsonPath += '[{}]'.format(item)
            else:
                jsonPath += '.{}'.format(item)
        return jsonPath        

    def getSchemaPortion(self, schemaPath):
        """
            Given the path return the relevant part of the schema
            Arguments:
                schemaPath: e.g. [u'allOf', 1, u'oneOf', 2, u'allOf', 1, u'properties', u'type', u'pattern']
        """
        schemaEl = self.schema
        for pathPart in schemaPath:
            try:
                if isinstance(schemaEl[pathPart], dict) and "$ref" in schemaEl[pathPart]:
                    schemaEl = self.resolver.resolve(schemaEl[pathPart]['$ref'])[1]
                else:
                    schemaEl = schemaEl[pathPart]
            except KeyError as error:
               # print (schemaEl)
                raise KeyError

        return schemaEl    

    def addReferences(self, schemaPart):
        """
            For the passed schemaPart add any references so that all #ref statements
            resolve in the schemaPart cut down schema. Note this currently is hardcoded to 
            copy types and classes but could be more clever.
        """
        definitions = {}
        definitions['types'] = self.schema['types']
        definitions['classes'] = self.schema['classes']
        for item in schemaPart:
            item.update(definitions)

        return schemaPart

    def parse(self, error_path, schemaEl, iiif_asset, IIIFJsonPath, parent=None, jsonPath="$"):
        """
            Private method which recursivly travels the schema JSON to find
            type checks and performs them until it finds a mismatch. If it finds
            a mismatch it returns False.

            Parameters:
                error_path (list of strings and ints): the path to the schema error 
                            e.g. [u'allOf', 1, u'oneOf', 2, u'allOf', 1, u'properties', u'type', u'pattern']
                            from validation_error.absolute_schema_path
                schemaEl: the current element we are testing in this iteration. Start with the root
                parent: the last element tested
                jsonPath: the path in the IIIF assset that relates to the current item in the schema we are looking at
                IIIFJsonPath (list of strings and ints): the path to the validation error
                            in the IIIF Json file. e.g.  [u'items', 0, u'items', 0, u'items', 0, u'body']
                            from validation_error.absolute_path

        """
        if len(error_path) <= 0:
            return True

        if isinstance(schemaEl, dict) and "$ref" in schemaEl:
            #print ('Found ref, trying to resolve: {}'.format(schemaEl['$ref']))
            return self.parse(error_path, self.resolver.resolve(schemaEl['$ref'])[1], iiif_asset, IIIFJsonPath, parent, jsonPath)


        #print ("Path: {} ".format(error_path))
        pathEl = error_path.pop(0)
        # Check current type to see if its a match
        if pathEl == 'type' and parent == 'properties':
            if 'pattern' in schemaEl['type']:
                value = schemaEl['type']['pattern']
            elif 'const' in schemaEl['type']:
                value = schemaEl['type']['const']
            elif 'oneOf' in schemaEl['type']:
                value = []
                for option in schemaEl['type']['oneOf']:
                    if 'pattern' in option:
                        value.append(option['pattern'])
                    elif 'const' in option:
                        value.append(option['const'])
                #print ('Using values: {}'.format(value))
            elif 'anyOf' in schemaEl['type']:
                value = []
                for option in schemaEl['type']['anyOf']:
                    if 'pattern' in option:
                        value.append(option['pattern'])
                    elif 'const' in option:
                        value.append(option['const'])
                #print ('Using values: {}'.format(value))

            if not self.isTypeMatch(jsonPath + '.type', iiif_asset, value, IIIFJsonPath):
                return False
        # Check child type to see if its a match        
        elif pathEl == 'properties' and 'type' in schemaEl['properties'] and 'pattern' in schemaEl['properties']['type']:
            value = schemaEl['properties']['type']['pattern']
            if not self.isTypeMatch(jsonPath + '.type', iiif_asset, value, IIIFJsonPath):
                return False
        # This is the case where additionalProperties has falied but need to check
        # if the type didn't match anyway
        elif pathEl == 'additionalProperties' and 'properties' in schemaEl and 'type' in schemaEl['properties'] and 'pattern' in schemaEl['properties']['type']:
            value = schemaEl['properties']['type']['pattern']
            if not self.isTypeMatch(jsonPath + '.type', iiif_asset, value, IIIFJsonPath):
                return False
        # if there is a property called items which is of type array add an item array    
        elif 'type' in schemaEl and schemaEl['type'] == 'array':    
            jsonPath += '.{}[_]'.format(parent)
            #print (schemaEl)
            #print (jsonPath)
        # For all properties add json key but ignore items which are handled differently above
        elif parent == 'properties' and pathEl != 'items' and "ref" in schemaEl[pathEl]:
            # check type
            jsonPath += '.{}'.format(pathEl)
            #print (schemaEl)


        if isinstance(schemaEl[pathEl], dict) and "$ref" in schemaEl[pathEl]:
            #print ('Found ref, trying to resolve: {}'.format(schemaEl[pathEl]['$ref']))
            return self.parse(error_path, self.resolver.resolve(schemaEl[pathEl]['$ref'])[1], iiif_asset, IIIFJsonPath, pathEl, jsonPath)
        else:    
            return self.parse(error_path, schemaEl[pathEl], iiif_asset, IIIFJsonPath, pathEl, jsonPath)

    def isTypeMatch(self, iiifPath, iiif_asset, schemaType, IIIFJsonPath):    
        """
            Checks the required type in the schema with the actual type 
            in the iiif_asset to see if it matches.
            Parameters:
                iiifPath: the json path in the iiif_asset to the type to be checked. Due to 
                          the way the schema works the index to arrays is left as _ e.g.
                          $.items[_].items[_].items[_]. The indexes in the array are contained
                          in IIIFJsonPath variable
                schemaType: the type from the schema that should match the type in the iiif_asset
                IIIFJsonPath: (Array of strings and int) path to the validation error in the iiif_asset
                              e.g.  [u'items', 0, u'items', 0, u'items', 0, u'body']. The indexes
                              in this list are used to replace the _ indexes in the iiifPath

             Returns True if the schema type matches the iiif_asset type                 
        """
        # get ints from IIIFJsonPath replace _ with numbers
        if IIIFJsonPath:
            indexes = []
            for item in IIIFJsonPath:
                if isinstance(item, int):
                    indexes.append(item)
            count = 0        
            #print (iiifPath)
            indexDelta = 0
            for index in find(iiifPath, '_'):
                index += indexDelta
                #print ('Replacing {} with {}'.format(iiifPath[index], indexes[count]))
                iiifPath = iiifPath[:index] + str(indexes[count]) + iiifPath[index + 1:]
                # if you replace [_] with a number greater than 9 you are taking up two spaces in the
                # string so the index in the for loop starts to be off by one. Calculating the delta
                # sorts this out
                if len(str(indexes[count])) > 1:
                    indexDelta += len(str(indexes[count])) -1
                count += 1

        #print ('JsonPath: {} IIIF Path {} type: {}'.format(iiifPath, IIIFJsonPath, schemaType))
        path = parse(iiifPath)
        results = path.find(iiif_asset)
        #print ('Path: {} Results: '.format(path, results))
        if not results:
            # type not found so return True as this maybe the correct error
            return True
        typeValue = results[0].value
        #print ('Found type {} and schemaType {}'.format(typeValue, schemaType))
        if isinstance(schemaType, list):
            for typeOption in schemaType:
                #print ('Testing {} = {}'.format(typeOption, typeValue)) 
                if re.match(typeOption, typeValue):
                    return True
            return False        
        else:
            return re.match(schemaType, typeValue)

def find(str, ch):
    """
        Used to create an list with the indexes of a particular character. e.g.:
        find('o_o_o','_') = [1,3]
    """
    for i, ltr in enumerate(str):
        if ltr == ch:
            yield i        

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
    schema_file = 'schema/iiif_3_0.json'
    with open(schema_file) as json_file:
        print ('Loading: {}'.format(schema_file)) 
        try:
            schema = json.load(json_file)
        except ValueError as err:
            print ('Failed to load JSON due to: {}'.format(err))
            exit(-1)
    errorParser = IIIFErrorParser(schema, iiif_json)

    # annotationPage
    path = [u'allOf', 1, u'oneOf', 2, u'allOf', 1, u'properties', u'type', u'pattern']
    print("Path: '{}' is valid: {}".format(path, errorParser.isValid(path)))
    # Annotation
    path = [u'allOf', 1, u'oneOf', 2, u'allOf', 1, u'properties', u'items', u'items', u'allOf', 1, u'properties', u'type', u'pattern'] 
    print("Path: '{}' is valid: {}".format(path, errorParser.isValid(path)))
    # Additional props fail
    path = [u'allOf', 1, u'oneOf', 2, u'allOf', 1, u'additionalProperties']
    print("Path: '{}' is valid: {}".format(path, errorParser.isValid(path)))
    # Collection
    path = [u'allOf', 1, u'oneOf', 1, u'allOf', 1, u'properties', u'thumbnail', u'items', u'oneOf']
    print("Collection Path: '{}' is valid: {}".format(path, errorParser.isValid(path)))
    # Collection 2
    path = [u'allOf', 1, u'oneOf', 1, u'allOf', 1, u'properties', u'type', u'pattern']
    print("Collection 2 Path: '{}' is valid: {}".format(path, errorParser.isValid(path)))
    # Collection 3
    path = [u'allOf', 1, u'oneOf', 1, u'allOf', 1, u'properties', u'items', u'items', u'oneOf']
    print("Collection 3 Path: '{}' is valid: {}".format(path, errorParser.isValid(path)))
    # success service
    path = [u'allOf', 1, u'oneOf', 0, u'allOf', 1, u'properties', u'thumbnail', u'items', u'oneOf']
    print("Success Service Path: '{}' is valid: {}".format(path, errorParser.isValid(path)))
    # Success service in canvas
    path = [u'allOf', 1, u'oneOf', 0, u'allOf', 1, u'properties', u'items', u'items', u'allOf', 1, u'properties', u'items', u'items', u'allOf', 1, u'properties', u'items', u'items', u'allOf', 1, u'properties', u'body', u'oneOf']
    print("Success Service Canvas Path: '{}' is valid: {}".format(path, errorParser.isValid(path, [u'items', 0, u'items', 0, u'items', 0, u'body'])))
