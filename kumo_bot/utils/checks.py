"""Custom checks for Discord commands."""
import discord
from discord import app_commands

from variables import Config


def vote_running():
    """Returns whether a vote is running."""

    async def predicate(ctx: discord.Interaction):
        """The predicate for the check."""
        config = Config(ctx.client)
        if not config.vote_running or ctx.user == ctx.client.user:
            raise app_commands.CheckFailure("No vote is currently running.")
        return True

    return app_commands.check(predicate)


def is_owner():
    """Returns whether the user is the owner of the bot."""

    async def predicate(ctx: discord.Interaction):
        """The predicate for the check."""
        if ctx.user.id != 414075045678284810:
            raise app_commands.CheckFailure(
                "You are not the owner of this bot.")
        return True

    return app_commands.check(predicate)