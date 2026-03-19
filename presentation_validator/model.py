import json

class ErrorDetail:
    title: str
    detail: str
    description: str
    path: str
    context: dict
    err: Exception

    def __init__(self, title, detail, description, path, context, err):
        self.title = title
        self.detail = detail
        self.description = description
        self.path = path
        self.context = context
        self.err = err

    def json(self):
        return {
            "title": self.title,
            "detail": self.detail,
            "description": self.description,
            "path": self.path,
            "context": self.context
        }

    def __str__(self):
        return f"{self.title}\nDetail: {self.detail}\nDescription: {self.description}\nPath: {self.path}\n:Context:\n{json.dumps(self.context, indent=2)}\n==============\n"

class ValidationResult:
#    {
#  "okay": 0,
#  "warnings": [],
#  "error": "",
#  "errorList": [
#    {
#      "title": "Error 1 of 3.\n Message: 'id' is a required property",
#      "detail": "AnnotationBody Annotation bodies MUST have an id and type property.",
#      "description": "",
#      "path": "/provider[0]/logo[0]/['id' is a required property]",
#      "context": {
#        "type": "Image",
#        "format": "image/png",
#        "height": 100,
#        "width": 120,
#        "service": "[ ... ]"
#      }
#    },

    passed: bool
    warnings: list[str]
    error: str
    errorList: list[ErrorDetail]
    url: str

    def __init__(self):
        self.passed = False
        self.warnings = []
        self.error = ""
        self.errorList = []
        self.url = ""

    def json(self):
        errorListJson = []
        for error in self.errorList:
            errorListJson.append(error.json())

        return {
            "okay": 1 if self.passed else 0,
            "warnings": self.warnings,
            "error": self.error,
            "errorList": errorListJson,
            "url": self.url
        }

