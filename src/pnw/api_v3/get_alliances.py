# Generated by ariadne-codegen
# Source: resources/queries.graphql

from typing import List, Optional

from pydantic import Field

from .base_model import BaseModel
from .fragments import AllianceFields, PaginatorFields


class GetAlliances(BaseModel):
    alliances: Optional["GetAlliancesAlliances"]


class GetAlliancesAlliances(BaseModel):
    data: List["GetAlliancesAlliancesData"]
    paginator_info: "GetAlliancesAlliancesPaginatorInfo" = Field(alias="paginatorInfo")


class GetAlliancesAlliancesData(AllianceFields):
    pass


class GetAlliancesAlliancesPaginatorInfo(PaginatorFields):
    pass


GetAlliances.model_rebuild()
GetAlliancesAlliances.model_rebuild()
