"""Custom checks for Discord commands."""
import discord
from discord import app_commands


def vote_running():
    """Returns whether a vote is running."""

    async def predicate(interaction: discord.Interaction):
        """The predicate for the check."""
        config = interaction.client.config
        if not config.vote_running or interaction.user == interaction.client.user:
            raise app_commands.CheckFailure("No vote is currently running.")
        return True

    return app_commands.check(predicate)


async def predicate_isowner(interaction: discord.Interaction):
    """The predicate for the is_owner check."""
    app_info = await interaction.client.application_info()
    if app_info.team:
        # Bot is owned by a team
        is_team_owner = interaction.user.id in [member.id for member in app_info.team.members]
    else:
        # Bot is owned by a single user
        is_team_owner = interaction.user.id == app_info.owner.id

    if not is_team_owner:
        raise app_commands.CheckFailure("You are not the owner of this bot.")
    return True


def is_owner():
    """Returns whether the user is the owner of the bot using Discord.py app owner data."""
    return app_commands.check(predicate_isowner)


async def predicate_isadmin(interaction: discord.Interaction):
    """The predicate for the is_admin check."""
    bypass = await predicate_isowner(interaction)
    if bypass:
        return True
    # Check if user has Administrator permission
    if interaction.guild:
        member = interaction.guild.get_member(interaction.user.id)
        if member and member.guild_permissions.administrator:
            return True
    raise app_commands.CheckFailure("You don't have permission to use this command.")


def is_admin():
    """Check if user has Administrator permission, or is owner."""
    return app_commands.check(predicate_isadmin)


def is_operator():
    """Check if user has Operator role, is admin or owner."""

    async def predicate(interaction: discord.Interaction):
        # Check if user has the configured admin role
        bypass = predicate_isadmin(interaction)
        if bypass:
            return True
        config = interaction.client.config
        try:
            if hasattr(config, "role_id") and config.role_id:
                member = (interaction.guild.get_member(interaction.user.id) if interaction.guild else None)
                if member and any(role.id == config.role_id for role in member.roles):
                    return True
        except (ValueError, AttributeError):
            pass

    return app_commands.check(predicate)
