"""Owner-only commands for the bot."""
import asyncio
import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

from kumo_bot.utils import checks


class OwnerCommands(commands.Cog):
    """Owner-only commands cog."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="override", description="Tech's admin commands.")
    @app_commands.describe(command="Command to use.")
    @checks.is_owner()
    async def override(self, interaction: discord.Interaction, command: str) -> None:
        """This command is used to override the bot's commands."""
        config = self.bot.config

        await interaction.response.defer(thinking=True)
        logging.info("Owner override triggered: %s", command)

        if command == "reboot":
            logging.info("Rebooting...")
            await interaction.followup.send("Rebooting...")
            await self.bot.close()

        elif command == "log":
            logging.info("Sending Log...")
            pth = self.bot.root
            fpath = pth / "discord.log"
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

    @app_commands.command(name="configuration", description="Displays the current configuration of the bot.")
    @checks.is_owner()
    async def configuration(self, interaction: discord.Interaction) -> None:
        """This command is used to check the current configuration of the bot."""
        config = self.bot.config

        last_vote = await config.lastvote
        last_win = await config.lastwin
        democracy = await config.democracy
        readable_config = discord.Embed(
            title="Current Configuration",
            description=f"Mode: {config.mode}\n"
            f"Guild: {config.guild}\n"
            f"Channel: {config.channel}\n"
            f"Bot Operator: {config.role}\n"
            f"Mention: {config.mention}\n"
            f"Last Vote: {last_vote}\n"
            f"Last Win: {last_win}\n"
            f"Vote Running: {config.vote_running}\n"
            f"Close Time: {config.closetime}\n"
            f"Vote Count Mode: {config.vote_count_mode}\n"
            f"Blacklist: {config.blacklist}\n"
            f"Owner Role: {config.owner_role}\n"
            f"Debug Tie: {config.debug_tie}",
            color=0x00ff00,
        ).add_field(
            name="Currently Blacklisted",
            value="\n".join(f"<@{did}>" for did in config.blacklist),
        ).add_field(
            name="Current Democracy:tm: Users",
            value="\n".join([a.mention for a in democracy]),
        )
        await interaction.response.send_message(embed=readable_config,
                                                ephemeral=True,
                                                allowed_mentions=discord.AllowedMentions.none())


    @commands.command()
    @commands.dm_only()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        """Syncs the bot's slash commands."""
        await ctx.send("Syncing...")
        await self.bot.tree.sync()
        await ctx.send("Synced!")


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(OwnerCommands(bot))
