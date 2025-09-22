"""Main bot class for KumoFeaturedBot."""
import logging
import pathlib

import discord
from discord.ext import commands
from lncrawl.core import app, sources
from lncrawl.binders import available_formats
from fanficfare import cli, loghandler

from kumo_bot.config.constants import handler, intents
from kumo_bot.config.settings import Config, Secret
from kumo_bot import cogs


class KumoBot(commands.Bot):
    """Main bot class."""

    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            status=discord.Status.online,
            activity=discord.Activity(type=discord.ActivityType.watching,
                                      name="for voter fraud."),
        )

        # Initialize configuration and secrets
        self.config = Config(self)
        self.secret = Secret()
        self.root = pathlib.Path(__file__).parent.parent

        # Set up command prefix from config
        self.command_prefix = self.config.prefix

        # Set up logging
        self.l_handler = handler
        handler.setLevel(logging.INFO)
        loghandler.setLevel(logging.CRITICAL)
        log_stuff = cli.logger
        log_stuff.addHandler(handler)

        # Set up lightnovel crawler
        sources.load_sources()
        self.lnc_app = app.App()
        self.lnc_app.no_suffix_after_filename = True
        self.lnc_app.output_formats = {
            x: (x in ["epub", "json"])
            for x in available_formats
        }

    async def setup_hook(self):
        """Setup hook called when the bot is starting."""
        logging.info("Loading cogs...")
        for extension in cogs.EXTENSIONS:
            try:
                await self.load_extension(extension)
                logging.info("Loaded extension: %s", extension)
            except commands.ExtensionError as err:
                logging.error("Failed to load cog %s: %s", extension, err)
        logging.info("Finished loading cogs.")

    @commands.command()
    @commands.dm_only()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        """Syncs the bot's slash commands."""
        await ctx.send("Syncing...")
        await self.tree.sync()
        await ctx.send("Synced!")

    def run_bot(self):
        """Run the bot."""
        self.run(self.secret.token, log_handler=handler, root_logger=True)
