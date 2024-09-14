# Generated by ariadne-codegen
# Source: resources/queries.graphql

from datetime import date
from typing import Annotated, List, Optional

from pydantic import AwareDatetime, BeforeValidator, Field

from .base_model import BaseModel
from .enums import (
    DomesticPolicy,
    EconomicPolicy,
    GovernmentType,
    SocialPolicy,
    WarPolicy,
    WarType,
)


class AlliancePositionFields(BaseModel):
    id: str
    date: AwareDatetime
    alliance_id: str
    name: str
    creator_id: str
    last_editor_id: str
    date_modified: AwareDatetime
    position_level: int
    leader: bool
    heir: bool
    officer: bool
    member: bool
    permissions: int


class AllianceFields(BaseModel):
    id: int
    name: str
    acronym: str
    score: float
    color: str
    date: AwareDatetime
    average_score: Optional[float]
    accept_members: bool
    flag: str
    rank: int
    alliance_positions: List["AllianceFieldsAlliancePositions"]


class AllianceFieldsAlliancePositions(AlliancePositionFields):
    pass


class CityFields(BaseModel):
    id: str
    nation_id: str
    name: str
    nuke_date: Optional[str]
    date: date
    infrastructure: float
    land: float
    powered: bool
    oil_power: int
    wind_power: int
    coal_power: int
    nuclear_power: int
    coal_mine: int
    oil_well: int
    uranium_mine: int
    barracks: int
    farm: int
    police_station: int
    hospital: int
    recycling_center: int
    subway: int
    supermarket: int
    bank: int
    shopping_mall: int
    stadium: int
    lead_mine: int
    iron_mine: int
    bauxite_mine: int
    oil_refinery: int
    aluminum_refinery: int
    steel_mill: int
    munitions_factory: int
    factory: int
    hangar: int
    drydock: int


class NationFields(BaseModel):
    id: int
    alliance: Annotated[
        Optional[int], BeforeValidator(lambda x: int(x) if int(x) != 0 else None)
    ] = Field(alias="alliance_id")
    alliance_position_id: Annotated[
        Optional[int], BeforeValidator(lambda x: int(x) if int(x) != 0 else None)
    ]
    nation_name: str
    leader_name: str
    continent: str
    war_policy: WarPolicy
    war_policy_turns: int
    domestic_policy: DomesticPolicy
    domestic_policy_turns: int
    color: str
    num_cities: int
    score: float
    update_tz: Optional[float]
    population: int
    flag: str
    vacation_mode_turns: int
    beige_turns: int
    espionage_available: bool
    last_active: AwareDatetime
    date: AwareDatetime
    soldiers: int
    tanks: int
    aircraft: int
    ships: int
    missiles: int
    nukes: int
    spies: int
    discord: str
    discord_id: Optional[int]
    turns_since_last_city: int
    turns_since_last_project: int
    projects: int
    project_bits: int
    moon_landing_date: Optional[AwareDatetime]
    mars_landing_date: Optional[AwareDatetime]
    wars_won: int
    wars_lost: int
    tax_id: str
    alliance_seniority: int
    gross_national_income: float
    gross_domestic_product: float
    soldier_casualties: int
    soldier_kills: int
    tank_casualties: int
    tank_kills: int
    aircraft_casualties: int
    aircraft_kills: int
    ship_casualties: int
    ship_kills: int
    missile_casualties: int
    missile_kills: int
    nuke_casualties: int
    nuke_kills: int
    spy_casualties: Optional[int]
    spy_kills: Optional[int]
    spy_attacks: Optional[int]
    money_looted: float
    total_infrastructure_destroyed: float
    total_infrastructure_lost: float
    vip: bool
    commendations: int
    denouncements: int
    offensive_wars_count: int
    defensive_wars_count: int
    economic_policy: EconomicPolicy
    social_policy: SocialPolicy
    government_type: GovernmentType
    alliance_join_date: Optional[AwareDatetime]


class PaginatorFields(BaseModel):
    count: int
    has_more_pages: bool = Field(alias="hasMorePages")


class SubscriptionAccountFields(BaseModel):
    id: int
    last_active: AwareDatetime
    discord_id: Optional[int]


class SubscriptionAllianceFields(BaseModel):
    id: int
    name: str
    acronym: str
    score: float
    color: str
    date_created: AwareDatetime = Field(alias="date")
    accepts_members: bool = Field(alias="accept_members")
    flag_url: str = Field(alias="flag")


class SubscriptionNationFields(BaseModel):
    id: int
    name: str = Field(alias="nation_name")
    leader_name: str
    alliance_seniority_days: int = Field(alias="alliance_seniority")
    continent: str
    war_policy: WarPolicy
    war_policy_turns: int
    domestic_policy: DomesticPolicy
    domestic_policy_turns: int
    color: str
    num_cities: int
    score: float
    update_timezone: Optional[float] = Field(alias="update_tz")
    population: int
    flag_url: str = Field(alias="flag")
    vacation_mode_turns: int
    beige_turns: int
    espionage_available: bool
    date_created: AwareDatetime = Field(alias="date")
    soldiers: int
    tanks: int
    aircraft: int
    ships: int
    missiles: int
    nukes: int
    spies: int
    turns_since_last_city: int
    turns_since_last_project: int
    num_projects: int = Field(alias="projects")
    project_bits: int
    wars_won: int
    wars_lost: int


class WarFields(BaseModel):
    id: str
    date: AwareDatetime
    end_date: Optional[AwareDatetime]
    reason: str
    war_type: WarType
    ground_control: Optional[str]
    air_superiority: Optional[str]
    naval_blockade: Optional[str]
    winner_id: Optional[str]
    turns_left: int
    att_id: str
    def_id: str
    att_points: int
    def_points: int
    att_peace: bool
    def_peace: bool
    att_resistance: int
    def_resistance: int
    att_fortify: bool
    def_fortify: bool
    att_gas_used: float
    def_gas_used: float
    att_mun_used: float
    def_mun_used: float
    att_alum_used: float
    def_alum_used: float
    att_steel_used: float
    def_steel_used: float
    att_infra_destroyed: float
    def_infra_destroyed: float
    att_money_looted: float
    def_money_looted: float
    att_soldiers_lost: int
    def_soldiers_lost: int
    att_tanks_lost: int
    def_tanks_lost: int
    att_aircraft_lost: int
    def_aircraft_lost: int
    att_ships_lost: int
    def_ships_lost: int
    att_missiles_used: int
    def_missiles_used: int
    att_nukes_used: int
    def_nukes_used: int
    att_infra_destroyed_value: float
    def_infra_destroyed_value: float


AlliancePositionFields.model_rebuild()
AllianceFields.model_rebuild()
CityFields.model_rebuild()
NationFields.model_rebuild()
PaginatorFields.model_rebuild()
SubscriptionAccountFields.model_rebuild()
SubscriptionAllianceFields.model_rebuild()
SubscriptionNationFields.model_rebuild()
WarFields.model_rebuild()
