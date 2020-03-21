import textwrap
from typing import Optional

import pydantic

from verydisco import schemas


class TestSchemaAsString:
    def test_schema_with_string_property(self):
        data = {
            "ModelName": {
                "properties": {
                    "foo": {"type": "string"},
                },
                "type": "object",
            },
        }
        parser = schemas.SchemaParser(data)
        result = parser.model_defs
        expected = textwrap.dedent('''
            class ModelName(pydantic.BaseModel):
                foo: str
        ''').lstrip()

        assert result["ModelName"] == expected

    def test_schema_with_boolean_property(self):
        data = {
            "ModelName": {
                "properties": {
                    "foo": {"type": "boolean"},
                },
                "type": "object",
            },
        }
        parser = schemas.SchemaParser(data)
        result = parser.model_defs
        expected = textwrap.dedent('''
            class ModelName(pydantic.BaseModel):
                foo: bool
        ''').lstrip()

        assert result["ModelName"] == expected

    def test_schema_with_integer_property(self):
        data = {
            "ModelName": {
                "properties": {
                    "foo": {
                        "format": "int32",
                        "type": "integer",
                    },
                },
                "type": "object",
            },
        }
        parser = schemas.SchemaParser(data)
        result = parser.model_defs
        expected = textwrap.dedent('''
            class ModelName(pydantic.BaseModel):
                foo: int
        ''').lstrip()

        assert result["ModelName"] == expected

    def test_schema_description_is_docstring(self):
        data = {
            "ModelName": {
                "description": "A ModelName instance.",
                "properties": {
                    "foo": {"type": "string"},
                },
                "type": "object",
            },
        }
        parser = schemas.SchemaParser(data)
        result = parser.model_defs
        expected = textwrap.dedent('''
            class ModelName(pydantic.BaseModel):
                """A ModelName instance."""
                foo: str
        ''').lstrip()

        assert result["ModelName"] == expected

    def test_schema_description_is_multiple_line_docstring(self):
        data = {
            "ModelName": {
                "description": "A ModelName instance." * 4,
                "properties": {
                    "foo": {"type": "string"},
                },
                "type": "object",
            },
        }
        parser = schemas.SchemaParser(data)
        result = parser.model_defs
        expected = textwrap.dedent('''
            class ModelName(pydantic.BaseModel):
                """A ModelName instance.A ModelName instance.A ModelName instance.A
                ModelName instance.
                """
                foo: str
        ''').lstrip()

        assert result["ModelName"] == expected

    def test_string_property_has_default_value(self):
        data = {
            "ModelName": {
                "properties": {
                    "foo": {
                        "default": "bar",
                        "type": "string",
                    },
                },
                "type": "object",
            },
        }
        parser = schemas.SchemaParser(data)
        result = parser.model_defs
        expected = textwrap.dedent('''
            class ModelName(pydantic.BaseModel):
                foo: str = 'bar'
        ''').lstrip()

        assert result["ModelName"] == expected

    def test_schema_with_nested_object(self):
        data = {
            "ModelName": {
                "properties": {
                    "foo": {
                        "properties": {
                            "bar": {"type": "string"},
                        },
                        "type": "object",
                    },
                },
                "type": "object",
            },
        }
        parser = schemas.SchemaParser(data)
        result = parser.model_defs
        expected = {
            "ModelName": textwrap.dedent('''
                class ModelName(pydantic.BaseModel):
                    foo: "_foo"
            ''').lstrip(),
            "_foo": textwrap.dedent('''
                class _foo(pydantic.BaseModel):
                    bar: str
            ''').lstrip(),
        }

        assert result == expected

    def test_schema_with_array_of_strings(self):
        data = {
            "ModelName": {
                "properties": {
                    "foo": {
                        "items": {
                            "type": "string",
                        },
                        "type": "array",
                    },
                },
                "type": "object",
            },
        }
        parser = schemas.SchemaParser(data)
        result = parser.model_defs
        expected = textwrap.dedent('''
            class ModelName(pydantic.BaseModel):
                foo: List[str]
        ''').lstrip()

        assert result["ModelName"] == expected

    def test_schema_with_array_of_objects(self):
        data = {
            "ModelName": {
                "properties": {
                    "foo": {
                        "items": {
                            "$ref": "OtherName",
                        },
                        "type": "array",
                    },
                },
                "type": "object",
            },
        }
        parser = schemas.SchemaParser(data)
        result = parser.model_defs
        expected = textwrap.dedent('''
            class ModelName(pydantic.BaseModel):
                foo: List["OtherName"]
        ''').lstrip()

        assert result["ModelName"] == expected


class TestBuildModels:
    def test_no_schemas(self):
        result = schemas.build_models({})

        assert result == {}

    def test_simple_schema_with_default(self):
        data = {
            "ModelName": {
                "properties": {
                    "foo": {
                        "default": "foo#default",
                        "type": "string",
                    },
                },
                "type": "object",
            },
        }
        result = schemas.build_models(data)

        assert sorted(result) == ["ModelName"]

        ModelName = result["ModelName"]
        obj = ModelName(ignored="!")
        assert obj.dict() == {"foo": "foo#default"}

    def test_schema_with_nested_object(self):
        data = {
            "ModelName": {
                "properties": {
                    "foo": {
                        "properties": {
                            "bar": {"type": "string"},
                        },
                        "type": "object",
                    },
                },
                "type": "object",
            },
        }
        result = schemas.build_models(data)

        assert sorted(result) == ["ModelName", "_foo"]

        ModelName = result["ModelName"]
        obj = ModelName(foo={"bar": "b", "ignored": "!"})
        assert obj.dict() == {"foo": {"bar": "b"}}

    def test_schema_with_reference_to_object(self):
        data = {
            "ModelName": {
                "properties": {
                    "foo": {
                        "$ref": "OtherName",
                    },
                },
                "type": "object",
            },
            "OtherName": {
                "properties": {
                    "bar": {
                        "type": "string",
                    },
                },
                "type": "object",
            },
        }
        result = schemas.build_models(data)

        assert sorted(result) == ["ModelName", "OtherName"]

        ModelName, OtherName = result["ModelName"], result["OtherName"]
        obj = ModelName(foo=OtherName(bar="b", ignored="!"))
        assert obj.dict() == {"foo": {"bar": "b"}}


class TestValidPropertyName:
    def test_builtin_name(self):
        name = "dir"
        result = schemas.SchemaParser.valid_property_name(name)

        assert result == "dir_"

    def test_keyword_name(self):
        name = "class"
        result = schemas.SchemaParser.valid_property_name(name)

        assert result == "class_"

    def test_valid_name(self):
        name = "foo"
        result = schemas.SchemaParser.valid_property_name(name)

        assert result == "foo"
