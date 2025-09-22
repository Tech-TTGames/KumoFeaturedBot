"""Voting utilities for parsing and processing votes."""
import discord


def parse_votemsg(votemsg: discord.Message) -> list[tuple[str, str]]:
    """Parses the previous vote messages into a list of all submissions."""
    all_competitors = []
    if votemsg.embeds and votemsg.embeds[0].title == "Vote":
        parse_pending = votemsg.embeds[0].description
    else:
        parse_pending = votemsg.content

    if not parse_pending:
        return all_competitors

    for line in parse_pending.splitlines():
        if " - " in line:
            clean = line.split(" - ", 2)
            uri = clean[1].lstrip("<").rstrip(">")
            submitees = clean[2] if 2 < len(clean) else ""
            all_competitors.append((uri, submitees))
    return all_competitors


def plurls(items: int) -> str:
    """Provide count of items, get s or nothing."""
    if items == 0:
        return ""
    return "s"
