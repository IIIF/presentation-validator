from iiif_prezi.loader import ManifestReader
from schema import schemavalidator
from jsonschema.exceptions import ValidationError, SchemaError

import requests
from urllib.parse import urlparse
import traceback

import json

from pyld import jsonld
jsonld.set_document_loader(jsonld.requests_document_loader(timeout=60))

IIIF_HEADER = "application/ld+json;profile=http://iiif.io/api/presentation/{iiif_version}/context.json"

def check_manifest(data, version, url=None, warnings=[]):
    """Check manifest data at version, return JSON."""
    infojson = {}
    # Check if 3.0 if so run through schema rather than this version...
    if version == '3.0':
        try:
            infojson = schemavalidator.validate(data, version, url)
            for error in infojson['errorList']:
                error.pop('error', None)
        
            if isinstance(data, str):
                mf = json.loads(data)
            else:
                mf = data

            if url and 'id' in mf and mf['id'] != url:
                raise ValidationError("The manifest id ({}) should be the same as the URL it is published at ({}).".format(mf["id"], url))
        except ValidationError as e:
            if infojson:
                infojson['errorList'].append({
                    'title': 'Resolve Error',
                    'detail': str(e),
                    'description': '',
                    'path': '/id',
                    'context': '{ \'id\': \'...\'}'
                    })
            else:
                infojson = {
                    'okay': 0,
                    'error': str(e),
                    'url': url,
                    'warnings': []
                }
        except Exception as e:    
            traceback.print_exc()
            infojson = {
                'okay': 0,
                'error': 'Presentation Validator bug: "{}". Please create a <a href="https://github.com/IIIF/presentation-validator/issues">Validator Issue</a>, including a link to the manifest.'.format(e),
                'url': url,
                'warnings': []
            }

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
            okay = 1
        except KeyError as e:    
            print ('Failed validation due to:')
            traceback.print_exc()
            err = 'Failed due to KeyError {}, check trace for details'.format(e)
            okay = 0
        except Exception as e:
            # Failed
            print ('Failed validation due to:')
            traceback.print_exc()
            err = e
            okay = 0

        warnings.extend(reader.get_warnings())
        infojson = {
            'okay': okay,
            'warnings': warnings,
            'error': str(err),
            'url': url
        }

    return infojson

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