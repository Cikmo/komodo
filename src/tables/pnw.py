"""
Here we define the database tables.
"""

from __future__ import annotations

import difflib
import inspect

#from abc import abstractmethod
from typing import Any, Optional

from piccolo.columns import Integer, Text, Timestamp, Varchar
from piccolo.engine import Engine
from piccolo.table import Table
from piccolo.utils.pydantic import create_pydantic_model
from pydantic import AliasChoices, BaseModel, Field, create_model
from pydantic.fields import FieldInfo


class PnwTable(Table):
    """
    A base class for all api based pnw tables.
    """

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

        # Enforce that all abstract methods are implemented
        abstract_methods = set(
            name
            for name, value in inspect.getmembers(cls)
            if getattr(value, "__isabstractmethod__", False)
        )

        if abstract_methods:
            raise TypeError(
                f"Can't instantiate class {cls.__name__} without implementing abstract methods: "
                + ", ".join(abstract_methods)
            )

        # Create a pydantic model for the table
        fields = {
            name: (field_type, field)
            for name, (field_type, field) in cls.pydantic_overrides().items()
        }

        # make sure all field names in overrides are valid, by checking cls._meta.colums[i]._meta.name. It is

        invalid_fields: list[str] = []
        for field_name in fields.keys():
            if not any(column._meta.name == field_name for column in cls._meta.columns): # type: ignore
                invalid_fields.append(field_name)
        if invalid_fields:
            similar_fields = []
            for field_name in invalid_fields:
                similar_fields.append(
                    difflib.get_close_matches(
                        field_name, [column._meta.name for column in cls._meta.columns] # type: ignore
                    )
                )

            err_message = f"PnwTable {cls.__name__} has invalid field names in pydantic_overrides: "
            for i, field_name in enumerate(invalid_fields):
                err_message += f"'{field_name}'"
                if similar_fields[i]:
                    err_message += f" (did you mean to use {', '.join(f'\'{field}\'' for field in similar_fields[i])}?)"
                err_message += ", "
            err_message = err_message[:-2]  # remove the last comma and space
            raise ValueError(err_message)

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
    usernime = Text()
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


class Nation:
    """"""
