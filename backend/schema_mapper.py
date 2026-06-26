"""Re-export canonical schema mapper from the validex package."""
from validex.schema_mapper import (
    KNOWN_ALIASES,
    SchemaMap,
    apply_canonical_schema,
    detect_schema,
    normalize_columns,
    normalize_header,
)

__all__ = [
    "KNOWN_ALIASES",
    "SchemaMap",
    "apply_canonical_schema",
    "detect_schema",
    "normalize_columns",
    "normalize_header",
]
