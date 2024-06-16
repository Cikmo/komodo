"""
Here we define the database tables.
"""

from __future__ import annotations

from typing import NoReturn, Self, Sequence, overload

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
from piccolo.table import Table
from piccolo.utils.pydantic import create_pydantic_model
from pydantic import AwareDatetime, Field

from src.pnw.api_v3 import NationFields
from src.tables.enums import (
    Color,
    Continent,
    DomesticPolicy,
    TreatyType,
    WarPolicy,
    WarType,
)


class Alliance(Table):
    """
    A table to store information about alliances in the game.
    """

    id = Integer(primary_key=True)
    name = Text()
    acronym = Text()
    score = Real()
    color = Text(choices=Color)
    date_created = Timestamptz(default=None)
    average_score = Real()
    accepts_members = Boolean()
    flag_url = Text()
    forum_link = Text()
    discord_link = Text()
    wiki_link = Text()
    rank = Integer()

    # reverse foreign keys
    @property
    def nations(self):
        """
        Returns a query object for all the members of this alliance.
        This includes applicants.
        """
        return Nation.objects().where(Nation.alliance == self.id)

    @property
    def treaties(self):
        """
        Returns a query object for all the treaties of this alliance.
        """
        return Treaty.objects().where(
            (Treaty.alliance_1 == self.id) | (Treaty.alliance_2 == self.id)
        )

    @property
    def positions(self):
        """
        Returns a query object for all the positions in this alliance.
        """
        return AlliancePosition.objects().where(AlliancePosition.alliance == self.id)

    # @property
    # def bank_records(self) -> NoReturn:
    #     """
    #     Returns a query object for all the bank records of this alliance.
    #     """
    #     raise NotImplementedError
    # I'm not sure if I should store bank records in the database
    # There might not be a point to it. I'll leave it out until I start working on banking.

    # @property
    # def tax_records(self) -> NoReturn:
    #     """
    #     Returns a query object for all the tax records of this alliance.
    #     """
    #     raise NotImplementedError
    # Same as bank records

    @property
    def tax_brackets(self):
        """
        Returns a query object for all the tax brackets of this alliance.
        """
        return TaxBracket.objects().where(TaxBracket.alliance == self.id)

    @property
    def wars(self) -> NoReturn:
        """
        Returns a query object for all the wars of this alliance.
        """
        raise NotImplementedError

    # def from_api_v3(cls, model: AllianceFields) -> Self:
    #     """Create a new alliance from the API v3 data.

    #     Args:
    #         data: The API v3 alliance to convert.

    #     Returns:
    #         Self: _description_
    #     """
    #     converted_model = AllianceModel.model_validate(model.model_dump())
    #     return cls(**converted_model.model_dump())


class AllianceModel(create_pydantic_model(Alliance)):
    """
    A pydantic model of the Alliance table. Has alias fields to match the API v3 model,
    meaning that you can pass the API v3 model directly to be validated here.
    """

    date_created: AwareDatetime = Field(alias="date")
    accepts_members: bool = Field(alias="accept_members")
    flag_url: str = Field(alias="flag")


class Treaty(Table):
    """
    A table to store information about treaties between alliances.
    """

    id = Integer(primary_key=True)
    date_accepted = Timestamptz(default=None, null=True)
    treaty_type = Text(choices=TreatyType)
    treaty_url = Text()
    turns_left = Integer()
    approved = Boolean()

    alliance_1 = ForeignKey(references=Alliance, on_delete=OnDelete.cascade, null=False)
    alliance_2 = ForeignKey(references=Alliance, on_delete=OnDelete.cascade, null=False)


class TreatyModel(create_pydantic_model(Treaty)):
    """
    A pydantic model of the Treaty table. Has alias fields to match the API v3 model,
    meaning that you can pass the API v3 model directly to be validated here.
    """

    date_accepted: AwareDatetime | None = Field(alias="date")


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
    score = Real()
    update_timezone: Real | None = Real(null=True)  # API name: update_tz
    population = Integer()
    flag_url = Text()  # API name: flag
    vacation_mode_turns = Integer()
    beige_turns = Integer()
    espionage_available = Boolean()
    last_active = Timestamptz(default=None)
    date_created = Timestamptz(default=None)  # API name: date
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
    project_bits = Integer()
    wars_won = Integer()
    wars_lost = Integer()
    offensive_war_count = Integer()  # API name: offensive_wars_count
    defensive_war_count = Integer()  # API name: defensive_wars_count
    alliance_join_date = Timestamptz(default=None)

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
        return City.objects().where(City.nation == self.id)

    @overload
    @classmethod
    def from_api_v3(cls, model: NationFields) -> Self: ...

    @overload
    @classmethod
    def from_api_v3(cls, model: Sequence[NationFields]) -> list[Self]: ...

    @classmethod
    def from_api_v3(
        cls, model: NationFields | Sequence[NationFields]
    ) -> Self | list[Self]:
        """Create a new nation from the API v3 data.

        Args:
            data: The API v3 nation to convert. Can be a single nation or a list of nations.

        Returns:
            Self | list[Self]: _description_
        """
        if isinstance(model, Sequence):
            return [cls._convert_api_v3_model_to_table(nation) for nation in model]

        return cls._convert_api_v3_model_to_table(model)

    @classmethod
    def _convert_api_v3_model_to_table(cls, model: NationFields) -> Self:
        """Convert the API v3 model to a Nation table instance.

        Args:
            model: The API v3 model to convert.

        Returns:
            An instance of the Nation table.
        """
        converted_model = NationModel.model_validate(model.model_dump())
        return cls(**converted_model.model_dump())


class NationModel(create_pydantic_model(Nation)):
    """
    A pydantic model of the Nation table. Has alias fields to match the API v3 model,
    meaning that you can pass the API v3 model directly to be validated here.
    """

    name: str = Field(alias="nation_name")
    update_timezone: float | None = Field(alias="update_tz")
    flag_url: str = Field(alias="flag")
    date_created: AwareDatetime = Field(alias="date")
    num_projects: int = Field(alias="projects")
    offensive_war_count: int = Field(alias="offensive_wars_count")
    defensive_war_count: int = Field(alias="defensive_wars_count")


class City(Table):
    """
    A table to store information about cities in the game.
    """

    id = Integer(primary_key=True)
    name = Text()
    date_created = Timestamptz(default=None)
    infrastructure = Integer()
    land = Integer()
    powered = Boolean()
    last_nuke_date: Timestamptz | None = Timestamptz(default=None)

    # Power
    oil_power_plants = Integer()
    wind_power_plants = Integer()
    coal_power_plants = Integer()
    nuclear_power_plants = Integer()

    # Raw Resources
    coal_mines = Integer()
    oil_wells = Integer()
    uranium_mines = Integer()
    bauxite_mines = Integer()
    lead_mines = Integer()
    iron_mines = Integer()
    farms = Integer()

    # Manufacturing
    oil_refineries = Integer()
    aluminum_refineries = Integer()
    steel_mills = Integer()
    munitions_factories = Integer()

    # Civil
    police_stations = Integer()
    hospitals = Integer()
    recycling_centers = Integer()
    subways = Integer()

    # Commerce
    supermarkets = Integer()
    banks = Integer()
    shopping_malls = Integer()
    stadiums = Integer()

    # Military
    barracks = Integer()
    factories = Integer()
    hangars = Integer()
    drydocks = Integer()

    # Foreign Keys
    nation = ForeignKey(references=Nation, null=False, on_delete=OnDelete.cascade)


# class BankRecord(Table):
#     """
#     A table to store bank records for alliances.
#     """

#     id = Integer(primary_key=True)
#     date = Timestamptz(default=None)

#     # how do i handle sender / receiver?
#     # what if one of them is deleted? Do I just store the ID?
#     # is there even a point to storing bank records at all?
#     # maybe I should just fetch them from the API when needed


class TaxBracket(Table):
    """
    A table to store tax brackets for alliances.
    """

    id = Integer(primary_key=True)
    name = Text()
    date_created = Timestamptz(default=None)
    date_modified = Timestamptz(default=None)
    money_tax_rate = Integer()
    resource_tax_rate = Integer()

    alliance = ForeignKey(references=Alliance, on_delete=OnDelete.cascade, null=False)
    creator = ForeignKey(references=Nation, on_delete=OnDelete.set_null)
    last_editor = ForeignKey(references=Nation, on_delete=OnDelete.set_null)


class AlliancePosition(Table):
    """
    A table to store information about the positions in an alliance.
    """

    id = Integer(primary_key=True)
    date_created = Timestamptz(default=None)
    date_modified = Timestamptz(default=None)
    name = Text()
    position_level = Integer()
    default_leader = Boolean()
    default_heir = Boolean()
    default_officer = Boolean()
    default_member = Boolean()
    permission_bits = Integer()

    alliance = ForeignKey(references=Alliance, on_delete=OnDelete.cascade, null=False)
    creator = ForeignKey(references="Nation", on_delete=OnDelete.set_null)
    last_editor = ForeignKey(references="Nation", on_delete=OnDelete.set_null)


class AlliancePositionModel(create_pydantic_model(AlliancePosition)):
    """
    A pydantic model of the AlliancePosition table. Has alias fields to match the API v3 model,
    meaning that you can pass the API v3 model directly to be validated here.
    """

    date_created: AwareDatetime | None = Field(alias="date")
    default_leader: bool = Field(alias="leader")
    default_heir: bool = Field(alias="heir")
    default_officer: bool = Field(alias="officer")
    default_member: bool = Field(alias="member")
    permission_bits: int = Field(alias="permissions")


class TaxBracketModel(create_pydantic_model(TaxBracket)):
    """
    A pydantic model of the TaxBracket table. Has alias fields to match the API v3 model,
    meaning that you can pass the API v3 model directly to be validated here.
    """

    date_created: AwareDatetime | None = Field(alias="date")
    name: str = Field(alias="bracket_name")
    money_tax_rate: int = Field(alias="tax_rate")


class War(Table):
    """
    A table to store information about wars in the game.
    """

    id = Integer(primary_key=True)
    date_started = Timestamptz(default=None)
    date_ended = Timestamptz(default=None, null=True)
    reason = Text()
    war_type = Text(choices=WarType)
    turns_left = Integer()
    attacker_action_points = Integer()
    defender_action_points = Integer()
    attacker_offering_peace = Boolean()
    defender_offering_peace = Boolean()
    attacker_resistance = Integer()
    defender_resistance = Integer()
    attacker_fortified = Boolean()
    defender_fortified = Boolean()
    attacker_gasoline_used = Integer()
    defender_gasoline_used = Integer()
    attacker_munitions_used = Integer()
    defender_munitions_used = Integer()
    attacker_aluminum_used = Integer()
    defender_aluminum_used = Integer()
    attacker_steel_used = Integer()
    defender_steel_used = Integer()
    attacker_infra_destroyed = Integer()
    defender_infra_destroyed = Integer()
    attacker_money_looted = Integer()
    defender_money_looted = Integer()
    attacker_soldiers_lost = Integer()
    defender_soldiers_lost = Integer()
    attacker_tanks_lost = Integer()
    defender_tanks_lost = Integer()
    attacker_aircraft_lost = Integer()
    defender_aircraft_lost = Integer()
    attacker_ships_lost = Integer()
    defender_ships_lost = Integer()
    attacker_missiles_used = Integer()
    defender_missiles_used = Integer()
    attacker_nukes_used = Integer()
    defender_nukes_used = Integer()
    attacker_infra_destroyed_value = Integer()
    defender_infra_destroyed_value = Integer()

    attacker_nation = ForeignKey(references=Nation, on_delete=OnDelete.set_null)
    defender_nation = ForeignKey(references=Nation, on_delete=OnDelete.set_null)
    ground_control_nation = ForeignKey(references=Nation, on_delete=OnDelete.set_null)
    air_superiority_nation = ForeignKey(references=Nation, on_delete=OnDelete.set_null)
    naval_blockade_nation = ForeignKey(references=Nation, on_delete=OnDelete.set_null)
    winner_nation = ForeignKey(references=Nation, on_delete=OnDelete.set_null)
    attacker_alliance = ForeignKey(references=Alliance, on_delete=OnDelete.set_null)
    defender_alliance = ForeignKey(references=Alliance, on_delete=OnDelete.set_null)


class WarModel(create_pydantic_model(War)):
    """
    A pydantic model of the War table. Has alias fields to match the API v3 model,
    meaning that you can pass the API v3 model directly to be validated here.
    """

    date_started: AwareDatetime | None = Field(alias="date")
    date_ended: AwareDatetime | None = Field(alias="end_date")
    ground_control_nation: int | None = Field(alias="ground_control")
    air_superiority_nation: int | None = Field(alias="air_superiority")
    naval_blockade_nation: int | None = Field(alias="naval_blockade")
    winner_nation: int | None = Field(alias="winner_id")
    attacker_nation: int = Field(alias="att_id")
    defender_nation: int = Field(alias="def_id")
    # TODO: I didn't do all of them yet.
