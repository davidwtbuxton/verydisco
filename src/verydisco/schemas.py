"""Create pydantic models from a Google service discovery document.

The Google API discovery service publishes descriptions in JSON format for
many public Google APIs. Google's google-api-python-client library consumes a
document to generate a Pythonic client for an API.

Example doc: https://www.googleapis.com/discovery/v1/apis/storage/v1/rest

Wouldn't it be cool if we took the document and generated Python models for
the schemas, and even FastAPI endpoint specifications? Answer is yes.
"""

import builtins
import keyword
import sys
import textwrap
from typing import Any, List, Optional, TextIO, Tuple

import pydantic

from . import utils


def build_from_document(doc: dict) -> dict:
    return build_models(doc["schemas"])


def build_models(schemas: dict) -> dict:
    """Create schema models from an API service discovery document."""
    parser = SchemaParser(schemas)
    global_context = dict(globals())
    local_context = {}

    for name, model_string in parser.model_defs.items():
        code_obj = compile(model_string, "<string>", "exec")
        exec(code_obj, global_context, local_context)

    for name in local_context:
        # Resolve ForwardRef types to actual models.
        local_context[name].update_forward_refs(**local_context)

    return local_context


def write_models(schemas: dict, fh: TextIO):
    """Create data models for schemas and write them to a file."""
    parser = SchemaParser(schemas)

    value = "\n\n".join(parser.model_defs.values())
    fh.write(value)


class SchemaParser:
    simple_types = {
        # There's also "object" and "array" which are special-cased.
        # https://tools.ietf.org/html/draft-zyp-json-schema-03#section-5.1
        "any": "Any",
        "boolean": "bool",
        "integer": "int",
        "null": "None",
        "number": "float",
        "string": "str",
    }
    python_keywords = set(keyword.kwlist) | set(dir(builtins))

    def __init__(self, schemas: dict):
        # Parsing a schema may result in several data models for the nested
        # objects, so we use the model_defs dict to collect the results.
        self.model_defs = {}

        for name, schema in schemas.items():
            self.schema_as_string(schema, class_name=name)

    def schema_as_string(self, schema: dict, class_name: Optional[str] = None):
        """Make a string for a data class from a schema, that can be exec'd."""
        indent = " " * 4
        description = schema.get("description", "")
        docstring = self.format_docstring(description, indent=indent)
        type_ = schema.get("type")
        id_ = schema.get("id")
        # Items are (name, type_, default).
        properties = []

        if "properties" in schema:
            for pname, pschema in schema["properties"].items():
                pname = self.valid_property_name(pname)
                prop_type, pdefault = self.parse_property(pschema, pname)
                properties.append((pname, prop_type, pdefault))

        # Some objects have no structure, e.g. storage#bucket which has "labels"
        # which are arbitrary key/value pairs. Ignoring them for now.
        if "additionalProperties" in schema:
            pass

        if not id_:
            if class_name:
                id_ = class_name
            else:
                # Make up a name for the model.
                names = "".join(name.capitalize() for name, _, _ in properties)
                id_ = "_" + names

        result = f'''class {id_}(pydantic.BaseModel):\n{docstring}'''

        for name, type_, default in properties:
            if default:
                line = f"{name}: {type_} = {default}"
            else:
                line = f"{name}: {type_}"

            result += f"{indent}{line}\n"

        # No class body, make it valid Python.
        if not properties and not docstring:
            result += f"{indent}pass\n"

        self.model_defs[id_] = result

    @classmethod
    def valid_property_name(cls, name: str) -> str:
        """Make valid Python identifiers for a property name.

        A name like "class" is a Python keyword so has to be converted. A name
        like "next" is a built-in, so it can be confusing to have it re-defined
        by a model.
        """
        if name in cls.python_keywords:
            name += "_"

        return name

    def parse_property(self, schema: dict,
                       name: str) -> Tuple[str, Optional[str]]:
        """Return the type (as a string) and default value (as string or None)."""
        # Easy case.
        try:
            type_ = schema["type"]
        except KeyError:
            type_ = schema["$ref"]

        if type_ in self.simple_types:
            default = schema.get("default")
            if default is not None:
                default = repr(default)

            py_type = self.simple_types[type_]

            return py_type, default

        elif type_ == "object":
            class_name = f"_{name}"
            self.schema_as_string(schema, class_name=class_name)

            return f'"{class_name}"', None

        elif type_ == "array":
            items = schema["items"]
            py_type, default = self.parse_property(items, name)

            return f"List[{py_type}]", default

        else:
            # Must be a $ref.
            return f'"{type_}"', None

    @classmethod
    def format_docstring(cls, text: str, indent: str = "") -> str:
        if text:
            wrapper = textwrap.TextWrapper(subsequent_indent=indent)
            result = wrapper.fill(text)
            result = f'{indent}"""{result}'

            max_line_length = 80
            if len(result) > (max_line_length - len('"""')):
                result += f'\n{indent}"""\n'
            else:
                result += '"""\n'

        else:
            result = ""

        return result


def main(argv: list):
    """Write API schema classes for a service discovery document to STDOUT."""
    location = argv[1]
    doc = utils.load_location(location)
    write_models(doc["schemas"], sys.stdout)
