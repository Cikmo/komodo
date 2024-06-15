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
from src.tables.enums import Color, Continent, DomesticPolicy, TreatyType, WarPolicy


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

    @property
    def bank_records(self) -> NoReturn:
        """
        Returns a query object for all the bank records of this alliance.
        """
        raise NotImplementedError

    @property
    def tax_records(self) -> NoReturn:
        """
        Returns a query object for all the tax records of this alliance.
        """
        raise NotImplementedError

    @property
    def tax_brackets(self) -> NoReturn:
        """
        Returns a query object for all the tax brackets of this alliance.
        """
        raise NotImplementedError

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


class BankRecord(Table):
    """
    A table to store bank records for alliances.
    """

    id = Integer(primary_key=True)
    date = Timestamptz(default=None)

    # how do i handle sender / receiver?
    # what if a sender is delted? Do I just store the ID?
