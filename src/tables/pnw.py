"""
Here we define the database tables.
"""

from __future__ import annotations

import difflib
import inspect

# from abc import abstractmethod
from typing import Any, Optional

from piccolo.columns import Integer, Text, Timestamp, Varchar
from piccolo.engine import Engine
from piccolo.table import Table
from piccolo.utils.pydantic import create_pydantic_model
from pydantic import AliasChoices, BaseModel, Field, create_model
from pydantic.fields import FieldInfo


class PnwTable(Table):
    """
    A base class for all API-based PNW tables.
    """

    # This is for type hinting. The actual model is created in the __init_subclass__ method.
    pydantic_model: type[BaseModel]

    def __init_subclass__(
        cls,
        tablename: Optional[str] = None,
        db: Optional[Engine[Any]] = None,
        tags: Optional[list[str]] = None,
        help_text: Optional[str] = None,
        schema: Optional[str] = None,
    ):
        super().__init_subclass__(
            tablename=tablename, db=db, tags=tags, help_text=help_text, schema=schema
        )
        cls._enforce_abstract_methods()
        cls._validate_and_create_pydantic_model()

    @classmethod
    def _enforce_abstract_methods(cls):
        """
        Ensure that all abstract methods are implemented.
        """
        abstract_methods = {
            name
            for name, value in inspect.getmembers(cls)
            if getattr(value, "__isabstractmethod__", False)
        }

        if abstract_methods:
            raise TypeError(
                f"Cannot instantiate class {cls.__name__} without implementing abstract methods: "
                + ", ".join(abstract_methods)
            )

    @classmethod
    def _validate_and_create_pydantic_model(cls):
        """
        Validate the pydantic overrides and create the pydantic model for the table.
        """
        fields = cls._get_pydantic_fields()

        invalid_fields, similar_fields = cls._find_invalid_fields(list(fields.keys()))

        if invalid_fields:
            raise ValueError(
                cls._construct_invalid_fields_error_message(
                    invalid_fields, similar_fields
                )
            )

        cls.pydantic_model = create_model(
            f"{cls.__name__}Pydantic",
            __base__=create_pydantic_model(cls),
            __config__=None,
            __doc__=None,
            __module__=__name__,
            __validators__=None,
            __cls_kwargs__=None,
            **fields,
        )

    @classmethod
    def _get_pydantic_fields(cls) -> dict[str, tuple[type, FieldInfo]]:
        """
        Retrieve the pydantic fields from the overrides.
        """
        return {
            name: (field_type, field)
            for name, (field_type, field) in cls.pydantic_overrides().items()
        }

    @classmethod
    def _find_invalid_fields(
        cls, field_names: list[str]
    ) -> tuple[list[str], list[list[str]]]:
        """
        Identify invalid fields and suggest similar field names if available.
        """
        invalid_fields = []
        similar_fields = []

        column_names = [column._meta.name for column in cls._meta.columns]  # type: ignore # pylint: disable=protected-access

        for field_name in field_names:
            if field_name not in column_names:
                invalid_fields.append(field_name)
                similar_fields.append(
                    difflib.get_close_matches(field_name, column_names)
                )

        return invalid_fields, similar_fields

    @classmethod
    def _construct_invalid_fields_error_message(
        cls, invalid_fields: list[str], similar_fields: list[list[str]]
    ) -> str:
        """
        Construct a detailed error message for invalid fields.
        """
        err_message = (
            f"PnwTable {cls.__name__} has invalid field names in pydantic_overrides: "
        )

        for i, field_name in enumerate(invalid_fields):
            err_message += f"'{field_name}'"
            if similar_fields[i]:
                err_message += f" (did you mean {', '.join(f"'{field}'" for field in similar_fields[i])}?)"
            err_message += ", "

        return err_message.rstrip(", ")

    ### Methods that can be overridden by subclasses ###

    @classmethod
    def pydantic_overrides(cls) -> dict[str, tuple[type, FieldInfo]]:
        """
        A dictionary of field overrides for the pydantic model.

        The format is: `{<field_name>: (<type>, Field(...))}`

        To create an alias for a field, you can do:
        ```
        {
            "<field_name>": (<type>, Field(validation_alias=AliasChoices("<field_name>", "<alias>")))
        }
        ```
        """
        return {}


class Test(PnwTable):
    """
    A table to store user information.
    """

    id = Integer(primary_key=True)
    username = Text()
    password = Varchar(length=100)
    created_at = Timestamp()

    @classmethod
    def pydantic_overrides(cls):

        return {
            "username": (
                str,
                Field(validation_alias=AliasChoices("username", "name")),
            ),
        }


test_data = {
    "id": 1,
    "name": "test",
    "password": "test",
    "created_at": "2021-01-01T00:00:00",
}

print(Test.pydantic_model(**test_data).model_dump_json())


class Nation:  # pylint: disable=empty-docstring
    """"""
