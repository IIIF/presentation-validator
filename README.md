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

## Local Installation


**Step one:  Install dependencies**

```bash
python setup.py install
```

**Step two:  Run the application**

```bash
python iiif-presentation-validator.py
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
