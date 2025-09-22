"""Voting utilities for parsing and processing votes."""
import discord


def parse_votemsg(votemsg: discord.Message) -> list[tuple[str, str]]:
    """Parses the previous vote messages into a list of all submissions."""
    all_competitors = []
    if votemsg.embeds and votemsg.embeds[0].description and votemsg.embeds[
            0].title == "Vote":
        for line in votemsg.embeds[0].description.splitlines():
            if " - " in line:
                clean = line.split(" - ")
                uri = clean[1].lstrip("<").rstrip(">")
                # We just take the actual string of this
                submitees = clean[2] if 2 < len(clean) else ""
                all_competitors.append((uri, submitees))
    else:
        for line in votemsg.content.splitlines():
            if " - " in line:
                clean = line.split(" - ")
                uri = clean[1].lstrip("<").rstrip(">")
                # We just take the actual string of this
                submitees = clean[2] if 2 < len(clean) else ""
                all_competitors.append((uri, submitees))
    return all_competitors
