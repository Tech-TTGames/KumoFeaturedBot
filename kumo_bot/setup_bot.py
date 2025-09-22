"""Setup bot class for initial configuration."""
import json
import logging
from typing import Any, Dict

from discord.ext import commands

from kumo_bot.config.constants import VERSION, handler, intents
from kumo_bot.config.settings import Secret


class SetupBot(commands.Bot):
    """Setup version of the bot for initial configuration."""

    def __init__(self):
        super().__init__(command_prefix=".", intents=intents)
        self.secret = Secret()

        # Add setup commands
        self.add_setup_commands()

    def add_setup_commands(self):
        """Add setup-specific commands."""
        @self.event
        async def on_ready():
            """This event is called when the bot is ready to be used."""
            logging.info("%s has connected to Discord!", str(self.user))

        @self.command(brief="Start setup.", description="Starts the setup process.")
        @commands.check_any(commands.has_permissions(administrator=True), commands.is_owner())
        async def setup(ctx):
            """Starts the setup process."""
            await ctx.send(f"Starting setup of KumoFeaturedBot {VERSION}...")
            confi: Dict[str, Any] = {"mode": "prod"}
            message = await ctx.author.send(
                "Hello! I'm going to ask you a few questions to get started."
                " Use 'cancel' anytime to cancel the setup process."
            )
            dm_channel = message.channel

            def dm_from_user(msg):
                """Check if the message is from the user in DMs."""
                return msg.channel == dm_channel

            # Get prefix
            await dm_channel.send(
                "Please select the prefix for the bot. (During setup, the prefix is '.')"
            )
            prefi = await self.wait_for("message", check=dm_from_user)
            if prefi.content == "cancel":
                return await dm_channel.send("Setup cancelled.")
            confi["prefix"] = prefi.content

            # Get guild ID
            await dm_channel.send(
                "Please provide the ID of the Guild that the bot will function in:"
            )
            while True:
                gld = await self.wait_for("message", check=dm_from_user)
                if gld.content == "cancel":
                    return await dm_channel.send("Setup cancelled.")
                if gld.content.isnumeric():
                    guild = self.get_guild(int(gld.content))
                    if guild is None:
                        await dm_channel.send(
                            "That is not a valid Guild ID or I am not present there. "
                            "Please try again."
                        )
                    else:
                        confi["guild"] = guild.id
                        await dm_channel.send(f"Guild set to {guild.name}.")
                        break
                else:
                    await dm_channel.send(
                        "That is not a valid Guild ID. "
                        "Please try again or use 'cancel' to cancel the setup."
                    )

            # Get channel ID
            await dm_channel.send(
                "Please provide the ID of the Channel that the bot will function in:"
            )
            while True:
                chn = await self.wait_for("message", check=dm_from_user)
                if chn.content == "cancel":
                    return await dm_channel.send("Setup cancelled.")
                if chn.content.isnumeric():
                    channel = self.get_channel(int(chn.content))
                    if channel is None or channel.guild.id != confi["guild"]:
                        await dm_channel.send(
                            "That is not a valid Channel ID or is not in the specified guild. "
                            "Please try again."
                        )
                    else:
                        confi["channel"] = channel.id
                        await dm_channel.send(f"Channel set to {channel.name}.")
                        break
                else:
                    await dm_channel.send(
                        "That is not a valid Channel ID. "
                        "Please try again or use 'cancel' to cancel the setup."
                    )

            # Get role ID
            await dm_channel.send(
                "Please provide the ID of the Role that will have access to bot commands:"
            )
            while True:
                rol = await self.wait_for("message", check=dm_from_user)
                if rol.content == "cancel":
                    return await dm_channel.send("Setup cancelled.")
                if rol.content.isnumeric():
                    role = guild.get_role(int(rol.content))
                    if role is None:
                        await dm_channel.send(
                            "That is not a valid Role ID in the specified guild. "
                            "Please try again."
                        )
                    else:
                        confi["role"] = role.id
                        await dm_channel.send(f"Role set to {role.name}.")
                        break
                else:
                    await dm_channel.send(
                        "That is not a valid Role ID. "
                        "Please try again or use 'cancel' to cancel the setup."
                    )

            # Finalize setup
            await dm_channel.send("Preparing to save configuration...")
            confi["mention"] = None
            confi["lastvote"] = None
            confi["lastwin"] = None
            confi["closetime"] = None
            confi["voterunning"] = False
            confi["blacklist"] = []
            confi["vote_count_mode"] = 0
            confi["debug_tie"] = False
            confi["owner_role"] = "Administrator"

            with open("config.json", "w+", encoding="utf-8") as config_file:
                json.dump(confi, config_file, indent=4)
                config_file.truncate()

            await dm_channel.send("Configuration saved. Setup complete.")
            await ctx.send("Setup complete. Restarting...")
            await self.close()

    def run_bot(self):
        """Run the setup bot."""
        self.run(self.secret.token, log_handler=handler, root_logger=True)
