IIIF Presentation Validator
======================

This is the codebase for the IIIF Presentation Validator, which can be seen at <http://iiif.io/api/presentation/validator/>.

## Usage

*(Write me)*

## Data Structure

**JSON Response**

``JSON
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
warnings | An array of warning messages      | (TBD)

## Local Installation

*(Write me)*