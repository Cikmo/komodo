"""
Developer commands
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from timeit import default_timer
from typing import TYPE_CHECKING, Any, Awaitable, Self

from pydantic import BaseModel

import discord
from discord.ext import commands
from src.bot.converters import NationConverter
from src.database.tables.pnw import City, Nation
from src.database.update import update_pnw_table
from src.discord.persistent_view import PersistentView
from src.discord.stateful_embed import StatefulEmbed
from src.pnw.utils import remaining_turn_change_duration

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
    async def turn(self, ctx: commands.Context[Bot], fake: bool = False):
        """Check if it's a turn change."""
        now = (
            datetime.now(timezone.utc).replace(hour=2, minute=0, second=30)
            if fake
            else None
        )

        if turn_change := remaining_turn_change_duration(now):
            await ctx.send(
                f"Turn change ends in {turn_change.total_seconds() // 60} minutes and {turn_change.total_seconds() % 60} seconds."
            )
            await asyncio.sleep(turn_change.total_seconds())
        await ctx.send("And we're done!")

    @dev.command(name="sync_nations")
    async def sync_nations_command(self, ctx: commands.Context[Bot], *nation_id: int):
        """Sync all nations."""
        msg = await ctx.reply(
            f"Syncing {'all' if not nation_id else 'specified'} nations..."
        )

        timer = default_timer()

        num_synced = await update_pnw_table(
            table_class=Nation,
            fetch_function=self.bot.api_v3.get_nations,
            query_args={"nation_id": nation_id} if nation_id else {},
            page_size=500 if not nation_id else 50,
            batch_size=10 if not nation_id else 1,
        )

        nation = await Nation.objects().get(where=Nation.id == 239259)
        assert nation is not None

        nation.refresh()

        timer = default_timer() - timer

        await msg.edit(
            content=f"Completed! Synced `{num_synced}` nations in `{timer:.2f}s`."
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
