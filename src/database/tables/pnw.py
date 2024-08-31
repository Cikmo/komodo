"""
Here we define the database tables.
"""

from __future__ import annotations

from datetime import datetime

from piccolo.columns import (
    BigInt,
    Boolean,
    ForeignKey,
    Integer,
    OnDelete,
    Real,
    Text,
    Timestamptz,
    Varchar,
)

from src.database.base_table import PnwBaseTable, PydanticOverride
from src.database.enums import Color, Continent, DomesticPolicy, WarPolicy
from src.pnw.api_v3 import AllianceFields, CityFields, NationFields


class Alliance(PnwBaseTable[AllianceFields]):
    """
    A table to store information about alliances in the game.
    """

    id = Integer(primary_key=True)
    name = Text()
    acronym = Text()
    score = Real()
    color = Text(choices=Color)
    date_created = Timestamptz()  # API name: date
    average_score = Real()
    accepts_members = Boolean()  # API name: accept_members
    flag_url = Text()  # API name: flag
    rank = Integer()

    @property
    def members(self):
        """
        Returns a query object for all the members of this alliance.
        """
        return Nation.objects().where(Nation.alliance == self)

    @classmethod
    def preprocess_api_v3_model(cls, model: AllianceFields) -> AllianceFields:
        if model.average_score is None:
            model.average_score = 0.0

        return model

    @classmethod
    def pydantic_overrides(cls) -> PydanticOverride:
        return [
            (cls.date_created, "date", datetime),
            (cls.accepts_members, "accept_members", bool),
            (cls.flag_url, "flag", str),
        ]


class Nation(PnwBaseTable[NationFields]):
    """
    A table to store information about nations in the game.
    """

    id = Integer(primary_key=True)
    name = Text(index=True)  # API name: nation_name
    leader_name = Text()
    continent = Varchar(length=2, choices=Continent)
    war_policy = Text(choices=WarPolicy)
    war_policy_turns = Integer()
    domestic_policy = Text(choices=DomesticPolicy)
    domestic_policy_turns = Integer()
    num_cities = Integer()
    color = Text(choices=Color)
    score = Real()
    update_timezone: Real | None = Real(null=True)  # API name: update_tz
    population = Integer()
    flag_url = Text()  # API name: flag
    vacation_mode_turns = Integer()
    beige_turns = Integer()
    espionage_available = Boolean()
    last_active = Timestamptz()
    date_created = Timestamptz()  # API name: date
    soldiers = Integer()
    tanks = Integer()
    aircraft = Integer()
    ships = Integer()
    missiles = Integer()
    nukes = Integer()
    spies = Integer()
    discord_id: BigInt | None = BigInt(index=True, null=True)
    turns_since_last_city = Integer()
    turns_since_last_project = Integer()
    num_projects = Integer()  # API name: projects
    project_bits = BigInt()
    wars_won = Integer()
    wars_lost = Integer()
    offensive_war_count = Integer()  # API name: offensive_wars_count
    defensive_war_count = Integer()  # API name: defensive_wars_count
    alliance_join_date: Timestamptz | None = Timestamptz(null=True)

    alliance = ForeignKey(references=Alliance, on_delete=OnDelete.set_null)
    # alliance_position = ForeignKey(
    #    references="AlliancePosition", on_delete=OnDelete.set_null
    # )

    # tax_bracket = ForeignKey(
    #    references="TaxBracket", on_delete=OnDelete.set_null
    # )

    ### Reverse Foreign Keys

    @property
    def cities(self):
        """
        Returns a query object for all the cities of this nation.
        """
        return City.objects().where(City.nation == self)

    @classmethod
    def preprocess_api_v3_model(cls, model: NationFields) -> NationFields:
        if model.alliance_id == "0" or model.alliance_obj is None:
            model.alliance_id = None

        return model

    @classmethod
    def pydantic_overrides(cls) -> PydanticOverride:
        return [
            (cls.name, "nation_name", str),
            (cls.update_timezone, "update_tz", float | None),
            (cls.flag_url, "flag", str),
            (cls.date_created, "date", datetime),
            (cls.num_projects, "projects", int),
            (cls.offensive_war_count, "offensive_wars_count", int),
            (cls.defensive_war_count, "defensive_wars_count", int),
            (cls.alliance, "alliance_id", int | None),
        ]


class City(PnwBaseTable[CityFields]):
    """
    A table to store information about cities in the game.
    """

    id = Integer(primary_key=True)
    name = Text()
    date_created = Timestamptz()  # API name: date
    infrastructure = Real()
    land = Real()
    powered = Boolean()
    last_nuke_date: Timestamptz | None = Timestamptz(
        null=True,
    )  # API name: nuke_date

    # Power
    oil_power_plants = Integer()  # API name: oil_power
    wind_power_plants = Integer()  # API name: wind_power
    coal_power_plants = Integer()  # API name: coal_power
    nuclear_power_plants = Integer()  # API name: nuclear_power

    # Raw Resources
    coal_mines = Integer()  # API name: coal_mine
    oil_wells = Integer()  # API name: oil_well
    uranium_mines = Integer()  # API name: uranium_mine
    bauxite_mines = Integer()  # API name: bauxite_mine
    lead_mines = Integer()  # API name: lead_mine
    iron_mines = Integer()  # API name: iron_mine
    farms = Integer()  # API name: farm

    # Manufacturing
    oil_refineries = Integer()  # API name: oil_refinery
    aluminum_refineries = Integer()  # API name: aluminum_refinery
    steel_mills = Integer()  # API name: steel_mill
    munitions_factories = Integer()  # API name: munitions_factory

    # Civil
    police_stations = Integer()  # API name: police_station
    hospitals = Integer()  # API name: hospital
    recycling_centers = Integer()  # API name: recycling_center
    subways = Integer()  # API name: subway

    # Commerce
    supermarkets = Integer()  # API name: supermarket
    banks = Integer()  # API name: bank
    shopping_malls = Integer()  # API name: shopping_mall
    stadiums = Integer()  # API name: stadium

    # Military
    barracks = Integer()
    factories = Integer()  # API name: factory
    hangars = Integer()  # API name: hangar
    drydocks = Integer()  # API name: drydock

    # Foreign Keys
    nation = ForeignKey(references=Nation, null=False, on_delete=OnDelete.cascade)

    @classmethod
    def preprocess_api_v3_model(cls, model: CityFields) -> CityFields:
        # For some reason the API returns a negative date if the city has never been nuked
        # to go around this we need to manually set it to None
        if model.nuke_date and model.nuke_date.startswith("-"):
            model.nuke_date = None

        return model

    @classmethod
    def pydantic_overrides(cls) -> PydanticOverride:
        return [
            (cls.date_created, "date", datetime),
            (cls.last_nuke_date, "nuke_date", datetime | None),
            (cls.oil_power_plants, "oil_power", int),
            (cls.wind_power_plants, "wind_power", int),
            (cls.coal_power_plants, "coal_power", int),
            (cls.nuclear_power_plants, "nuclear_power", int),
            (cls.coal_mines, "coal_mine", int),
            (cls.oil_wells, "oil_well", int),
            (cls.uranium_mines, "uranium_mine", int),
            (cls.bauxite_mines, "bauxite_mine", int),
            (cls.lead_mines, "lead_mine", int),
            (cls.iron_mines, "iron_mine", int),
            (cls.farms, "farm", int),
            (cls.oil_refineries, "oil_refinery", int),
            (cls.aluminum_refineries, "aluminum_refinery", int),
            (cls.steel_mills, "steel_mill", int),
            (cls.munitions_factories, "munitions_factory", int),
            (cls.police_stations, "police_station", int),
            (cls.hospitals, "hospital", int),
            (cls.recycling_centers, "recycling_center", int),
            (cls.subways, "subway", int),
            (cls.supermarkets, "supermarket", int),
            (cls.banks, "bank", int),
            (cls.shopping_malls, "shopping_mall", int),
            (cls.stadiums, "stadium", int),
            (cls.factories, "factory", int),
            (cls.hangars, "hangar", int),
            (cls.drydocks, "drydock", int),
            (cls.nation, "nation_id", int),
        ]
