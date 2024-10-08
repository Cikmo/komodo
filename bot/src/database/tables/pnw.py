"""
Here we define the database tables.
"""

from __future__ import annotations

from enum import Enum

from piccolo.columns import (
    BigInt,
    Boolean,
    Date,
    DoublePrecision,
    ForeignKey,
    Integer,
    OnDelete,
    Real,
    Text,
    Timestamptz,
    Varchar,
)
from piccolo.table import Table

from src.database.base_table import PnwBaseTable
from src.database.enums import Color, Continent, DomesticPolicy, WarPolicy, WarType
from src.pnw.api_v3 import WarFields


class Alliance(Table):
    """
    A table to store information about alliances in the game.
    """

    id = Integer(primary_key=True)
    name = Text()
    acronym = Text()
    score = DoublePrecision()
    color = Text(choices=Color)
    date_created = Timestamptz()  # API name: date
    accepts_members = Boolean()  # API name: accept_members
    flag_url = Text()  # API name: flag

    @property
    def members(self):
        """
        Returns a query object for all the members of this alliance.
        """
        return Nation.objects().where(Nation.alliance == self)


class AlliancePosition(Table):
    """
    A table to store information about the positions in an alliance.
    """

    class DefaultPosition(Enum):
        """Enum for the default alliance position ids."""

        APPLICANT = 0
        MEMBER = 232
        OFFICER = 231
        HEIR = 230
        LEADER = 229

    id = Integer(primary_key=True)
    name = Text()
    date_created = Timestamptz()  # API name: date
    date_modified = Timestamptz()
    position_level = Integer()
    permission_bits = Integer()  # API name: permissions
    creator_id = Integer()
    last_editor_id = Integer()

    alliance = ForeignKey(references=Alliance, on_delete=OnDelete.cascade, null=False)

    def is_default_position(self, position: DefaultPosition) -> bool:
        """
        Returns whether this position is a default position.
        """
        return self.id == position.value

    @property
    def creator(self):
        """
        Returns the creator of this position. May not exist.
        """
        return Nation.objects().where(Nation.id == self.creator_id).first()

    @property
    def last_editor(self):
        """
        Returns the last editor of this position. May not exist.
        """
        return Nation.objects().where(Nation.id == self.last_editor_id).first()


class Nation(Table):
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
    score = DoublePrecision()
    update_timezone = DoublePrecision(null=True, default=None)  # API name: update_tz
    population = Integer()
    flag_url = Text()  # API name: flag
    vacation_mode_turns = Integer()
    beige_turns = Integer()
    espionage_available = Boolean()
    last_active = Timestamptz(null=True, default=None)
    date_created = Timestamptz()  # API name: date
    soldiers = Integer()
    tanks = Integer()
    aircraft = Integer()
    ships = Integer()
    missiles = Integer()
    nukes = Integer()
    spies = Integer()
    discord_id = BigInt(index=True, null=True, default=None)
    turns_since_last_city = Integer()
    turns_since_last_project = Integer()
    num_projects = Integer()  # API name: projects
    project_bits = BigInt()
    wars_won = Integer()
    wars_lost = Integer()
    alliance_seniority_days = Integer()

    alliance = ForeignKey(references=Alliance, on_delete=OnDelete.set_null)
    alliance_position = ForeignKey(
        AlliancePosition,
        on_delete=OnDelete.set_null,
    )

    ### Reverse Foreign Keys

    @property
    def cities(self):
        """
        Returns a query object for all the cities of this nation.
        """
        return City.objects().where(City.nation == self)


# a = {
#     "id": 1046222,  # yes
#     "nation_id": 239259,  # yes
#     "name": "Raftel's city",  # yes
#     "date": "2023-07-15",  # yes
#     "infrastructure": 663.93,  # yes
#     "land": 2250.0,  # yes
#     "oil_power": 0,  # yes
#     "wind_power": 0,  # yes
#     "coal_power": 0,  # yes
#     "nuclear_power": 2,  # yes
#     "coal_mine": 0,  # yes
#     "oil_well": 10,  # yes
#     "uranium_mine": 0,  # yes
#     "barracks": 5,  # yes
#     "farm": 0,  # yes
#     "police_station": 1,  # yes
#     "hospital": 2,  # yes
#     "recycling_center": 1,  # yes
#     "subway": 1,  # yes
#     "supermarket": 3,  # yes
#     "bank": 5,  # yes
#     "shopping_mall": 4,  # yes
#     "stadium": 3,  # yes
#     "lead_mine": 0,  # yes
#     "iron_mine": 0,  # yes
#     "bauxite_mine": 0,
#     "oil_refinery": 0,  # yes
#     "aluminum_refinery": 0,  # yes
#     "steel_mill": 0,  # yes
#     "munitions_factory": 0,  # yes
#     "factory": 5,  # yes
#     "hangar": 5,  # yes
#     "drydock": 3,  # yes
#     "nuke_date": "0000-00-00",  # yes
# }


class City(Table):
    """
    A table to store information about cities in the game.
    """

    id = Integer(primary_key=True)
    name = Text()
    date_created = Date()  # API name: date
    infrastructure = DoublePrecision()
    land = DoublePrecision()
    last_nuke_in_game_date = Date(
        null=True,
        default=None,
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

    # @classmethod
    # def preprocess_api_v3_model(cls, model: CityFields) -> CityFields:
    #     # For some reason the API returns a negative date if the city has never been nuked
    #     # to go around this we need to manually set it to None
    #     if model.nuke_date and model.nuke_date.startswith("-"):
    #         model.nuke_date = None

    #     return model

    # @classmethod
    # def pydantic_overrides(cls) -> PydanticOverride:
    #     return [
    #         (cls.date_created, "date", datetime),
    #         (cls.last_nuke_date, "nuke_date", datetime | None),
    #         (cls.oil_power_plants, "oil_power", int),
    #         (cls.wind_power_plants, "wind_power", int),
    #         (cls.coal_power_plants, "coal_power", int),
    #         (cls.nuclear_power_plants, "nuclear_power", int),
    #         (cls.coal_mines, "coal_mine", int),
    #         (cls.oil_wells, "oil_well", int),
    #         (cls.uranium_mines, "uranium_mine", int),
    #         (cls.bauxite_mines, "bauxite_mine", int),
    #         (cls.lead_mines, "lead_mine", int),
    #         (cls.iron_mines, "iron_mine", int),
    #         (cls.farms, "farm", int),
    #         (cls.oil_refineries, "oil_refinery", int),
    #         (cls.aluminum_refineries, "aluminum_refinery", int),
    #         (cls.steel_mills, "steel_mill", int),
    #         (cls.munitions_factories, "munitions_factory", int),
    #         (cls.police_stations, "police_station", int),
    #         (cls.hospitals, "hospital", int),
    #         (cls.recycling_centers, "recycling_center", int),
    #         (cls.subways, "subway", int),
    #         (cls.supermarkets, "supermarket", int),
    #         (cls.banks, "bank", int),
    #         (cls.shopping_malls, "shopping_mall", int),
    #         (cls.stadiums, "stadium", int),
    #         (cls.factories, "factory", int),
    #         (cls.hangars, "hangar", int),
    #         (cls.drydocks, "drydock", int),
    #         (cls.nation, "nation_id", int),
    #     ]


class War(PnwBaseTable[WarFields]):
    """
    A table to store information about wars in the game.
    """

    id = Integer(primary_key=True)
    start_date = Timestamptz()  # API name: date
    end_date = Timestamptz(default=None, null=True)
    reason = Text()
    war_type = Text(choices=WarType)
    turns_left = Integer()
    attacker_action_points = Integer()  # API name: att_points
    defender_action_points = Integer()  # API name: def_points
    attacker_offering_peace = Boolean()  # API name: att_peace
    defender_offering_peace = Boolean()  # API name: def_peace
    attacker_resistance = Integer()  # API name: att_resistance
    defender_resistance = Integer()  # API name: def_resistance
    attacker_fortified = Boolean()  # API name: att_fortify
    defender_fortified = Boolean()  # API name: def_fortify
    attacker_gasoline_used = Real()  # API name: att_gas_used
    defender_gasoline_used = Real()  # API name: def_gas_used
    attacker_munitions_used = Real()  # API name: att_mun_used
    defender_munitions_used = Real()  # API name: def_mun_used
    attacker_aluminum_used = Real()  # API name: att_alum_used
    defender_aluminum_used = Real()  # API name: def_alum_used
    attacker_steel_used = Real()  # API name: att_steel_used
    defender_steel_used = Real()  # API name: def_steel_used
    attacker_infra_destroyed = Real()  # API name: att_infra_destroyed
    defender_infra_destroyed = Real()  # API name: def_infra_destroyed
    attacker_money_looted = Real()  # API name: att_money_looted
    defender_money_looted = Real()  # API name: def_money_looted
    attacker_soldiers_lost = Integer()  # API name: att_soldiers_lost
    defender_soldiers_lost = Integer()  # API name: def_soldiers_lost
    attacker_tanks_lost = Integer()  # API name: att_tanks_lost
    defender_tanks_lost = Integer()  # API name: def_tanks_lost
    attacker_aircraft_lost = Integer()  # API name: att_aircraft_lost
    defender_aircraft_lost = Integer()  # API name: def_aircraft_lost
    attacker_ships_lost = Integer()  # API name: att_ships_lost
    defender_ships_lost = Integer()  # API name: def_ships_lost
    attacker_missiles_used = Integer()  # API name: att_missiles_used
    defender_missiles_used = Integer()  # API name: def_missiles_used
    attacker_nukes_used = Integer()  # API name: att_nukes_used
    defender_nukes_used = Integer()  # API name: def_nukes_used
    attacker_infra_destroyed_value = Real()  # API name: att_infra_destroyed_value
    defender_infra_destroyed_value = Real()  # API name: def_infra_destroyed_value

    attacker_id = Integer()  # API name: att_id
    defender_id = Integer()  # API name: def_id
    ground_control_id = Integer(null=True)  # API name: ground_control
    air_superiority_id = Integer(null=True)  # API name: air_superiority
    naval_blockade_id = Integer(null=True)  # API name: naval_blockade
    winner_id = Integer(null=True)

    @classmethod
    def preprocess_api_v3_model(cls, model: WarFields) -> WarFields:
        if model.ground_control == "0":
            model.ground_control = None
        if model.air_superiority == "0":
            model.air_superiority = None
        if model.naval_blockade == "0":
            model.naval_blockade = None
        if model.winner_id == "0":
            model.winner_id = None

        return model

    # @classmethod
    # def pydantic_overrides(cls) -> PydanticOverride:
    #     return [
    #         (cls.start_date, "date", datetime),
    #         (cls.attacker_action_points, "att_points", int),
    #         (cls.defender_action_points, "def_points", int),
    #         (cls.attacker_offering_peace, "att_peace", bool),
    #         (cls.defender_offering_peace, "def_peace", bool),
    #         (cls.attacker_resistance, "att_resistance", int),
    #         (cls.defender_resistance, "def_resistance", int),
    #         (cls.attacker_fortified, "att_fortify", bool),
    #         (cls.defender_fortified, "def_fortify", bool),
    #         (cls.attacker_gasoline_used, "att_gas_used", float),
    #         (cls.defender_gasoline_used, "def_gas_used", float),
    #         (cls.attacker_munitions_used, "att_mun_used", float),
    #         (cls.defender_munitions_used, "def_mun_used", float),
    #         (cls.attacker_aluminum_used, "att_alum_used", float),
    #         (cls.defender_aluminum_used, "def_alum_used", float),
    #         (cls.attacker_steel_used, "att_steel_used", float),
    #         (cls.defender_steel_used, "def_steel_used", float),
    #         (cls.attacker_infra_destroyed, "att_infra_destroyed", float),
    #         (cls.defender_infra_destroyed, "def_infra_destroyed", float),
    #         (cls.attacker_money_looted, "att_money_looted", int),
    #         (cls.defender_money_looted, "def_money_looted", int),
    #         (cls.attacker_soldiers_lost, "att_soldiers_lost", int),
    #         (cls.defender_soldiers_lost, "def_soldiers_lost", int),
    #         (cls.attacker_tanks_lost, "att_tanks_lost", int),
    #         (cls.defender_tanks_lost, "def_tanks_lost", int),
    #         (cls.attacker_aircraft_lost, "att_aircraft_lost", int),
    #         (cls.defender_aircraft_lost, "def_aircraft_lost", int),
    #         (cls.attacker_ships_lost, "att_ships_lost", int),
    #         (cls.defender_ships_lost, "def_ships_lost", int),
    #         (cls.attacker_missiles_used, "att_missiles_used", int),
    #         (cls.defender_missiles_used, "def_missiles_used", int),
    #         (cls.attacker_nukes_used, "att_nukes_used", int),
    #         (cls.defender_nukes_used, "def_nukes_used", int),
    #         (cls.attacker_infra_destroyed_value, "att_infra_destroyed_value", float),
    #         (cls.defender_infra_destroyed_value, "def_infra_destroyed_value", float),
    #         (cls.attacker_id, "att_id", int),
    #         (cls.defender_id, "def_id", int),
    #         (cls.ground_control_id, "ground_control", int | None),
    #         (cls.air_superiority_id, "air_superiority", int | None),
    #         (cls.naval_blockade_id, "naval_blockade", int | None),
    #         (cls.winner_id, "winner_id", int | None),
    #     ]
