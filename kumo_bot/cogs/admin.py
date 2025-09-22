"""Admin commands for the bot."""
import asyncio
import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

from kumo_bot.utils.checks import has_admin_role
from kumo_bot.utils.downloaders import fetch_download


class AdminCommands(commands.Cog):
    """Admin commands cog."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="blacklist", description="Blacklists a user.")
    @has_admin_role()
    async def blacklist(self, interaction: discord.Interaction,
                        user: discord.User) -> None:
        """This command is used to blacklist a user from voting."""
        from kumo_bot.config.settings import Config
        config = Config(self.bot)
        
        blacklst = config.blacklist
        if user.id in blacklst:
            blacklst.remove(user.id)
            await interaction.response.send_message(
                f"User {user.mention} unblacklisted.", ephemeral=True)
        else:
            blacklst.append(user.id)
            await interaction.response.send_message(
                f"User {user.mention} blacklisted.", ephemeral=True)
        config.blacklist = blacklst

    @app_commands.command(name="votecountmode",
                          description="Sets the vote count mode.")
    @has_admin_role()
    @app_commands.describe(mode="Vote count mode.")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Legacy (all messages)", value=1),
        app_commands.Choice(name="Modern (messages before vote)", value=0),
        app_commands.Choice(name="Modern+ (messages before vote, 10-25 required)",
                            value=2),
    ])
    async def votecountmode(self, interaction: discord.Interaction,
                            mode: app_commands.Choice[int]) -> None:
        """This command is used to configure the vote count mode."""
        from kumo_bot.config.settings import Config
        config = Config(self.bot)
        config.vote_count_mode = mode.value

        await interaction.response.send_message(
            f"Vote count mode set to {mode.name}.",
            ephemeral=True,
        )

    @app_commands.command(name="accessrole", description="Sets botrole.")
    @has_admin_role()
    @app_commands.describe(addrole="Role to be set as botrole.")
    async def accessrole(self, interaction: discord.Interaction,
                         addrole: discord.Role) -> None:
        """Sets the <addrole> as the bot role."""
        from kumo_bot.config.settings import Config
        config = Config(self.bot)
        config.role = addrole

        await interaction.response.send_message(
            f"Role {addrole} has been set as to have access.", ephemeral=True)

    @app_commands.command(name="setmention", description="Sets mention.")
    @has_admin_role()
    @app_commands.describe(mention="Role to be set as mention.")
    async def setmention(self, interaction: discord.Interaction,
                         mention: discord.Role) -> None:
        """Sets the <mention> as the mention."""
        from kumo_bot.config.settings import Config
        config = Config(self.bot)
        config.mention = mention

        await interaction.response.send_message(
            f"Role {mention} has been set to be mentioned.", ephemeral=True)

    @app_commands.command(name="pinops", description="Pin operations.")
    @has_admin_role()
    @app_commands.describe(pind="ID of the message to be pinned/unpinned.")
    async def pinops(self, interaction: discord.Interaction, pind: str) -> None:
        """Pins or unpins a message."""
        INVALID_CHANNEL_LIKES = (discord.StageChannel, discord.ForumChannel, discord.CategoryChannel)
        
        if (isinstance(interaction.channel, INVALID_CHANNEL_LIKES)
                or interaction.channel is None):
            await interaction.response.send_message(
                "This command cannot be used in this channel.", ephemeral=True)
            return
        if not pind.isdigit():
            await interaction.response.send_message("Message ID must be a number.",
                                                    ephemeral=True)
            return
        pind_i = int(pind)
        msg = await interaction.channel.fetch_message(pind_i)
        if msg.pinned:
            await msg.unpin()
            await interaction.response.send_message(
                f"Message {pind} has been unpinned.", ephemeral=True)
        else:
            await msg.pin()
            await interaction.response.send_message(
                f"Message {pind} has been pinned.", ephemeral=True)

    @app_commands.command(name="download", description="Downloads a fic.")
    @has_admin_role()
    @app_commands.describe(url="URL of the fic to be downloaded.")
    async def download(self, interaction: discord.Interaction, url: str) -> None:
        """Downloads a fic."""
        await interaction.response.defer(thinking=True)
        logging.info("Downloading fic from %s", url)
        
        # Import here to avoid circular imports
        from lncrawl.core import app
        from fanficfare import cli
        from lncrawl.binders import available_formats
        
        # Initialize the application
        application = app.App()
        application.no_suffix_after_filename = True
        application.output_formats = {
            x: (x in ["epub", "json"])
            for x in available_formats
        }
        log_stuff = cli.logger
        
        try:
            file = await asyncio.wait_for(fetch_download(url, application, log_stuff), timeout=800)
        except Exception as e:
            logging.warning("Failed to download fic. %s Error Stack:\n",
                            e,
                            exc_info=True)
            file = None
        if file is None:
            await interaction.followup.send("Error while downloading fic.")
            return
        await interaction.followup.send(file=file)


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(AdminCommands(bot))