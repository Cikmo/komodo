# Generated by ariadne-codegen
# Source: resources/queries.graphql

from typing import List, Optional

from pydantic import Field

from .base_model import BaseModel
from .fragments import PaginatorFields, WarFields


class GetWars(BaseModel):
    wars: Optional["GetWarsWars"]


class GetWarsWars(BaseModel):
    data: List["GetWarsWarsData"]
    paginator_info: "GetWarsWarsPaginatorInfo" = Field(alias="paginatorInfo")


class GetWarsWarsData(WarFields):
    pass


class GetWarsWarsPaginatorInfo(PaginatorFields):
    pass


GetWars.model_rebuild()
GetWarsWars.model_rebuild()