"""
Guide: https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612
"""

import logging
import math
import traceback

import discord
from discord.ext import commands

from src.bot import Bot

logger = logging.getLogger(__name__)


class CommandErrorHandler(commands.Cog):
    """Cog for handling command errors."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context[Bot], error: commands.CommandError
    ):
        """The event triggered when an error is raised while invoking a command.
        Parameters
        ------------
        ctx: commands.Context
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.
        """
        if not ctx.command:
            return
        if hasattr(ctx.command, "on_error"):
            return

        cog = ctx.cog
        if cog:
            if (
                cog._get_overridden_method(  # pylint: disable=protected-access
                    cog.cog_command_error
                )
                is not None
            ):
                return

        ignored = (commands.CommandNotFound,)
        error = getattr(error, "original", error)

        if isinstance(error, ignored):
            return

        embed_title: str = ""
        embed_description: str | None = None

        match error:
            case commands.DisabledCommand():
                embed_title = "Command Disabled"
                embed_description = f"{ctx.command} has been disabled."
            case commands.NoPrivateMessage():
                try:
                    embed_title = "Command Not Allowed in DMs"
                    embed_description = (
                        f"{ctx.command} can not be used in Private Messages."
                    )
                except discord.HTTPException:
                    pass
            case commands.PrivateMessageOnly():
                try:
                    embed_title = "Command Only Allowed in DMs"
                    embed_description = (
                        f"{ctx.command} can only be used in Private Messages."
                    )
                except discord.HTTPException:
                    pass
            case commands.BadArgument():
                await ctx.send_help(ctx.command)
            case commands.CommandOnCooldown():
                embed_title = "Command On Cooldown"
                embed_description = f"This command is on cooldown, please retry in {math.ceil(error.retry_after)}s."
            case commands.MaxConcurrencyReached():
                embed_title = "Command Max Concurrency Reached"
                embed_description = (
                    "Too many people using this command. Please try again in a bit."
                )
            case commands.MissingPermissions():
                missing = [
                    perm.replace("_", " ").replace("guild", "server").title()
                    for perm in error.missing_permissions
                ]
                if len(missing) > 2:
                    fmt = f"**{'**, **'.join(missing[:-1])}, and **{missing[-1]}**"
                else:
                    fmt = " and ".join(f"**{missing}**")
                embed_title = "Missing Permissions"
                embed_description = (
                    f"You need the **{fmt}** permission(s) to use this command."
                )
            case commands.BotMissingPermissions():
                missing = [
                    perm.replace("_", " ").replace("guild", "server").title()
                    for perm in error.missing_permissions
                ]
                if len(missing) > 2:
                    fmt = f"**{'**, **'.join(missing[:-1])}, and **{missing[-1]}**"
                else:
                    fmt = " and ".join(f"**{missing}**")
                embed_title = "I'm not allowed to do that"
                embed_description = (
                    f"I need the **{fmt}** permission(s) to run this command."
                )
            case commands.MissingRequiredArgument():
                embed_title = f"Missing required argument `{error.param.name}`."
                embed_description = f"\n\nUsage: `{ctx.prefix}{ctx.command.name} {ctx.command.signature}`"
            case commands.UserInputError():
                embed_title = "Invalid Input"
                embed_description = None
                await ctx.send_help(ctx.command)
            case commands.NotOwner():
                embed_title = "Not Owner"
                embed_description = (
                    "Only the developer of the bot can use this command."
                )
            case commands.MissingRole():
                embed_title = "Missing Role"
                embed_description = f"You are missing the `{error.missing_role}` role."
            case commands.MissingAnyRole():
                roles = [f"`{role}`" for role in error.missing_roles]
                if len(roles) > 2:
                    embed_title = "Missing Roles"
                    embed_description = f"You are missing the {', '.join(roles[:-1])} and {roles[-1]} roles."
                else:
                    embed_title = "Missing Roles"
                    embed_description = (
                        f"You are missing the {' and '.join(roles)} roles."
                    )
            case commands.CheckFailure():
                # This is where custom command exceptions will be handled
                embed_title = "No Permission"
                embed_description = "You do not have permission to use this command."
            case _:
                logger.error(
                    "Ignoring exception in command %s:", ctx.command, exc_info=error
                )
                embed_title = "An error occurred while processing this command."
                # get linenumber of error
                error_traceback = "".join(
                    traceback.format_exception(type(error), error, error.__traceback__)
                )
                linenumber = error_traceback.split("line ")[-1].split(",")[0]
                filename = (
                    error_traceback.split("File ")[-1]
                    .split(",")[0]
                    .replace("/app/bot/cogs", "")
                )

                embed_description = (
                    "Please contact <@!267814904226906115> if the issue persists.\n\n"
                    f"**Error at line {linenumber} in {filename}:**\n"
                    f"```py\n{error}\n```"
                )

        error_embed = discord.Embed(
            title=embed_title, description=embed_description, color=discord.Color.red()
        )
        await ctx.reply(
            embed=error_embed, allowed_mentions=discord.AllowedMentions.none()
        )


async def setup(bot: Bot):
    await bot.add_cog(CommandErrorHandler(bot))
