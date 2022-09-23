from typing import Optional
import discord
from sqlalchemy import select, update

from . import Session, engine
from .tables import GuildSettings, BotOptions, Base


def init_database():
    Base.metadata.create_all(engine)


def get_guild_settings(guild: discord.Guild) -> GuildSettings:
    """
    Returns the database entry on a given server's settings.

    If the server isn't registered in the database, it'll be added
    """
    stmt = select(GuildSettings).filter_by(id=guild.id)
    with Session() as session:
        data = session.execute(stmt).scalar()
        if data is None:
            register_guild(guild)
            data = session.execute(stmt).scalar()
        return data


def register_guild(guild: discord.Guild):
    """
    Gives the guild a database entry.
    """
    with Session() as session:
        session.add(GuildSettings(id=guild.id))
        session.commit()


def get_command_prefix(guild: discord.Guild) -> str:
    guild = get_guild_settings(guild)
    return guild.prefix


def set_archive_channel(guild: int, channel: Optional[int]):
    if isinstance(guild, discord.Guild):
        guild = guild.id
    if isinstance(channel, discord.TextChannel):
        channel = channel.id
    stmt = (
        update(GuildSettings)
        .where(GuildSettings.id == guild)
        .values(archive_channel=channel)
    )
    with Session() as session:
        session.execute(stmt)
        session.commit()


def get_archive_channel(guild: discord.Guild) -> int:
    settings = get_guild_settings(guild)
    return settings.archive_channel
