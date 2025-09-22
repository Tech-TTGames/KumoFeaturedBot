"""Events cog for the bot."""
import logging
import discord
from discord import app_commands
from discord.ext import commands


class Events(commands.Cog):
    """Events cog for handling bot events."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: discord.Interaction, error):
        """The event triggered when an error is raised while invoking a command."""
        if hasattr(ctx.command, "on_error"):
            return

        ignored = (app_commands.CommandNotFound,)
        error = getattr(error, "original", error)

        if isinstance(error, ignored):
            return

        if isinstance(error, app_commands.NoPrivateMessage):
            try:
                await ctx.user.send(f"{ctx.command} can not be used in Private Messages.")
            except discord.HTTPException:
                logging.debug(f"User %s tried to use command in Private Messages.", ctx.user.name)

        elif isinstance(error, app_commands.CheckFailure):
            await ctx.response.send_message(error, ephemeral=True)

        elif isinstance(error, app_commands.BotMissingPermissions):
            await ctx.response.send_message(
                "I'm missing permissions to execute the command!\n"
                f"{error.missing_permissions}",
                ephemeral=True,
            )

        elif isinstance(error, app_commands.MissingRole):
            await ctx.response.send_message("You are missing the role to run this command.", ephemeral=True)

        else:
            logging.exception(
                "Ignoring exception %s in command %s:",
                str(error),
                ctx.command,
                exc_info=error,
            )

    @commands.Cog.listener()
    async def on_ready(self):
        """This event is called when the bot is ready to be used."""
        config = self.bot.config
        cg = self.bot.get_cog("VotingCommands")

        logging.info("%s has connected to Discord!", str(self.bot.user))
        if config.armed:
            return
        if config.closetime:
            config.armed = True
            logging.info("Resuming vote at %s", config.closetime)
            await discord.utils.sleep_until(config.closetime)
            logging.info("Closing vote via INTERNAL event.")
            await cg.endvote_internal("INTERNAL")
        config.armed = True


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(Events(bot))
