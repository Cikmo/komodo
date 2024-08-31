# Generated by ariadne-codegen
# Source: resources/queries.graphql

from typing import Any, Dict, List, Optional, Union

from .async_base_client import AsyncBaseClient
from .base_model import UNSET, UnsetType
from .get_alliances import GetAlliances
from .get_cities import GetCities
from .get_nations import GetNations
from .input_types import (
    QueryAlliancesOrderByOrderByClause,
    QueryCitiesOrderByOrderByClause,
    QueryNationsOrderByOrderByClause,
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
        order_by: Union[
            Optional[List[QueryNationsOrderByOrderByClause]], UnsetType
        ] = UNSET,
        page_size: Union[Optional[int], UnsetType] = UNSET,
        page: Union[Optional[int], UnsetType] = UNSET,
        **kwargs: Any
    ) -> GetNations:
        query = gql(
            """
            query get_nations($nation_id: [Int!], $nation_name: [String!], $discord_id: [String!], $discord_name: [String!], $order_by: [QueryNationsOrderByOrderByClause!], $page_size: Int = 50, $page: Int) {
              nations(
                id: $nation_id
                nation_name: $nation_name
                discord_id: $discord_id
                discord: $discord_name
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
              alliance_id
              alliance_obj: alliance {
                id
              }
              alliance_position
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
              credits_redeemed_this_month
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
            query get_cities($city_id: [Int!], $nation_id: [Int!], $order_by: [QueryCitiesOrderByOrderByClause!], $page_size: Int = 50, $page: Int) {
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
            query get_alliances($alliance_id: [Int!], $alliance_name: [String!], $color: [String!], $order_by: [QueryAlliancesOrderByOrderByClause!], $page_size: Int = 10, $page: Int) {
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
