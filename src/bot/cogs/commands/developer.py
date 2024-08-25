"""
Developer commands
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Self

from pydantic import BaseModel

import discord
from discord.ext import commands
from src.bot.converters import NationConverter
from src.database.tables.pnw import City, Nation
from src.discord.persistent_view import PersistentView
from src.discord.stateful_embed import StatefulEmbed
from src.pnw.sync import sync_all_nations

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
    async def sync_all_nations(self, ctx: commands.Context[Bot]):
        """Sync all nations."""
        msg = await ctx.reply("Syncing all nations, this may take a moment...")

        num_synced = await sync_all_nations(self.bot)

        await msg.edit(content=f"Completed! Synced {num_synced} nations.")

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

    @dev.command()
    async def cities(self, ctx: commands.Context[Bot]):
        """Get all cities from norlandia and add to database."""
        cities_api = (await self.bot.api_v3.get_cities(nation_id=[239259])).cities.data

        cities = City.from_api_v3(cities_api)

        inserted = await City.insert(
            *cities,
        )

        await ctx.reply(f"Added {len(inserted)} cities to the database.")

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
            await self.bot.api_v3.get_nations(discord_id=[str(user.id)])
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

        await self.bot.api_v3.mutation_bank_withdraw(
            receiver=nation.id, receiver_type=1, note=note, **resource_amount
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
