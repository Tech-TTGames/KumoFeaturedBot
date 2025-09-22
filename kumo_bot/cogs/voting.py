"""Voting commands for the bot."""
import datetime
import logging
import re
from random import choice, shuffle
from typing import Dict, Union

import discord
from discord import app_commands
from discord.ext import commands

from kumo_bot.config.constants import EMOJI_ALPHABET
from kumo_bot.utils.checks import vote_running, has_admin_role
from kumo_bot.utils.voting import parse_votemsg


class VotingCommands(commands.Cog):
    """Voting commands cog."""

    def __init__(self, bot):
        self.bot = bot
        self.double_clause = False

    @app_commands.command(name="startvote", description="Starts a vote.")
    @app_commands.guild_only()
    @has_admin_role()
    @app_commands.describe(
        cha="The channel to start the vote in.",
        polltime="Time to close the vote after in hours.",
        cap="Max submissions to vote on.",
        clear="Clear channel after vote? (True/False)",
        presend="Send message links before vote? (True/False)",
        allow_duplicates="Allow multiple submissions from the same user? (True/False)",
    )
    @app_commands.rename(cha="channel")
    async def startvote(self, interaction: discord.Interaction,
                        cha: discord.TextChannel,
                        polltime: int = 0,
                        cap: int = 8,
                        clear: bool = False,
                        presend: bool = False,
                        allow_duplicates: bool = False) -> None:
        """This command is used to start a vote."""
        config = Config(self.bot)

        invalid_channel_types = (
            discord.StageChannel, discord.ForumChannel, discord.CategoryChannel
        )

        submitted = {}
        submitted_old = []
        submitees = []

        intchannel = interaction.channel
        if isinstance(intchannel, INVALID_CHANNEL_LIKES) or intchannel is None:
            raise app_commands.AppCommandError(
                "This channel is not a text channel.")

        winmsg = await config.lastwin
        if winmsg is not None:
            await winmsg.unpin()

        votemsg = await config.lastvote
        if votemsg is not None:
            await votemsg.unpin()

        if votemsg is not None:
            submitted_old = parse_votemsg(votemsg)

        role = config.mention
        await interaction.response.defer(thinking=True)
        async with intchannel.typing():
            timed = discord.utils.utcnow() - datetime.timedelta(days=31)
            async for message in intchannel.history(after=timed, limit=None):
                if message.content.startswith("https://") and (
                        message.author not in submitees or allow_duplicates):
                    url = re.search(r"(?P<url>https?://\S+)", message.content)
                    if url is None or url in submitted_old or message.author.id in config.blacklist:
                        continue
                    if url not in submitted:
                        submitted[str(url.group("url"))] = [message.author.mention]
                        submitees.append(message.author)
                    else:
                        submitted[str(url.group("url"))].append(message.author.mention)
                        submitees.append(message.author)

        if len(submitted) == 0:
            await interaction.followup.send(
                "No submissions found in the last 31 days.", ephemeral=True)
            return

        if len(submitted) >= cap:
            submitted = dict(list(submitted.items())[:cap])
        if len(submitted) > len(EMOJI_ALPHABET):
            await interaction.followup.send(
                "Too many submissions! Please reduce the cap.", ephemeral=True)
            return

        submission_list = []
        for key, value in submitted.items():
            emoji = EMOJI_ALPHABET[len(submission_list)]
            submission_text = f"{emoji} - {key} - {', '.join(value)}"
            submission_list.append(submission_text)

        shuffle(submission_list)

        embed = discord.Embed(
            title="Vote",
            description="\n".join(submission_list),
            color=0x00ff00,
        )

        # Clear channel if requested
        if clear and intchannel:
            try:
                deleted = await intchannel.purge(
                    limit=None,
                    check=lambda m: not m.pinned and m.author != self.bot.user
                )
                logging.info("Cleared %d messages from channel", len(deleted))
            except discord.Forbidden:
                await interaction.followup.send(
                    "Missing permissions to clear channel.", ephemeral=True)

        # Set channel for voting
        config.channel = cha

        # Send presend messages if requested
        if presend:
            for key in submitted:
                await cha.send(key)

        # Send vote message
        mention_text = role.mention if role else ""
        vote_msg = await cha.send(f"{mention_text} Vote is starting!", embed=embed)

        # Add reactions
        for i, _ in enumerate(submission_list):
            await vote_msg.add_reaction(EMOJI_ALPHABET[i])

        # Pin vote message
        await vote_msg.pin()
        config.lastvote = vote_msg

        # Set vote as running
        config.vote_running = True

        # Set auto-close if specified
        if polltime > 0:
            close_time = discord.utils.utcnow() + datetime.timedelta(hours=polltime)
            config.closetime = close_time
            logging.info("Vote will auto-close at %s", close_time)

        await interaction.followup.send(f"Vote started in {cha.mention}!", ephemeral=True)

    @app_commands.command(name="endvote", description="Ends vote.")
    @app_commands.guild_only()
    @has_admin_role()
    @vote_running()
    async def endvote(self, interaction: discord.Interaction) -> None:
        """This command is used to end a vote."""
        await endvote_internal(interaction)

    @app_commands.command(name="autoclose", description="Sets the autoclose time.")
    @has_admin_role()
    @app_commands.describe(
        hours="Hours to close after.",
        minutes="Minutes to close after."
    )
    async def autoclose(self, interaction: discord.Interaction,
                     hours: int = 0, minutes: int = 0) -> None:
        """This command is used to set the autoclose time."""
        config = Config(self.bot)

        if hours == 0 and minutes == 0:
            config.closetime = None
            await interaction.response.send_message("Autoclose disabled.", ephemeral=True)
        else:
            total_minutes = hours * 60 + minutes
            close_time = discord.utils.utcnow() + datetime.timedelta(minutes=total_minutes)
            config.closetime = close_time
            close_time_str = close_time.strftime('%Y-%m-%d %H:%M:%S')
            await interaction.response.send_message(
                f"Vote will close in {hours}h {minutes}m at {close_time_str} UTC.",
                ephemeral=True
            )


async def endvote_internal(interaction: Union[discord.Interaction, str]) -> None:
    """This command is used to end a vote."""

    # Get bot instance from interaction or use a global reference
    if isinstance(interaction, str):
        # This is called from timer - we need bot reference
        return  # For now, skip internal timer calls

    bot = interaction.client
    config = Config(bot)

    channel = config.channel
    vote: Dict[str, int] = {}

    if not config.vote_running:
        logging.info("Vote already closed.")
        return

    # Prevent double closing
    cog = bot.get_cog('VotingCommands')
    if cog.double_clause:
        logging.info("Double closing attempted.")
        return
    cog.double_clause = True

    if interaction != "INTERNAL":
        oper = interaction.user
        await interaction.response.defer(thinking=True, ephemeral=True)
    else:
        oper = "system"

    await channel.send("Ending vote...", delete_after=60)
    votemsg = await config.lastvote

    if votemsg is None:
        if interaction != "INTERNAL":
            await interaction.followup.send("Vote message not found.", ephemeral=True)
        return

    await votemsg.unpin()
    await channel.send("Gathering votes...")

    # Simple vote counting - count reactions
    submitted = parse_votemsg(votemsg)

    for reaction in votemsg.reactions:
        if reaction.emoji in EMOJI_ALPHABET:
            emoji_index = EMOJI_ALPHABET.index(reaction.emoji)
            if emoji_index < len(submitted):
                vote[reaction.emoji] = reaction.count - 1  # Subtract bot's reaction

    if not vote:
        await channel.send("No votes found!")
        config.vote_running = False
        config.closetime = None
        cog.double_clause = False
        return

    # Find winner
    max_votes = max(vote.values())
    winners = [emoji for emoji, count in vote.items() if count == max_votes]

    if len(winners) > 1:
        # Handle tie
        winner_emoji = choice(winners)
        await channel.send(f"We have a tie! Randomly selecting winner: {winner_emoji}")
    else:
        winner_emoji = winners[0]

    # Get winner URL
    winner_index = EMOJI_ALPHABET.index(winner_emoji)
    winner_url = submitted[winner_index][0] if winner_index < len(submitted) else "Unknown"

    # Create results embed
    result_embed = discord.Embed(
        title="Vote Results",
        description=f"🏆 Winner: {winner_emoji} with {max_votes} votes\n{winner_url}",
        color=0xffd700,
    )

    # Add vote breakdown
    vote_breakdown = "\n".join([f"{emoji}: {count} votes" for emoji, count in sorted(vote.items())])
    result_embed.add_field(name="Vote Breakdown", value=vote_breakdown, inline=False)

    win_msg = await channel.send(embed=result_embed)
    await win_msg.pin()

    # Update config
    config.lastwin = win_msg
    config.lastvote = None
    config.vote_running = False
    config.closetime = None
    cog.double_clause = False

    if interaction != "INTERNAL":
        await interaction.followup.send("Vote ended successfully!", ephemeral=True)

    logging.info("Vote ended by %s. Winner: %s", oper, winner_url)


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(VotingCommands(bot))
