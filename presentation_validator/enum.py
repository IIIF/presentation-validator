from enum import Enum


class IIIFVersion(str, Enum):
    V1_0 = "1.0"
    V2_0 = "2.0"
    V2_1 = "2.1"
    V3_0 = "3.0"
    V4_0 = "4.0"

    DEFAULT = V3_0

    @classmethod
    def default(cls) -> "IIIFVersion":
        return cls.DEFAULT

    @classmethod
    def from_string(cls, value: str | None):
        if value is None:
            return None
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Unsupported IIIF version: {value}")

    @classmethod
    def from_context(cls,context):
        if isinstance(context, list):
            context_str = context[-1]
        else:
            context_str = context

        # peak into the json to find the version
        if 'http://iiif.io/api/presentation/4/context.json' in context_str:
            version = IIIFVersion.V4_0
        elif 'http://iiif.io/api/presentation/3/context.json' in context_str:
            version = IIIFVersion.V3_0
        elif 'http://iiif.io/api/presentation/2/context.json' in context_str:
            version = IIIFVersion.V2_1
        elif 'http://www.shared-canvas.org/ns/context.json' in context_str:
            version = IIIFVersion.V1_0
        else:
            raise ValueError(f"Unsupported IIIF version: {context_str}")

        return version    

    @classmethod
    def values_str(cls) -> str:
        return ", ".join(v.value for v in cls)        

    @property
    def major(self) -> int:
        return int(self.value.split(".")[0])

