import sqlalchemy as _sql
from sqlalchemy.ext.declarative import declarative_base as __declarative_base

MAX_COMMAND_PREFIX_LEN  = 20


Base = __declarative_base()


class BotOptions(Base):
    """
    This table should only have a single row... I should just use json yeah
    """
    __tablename__   = "Options"
    id: int         = _sql.Column(_sql.BigInteger, primary_key=True)
    game_name: str  = _sql.Column(_sql.String, comment="The Discord presence game name")
    
    def __repr__(self):
        return f"BotOptions({self.id=}, {self.game_name=})"


class GuildSettings(Base):
    __tablename__        = "Guild"
    id: int              = _sql.Column(_sql.BigInteger, primary_key=True, comment="ID of server")
    prefix: str          = _sql.Column(_sql.String(MAX_COMMAND_PREFIX_LEN), default="alexa")
    archive_channel: int = _sql.Column(_sql.BigInteger, comment="ID of channel")
    def __repr__(self):
        return f"GuildSettings({self.id=}, {self.prefix=}, {self.archive_channel=})"
