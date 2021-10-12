import discord

from . import session
from .tables import ServerData, BotOptions


def register_guild(guild: discord.Guild):
    """
    Gives the guild a database entry.
    """
    session.add(ServerData(id=guild.id))
    session.commit()

def get_guild(guild: discord.Guild) -> ServerData:
    return session.query(ServerData).filter_by(id=guild.id).first()

def get_command_prefix(guild: discord.Guild) -> str:
    prefix = session.query(ServerData.prefix).filter_by(id=guild.id).first()
    if prefix is None:                          # Server's not in DB
        register_server(guild)
        prefix = ServerData.prefix.default.arg
    return prefix

