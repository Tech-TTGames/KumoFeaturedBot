"""Utility commands for the bot."""
import discord
from discord import app_commands
from discord.ext import commands

from kumo_bot.config.constants import VERSION


class UtilityCommands(commands.Cog):
    """Utility commands cog."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Pings the bot.")
    async def ping(self, interaction: discord.Interaction) -> None:
        """This command is used to check if the bot is online."""
        await interaction.response.send_message(
            "Pong! The bot is online.\nPing: " + str(round(self.bot.latency * 1000)) +
            "ms")

    @app_commands.command(name="version",
                          description="Displays the current version of the bot.")
    async def version(self, interaction: discord.Interaction) -> None:
        """This command is used to check the current version of the bot."""
        await interaction.response.send_message(
            "KumoFeaturedBot " + VERSION + " by Tech. TTGames#8616 is running.")


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(UtilityCommands(bot))