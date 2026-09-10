"""
Tiny, dependency-free helpers for testing the JSON Schemas in app.agents.

Two jobs:
1. `assert_upstage_compatible(schema)` checks a schema against the constraints
   Upstage documents for structured outputs (root object, every property in
   `required`, additionalProperties false on every object, strict true, only
   the supported keywords/types).
2. `validate(instance, schema)` is a minimal validator for the subset we use
   (object / string / integer / number / boolean / array, enum, required,
   additionalProperties). It lets tests prove that a schema would reject a
   missing field, a wrong type, or an unknown enum value, without a network
   call or an extra dependency.
"""

SUPPORTED_TYPES = {"string", "number", "integer", "boolean", "object", "array"}
SUPPORTED_KEYWORDS = {
    "type", "properties", "required", "additionalProperties", "enum",
    "description", "items", "$defs", "$ref",
}
UNSUPPORTED_KEYWORDS = {
    "allOf", "oneOf", "not", "dependentRequired", "dependentSchemas",
    "if", "then", "else", "patternProperties", "anyOf",
}


class SchemaError(AssertionError):
    pass


# ---------------------------------------------------------------------------
# Upstage structured-outputs constraints
# ---------------------------------------------------------------------------
def assert_upstage_compatible(wrapper: dict):
    """`wrapper` is the value passed as response_format["json_schema"]."""
    if set(wrapper) != {"name", "strict", "schema"}:
        raise SchemaError(f"wrapper keys must be name/strict/schema, got {sorted(wrapper)}")
    if wrapper["strict"] is not True:
        raise SchemaError("strict must be True")
    if not isinstance(wrapper["name"], str) or not wrapper["name"]:
        raise SchemaError("name must be a non-empty string")
    root = wrapper["schema"]
    if root.get("type") != "object":
        raise SchemaError("root must be an object")
    _walk(root, "$", depth=0)


def _walk(node: dict, path: str, depth: int):
    if depth > 10:
        raise SchemaError(f"{path}: nesting deeper than 10 levels")
    bad = set(node) & UNSUPPORTED_KEYWORDS
    if bad:
        raise SchemaError(f"{path}: unsupported keywords {sorted(bad)}")
    unknown = set(node) - SUPPORTED_KEYWORDS
    if unknown:
        raise SchemaError(f"{path}: keywords outside the documented subset {sorted(unknown)}")
    if "$ref" in node and not str(node["$ref"]).startswith("#/$defs/"):
        raise SchemaError(f"{path}: only local #/$defs/<name> references are allowed")

    t = node.get("type")
    types = t if isinstance(t, list) else [t]
    for tt in types:
        if tt not in SUPPORTED_TYPES | {"null"}:
            raise SchemaError(f"{path}: unsupported type {tt!r}")

    if "object" in types:
        props = node.get("properties", {})
        if node.get("additionalProperties") is not False:
            raise SchemaError(f"{path}: additionalProperties must be false on every object")
        if set(node.get("required", [])) != set(props):
            raise SchemaError(f"{path}: required must list every property exactly once")
        for name, sub in props.items():
            _walk(sub, f"{path}.{name}", depth + 1)
    if "array" in types:
        _walk(node["items"], f"{path}[]", depth + 1)


# ---------------------------------------------------------------------------
# Minimal instance validator
# ---------------------------------------------------------------------------
def validate(instance, schema: dict, path: str = "$"):
    """Raise SchemaError if `instance` does not satisfy `schema` (subset)."""
    if "enum" in schema and instance not in schema["enum"]:
        raise SchemaError(f"{path}: {instance!r} not in enum {schema['enum']}")

    t = schema.get("type")
    types = t if isinstance(t, list) else [t]

    if instance is None:
        if "null" in types:
            return
        raise SchemaError(f"{path}: null not allowed")

    if "object" in types and isinstance(instance, dict):
        props = schema.get("properties", {})
        missing = [k for k in schema.get("required", []) if k not in instance]
        if missing:
            raise SchemaError(f"{path}: missing required {missing}")
        if schema.get("additionalProperties") is False:
            extra = [k for k in instance if k not in props]
            if extra:
                raise SchemaError(f"{path}: unexpected keys {extra}")
        for k, v in instance.items():
            if k in props:
                validate(v, props[k], f"{path}.{k}")
        return
    if "array" in types and isinstance(instance, list):
        for i, v in enumerate(instance):
            validate(v, schema["items"], f"{path}[{i}]")
        return
    if "string" in types and isinstance(instance, str):
        return
    if "boolean" in types and isinstance(instance, bool):
        return
    if "integer" in types and isinstance(instance, int) and not isinstance(instance, bool):
        return
    if "number" in types and isinstance(instance, (int, float)) and not isinstance(instance, bool):
        return
    raise SchemaError(f"{path}: {type(instance).__name__} does not match type {t!r}")


def is_valid(instance, schema: dict) -> bool:
    try:
        validate(instance, schema)
        return True
    except SchemaError:
        return False
