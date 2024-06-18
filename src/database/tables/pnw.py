"""
Here we define the database tables.
"""

from __future__ import annotations

from piccolo.columns import (
    BigInt,
    Boolean,
    Column,
    Integer,
    Real,
    Text,
    Timestamptz,
    Varchar,
)

from src.database.base_table import PnwBaseTable
from src.database.enums import Color, Continent, DomesticPolicy, WarPolicy
from src.pnw.api_v3 import NationFields


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

    @classmethod
    def pydantic_overrides(cls) -> tuple[tuple[Column, str, type]]:
        return (
            (cls.name, "nation_name", str),
            (cls.update_timezone, "update_tz", float),  # type: ignore
            (cls.flag_url, "flag", str),
            (cls.date_created, "date", str),
            (cls.num_projects, "projects", int),
            (cls.offensive_war_count, "offensive_wars_count", int),
            (cls.defensive_war_count, "defensive_wars_count", int),
        )

    # alliance = ForeignKey(references=Alliance, on_delete=OnDelete.set_null)
    # alliance_position = ForeignKey(
    #    references="AlliancePosition", on_delete=OnDelete.set_null
    # )

    # tax_bracket = ForeignKey(
    #    references="TaxBracket", on_delete=OnDelete.set_null
    # )

    ### Reverse Foreign Keys

    # @property
    # def cities(self):
    #     """
    #     Returns a query object for all the cities of this nation.
    #     """
    #     return City.objects().where(City.nation == self.id)
