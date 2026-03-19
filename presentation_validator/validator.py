from iiif_prezi.loader import ManifestReader
from jsonschema.exceptions import ValidationError
from presentation_validator.model import ValidationResult, ErrorDetail
from presentation_validator.v3 import schemavalidator

import requests
from urllib.parse import urlparse
import traceback

import json

from pyld import jsonld
jsonld.set_document_loader(jsonld.requests_document_loader(timeout=60))

IIIF_HEADER = "application/ld+json;profile=http://iiif.io/api/presentation/{version}/context.json"

def check_manifest(data, version, url=None, warnings=[]):
    """Check manifest data at version, return JSON."""
    if isinstance(data, str):
        try:
            manifest = json.loads(data)
        except json.JSONDecodeError as e:
            result = ValidationResult()
            result.passed = False
            result.error = str(e)
            return result
    else:
        manifest = data

    result = ValidationResult()

    if not version:
        # peak into the json to find the version
        context = manifest.get('@context', '')
        if 'http://iiif.io/api/presentation/4/context.json' in context:
            version = '4.0'
        elif 'http://iiif.io/api/presentation/3/context.json' in context:
            version = '3.0'
        elif 'http://iiif.io/api/presentation/2/context.json' in context:
            version = '2.1'
        else:
            result.passed = False
            result.error = "Unable to determine IIIF presentation version from @context"
            return result

    # Check if 3.0 if so run through schema rather than this version...
    if version == '3.0':
        try:
            result = schemavalidator.validate(manifest, version, url)
        
            if url and 'id' in manifest and manifest['id'] != url:
                raise ValidationError(f"The manifest id ({manifest['id']}) should be the same as the URL it is published at ({url}).")
        except ValidationError as e:
            if result.errorList:
                result.errorList.append(ErrorDetail(
                    'Resolve Error',
                    str(e),
                    '',
                    '/id',
                    '{ \'id\': \'...\'}',
                    e))
            else:
                result.passed = False
                result.error = str(e)
        except Exception as e:    
            traceback.print_exc()
            result.passed = False
            result.error = f'Presentation Validator bug: "{e}". Please create a <a href="https://github.com/IIIF/presentation-validator/issues">Validator Issue</a>, including a link to the manifest.'
    else:
        if isinstance(data, dict):
            data = json.dumps(data, indent=3)

        reader = ManifestReader(data, version=version)
        err = None
        try:
            mf = reader.read()
            mf.toJSON()
            if url and mf.id != url:
                raise ValidationError("Manifest @id ({}) is different to the location where it was retrieved ({})".format(mf.id, url))
            # Passed!
            result.passed = True
        except KeyError as e:    
            print ('Failed validation due to:')
            traceback.print_exc()
            err = 'Failed due to KeyError {}, check trace for details'.format(e)
            result.passed = False
        except Exception as e:
            # Failed
            print ('Failed validation due to:')
            traceback.print_exc()
            result.passed = False
            err = e

        warnings.extend(reader.get_warnings())

        result.warnings = warnings
        result.error = str(err)
        result.url = url

    return result

def fetch_manifest(url, accept, version):
    """
    Fetch a manifest from a URL.

    Args:
        url: URL to retrieve.
        accept: Whether to send an Accept header requesting a IIIF media type.
        version: Requested IIIF Presentation version, used to build the Accept header.
    """
    accept_header = None
    if accept and version:
        if version in ("2.0", "2.1"):
            accept_header = IIIF_HEADER.format(version=2)
        elif version in ("3.0",):
            accept_header = IIIF_HEADER.format(version=3)
        else:
            accept_header = "application/json"

    parsed_url = urlparse(url)
    if (parsed_url.scheme != 'http' and parsed_url.scheme != 'https'):
        raise ValueError("URLs must use HTTP or HTTPS")

    headers = {
        "User-Agent": "IIIF Validation Service",
        "Accept-Encoding": "gzip",
    }

    if accept_header:
        headers["Accept"] = accept_header

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    warnings = []

    ct = response.headers.get("content-type", "")
    cors = response.headers.get("access-control-allow-origin", "")

    if not ct.startswith("application/json") and not ct.startswith("application/ld+json"):
        warnings.append(
            'URL does not have correct content-type header: got "%s", expected JSON' % ct
        )

    if cors != "*":
        warnings.append(
            'URL does not have correct access-control-allow-origin header: got "%s", expected *'
            % cors
        )

    content_encoding = response.headers.get("Content-Encoding", "")
    if content_encoding != "gzip":
        warnings.append(
            "The remote server did not use the requested gzip transfer compression, "
            "which will slow access. (Content-Encoding: %s)" % content_encoding
        )
    elif "Accept-Encoding" not in response.headers.get("Vary", ""):
        warnings.append(
            "gzip transfer compression is enabled but the Vary header does not include "
            "Accept-Encoding, which can cause compatibility issues"
        )

    return response.json(), warnings