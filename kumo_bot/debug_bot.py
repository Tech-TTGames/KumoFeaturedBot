"""Debug bot class that extends the main bot with debug features."""
import logging

import discord
from discord.ext import commands

from kumo_bot.bot import KumoBot
from kumo_bot.config.constants import VERSION, handler


class DebugBot(KumoBot):
    """Debug version of the bot with additional debug commands."""

    def __init__(self):
        super().__init__()
        self.command_prefix = "<"  # Debug prefix

        # Override activity for debug mode
        self.activity = discord.Activity(type=discord.ActivityType.playing,
                                         name="with fire. [DEBUG MODE]")

        # Add debug commands
        self.add_debug_commands()

    def add_debug_commands(self):
        """Add debug-specific commands."""

        @self.command(brief="Pings the bot.",
                      description="Pings the bot. What do you expect.")
        async def ping(ctx):
            """This command is used to check if the bot is online."""
            await ctx.send(
                "Pong! The bot is online.\nPing: " +
                str(round(self.latency * 1000)) +
                "ms\n*Warning! This bot is currently in debug mode.*")
            await self.change_presence(
                status=discord.Status.dnd,
                activity=discord.Activity(type=discord.ActivityType.playing,
                                          name="with fire. [DEBUG MODE]"),
            )

        @self.command(
            brief="Displays the current version",
            description="Displays the current version of the bot.",
        )
        async def version(ctx):
            """This command is used to check the current version of the bot."""
            await ctx.send("KumoFeaturedBot " + VERSION +
                           " by Tech. TTGames#8616 is running."
                           "\n*Warning! This bot is currently in debug mode.*")

        @self.command(brief="[REDACTED]", description="Tech's admin commands.")
        @commands.is_owner()
        async def override(ctx,
                           command: str = commands.parameter(
                               default=None, description="Command")):
            """Various commands for testing."""
            if command is None:
                await ctx.send(
                    "Available commands: testget, reboot, testhistory, pull, set"
                )
                return

            if command == "testget":
                # Simplified test command
                await ctx.send("Test command executed in debug mode.")

            elif command == "reboot":
                logging.info("Rebooting...")
                await ctx.send("Rebooting...")
                await self.close()

            elif command == "testhistory":
                await ctx.send(
                    "History test not implemented in modular version.")

            elif command == "pull":
                await ctx.send("Pull command disabled in debug mode.")

            elif command.startswith("set"):
                await ctx.send(
                    "Set command not implemented in modular version.")

            else:
                await ctx.send("Unknown debug command.")

    async def load_extensions(self):
        """Load only utility extensions for debug mode."""
        extensions = [
            "kumo_bot.cogs.utility",
            "kumo_bot.cogs.events",
        ]

        for extension in extensions:
            try:
                await self.load_extension(extension)
                logging.info("Loaded extension: %s", extension)
            except commands.ExtensionError as e:
                logging.error("Failed to load extension %s: %s", extension, e)

    def run_bot(self):
        """Run the debug bot."""
        self.run(self.secret.token,
                 log_handler=handler,
                 log_level=logging.DEBUG,
                 root_logger=True)
