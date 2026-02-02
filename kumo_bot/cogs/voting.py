"""Voting commands for the bot."""
import asyncio
import datetime
import logging
import re
from random import choice, shuffle, randint
from typing import Dict, Union, List

import discord
from discord import app_commands
from discord.ext import commands

from kumo_bot.config import constants
from kumo_bot.utils import checks, voting, downloaders


class VotingCommands(commands.Cog):
    """Voting commands cog."""

    def __init__(self, bot):
        self.bot = bot
        self.double_clause = False

    @app_commands.command(name="startvote", description="Starts a vote.")
    @app_commands.guild_only()
    @checks.is_operator()
    @app_commands.describe(
        cha="The channel to start the vote in.",
        polltime="Time to close the vote after in hours.",
        cap="Max submissions to vote on.",
        clear="Clear channel after vote? (True/False)",
        presend="Send message links before vote? (True/False)",
        allow_duplicates="Allow multiple submissions from the same user? (True/False)",
    )
    @app_commands.rename(cha="channel")
    async def startvote(self,
                        interaction: discord.Interaction,
                        cha: discord.TextChannel,
                        polltime: int = 0,
                        cap: int = 8,
                        clear: bool = False,
                        presend: bool = False,
                        allow_duplicates: bool = False) -> None:
        """This command is used to start a vote."""
        config = self.bot.config

        invalid_channel_types = (discord.StageChannel, discord.ForumChannel, discord.CategoryChannel)

        submitted = {}
        submitted_old = []
        submitees = []

        intchannel = interaction.channel
        if isinstance(intchannel, invalid_channel_types) or intchannel is None:
            raise app_commands.AppCommandError("This channel is not a text channel.")

        winmsg = await config.lastwin
        if winmsg is not None:
            await winmsg.unpin()

        votemsg = await config.lastvote
        if votemsg is not None:
            await votemsg.unpin()

        if votemsg is not None:
            submitted_old = voting.parse_votemsg(votemsg)

        role = config.mention
        await interaction.response.defer(thinking=True, ephemeral=True)
        async with intchannel.typing():
            async for message in intchannel.history(limit=None, oldest_first=True):
                if message.content.startswith("https://") and (message.author not in submitees or allow_duplicates):
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
            await interaction.followup.send("No submissions found in the last 31 days.", ephemeral=True)
            return

        submitted = list(submitted.items())
        shuffle(submitted)
        if len(submitted) > cap:
            submitted = submitted[:cap]
        if len(submitted) > len(constants.EMOJI_ALPHABET):
            await interaction.followup.send("Too many submissions! Please reduce the cap.", ephemeral=True)
            return

        message_lines = []
        for key, value in submitted:
            emoji = constants.EMOJI_ALPHABET[len(message_lines)]
            submitters = ", ".join(value)
            submission_text = f"{emoji} - <{key}> - {submitters}"
            message_lines.append(submission_text)
            if presend:
                await cha.send(f"{emoji}: {key} Submitted by: {submitters}")

        message_lines.append("Vote by reacting with the corresponding letter emoji.")
        if polltime:
            timed = discord.utils.utcnow() + datetime.timedelta(hours=polltime)
            message_lines.append(f"Vote will close <t:{round(timed.timestamp())}:R>.")

        embed = discord.Embed(
            title="Vote",
            description="\n".join(message_lines),
            color=0x00ff00,
        )

        # Clear channel if requested
        if clear and intchannel:
            try:
                deleted = await intchannel.purge(limit=None, check=lambda m: not m.pinned and m.author != self.bot.user)
                logging.info("Cleared %d messages from channel", len(deleted))
            except discord.Forbidden:
                logging.info("Failed to clear some messages from channel.")
            explanation = False
            async for message in intchannel.history(limit=3, oldest_first=True):
                if message.author == self.bot.user and message.embeds:
                    explanation = True
                    break
            if not explanation:
                embd = discord.Embed(
                    title="Suggestion Collection",
                    description="Send suggestions here!\nSuggestions are accepted until the beginning of the vote.",
                    color=0xb9f9fc,
                ).add_field(name="One suggestion per user!",
                            value="If you suggest more than one thing, all of the extra suggestions will be ignored."
                           ).add_field(name="All suggestions must come with a link at the beginning of the message!",
                                       value="They will be otherwise ignored as 'non-suggestions'.").set_footer(
                                           text="This thread is not for conversation.")
                await intchannel.send(embed=embd)

        # Set channel for voting
        config.channel = cha
        # Send vote message
        mention_text = role.mention if role else ""
        vote_msg = await cha.send(f"{mention_text} Vote is starting!",
                                  embed=embed,
                                  allowed_mentions=discord.AllowedMentions(users=False, everyone=False))
        # Add reactions
        for i, _ in enumerate(submitted):
            await vote_msg.add_reaction(constants.EMOJI_ALPHABET[i])

        # Pin vote message
        await vote_msg.pin()
        config.lastvote = vote_msg

        # Set vote as running
        config.vote_running = True

        # Set auto-close if specified
        if polltime > 0:
            config.closetime = timed
            logging.info("Vote will close at %s", str(timed))

            await interaction.followup.send(f"Vote started in {cha.mention}!", ephemeral=True)

            # Wait for the timer and then close
            await discord.utils.sleep_until(timed)
            logging.info("Closing vote in %s due to poll-time end.", str(cha))
            await self.endvote_internal("INTERNAL")
        else:
            await interaction.followup.send(f"Vote started in {cha.mention}!", ephemeral=True)

    @app_commands.command(name="endvote", description="Ends vote.")
    @app_commands.guild_only()
    @checks.is_operator()
    @checks.vote_running()
    async def endvote(self, interaction: discord.Interaction) -> None:
        """This command is used to end a vote."""
        await self.endvote_internal(interaction)

    @app_commands.command(name="autoclose", description="Sets the autoclose time.")
    @checks.is_operator()
    @checks.vote_running()
    @app_commands.describe(hours="Hours to close after.", minutes="Minutes to close after.")
    async def autoclose(self, interaction: discord.Interaction, hours: int = 0, minutes: int = 0) -> None:
        """This command is used to set the autoclose time."""
        config = self.bot.config

        if hours == 0 and minutes == 0:
            config.closetime = None
            await interaction.response.send_message("Attempting Autoclose Abort. Reboot to enforce.", ephemeral=True)
        else:
            if hours == 99:
                hours = randint(1, 72)
            if minutes > 59:
                minutes = randint(0, 59)
            timed = discord.utils.utcnow() + datetime.timedelta(hours=hours, minutes=minutes)
            config.closetime = timed

            await interaction.response.send_message(
                f"Vote will close <t:{str(round(config.closetime.timestamp()))}:R>.",
                ephemeral=True,
            )
            await discord.utils.sleep_until(timed)
            if not config.vote_running:
                logging.info("Vote already closed.")
                return
            await self.endvote_internal("INTERNAL")

    async def endvote_internal(self, interaction: Union[discord.Interaction, str]) -> None:
        """This command is used to end a vote with advanced features."""
        config = self.bot.config
        channel = config.channel
        vote: Dict[str, int] = {}
        usrlib: Dict[Union[discord.Member, discord.User], Union[int, float]] = {}
        disregarded: List[Union[discord.Member, discord.User]] = []
        disreg_votes: Dict[str, List[int]] = {}
        disreg_total: int = 0
        disreg_reqs: int = 15

        if not config.vote_running:
            logging.info("Vote already closed.")
            return

        # Prevent double closing
        if self.double_clause:
            logging.info("Double closing attempted.")
            return
        self.double_clause = True

        if config.vote_count_mode == 2:
            disreg_reqs = randint(10, 25)
        role = config.mention

        if interaction != "INTERNAL":
            oper = interaction.user
            await interaction.response.defer(thinking=True, ephemeral=True)
        else:
            oper = "system"

        await channel.send("Ending vote...", delete_after=60)
        votemsg = await config.lastvote

        if votemsg is None:
            raise app_commands.errors.AppCommandError("Vote message not found.")

        await votemsg.unpin()
        await channel.send("Gathering votes and applying fraud protection... (This may take a while)")

        async with channel.typing():
            submitted = voting.parse_votemsg(votemsg)

            start_time = votemsg.created_at
            if config.vote_count_mode == 1:
                logging.info("Using legacy message count mode.")
                start_time = discord.utils.utcnow()
            timed = start_time - datetime.timedelta(days=31)

            async for message in channel.history(after=timed, before=start_time, oldest_first=True, limit=None):
                if message.author not in usrlib:
                    usrlib[message.author] = 1
                else:
                    usrlib[message.author] += 1

            for key in constants.EMOJI_ALPHABET[:len(submitted)]:
                vote[key] = 0
                disreg_votes[key] = [0] * disreg_reqs

            # Enhanced vote counting with fraud protection
            for reaction in votemsg.reactions:
                if reaction.emoji in constants.EMOJI_ALPHABET[:len(submitted)]:
                    async for user in reaction.users():
                        if user == self.bot.user:
                            continue
                        if user.id in config.blacklist:
                            if user not in disregarded:
                                disregarded.append(user)
                            disreg_total += 1
                            continue
                        if user not in usrlib:
                            if user not in disregarded:
                                disregarded.append(user)
                            disreg_total += 1
                            continue

                        user_messages = usrlib[user]
                        if user_messages >= disreg_reqs:
                            vote[reaction.emoji] += 1
                        else:
                            if user not in disregarded:
                                disregarded.append(user)
                            disreg_votes[reaction.emoji][int(user_messages)] += 1
                            disreg_total += 1

        # Create results message
        msg_text = "This week's featured results are:\n"
        for i in range(len(vote)):
            msg_text += (f"{constants.EMOJI_ALPHABET[i]} - {vote[constants.EMOJI_ALPHABET[i]]} vote" +
                         f"{voting.plurls(vote[constants.EMOJI_ALPHABET[i]])}\n")

        results_embed = discord.Embed(title="RESULTS", description=msg_text, color=0x00FF00)
        await channel.send(embed=results_embed, reference=votemsg, mention_author=False)

        # Advanced tie resolution
        max_vote = max(vote.values())
        win_candidates = [k for k, v in vote.items() if v == max_vote]
        win_id = None
        tiebreak = 0

        # Advanced tie-breaking logic
        if len(win_candidates) > 1:
            for i in range(disreg_reqs - 1, -1, -1):
                lvl_vals = {c: disreg_votes[c][i] for c in win_candidates}
                cap = max(lvl_vals.values())
                for c, v in lvl_vals.items():
                    if v != cap:
                        win_candidates.remove(c)
                if len(win_candidates) == 1:
                    win_id = win_candidates[0]
                    tiebreak = 1
                    break
        else:
            win_id = win_candidates[0]

        # If still tied, random selection
        if win_id is None:
            tiebreak = 2
            win_id = choice(win_candidates)

        # Debug tie functionality for manual override
        if tiebreak and config.debug_tie:
            await channel.send("Stand by for Stalemate Resolution.")
            owner = self.bot.application.owner
            dm_channel = owner.dm_channel
            if dm_channel is None:
                dm_channel = await owner.create_dm()

            def dm_from_user(msg):
                return msg.channel == dm_channel and msg.author == owner

            tiebreak_confirm = discord.Embed(
                title="Stalemate Resolution Associate Response Required",
                color=discord.Color.red(),
            )
            tiebreak_confirm.add_field(name="Current Resolution", value=f"Winner: {win_id}\nMethod: {tiebreak}")
            candidate_data = []
            for candidate in win_candidates:
                base_str = f"{candidate} - DISREG VOTES:"
                for level, data in enumerate(disreg_votes[candidate]):
                    base_str += f"\n{level} - {data}"
                candidate_data.append(base_str)
            tiebreak_confirm.add_field(name="Candidates", value="\n".join(candidate_data))
            tiebreak_confirm.set_footer(text="Awaiting Stalemate Resolution Associate Response...")
            await dm_channel.send(embed=tiebreak_confirm)

            resolution = await self.bot.wait_for("message", check=dm_from_user)
            if resolution.content.lower() == "override":
                await dm_channel.send("Overriding Resolution. Please enter override winner")
                while True:
                    winner_override = await self.bot.wait_for("message", check=dm_from_user)
                    if winner_override.content.strip() in win_candidates:
                        win_id = winner_override.content.strip()
                        break
                    await dm_channel.send("Please respond with solely an emoji from win candidates.")
                await dm_channel.send("Thank You. Please enter stalemate solution (1, 2 or 3).")
                while True:
                    tiebreak_inf = await self.bot.wait_for("message", check=dm_from_user)
                    if tiebreak_inf.content.isnumeric():
                        if int(tiebreak_inf.content) in [1, 2, 3]:
                            tiebreak = int(tiebreak_inf.content)
                            break
                    await dm_channel.send("Please respond with solely a number between 1 and 3.")
            else:
                await dm_channel.send("Automatic Stalemate Resolution Confirmed.")
            await dm_channel.send("Thank You. This concludes the Stalemate Resolution.")

        # Fraud protection report
        if disregarded:
            fraport_text = (f"Total disregarded votes: {disreg_total}\n" +
                            f"Total disregarded users: {len(disregarded)}\n" + "Disregarded users:\n")
            for usr in disregarded:
                if usr in usrlib:
                    fraport_text += f"{usr.mention} - {usrlib[usr]} message{voting.plurls(usrlib[usr])}\n"
                elif usr.id in config.blacklist:
                    fraport_text += f"{usr.mention} - Blacklisted\n"
                else:
                    fraport_text += f"{usr.mention} - 0 messages\n"
            fraprot = discord.Embed(title="Fraud Protection Log", description=fraport_text, color=0xFC0303)
            fraprot.set_footer(text="This is a public safety announcement.")
        else:
            fraprot = discord.Embed(
                title="Fraud Protection Log",
                description="No users were disregarded.",
                color=0x00FFF7,
            )
            fraprot.set_footer(text="Thank you for your cooperation.")

        await channel.send(embed=fraprot)

        # Try to download winner's file
        try:
            downed = await asyncio.wait_for(downloaders.fetch_download(
                submitted[constants.EMOJI_ALPHABET.index(win_id)][0]),
                                            timeout=1200)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.warning("Failed to download winner. %s Error Stack:\n", e, exc_info=True)
            downed = None

        # Create winner announcement
        message_txt = (f"{role.mention} This week's featured results are in!\n" +
                       f"The winner is {submitted[constants.EMOJI_ALPHABET.index(win_id)][0]}" +
                       f" submitted by {submitted[constants.EMOJI_ALPHABET.index(win_id)][1]}" +
                       f" with {vote[win_id]} vote{voting.plurls(vote[win_id])}!")

        if tiebreak == 1:
            message_txt += "\n\n(Stalemate Resolution Rule 1: Highest disregarded votes)"
        elif tiebreak == 2:
            message_txt += "\n\n(Stalemate Resolution Rule 2: Random)"
        elif tiebreak == 3:
            message_txt += "\n\n(Stalemate Resolution Rule 3: Stalemate Resolution Associate)"

        if downed is None:
            message_txt += "\n\nThe winner's epub could not be downloaded."
            message = await channel.send(message_txt)
        else:
            message = await channel.send(message_txt, file=downed)

        await message.add_reaction("🎉")
        await message.pin()

        # Update configuration
        config.lastwin = message
        config.vote_running = False
        config.closetime = None
        self.double_clause = False

        if interaction != "INTERNAL":
            await interaction.followup.send("Vote ended.", ephemeral=True)

        self.double_clause = False
        logging.info("Vote ended by %s. Winner: %s", oper, submitted[constants.EMOJI_ALPHABET.index(win_id)][0])


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(VotingCommands(bot))
