IIIF Presentation Validator
======================

This is the codebase for the IIIF Presentation Validator, which can be seen at <http://iiif.io/api/presentation/validator/>.

## Usage

*(Write me)*

## Data Structure

**JSON Response**

```JSON
  {
    "url": "<SUBMITTED URL>",
    "error": "<ERROR MESSAGE>",
    "okay": 1,
    "warnings": []
  }
```

Key      |  Definition                       | Example Value
---------|-----------------------------------|----------
url      | Submitted URL for the manifest    | http://example.com/iiif/manifest.json
error    | The text of the breaking error    | sc:Manifest['thumbnail'] has broken value
okay     | Did the manifest parse properly?  | 1 *or* 0
warnings | An array of warning messages      | "WARNING: Resource type 'sc:Manifest' should have 'description' set\n"

## Installing localy

### Option 1: Using uv (recommended)

```
uv sync
```

### Option 2: Using pip

```
pip install .
```

Either option will install the `iiif-validator` command. This command allows you to run the validator server or validate local or remote files from the command line. 

## Command line validation 

To validate a manifest from the command line:
```
# Using uv
uv run iiif-validator validate --version <version> <url-or-file>

# Using pip install
iiif-validator validate --version <version> <url-or-file>
```

It is also possible to validate a directory and any sub directories:

```
# Using uv
uv run iiif-validator validate-dir --version <version> --extension <extension> <directory>

# Using pip install
iiif-validator validate-dir --version <version> --extension <extension> <directory>
```

## Server

To run the server:
```
# Using uv
uv run iiif-validator serve

# Using pip install
iiif-validator serve
```

This should start up a local server, running at <localhost:8080>. To test it, try [this url](http://localhost:8080/validate?url=http://iiif.io/api/presentation/2.1/example/fixtures/1/manifest.json) and see if you get a JSON response that looks like this:

```json
{
  "url": "http://iiif.io/api/presentation/2.1/example/fixtures/1/manifest.json",
  "error": "None", 
  "okay": 1, 
  "warnings": ["WARNING: Resource type 'sc:Manifest' should have 'description' set\n", "WARNING: Resource type 'sc:Sequence' should have '@id' set\n", "WARNING: Resource type 'oa:Annotation' should have '@id' set\n", "WARNING: Resource type 'dctypes:Image' should have 'format' set\n"]
}
```
You may also use `--hostname` to specify a hostname or IP address to which to bind and `--port` for a port to which to bind.
