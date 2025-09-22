"""Event handlers for the bot."""
import logging
import discord
from discord import app_commands

from variables import Config


class EventHandlers:
    """Event handlers for the bot."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config(bot)

    async def on_command_error(self, ctx: discord.Interaction, error):
        """The event triggered when an error is raised while invoking a command."""
        if hasattr(ctx.command, "on_error"):
            return

        ignored = (app_commands.CommandNotFound, )
        error = getattr(error, "original", error)

        if isinstance(error, ignored):
            return

        if isinstance(error, app_commands.NoPrivateMessage):
            try:
                await ctx.user.send(
                    f"{ctx.command} can not be used in Private Messages.")
            except discord.HTTPException:
                pass

        elif isinstance(error, app_commands.CheckFailure):
            await ctx.response.send_message(error, ephemeral=True)

        elif isinstance(error, app_commands.BotMissingPermissions):
            await ctx.response.send_message(
                "I'm missing permissions to execute the command!\n"
                f"{error.missing_permissions}",
                ephemeral=True,
            )

        elif isinstance(error, app_commands.MissingRole):
            await ctx.response.send_message(
                "You are missing the role to run this command.", ephemeral=True)

        else:
            logging.exception(
                "Ignoring exception %s in command %s:",
                str(error),
                ctx.command,
                exc_info=error,
            )

    async def on_ready(self, endvote_internal_func=None):
        """This event is called when the bot is ready to be used."""
        logging.info("%s has connected to Discord!", str(self.bot.user))
        if self.config.armed:
            return
        if self.config.closetime and endvote_internal_func:
            self.config.armed = True
            logging.info("Resuming vote at %s", self.config.closetime)
            await discord.utils.sleep_until(self.config.closetime)
            logging.info("Closing vote via INTERNAL event.")
            await endvote_internal_func("INTERNAL")  # type: ignore
        self.config.armed = True