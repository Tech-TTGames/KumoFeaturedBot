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
        super().__init__()
        self.command_prefix = "<"  # Debug prefix

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

    @app_commands.command(description="Emergency config editor for debug mode")
    @app_commands.describe(
        setting="Config setting to edit (guild, channel, lastvote, lastwin, voterunning, closetime, mention)",
        value="Value to set (message ID for lastvote/lastwin, true/false for voterunning, etc.)"
    )
    @checks.is_owner()
    async def edit_config(self, interaction: discord.Interaction, setting: str, value: str = None):
        """Emergency configuration editor for debug mode."""
        await interaction.response.defer(ephemeral=True)
        
        config = self.config
        
        try:
            if setting == "guild":
                gld = interaction.guild
                if gld:
                    config.guild = gld
                    await interaction.followup.send(f"Guild set to: {gld.name} (ID: {gld.id})")
                else:
                    await interaction.followup.send("This command must be used in a guild.")
                    
            elif setting == "channel":
                chn = interaction.channel
                config.channel = chn
                await interaction.followup.send(f"Channel set to: {chn.mention} (ID: {chn.id})")
                
            elif setting == "lastvote":
                if value is None:
                    await interaction.followup.send("Message ID required for lastvote")
                    return
                try:
                    message_id = int(value)
                    lastvote_msg = await config.channel.fetch_message(message_id)
                    config.lastvote = lastvote_msg.id
                    await interaction.followup.send(f"Last vote set to message ID: {message_id}")
                except (ValueError, discord.NotFound) as e:
                    await interaction.followup.send(f"Invalid message ID or message not found: {e}")
                    
            elif setting == "lastwin":
                if value is None:
                    await interaction.followup.send("Message ID required for lastwin")
                    return
                try:
                    message_id = int(value)
                    lastwin_msg = await config.channel.fetch_message(message_id)
                    config.lastwin = lastwin_msg.id
                    await interaction.followup.send(f"Last win set to message ID: {message_id}")
                except (ValueError, discord.NotFound) as e:
                    await interaction.followup.send(f"Invalid message ID or message not found: {e}")
                    
            elif setting == "voterunning":
                if value is None:
                    await interaction.followup.send("Value required for voterunning (true/false)")
                    return
                vote_status = value.lower() in ["true", "1", "yes", "on"]
                config.vote_running = vote_status
                await interaction.followup.send(f"Vote running set to: {vote_status}")
                
            elif setting == "closetime":
                if value is None:
                    # Clear closetime
                    config.closetime = None
                    await interaction.followup.send("Close time cleared")
                else:
                    try:
                        timestamp = int(value)
                        config.closetime = timestamp
                        readable_time = discord.utils.format_dt(discord.utils.snowflake_time(timestamp))
                        await interaction.followup.send(f"Close time set to: {readable_time}")
                    except ValueError:
                        await interaction.followup.send("Invalid timestamp for closetime")
                        
            elif setting == "mention":
                if value is None:
                    config.mention = None
                    await interaction.followup.send("Mention role cleared")
                else:
                    try:
                        role_id = int(value)
                        role = interaction.guild.get_role(role_id)
                        if role:
                            config.mention = role.id
                            await interaction.followup.send(f"Mention role set to: {role.name}")
                        else:
                            await interaction.followup.send("Role not found")
                    except ValueError:
                        await interaction.followup.send("Invalid role ID")
                        
            else:
                available_settings = ["guild", "channel", "lastvote", "lastwin", "voterunning", "closetime", "mention"]
                await interaction.followup.send(f"Unknown setting: {setting}\n"
                                               f"Available settings: {', '.join(available_settings)}")
                
        except Exception as e:
            logging.error("Error in edit_config: %s", e, exc_info=True)
            await interaction.followup.send(f"Error updating config: {e}")

    @app_commands.command(description="Show current config status for debugging")
    @checks.is_owner()
    async def config_status(self, interaction: discord.Interaction):
        """Show current configuration status for debugging."""
        await interaction.response.defer(ephemeral=True)
        
        config = self.config
        
        try:
            status = "**Current Configuration Status:**\n"
            status += f"Mode: `{config.mode}`\n"
            status += f"Guild: `{config.guild.name if config.guild else 'Not set'}` (ID: {config.guild.id if config.guild else 'N/A'})\n"
            status += f"Channel: `{config.channel.name if config.channel else 'Not set'}` (ID: {config.channel.id if config.channel else 'N/A'})\n"
            status += f"Vote Running: `{config.vote_running}`\n"
            status += f"Vote Count Mode: `{config.vote_count_mode}`\n"
            status += f"Debug Tie: `{config.debug_tie}`\n"
            
            if config.lastvote:
                status += f"Last Vote: Message ID `{config.lastvote}`\n"
            else:
                status += "Last Vote: `Not set`\n"
                
            if config.lastwin:
                status += f"Last Win: Message ID `{config.lastwin}`\n"
            else:
                status += "Last Win: `Not set`\n"
                
            if config.closetime:
                readable_time = discord.utils.format_dt(discord.utils.snowflake_time(config.closetime))
                status += f"Close Time: {readable_time}\n"
            else:
                status += "Close Time: `Not set`\n"
                
            if config.mention:
                mention_role = interaction.guild.get_role(config.mention) if interaction.guild else None
                status += f"Mention Role: `{mention_role.name if mention_role else 'Role not found'}` (ID: {config.mention})\n"
            else:
                status += "Mention Role: `Not set`\n"
                
            blacklist_count = len(config.blacklist) if hasattr(config, 'blacklist') else 0
            status += f"Blacklist: `{blacklist_count} users`\n"
            
            await interaction.followup.send(status)
            
        except Exception as e:
            logging.error("Error in config_status: %s", e, exc_info=True)
            await interaction.followup.send(f"Error retrieving config status: {e}")

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
