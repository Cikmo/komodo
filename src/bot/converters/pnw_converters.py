"""Converters for Politics and War related objects."""

import logging

from piccolo.query.functions import Lower

import discord
from discord.ext import commands
from src.bot import Bot
from src.database.tables.pnw import Nation
from src.pnw.api_v3.get_nations import NationFields

logger = logging.getLogger(__name__)


class NationConverter(commands.Converter[Nation | None]):
    """Converts a string to a nation. Can be a nation name, nation id, nation url, discord id,
    discord member object or the literal "me" (the author of the command).

    Lookup order:
    1. "me" (author's Discord ID)
    2. Nation ID (integer)
    3. Nation URL (contains "politicsandwar.com/nation/id=")
    4. Nation name (case-insensitive)
    5. Discord Member or User object
    6. Discord Member or User by ID or username
    """

    async def convert(
        self,
        ctx: commands.Context[commands.Bot | commands.AutoShardedBot],
        argument: str | int | discord.Member | discord.User,
    ) -> Nation | None:
        """Converts a string to a nation.

        Args:
            ctx: The context of the command.
            argument: The string to convert. Can be a nation name, nation id,
            or discord id. If "me" is passed, the author of the command will be used.

        Returns:
            The nation if found, otherwise None.
        """
        nation = None

        if isinstance(argument, (str, int)):
            nation = await self._convert_from_string_or_int(ctx, argument)
            if nation:
                return nation

        user = await self._try_to_get_user(ctx, argument)

        if not user:
            return None

        return await self._convert_from_user(user)

    @staticmethod
    async def get_author(ctx: commands.Context[Bot]) -> Nation | None:
        """Get the nation of the author of a command."""

        return await Nation.objects().where(Nation.discord_id == ctx.author.id).first()

    async def _convert_from_string_or_int(
        self,
        ctx: commands.Context[commands.Bot | commands.AutoShardedBot],
        argument: str | int,
    ) -> Nation | None:
        """Converts a string or integer to a nation.

        Args:
            ctx: The context of the command.
            argument: The string or integer to convert.

        Returns:
            The nation if found, otherwise None.
        """

        if argument == "me":
            return (
                await Nation.objects()
                .where(Nation.discord_id == ctx.author.id)
                .first()
                .run()
            )

        return await NationConverterNoDiscord().convert(ctx, argument)

    async def _convert_from_user(
        self, user: discord.Member | discord.User
    ) -> Nation | None:

        return await Nation.objects().where(Nation.discord_id == user.id).first().run()

    async def _try_to_get_user(
        self,
        ctx: commands.Context[commands.Bot | commands.AutoShardedBot],
        argument: str | int | discord.Member | discord.User,
    ) -> discord.Member | discord.User | None:
        """Try to get a discord.Member or discord.User object from the argument.

        Args:
            ctx: The command context.
            argument: The argument to convert.

        Returns:
            The discord.Member or discord.User object if found, otherwise None.
        """

        if isinstance(argument, (discord.Member, discord.User)):
            return argument

        argument = str(argument)

        try:
            return await commands.MemberConverter().convert(ctx, argument)
        except commands.MemberNotFound:
            pass
        try:
            return await commands.UserConverter().convert(ctx, argument)
        except commands.UserNotFound:
            pass

        return None


class NationConverterNoDiscord(commands.Converter[Nation | None]):
    """Converts a string to a nation. Can be a nation name, nation id, or URL-

    Lookup order:
    1. Nation ID (integer)
    2. Nation URL (contains "politicsandwar.com/nation/id=")
    3. Nation name (case-insensitive)
    """

    async def convert(
        self,
        ctx: commands.Context[  # pylint: disable=unused-argument
            commands.Bot | commands.AutoShardedBot
        ],
        argument: str | int,
    ) -> Nation | None:
        """Converts a string to a nation.

        Args:
            ctx: The context of the command.
            argument: The string to convert. Can be a nation name, nation id, or discord id.

        Returns:
            The nation if found, otherwise None.
        """
        if isinstance(argument, int) or argument.isdigit():
            num = int(argument)

            # Postgres complains when we pass a discord id, cause it's not a 32-bit integer
            if num.bit_length() > 31:
                return None

            return await Nation.objects().where(Nation.id == num).first().run()

        argument = argument.lower()

        if "politicsandwar.com/nation/id=" in argument:
            nation_id = argument.split("id=")[1]
            if not nation_id.isdigit():
                return None
            return await Nation.objects().get((Nation.id == int(nation_id))).run()

        return (
            await Nation.objects().where(Lower(Nation.name) == argument).first().run()
        )


class NationAPIModelConverter(commands.Converter[NationFields | None]):
    """Converts a string to a api nation model. Can be a nation name, nation id, or URL-

    Lookup order:
    1. Nation ID (integer)
    2. Nation URL (contains "politicsandwar.com/nation/id=")
    3. Nation name (case-insensitive)
    """

    async def convert(  # type: ignore cause I'm using a custom bot type
        self,
        ctx: commands.Context[Bot],
        argument: str | int,
    ) -> NationFields | None:
        """Converts a string to a nation.

        Args:
            ctx: The context of the command.
            argument: The string to convert. Can be a nation name, nation id, or discord id.

        Returns:
            The nation if found, otherwise None.
        """
        if isinstance(argument, int) or argument.isdigit():
            num = int(argument)

            nations = (await ctx.bot.api_v3.get_nations(nation_id=[num])).nations.data
            return nations[0] if nations else None

        argument = argument.lower()

        if "politicsandwar.com/nation/id=" in argument:
            nation_id = argument.split("id=")[1]
            if not nation_id.isdigit():
                return None
            nations = (
                await ctx.bot.api_v3.get_nations(nation_id=[int(nation_id)])
            ).nations.data
            return nations[0] if nations else None

        nations = (
            await ctx.bot.api_v3.get_nations(nation_name=[argument])
        ).nations.data
        return nations[0] if nations else None
