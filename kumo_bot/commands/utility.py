"""Utility commands for the bot."""
import discord
from discord import app_commands
from discord.ext import commands

from variables import VERSION


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

    @app_commands.command(name="configuration",
                          description="Displays the current configuration of the bot.")
    @commands.is_owner()
    async def configuration(self, interaction: discord.Interaction) -> None:
        """This command is used to check the current configuration of the bot."""
        from variables import Config
        config = Config(self.bot)
        
        last_vote = await config.lastvote
        last_win = await config.lastwin
        democracy = await config.democracy
        readable_config = discord.Embed(
            title="Current Configuration",
            description=f"Guild: {config.guild}\n"
            f"Channel: {config.channel}\n"
            f"Role: {config.role}\n"
            f"Mention: {config.mention}\n"
            f"Last Vote: {last_vote}\n"
            f"Last Win: {last_win}\n"
            f"Democracy: {democracy}\n"
            f"Vote Running: {config.vote_running}\n"
            f"Close Time: {config.closetime}\n"
            f"Mode: {config.mode}\n"
            f"Vote Count Mode: {config.vote_count_mode}\n"
            f"Blacklist: {config.blacklist}\n"
            f"Owner Role: {config.owner_role}\n"
            f"Debug Tie: {config.debug_tie}",
            color=0x00ff00,
        )
        await interaction.response.send_message(embed=readable_config, ephemeral=True)


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(UtilityCommands(bot))