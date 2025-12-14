"""
Utilities for web UI: generating sample data from OpenAPI JSON schema.
"""
from typing import Any, Dict, Optional
from datetime import datetime, timezone


def schema_to_example(schema: Dict[str, Any], components: Optional[Dict[str, Any]] = None) -> Any:
    """Generate a simple example from a given OpenAPI schema.
    Resolves basic types and $ref (with components provided).
    """
    if not schema:
        return None
    # Resolve $ref
    if '$ref' in schema and components:
        ref = schema['$ref']
        # Example: '#/components/schemas/MyObj'
        if ref.startswith('#/components/schemas/'):
            name = ref.split('/')[-1]
            comp = components.get('schemas', {}).get(name)
            if comp:
                return schema_to_example(comp, components)
    # handle allOf: merge
    if 'allOf' in schema:
        result = {}
        for s in schema['allOf']:
            val = schema_to_example(s, components)
            if isinstance(val, dict):
                result.update(val)
        return result
    if 'oneOf' in schema or 'anyOf' in schema:
        arr = schema.get('oneOf') or schema.get('anyOf')
        # choose first
        return schema_to_example(arr[0], components)
    typ = schema.get('type')
    if not typ:
        # guess by presence of properties
        if 'properties' in schema:
            typ = 'object'
        else:
            return None
    if typ == 'object':
        res = {}
        props = schema.get('properties', {})
        for k, v in props.items():
            res[k] = schema_to_example(v, components)
        # include additionalProperties as empty object
        additional = schema.get('additionalProperties')
        if additional is True:
            res['extra'] = {}
        elif isinstance(additional, dict):
            res['extra'] = schema_to_example(additional, components)
        return res
    if typ == 'array':
        items = schema.get('items', {})
        return [schema_to_example(items, components)]
    if typ == 'string':
        enum = schema.get('enum')
        fmt = schema.get('format')
        if enum:
            return enum[0]
        if fmt == 'date-time':
            return datetime.now(timezone.utc).isoformat() + 'Z'
        if fmt == 'date':
            return datetime.now(timezone.utc).date().isoformat()
        return schema.get('example') or schema.get('default') or 'string_example'
    if typ in ('integer', 'number'):
        enum = schema.get('enum')
        if enum:
            return enum[0]
        return schema.get('example') or schema.get('default') or 0
    if typ == 'boolean':
        return schema.get('example') or schema.get('default') or False
    return None
