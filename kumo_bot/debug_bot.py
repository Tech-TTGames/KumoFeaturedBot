"""Debug bot class that extends the main bot with debug features."""
import asyncio
import datetime
import logging
import os
import re

import discord
from discord import app_commands
from discord.ext import commands

from kumo_bot.bot import KumoBot
from kumo_bot.utils import checks
from kumo_bot.config.constants import VERSION, handler, EMOJI_ALPHABET


class DebugBot(KumoBot):
    """Debug version of the bot with additional debug commands."""

    def __init__(self):
        super().__init__(True, ">")

        # Override activity for debug mode
        self.activity = discord.Activity(type=discord.ActivityType.playing, name="with fire. [DEBUG MODE]")

    @app_commands.command(description="Pings the bot. What do you expect.")
    async def ping(self, ctx):
        """This command is used to check if the bot is online."""
        await ctx.send("Pong! The bot is online.\nPing: " + str(round(self.latency * 1000)) +
                       "ms\n*Warning! This bot is currently in debug mode.*")
        await self.change_presence(
            status=discord.Status.dnd,
            activity=discord.Activity(type=discord.ActivityType.playing, name="with fire. [DEBUG MODE]"),
        )

    @app_commands.command(description="Displays the current version of the bot.",)
    async def version(self, ctx):
        """This command is used to check the current version of the bot."""
        await ctx.send("KumoFeaturedBot " + VERSION + " by @techttgames is running."
                       "\n*Warning! This bot is currently in debug mode.*")

    @app_commands.command(description="Tech's admin commands.")
    @checks.is_owner()
    async def override(self, ctx, command: str = commands.parameter(default=None, description="Command")):
        """Various commands for testing."""
        if command is None:
            await ctx.send("Available commands: testget, reboot, testhistory, testhist, pull, set\n"
                           "For emergency config editing, use `/edit_config` slash command.")
            return

        config = self.config

        if command == "testget":
            # Test submission gathering functionality
            submitted = []
            submitees = []
            await ctx.send("Gathering submissions...", delete_after=10)
            async with ctx.typing():
                timed = discord.utils.utcnow() - datetime.timedelta(days=31)
                async for message in ctx.history(after=timed, limit=None):
                    if (message.content.startswith("https://") and message.author not in submitees):
                        url = re.search(r"(?P<url>https?://\S+)", message.content)
                        if url not in submitted and url is not None:
                            submitted.append(str(url.group("url")))
                            submitees.append(message.author)
            submitted = list(dict.fromkeys(submitted))
            await ctx.author.send(f"Found {len(submitted)} submissions:\n" + "\n".join(submitted[:10])
                                 )  # Limit to first 10
            logging.debug("Test Gathering results: %s", submitted)

        elif command in ["testhistory", "testhist"]:
            # Test vote history and user activity analysis
            async with ctx.typing():
                usrlib = {}
                vote = {}
                channel = config.channel
                votemsg = await config.lastvote
                timed = discord.utils.utcnow() - datetime.timedelta(days=31)

                # Count user activity
                async for message in channel.history(after=timed, limit=None):
                    if message.author not in usrlib:
                        usrlib[message.author] = 1
                    else:
                        usrlib[message.author] += 1

                # Analyze last vote if exists
                if votemsg:
                    for reaction in votemsg.reactions:
                        if reaction.emoji in EMOJI_ALPHABET:
                            vote[reaction.emoji] = 0
                            async for user in reaction.users():
                                if user != self.user and user in usrlib:
                                    # Check if user meets activity threshold
                                    if usrlib[user] >= 5:
                                        vote[reaction.emoji] += 1
                else:
                    vote = "No vote message found."

                result = "User activity analysis:\n"
                result += f"Active users (5+ messages): {len([u for u, c in usrlib.items() if c >= 5])}\n"
                result += f"Total users: {len(usrlib)}\n"
                if isinstance(vote, dict):
                    result += f"Vote results: {vote}"
                else:
                    result += vote

                await ctx.author.send(result)
                logging.debug("Test History results: %s", vote)

        elif command.startswith("set"):
            # Configuration setting commands for testing
            parts = command.split(" ", 2)
            if len(parts) < 3:
                await ctx.send("Usage: `set <property> <value>`\n"
                               "Available properties: mode, debug_tie, vote_count_mode")
                return

            _, prop, value = parts

            if prop == "mode":
                config.mode = value
                await ctx.send(f"Mode set to: {value}")
            elif prop == "debug_tie":
                config.debug_tie = value.lower() in ["true", "1", "yes"]
                await ctx.send(f"Debug tie set to: {config.debug_tie}")
            elif prop == "vote_count_mode":
                try:
                    config.vote_count_mode = int(value)
                    await ctx.send(f"Vote count mode set to: {value}")
                except ValueError:
                    await ctx.send("Vote count mode must be a number (0-2)")
            else:
                await ctx.send(f"Unknown property: {prop}")

        elif command == "reboot":
            logging.info("Rebooting...")
            await ctx.send("Rebooting...")
            await self.close()

        elif command == "pull":
            pull = await asyncio.create_subprocess_shell(
                "git pull",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd(),
            )
            stdo, stdr = await pull.communicate()
            await ctx.send("Pulled.")
            if stdo:
                await ctx.send(f"[stdout]\n```{stdo.decode()}```")
                logging.info("[stdout]\n%s", stdo.decode())
            if stdr:
                await ctx.send(f"[stderr]\n```{stdr.decode()}```")
                logging.info("[stderr]\n%s", stdr.decode())

        else:
            await ctx.send("Unknown debug command.")

    @app_commands.command(description="Load a specific module")
    @checks.is_owner()
    async def load(self, interaction: discord.Interaction, module: str):
        """Load a specific module."""
        try:
            await self.load_extension(module)
            logging.info("Loaded extension: %s", module)
            await interaction.response.send_message(f"Successfully loaded extension: {module}", ephemeral=True)
        except commands.ExtensionError as e:
            logging.error("Failed to load extension %s: %s", module, e)
            await interaction.response.send_message(f"Failed to load extension {module}.\nError: {e}", ephemeral=True)

    @app_commands.command(description="[DANGEROUS] Emergency config editor for debug mode")
    @app_commands.describe(setting="Literal config key to set.", value="Literal value to set.")
    @checks.is_owner()
    async def edit_config(self, interaction: discord.Interaction, setting: str, value: str = None):
        """Emergency configuration editor for debug mode."""
        await interaction.response.send_message(f"Forcing {setting}: {value}", ephemeral=True)
        self.config[setting] = value
        # This is debug mode this violation is intentional.
        self.config.update()
        logging.info("Owner override coerced %s: %s", setting, value)

    @app_commands.command(description="Show current config status for debugging")
    @checks.is_owner()
    @app_commands.dm_only()
    async def config_status(self, interaction: discord.Interaction):
        """Show current configuration status for debugging."""
        await interaction.response.send_message("DUMPING CURRENT CONFIG STATUS...")
        await interaction.followup.send(f"Current config status: {str(dict(self.config))}")

    @commands.command()
    @commands.dm_only()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        """Syncs the bot's slash commands."""
        await ctx.send("Syncing...")
        await self.tree.sync()
        await ctx.send("Synced!")

    async def load_extensions(self):
        """Load extensions for debug mode."""
        extensions = [
            "kumo_bot.cogs.admin",  # Fixed: utility was consolidated into admin
            "kumo_bot.cogs.events",
            "kumo_bot.cogs.voting",  # Add voting for testing
        ]

        for extension in extensions:
            try:
                await self.load_extension(extension)
                logging.info("Loaded extension: %s", extension)
            except commands.ExtensionError as e:
                logging.error("Failed to load extension %s: %s", extension, e)

    def run_bot(self):
        """Run the debug bot."""
        self.run(self.secret.token, log_handler=handler, log_level=logging.DEBUG, root_logger=True)
