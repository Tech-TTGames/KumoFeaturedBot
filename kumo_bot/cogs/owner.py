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
            
        elif command == "testget":
            # Test submission gathering functionality (send results via DM)
            submitted = []
            submitees = []
            channel = config.channel
            
            try:
                from datetime import timedelta
                timed = discord.utils.utcnow() - timedelta(days=31)
                async for message in channel.history(after=timed, limit=None):
                    if (message.content.startswith("https://") and message.author not in submitees):
                        import re
                        url = re.search(r"(?P<url>https?://\S+)", message.content)
                        if url not in submitted and url is not None:
                            submitted.append(str(url.group("url")))
                            submitees.append(message.author)
                submitted = list(dict.fromkeys(submitted))
                
                result = f"Found {len(submitted)} submissions:\n" + "\n".join(submitted[:20])  # Limit to first 20
                await interaction.user.send(result)
                await interaction.followup.send(f"Test completed. Found {len(submitted)} submissions. Results sent via DM.")
                logging.debug("Test Gathering results: %s", submitted)
                
            except Exception as e:
                await interaction.followup.send(f"Error during testget: {e}")
                logging.error("Error in testget: %s", e, exc_info=True)
                
        elif command == "testhistory":
            # Test vote history and user activity analysis
            try:
                from kumo_bot.config.constants import EMOJI_ALPHABET
                from datetime import timedelta
                
                usrlib = {}
                vote = {}
                channel = config.channel
                votemsg = await config.lastvote
                timed = discord.utils.utcnow() - timedelta(days=31)

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
                                if user != self.bot.user and user in usrlib:
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
                    result += str(vote)

                await interaction.user.send(result)
                await interaction.followup.send("Test completed. Results sent via DM.")
                logging.debug("Test History results: %s", vote)
                
            except Exception as e:
                await interaction.followup.send(f"Error during testhistory: {e}")
                logging.error("Error in testhistory: %s", e, exc_info=True)
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


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(OwnerCommands(bot))
