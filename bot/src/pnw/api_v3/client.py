# Generated by ariadne-codegen
# Source: resources/queries.graphql

from typing import Any, Dict, List, Optional, Union

from pydantic import AwareDatetime

from .async_base_client import AsyncBaseClient
from .base_model import UNSET, UnsetType
from .get_alliances import GetAlliances
from .get_cities import GetCities
from .get_nations import GetNations
from .get_wars import GetWars
from .input_types import (
    QueryAlliancesOrderByOrderByClause,
    QueryCitiesOrderByOrderByClause,
    QueryNationsOrderByOrderByClause,
    QueryWarsOrderByOrderByClause,
)
from .mutation_bank_withdraw import MutationBankWithdraw


def gql(q: str) -> str:
    return q


class Client(AsyncBaseClient):
    async def get_nations(
        self,
        nation_id: Union[Optional[List[int]], UnsetType] = UNSET,
        nation_name: Union[Optional[List[str]], UnsetType] = UNSET,
        discord_id: Union[Optional[List[str]], UnsetType] = UNSET,
        discord_name: Union[Optional[List[str]], UnsetType] = UNSET,
        vacation_mode: Union[Optional[bool], UnsetType] = UNSET,
        order_by: Union[
            Optional[List[QueryNationsOrderByOrderByClause]], UnsetType
        ] = UNSET,
        page_size: Union[Optional[int], UnsetType] = UNSET,
        page: Union[Optional[int], UnsetType] = UNSET,
        **kwargs: Any
    ) -> GetNations:
        query = gql(
            """
            query get_nations($nation_id: [Int!], $nation_name: [String!], $discord_id: [String!], $discord_name: [String!], $vacation_mode: Boolean, $order_by: [QueryNationsOrderByOrderByClause!] = {column: DATE, order: ASC}, $page_size: Int = 50, $page: Int) {
              nations(
                id: $nation_id
                nation_name: $nation_name
                discord_id: $discord_id
                discord: $discord_name
                vmode: $vacation_mode
                orderBy: $order_by
                first: $page_size
                page: $page
              ) {
                data {
                  ...nationFields
                }
                paginatorInfo {
                  ...paginatorFields
                }
              }
            }

            fragment nationFields on Nation {
              id
              alliance: alliance_id
              alliance_position_id
              nation_name
              leader_name
              continent
              war_policy
              war_policy_turns
              domestic_policy
              domestic_policy_turns
              color
              num_cities
              score
              update_tz
              population
              flag
              vacation_mode_turns
              beige_turns
              espionage_available
              last_active
              date
              soldiers
              tanks
              aircraft
              ships
              missiles
              nukes
              spies
              discord
              discord_id
              turns_since_last_city
              turns_since_last_project
              projects
              project_bits
              moon_landing_date
              mars_landing_date
              wars_won
              wars_lost
              tax_id
              alliance_seniority
              gross_national_income
              gross_domestic_product
              soldier_casualties
              soldier_kills
              tank_casualties
              tank_kills
              aircraft_casualties
              aircraft_kills
              ship_casualties
              ship_kills
              missile_casualties
              missile_kills
              nuke_casualties
              nuke_kills
              spy_casualties
              spy_kills
              spy_attacks
              money_looted
              total_infrastructure_destroyed
              total_infrastructure_lost
              vip
              commendations
              denouncements
              offensive_wars_count
              defensive_wars_count
              economic_policy
              social_policy
              government_type
              alliance_join_date
            }

            fragment paginatorFields on PaginatorInfo {
              count
              hasMorePages
            }
            """
        )
        variables: Dict[str, object] = {
            "nation_id": nation_id,
            "nation_name": nation_name,
            "discord_id": discord_id,
            "discord_name": discord_name,
            "vacation_mode": vacation_mode,
            "order_by": order_by,
            "page_size": page_size,
            "page": page,
        }
        response = await self.execute(
            query=query, operation_name="get_nations", variables=variables, **kwargs
        )
        data = self.get_data(response)
        return GetNations.model_validate(data)

    async def get_cities(
        self,
        city_id: Union[Optional[List[int]], UnsetType] = UNSET,
        nation_id: Union[Optional[List[int]], UnsetType] = UNSET,
        order_by: Union[
            Optional[List[QueryCitiesOrderByOrderByClause]], UnsetType
        ] = UNSET,
        page_size: Union[Optional[int], UnsetType] = UNSET,
        page: Union[Optional[int], UnsetType] = UNSET,
        **kwargs: Any
    ) -> GetCities:
        query = gql(
            """
            query get_cities($city_id: [Int!], $nation_id: [Int!], $order_by: [QueryCitiesOrderByOrderByClause!] = {column: ID, order: ASC}, $page_size: Int = 50, $page: Int) {
              cities(
                id: $city_id
                nation_id: $nation_id
                orderBy: $order_by
                first: $page_size
                page: $page
              ) {
                data {
                  ...cityFields
                }
                paginatorInfo {
                  ...paginatorFields
                }
              }
            }

            fragment cityFields on City {
              id
              nation_id
              name
              nuke_date
              date
              infrastructure
              land
              powered
              oil_power
              wind_power
              coal_power
              nuclear_power
              coal_mine
              oil_well
              uranium_mine
              barracks
              farm
              police_station
              hospital
              recycling_center
              subway
              supermarket
              bank
              shopping_mall
              stadium
              lead_mine
              iron_mine
              bauxite_mine
              oil_refinery
              aluminum_refinery
              steel_mill
              munitions_factory
              factory
              hangar
              drydock
            }

            fragment paginatorFields on PaginatorInfo {
              count
              hasMorePages
            }
            """
        )
        variables: Dict[str, object] = {
            "city_id": city_id,
            "nation_id": nation_id,
            "order_by": order_by,
            "page_size": page_size,
            "page": page,
        }
        response = await self.execute(
            query=query, operation_name="get_cities", variables=variables, **kwargs
        )
        data = self.get_data(response)
        return GetCities.model_validate(data)

    async def get_alliances(
        self,
        alliance_id: Union[Optional[List[int]], UnsetType] = UNSET,
        alliance_name: Union[Optional[List[str]], UnsetType] = UNSET,
        color: Union[Optional[List[str]], UnsetType] = UNSET,
        order_by: Union[
            Optional[List[QueryAlliancesOrderByOrderByClause]], UnsetType
        ] = UNSET,
        page_size: Union[Optional[int], UnsetType] = UNSET,
        page: Union[Optional[int], UnsetType] = UNSET,
        **kwargs: Any
    ) -> GetAlliances:
        query = gql(
            """
            query get_alliances($alliance_id: [Int!], $alliance_name: [String!], $color: [String!], $order_by: [QueryAlliancesOrderByOrderByClause!] = {column: DATE, order: ASC}, $page_size: Int = 10, $page: Int) {
              alliances(
                id: $alliance_id
                name: $alliance_name
                color: $color
                orderBy: $order_by
                first: $page_size
                page: $page
              ) {
                data {
                  ...allianceFields
                }
                paginatorInfo {
                  ...paginatorFields
                }
              }
            }

            fragment allianceFields on Alliance {
              id
              name
              acronym
              score
              color
              date
              average_score
              accept_members
              flag
              rank
              alliance_positions {
                ...alliancePositionFields
              }
            }

            fragment alliancePositionFields on AlliancePosition {
              id
              date
              alliance_id
              name
              creator_id
              last_editor_id
              date_modified
              position_level
              leader
              heir
              officer
              member
              permissions
            }

            fragment paginatorFields on PaginatorInfo {
              count
              hasMorePages
            }
            """
        )
        variables: Dict[str, object] = {
            "alliance_id": alliance_id,
            "alliance_name": alliance_name,
            "color": color,
            "order_by": order_by,
            "page_size": page_size,
            "page": page,
        }
        response = await self.execute(
            query=query, operation_name="get_alliances", variables=variables, **kwargs
        )
        data = self.get_data(response)
        return GetAlliances.model_validate(data)

    async def get_wars(
        self,
        war_id: Union[Optional[List[int]], UnsetType] = UNSET,
        active: Union[Optional[bool], UnsetType] = UNSET,
        after: Union[Optional[AwareDatetime], UnsetType] = UNSET,
        order_by: Union[
            Optional[List[QueryWarsOrderByOrderByClause]], UnsetType
        ] = UNSET,
        page_size: Union[Optional[int], UnsetType] = UNSET,
        page: Union[Optional[int], UnsetType] = UNSET,
        **kwargs: Any
    ) -> GetWars:
        query = gql(
            """
            query get_wars($war_id: [Int!], $active: Boolean = false, $after: DateTime, $order_by: [QueryWarsOrderByOrderByClause!] = {column: DATE, order: ASC}, $page_size: Int = 50, $page: Int) {
              wars(
                id: $war_id
                active: $active
                after: $after
                orderBy: $order_by
                first: $page_size
                page: $page
              ) {
                data {
                  ...warFields
                }
                paginatorInfo {
                  ...paginatorFields
                }
              }
            }

            fragment paginatorFields on PaginatorInfo {
              count
              hasMorePages
            }

            fragment warFields on War {
              id
              date
              end_date
              reason
              war_type
              ground_control
              air_superiority
              naval_blockade
              winner_id
              turns_left
              att_id
              def_id
              att_points
              def_points
              att_peace
              def_peace
              att_resistance
              def_resistance
              att_fortify
              def_fortify
              att_gas_used
              def_gas_used
              att_mun_used
              def_mun_used
              att_alum_used
              def_alum_used
              att_steel_used
              def_steel_used
              att_infra_destroyed
              def_infra_destroyed
              att_money_looted
              def_money_looted
              att_soldiers_lost
              def_soldiers_lost
              att_tanks_lost
              def_tanks_lost
              att_aircraft_lost
              def_aircraft_lost
              att_ships_lost
              def_ships_lost
              att_missiles_used
              def_missiles_used
              att_nukes_used
              def_nukes_used
              att_infra_destroyed_value
              def_infra_destroyed_value
            }
            """
        )
        variables: Dict[str, object] = {
            "war_id": war_id,
            "active": active,
            "after": after,
            "order_by": order_by,
            "page_size": page_size,
            "page": page,
        }
        response = await self.execute(
            query=query, operation_name="get_wars", variables=variables, **kwargs
        )
        data = self.get_data(response)
        return GetWars.model_validate(data)

    async def mutation_bank_withdraw(
        self,
        receiver: str,
        receiver_type: int,
        note: str,
        money: Union[Optional[float], UnsetType] = UNSET,
        coal: Union[Optional[float], UnsetType] = UNSET,
        oil: Union[Optional[float], UnsetType] = UNSET,
        uranium: Union[Optional[float], UnsetType] = UNSET,
        iron: Union[Optional[float], UnsetType] = UNSET,
        bauxite: Union[Optional[float], UnsetType] = UNSET,
        lead: Union[Optional[float], UnsetType] = UNSET,
        gasoline: Union[Optional[float], UnsetType] = UNSET,
        munitions: Union[Optional[float], UnsetType] = UNSET,
        steel: Union[Optional[float], UnsetType] = UNSET,
        aluminum: Union[Optional[float], UnsetType] = UNSET,
        food: Union[Optional[float], UnsetType] = UNSET,
        **kwargs: Any
    ) -> MutationBankWithdraw:
        query = gql(
            """
            mutation mutation_bank_withdraw($receiver: ID!, $receiver_type: Int!, $money: Float = 0, $coal: Float = 0, $oil: Float = 0, $uranium: Float = 0, $iron: Float = 0, $bauxite: Float = 0, $lead: Float = 0, $gasoline: Float = 0, $munitions: Float = 0, $steel: Float = 0, $aluminum: Float = 0, $food: Float = 0, $note: String!) {
              bankWithdraw(
                receiver: $receiver
                receiver_type: $receiver_type
                money: $money
                coal: $coal
                oil: $oil
                uranium: $uranium
                iron: $iron
                bauxite: $bauxite
                lead: $lead
                gasoline: $gasoline
                munitions: $munitions
                steel: $steel
                aluminum: $aluminum
                food: $food
                note: $note
              ) {
                id
              }
            }
            """
        )
        variables: Dict[str, object] = {
            "receiver": receiver,
            "receiver_type": receiver_type,
            "money": money,
            "coal": coal,
            "oil": oil,
            "uranium": uranium,
            "iron": iron,
            "bauxite": bauxite,
            "lead": lead,
            "gasoline": gasoline,
            "munitions": munitions,
            "steel": steel,
            "aluminum": aluminum,
            "food": food,
            "note": note,
        }
        response = await self.execute(
            query=query,
            operation_name="mutation_bank_withdraw",
            variables=variables,
            **kwargs
        )
        data = self.get_data(response)
        return MutationBankWithdraw.model_validate(data)
