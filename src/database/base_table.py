"""
This module contains base classes for tables in the database. We create custom base classes
to extend the functionality of the Piccolo Table class, and to enforce certain patterns and
conventions.
"""

from __future__ import annotations

import difflib
import inspect

# from abc import abstractmethod
from typing import (
    Any,
    Generic,
    Optional,
    Self,
    Sequence,
    TypeVar,
    get_args,
    get_origin,
    overload,
)

from piccolo.columns import Column
from piccolo.engine import Engine
from piccolo.table import Table
from piccolo.utils.pydantic import create_pydantic_model
from pydantic import AliasChoices, BaseModel, Field, create_model
from pydantic.fields import FieldInfo


class BaseTable(Table):
    """
    A base class for all Piccolo tables in this project.
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
        fields = cls._get_pydantic_override_fields()

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
    def _get_pydantic_override_fields(cls) -> dict[str, tuple[type, FieldInfo]]:
        """
        Retrieve the pydantic fields from the overrides.
        """

        overrides: Sequence[tuple[Column, str, type]] = cls.pydantic_overrides()
        overrides_dict: dict[str, tuple[type, FieldInfo]] = {}

        for override in overrides:
            overrides_dict[override[0]._meta.name] = (  # type: ignore # pylint: disable=protected-access
                override[2],
                Field(
                    validation_alias=AliasChoices(
                        override[0]._meta.name, override[1]  # type: ignore # pylint: disable=protected-access
                    )
                ),
            )

        return overrides_dict

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
    def pydantic_overrides(cls) -> Sequence[tuple[Column, str, type]]:
        """
        Override this method to provide custom pydantic overrides for the table.
        You can access the pydantic model from the class attribute `pydantic_model`.

        Expected return format:
        [
            (column, alias, field_type),
            ...
        ]

        Where:
        - column: The column to override.
        - alias: The alias to use in the pydantic model.
        - field_type: The type of the field.

        Example:
        ```python
        @classmethod
        def pydantic_overrides(cls):
            return [
                (cls.name, "nation_name", str),
                (cls.update_timezone, "update_tz", float),
                ...
            ]
        """
        return []


T = TypeVar("T", bound=BaseModel)


class PnwBaseTable(Generic[T], BaseTable):
    """
    A base class for all tables in the Politics and War database.
    """

    api_v3_model: type[BaseModel]

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

        # Set the api_v3_model attribute based on the generic type parameter
        orig_bases: tuple[type, ...] = getattr(cls, "__orig_bases__", ())

        for base in orig_bases:
            origin = get_origin(base)
            if origin is PnwBaseTable:
                cls.api_v3_model = get_args(base)[0]
                break

        if not hasattr(cls, "api_v3_model"):
            raise TypeError(
                f"Class {cls.__name__} must have a generic type parameter to set the api_v3_model."
            )

    @overload
    @classmethod
    def from_api_v3(cls, model: T) -> Self: ...

    @overload
    @classmethod
    def from_api_v3(cls, model: Sequence[T]) -> list[Self]: ...

    @classmethod
    def from_api_v3(cls, model: T | Sequence[T]) -> Self | list[Self]:
        """Create a new table instance from the API v3 data.

        Args:
            model: The API v3 model to convert. Can be a single model or a list of models.

        Returns:
            Self | list[Self]: The converted table instance(s).
        """
        if isinstance(model, Sequence):
            return [cls._convert_api_v3_model_to_table(m) for m in model]
        return cls._convert_api_v3_model_to_table(model)

    @classmethod
    def _convert_api_v3_model_to_table(cls, model: T) -> Self:
        """
        Convert an API v3 model to a table instance.
        """
        converted_model = cls.api_v3_model.model_validate(model.model_dump())
        return cls(**converted_model.model_dump())
