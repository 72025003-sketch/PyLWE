class LweError(Exception):
    """Base exception for all pylwe errors."""
    pass

class LweParseError(LweError):
    """Raised when an LWE packet is malformed and cannot be parsed."""
    pass

class LweTagError(LweParseError):
    """Raised when LWE tags are malformed or violate specifications."""
    pass

class LweChecksumError(LweTagError):
    """Raised when an LWE tag block checksum is invalid."""
    pass

class LweGenerateError(Exception):
    """Raised when generating an IEC 61162-450 LWE packet fails."""
    pass
