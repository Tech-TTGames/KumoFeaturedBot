"""Main bot class for KumoFeaturedBot."""
import logging
import os
from typing import List

import discord
from discord.ext import commands
from lncrawl.core import app, sources, proxy
from lncrawl.binders import available_formats
from fanficfare import cli, loghandler

from variables import Config, Secret, handler, intents
from kumo_bot.events.handlers import EventHandlers


class KumoBot(commands.Bot):
    """Main bot class."""

    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for voter fraud."
            ),
        )
        
        # Initialize configuration and secrets
        self.config = Config(self)
        self.secret = Secret()
        
        # Set up command prefix from config
        self.command_prefix = self.config.prefix
        
        # Set up logging
        handler.setLevel(logging.INFO)
        loghandler.setLevel(logging.CRITICAL)
        log_stuff = cli.logger
        log_stuff.addHandler(handler)
        
        # Set up lightnovel crawler
        sources.load_sources()
        self.application = app.App()
        self.application.no_suffix_after_filename = True
        self.application.output_formats = {
            x: (x in ["epub", "json"])
            for x in available_formats
        }
        
        # Initialize event handlers
        self.event_handlers = EventHandlers(self)
        
        # Setup events
        self.setup_events()

    def setup_events(self):
        """Set up event handlers."""
        @self.event
        async def on_command_error(ctx: discord.Interaction, error):
            await self.event_handlers.on_command_error(ctx, error)

        @self.event
        async def on_ready():
            # Import here to avoid circular imports
            from kumo_bot.commands.voting import endvote_internal
            await self.event_handlers.on_ready(endvote_internal)

    async def load_extensions(self):
        """Load all command extensions."""
        extensions = [
            'kumo_bot.commands.utility',
            'kumo_bot.commands.admin',
            'kumo_bot.commands.voting',
        ]
        
        for extension in extensions:
            try:
                await self.load_extension(extension)
                logging.info(f"Loaded extension: {extension}")
            except Exception as e:
                logging.error(f"Failed to load extension {extension}: {e}")

    async def setup_hook(self):
        """Setup hook called when the bot is starting."""
        await self.load_extensions()

    @commands.command()
    @commands.dm_only()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        """Syncs the bot's slash commands."""
        await ctx.send("Syncing...")
        await self.tree.sync()

    def run_bot(self):
        """Run the bot."""
        self.run(self.secret.token, log_handler=handler, root_logger=True)