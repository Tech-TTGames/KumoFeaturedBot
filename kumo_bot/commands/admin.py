"""Admin commands for the bot."""
import asyncio
import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

from kumo_bot.utils.checks import is_owner
from kumo_bot.utils.downloaders import fetch_download


class AdminCommands(commands.Cog):
    """Admin commands cog."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="blacklist", description="Blacklists a user.")
    @app_commands.checks.has_any_role(465888032537444353)  # Will be made dynamic
    async def blacklist(self, interaction: discord.Interaction,
                        user: discord.User) -> None:
        """This command is used to blacklist a user from voting."""
        from variables import Config
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
    @app_commands.checks.has_any_role(465888032537444353)  # Will be made dynamic
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
        from variables import Config
        config = Config(self.bot)
        config.vote_count_mode = mode.value

        await interaction.response.send_message(
            f"Vote count mode set to {mode.name}.",
            ephemeral=True,
        )

    @app_commands.command(name="override", description="Tech's admin commands.")
    @app_commands.describe(command="Command to use.")
    @is_owner()
    async def override(self, interaction: discord.Interaction, command: str) -> None:
        """This command is used to override the bot's commands."""
        from variables import Config
        config = Config(self.bot)
        
        await interaction.response.defer(thinking=True)
        logging.info("Owner override triggered: %s", command)

        if command == "reboot":
            logging.info("Rebooting...")
            await interaction.followup.send("Rebooting...")
            await self.bot.close()

        elif command == "log":
            logging.info("Sending Log...")
            dir_path = os.path.dirname(os.path.realpath(__file__))
            fpath = os.path.join(dir_path, "discord.log")
            await interaction.user.send(file=discord.File(fp=fpath))
            await interaction.followup.send("Sent!")

        elif command == "pull":
            pull = await asyncio.create_subprocess_shell(
                "git pull",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd(),
            )
            stdo, stdr = await pull.communicate()
            await interaction.followup.send("Pulling...")
            if stdo:
                await interaction.followup.send(f"[stdout]\n{stdo.decode()}")
                logging.info("[stdout]\n%s", stdo.decode())

            if stdr:
                await interaction.followup.send(f"[stderr]\n{stdr.decode()}")
                logging.info("[stderr]\n%s", stdr.decode())

            await interaction.followup.send("Rebooting...")
            logging.info("Rebooting...")
            await self.bot.close()

        elif command == "debug":
            config.mode = "debug"
            logging.info("Rebooting with debug mode...")
            await interaction.followup.send("Debug mode enabling...")
            await self.bot.close()
        elif command == "debugties":
            config.debug_tie = not config.debug_tie
            logging.info("Debug Tie toggled: %s", config.debug_tie)
            await interaction.followup.send(f"Debug Tie toggled: {config.debug_tie}")
        else:
            await interaction.followup.send("Invalid override command.")

    @app_commands.command(name="accessrole", description="Sets botrole.")
    @app_commands.checks.has_any_role(465888032537444353)  # Will be made dynamic
    @app_commands.describe(addrole="Role to be set as botrole.")
    async def accessrole(self, interaction: discord.Interaction,
                         addrole: discord.Role) -> None:
        """Sets the <addrole> as the bot role."""
        from variables import Config
        config = Config(self.bot)
        config.role = addrole

        await interaction.response.send_message(
            f"Role {addrole} has been set as to have access.", ephemeral=True)

    @app_commands.command(name="setmention", description="Sets mention.")
    @app_commands.checks.has_any_role(465888032537444353)  # Will be made dynamic
    @app_commands.describe(mention="Role to be set as mention.")
    async def setmention(self, interaction: discord.Interaction,
                         mention: discord.Role) -> None:
        """Sets the <mention> as the mention."""
        from variables import Config
        config = Config(self.bot)
        config.mention = mention

        await interaction.response.send_message(
            f"Role {mention} has been set to be mentioned.", ephemeral=True)

    @app_commands.command(name="pinops", description="Pin operations.")
    @app_commands.checks.has_any_role(465888032537444353)  # Will be made dynamic
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
    @app_commands.checks.has_any_role(465888032537444353)  # Will be made dynamic
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