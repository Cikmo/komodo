"""
Developer commands
"""

from __future__ import annotations

import asyncio
import logging
from timeit import default_timer
from typing import TYPE_CHECKING, Any, Awaitable, Self, cast

from pydantic import BaseModel

import discord
from discord.ext import commands
from src.bot.converters import NationConverter
from src.database.old_update import update_all_tables
from src.database.tables.pnw import Nation
from src.discord.persistent_view import PersistentView
from src.discord.stateful_embed import StatefulEmbed
from src.pnw.api_v3 import SubscriptionNationFields
from src.pnw.subscriptions.subscription import SubscriptionEvent, SubscriptionModel

if TYPE_CHECKING:
    from src.bot import Bot

logger = logging.getLogger(__name__)


class Confirm(PersistentView):
    """A view that adds a confirm and cancel button."""

    @discord.ui.button(
        label="Confirm", style=discord.ButtonStyle.green, custom_id="confirm"
    )
    async def confirm(
        self, interaction: discord.Interaction, _button: discord.ui.Button[Self]
    ):
        """On confirm button press."""
        if not interaction.message:
            return

        state = WhoEmbed.from_message(interaction.message)

        if not state:
            await interaction.response.send_message(
                "Could not find state.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"{state.name} {state.age} {state.favorite_color}"
        )

    @discord.ui.button(
        label="Cancel", style=discord.ButtonStyle.grey, custom_id="cancel"
    )
    async def cancel(
        self, interaction: discord.Interaction, _button: discord.ui.Button[Self]
    ):
        """On cancel button press."""
        tasks: list[Awaitable[Any]] = []

        tasks.append(self.disable_components(interaction))
        tasks.append(interaction.response.send_message("Cancelled!", ephemeral=True))

        await asyncio.gather(*tasks)


class WhoStateModel(BaseModel):
    """Model for the state of a Who message."""

    name: str
    age: int
    favorite_color: str


class WhoEmbed(StatefulEmbed[WhoStateModel]):
    """A stateful embed for the who command."""

    def __init__(self, state: WhoStateModel):
        super().__init__()
        self.state = state
        self.title = "Who Embed"
        self.description = "Who Description"
        self.add_field(name="Name", value=state.name)
        self.add_field(name="Age", value=state.age)
        self.add_field(name="Favorite Color", value=state.favorite_color)


class Developer(commands.Cog):
    """Developer commands."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.confirm_view = Confirm()
        self.bot.add_view(self.confirm_view)

    @commands.group(name="dev", aliases=["!"])
    @commands.is_owner()
    async def dev(self, ctx: commands.Context[Bot]):
        """Group for developer commands."""
        pass

    @dev.command()
    async def button(self, ctx: commands.Context[Bot]):
        """Button test."""

        state = WhoStateModel(name="Christian", age=22, favorite_color="red")

        embed = WhoEmbed(state=state)

        await ctx.reply(embed=embed, view=self.confirm_view)

    @dev.command()
    async def subscribe(
        self,
        ctx: commands.Context[Bot],
    ):
        """Test command."""
        await self.bot.pnw.subscriptions.subscribe(
            SubscriptionModel.NATION,
            SubscriptionEvent.UPDATE,
            [self.nation_update_callback],
        )

        await ctx.reply("Subscribed to nation updates.")

    async def nation_create_callback(self, data: SubscriptionNationFields):
        """Callback for nation creation."""

        nation = cast(Nation, Nation.from_api_v3(data))  # type: ignore

        nation_in_db = (
            await Nation.select(Nation.id).where(Nation.id == nation.id).first()
        )

        if nation_in_db:
            return

        await nation.save()

        self.bot.dispatch("pnw_nation_create", nation)

    async def nation_update_callback(self, data: SubscriptionNationFields):
        """Callback for nation updates."""

        nation_in_db = await Nation.objects().where(Nation.id == data.id).first()

        if not nation_in_db:
            return await self.nation_create_callback(data)

        new_nation = cast(Nation, Nation.from_api_v3(data))  # type: ignore
        new_nation._exists_in_db = True  # type: ignore # pylint: disable=protected-access

        await new_nation.save()
        logger.info("Updated nation %s", nation_in_db.name)

    @dev.command()
    async def debugclose(
        self,
        ctx: commands.Context[Bot],
        model: SubscriptionModel,
        event: SubscriptionEvent,
    ) -> None:
        """Close the debug channel."""
        sub = self.bot.pnw.subscriptions.get(model, event)
        if not sub:
            await ctx.reply("Subscription not found.")
            return

        await sub._channel._connection._ws.close()  # type: ignore # pylint: disable=protected-access

        await ctx.reply(f"Closed {model.value} {event.value}.")

    @dev.command()
    async def sublist(self, ctx: commands.Context[Bot]):
        """List all subscriptions."""
        await ctx.reply("\n".join(self.bot.pnw.subscriptions.subscriptions))

    @dev.command()
    async def sync_all(self, ctx: commands.Context[Bot]):
        """Sync all nations."""
        msg = await ctx.reply("Syncing everything...")

        timer = default_timer()

        alliances, positions, nations, cities, wars = await update_all_tables(
            self.bot.pnw.v3
        )

        timer = default_timer() - timer

        await msg.edit(
            content=f"Completed! Synced `{alliances}` alliances, `{positions}` positions, `{nations}`"
            f" nations, `{cities}` cities, and `{wars}` wars in `{timer:.2f}s`."
        )

    @dev.command()
    async def who(
        self,
        ctx: commands.Context[Bot],
        nation: Nation | None = commands.parameter(
            converter=NationConverter, default=NationConverter.get_author
        ),
    ):
        """Get your nation."""
        if not nation:
            await ctx.reply("Nation not found.")
            return

        await ctx.reply(f"Your nation is {nation.name}.")

    # @dev.command()
    # async def cities(self, ctx: commands.Context[Bot]):
    #     """Get all cities from norlandia and add to database."""
    #     cities_api = (await self.bot.pnw.v3.get_cities(nation_id=[239259])).cities.data

    #     cities = City.from_api_v3(cities_api)

    #     inserted = await City.insert(
    #         *cities,
    #     )

    #     await ctx.reply(f"Added {len(inserted)} cities to the database.")

    # @dev.command()
    # async def create(self, ctx: commands.Context[Bot], nation_name: str):
    #     """Ping the bot."""
    #     nation_data = (
    #         await self.bot.api_v3.get_nations(nation_name=[nation_name])
    #     ).nations.data

    #     nation_from_api = nation_data[0] if nation_data else None

    #     if not nation_from_api:
    #         await ctx.reply("Nation not found.")
    #         return

    #     nation = Nation.from_api_v3(nation_from_api)

    #     await nation.save()

    #     await ctx.reply(f"Saved {nation_name} to the database.")

    # @dev.command()
    # async def who(
    #     self,
    #     ctx: commands.Context[Bot],
    #     nation: Nation = commands.parameter(converter=NationConverter),
    # ):
    #     """Look up a nation in the database."""
    #     if not nation:
    #         await ctx.reply("Nation not found.")
    #         return

    #     await ctx.reply(f"Found {nation.name} in the database.")

    @dev.command()
    async def withdraw(
        self,
        ctx: commands.Context[Bot],
        user: discord.User,
        resource: str,
        amount: int,
        note: str,
    ):
        """Withdraw money from the bank."""

        nation_data = (
            await self.bot.pnw.v3.get_nations(discord_id=[str(user.id)])
        ).nations.data

        nation = nation_data[0] if nation_data else None

        if not nation:
            await ctx.reply("Nation not found.")
            return

        resource_amount = {
            "money": 0,
            "coal": 0,
            "oil": 0,
            "uranium": 0,
            "iron": 0,
            "bauxite": 0,
            "lead": 0,
            "gasoline": 0,
            "munitions": 0,
            "steel": 0,
            "aluminum": 0,
            "food": 0,
        }

        if resource.lower() not in resource_amount:
            await ctx.reply("Invalid resource.")
            return

        resource_amount[resource.lower()] = amount

        await self.bot.pnw.v3.mutation_bank_withdraw(
            receiver=str(nation.id), receiver_type=1, note=note, **resource_amount
        )

        await ctx.reply(
            f"Withdrew ${amount} from the bank with note: `{note}` to {nation.nation_name}."
        )

    @dev.command()
    async def reload(self, ctx: commands.Context[Bot], cog_name: str):
        """Reload a cog by name."""
        try:
            await self.bot.reload_cog(cog_name)
            await ctx.reply(f"Reloaded cog {cog_name}")
        except commands.ExtensionNotFound:
            await ctx.reply(f"Could not find cog {cog_name}")
        except commands.ExtensionNotLoaded:
            await ctx.invoke(self.load, cog_name=cog_name)

    @dev.command()
    async def load(self, ctx: commands.Context[Bot], cog_name: str):
        """Load a cog by name."""
        try:
            await self.bot.load_cog(cog_name)
            await ctx.reply(f"Loaded cog {cog_name}")
        except commands.ExtensionNotFound:
            await ctx.reply(f"Could not find cog {cog_name}")
        except commands.ExtensionAlreadyLoaded:
            await ctx.reply(f"Cog {cog_name} is already loaded")

    @dev.command()
    async def unload(self, ctx: commands.Context[Bot], cog_name: str):
        """Unload a cog by name."""
        try:
            await self.bot.unload_cog(cog_name)
            await ctx.reply(f"Unloaded cog {cog_name}")
        except commands.ExtensionNotFound:
            await ctx.reply(f"Could not find cog {cog_name}")
        except commands.ExtensionNotLoaded:
            await ctx.reply(
                f"Cog {cog_name} is not loaded, so it cannot be unloaded. Dumbass."
            )


async def setup(bot: Bot):
    """Called as extension is loaded"""
    await bot.add_cog(Developer(bot))


# {
#     "id": 642709,
#     "alliance_id": 0,
#     "alliance_position": "NOALLIANCE",
#     "alliance_position_id": 0,
#     "nation_name": "Dytopia",
#     "leader_name": "Josh Finder",
#     "continent": "eu",
#     "war_policy": "BLITZKRIEG",
#     "domestic_policy": "MANIFEST_DESTINY",
#     "war_policy_turns": 60,
#     "domestic_policy_turns": 0,
#     "color": "beige",
#     "num_cities": 1,
#     "score": 10.5,
#     "update_tz": None,
#     "population": 2000,
#     "flag": "https://politicsandwar.com/uploads/6bc661e71a61b3a7a9f4f5bba314137d9d66de701000x599804.png",
#     "vacation_mode_turns": 0,
#     "beige_turns": 168,
#     "espionage_available": True,
#     "date": "2024-09-08T17:03:16+00:00",
#     "soldiers": 0,
#     "tanks": 0,
#     "aircraft": 0,
#     "ships": 0,
#     "missiles": 0,
#     "nukes": 0,
#     "spies": 0,
#     "discord": "",
#     "turns_since_last_city": 121,
#     "turns_since_last_project": 121,
#     "money": None,
#     "coal": None,
#     "oil": None,
#     "uranium": None,
#     "iron": None,
#     "bauxite": None,
#     "lead": None,
#     "gasoline": None,
#     "munitions": None,
#     "steel": None,
#     "aluminum": None,
#     "food": None,
#     "projects": 0,
#     "iron_works": 0,
#     "bauxite_works": 0,
#     "arms_stockpile": 0,
#     "emergency_gasoline_reserve": 0,
#     "mass_irrigation": 0,
#     "international_trade_center": 0,
#     "missile_launch_pad": 0,
#     "nuclear_research_facility": 0,
#     "iron_dome": 0,
#     "vital_defense_system": 0,
#     "central_intelligence_agency": 0,
#     "center_for_civil_engineering": 0,
#     "propaganda_bureau": 0,
#     "uranium_enrichment_program": 0,
#     "urban_planning": 0,
#     "advanced_urban_planning": 0,
#     "space_program": 0,
#     "spy_satellite": 0,
#     "moon_landing": 0,
#     "moon_landing_date": None,
#     "pirate_economy": 0,
#     "recycling_initiative": 0,
#     "telecommunications_satellite": 0,
#     "green_technologies": 0,
#     "arable_land_agency": 0,
#     "clinical_research_center": 0,
#     "specialized_police_training_program": 0,
#     "advanced_engineering_corps": 0,
#     "government_support_agency": 0,
#     "research_and_development_center": 0,
#     "resource_production_center": 0,
#     "wars_won": 0,
#     "wars_lost": 0,
#     "tax_id": 0,
#     "alliance_seniority": 0,
#     "gross_national_income": 0.0,
#     "gross_domestic_product": 1,
#     "soldier_casualties": 0,
#     "soldier_kills": 0,
#     "tank_casualties": 0,
#     "tank_kills": 0,
#     "aircraft_casualties": 0,
#     "aircraft_kills": 0,
#     "ship_casualties": 0,
#     "ship_kills": 0,
#     "missile_casualties": 0,
#     "missile_kills": 0,
#     "nuke_casualties": 0,
#     "nuke_kills": 0,
#     "spy_casualties": None,
#     "spy_kills": None,
#     "money_looted": 0.0,
#     "metropolitan_planning": 0,
#     "military_salvage": 0,
#     "fallout_shelter": 0,
#     "bureau_of_domestic_affairs": 0,
#     "advanced_pirate_economy": 0,
#     "mars_landing": 0,
#     "mars_landing_date": None,
#     "surveillance_network": 0,
#     "guiding_satellite": 0,
#     "nuclear_launch_facility": 0,
#     "project_bits": "0",
# }
