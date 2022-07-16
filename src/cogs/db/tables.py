from sqlalchemy import Column, String, BigInteger, __version__ as v
from sqlalchemy.ext.declarative import declarative_base
from os import getcwd

MAX_PREFIX_LEN  = 20


Base = declarative_base()


class BotOptions(Base):
    """
    This table should only have a single row... I should just use json yeah
    """
    __tablename__   = "Options"
    id              = Column(BigInteger, primary_key=True)
    game_name       = Column(String, comment="The Discord presence game name")
    
    def __repr__(self):
        return f"BotOptions({self.id=}, {self.game_name=})"


class GuildSettings(Base):
    __tablename__   = "Guild"
    id              = Column(BigInteger, primary_key=True, comment="ID of server")
    prefix          = Column(String(MAX_PREFIX_LEN), default="alexa")
    archive_channel = Column(BigInteger, comment="ID of channel")
    def __repr__(self):
        return f"GuildSettings({self.id=}, {self.prefix=}, {self.archive_channel=})"
    
    
if __name__ == "__main__":
    from . import engine
    print("sqlalchemy version:", v)
    print(getcwd())
    if input(
    "Y/N: Update schema? >").lower() == "y":
        Base.metadata.create_all(engine)
        input("Completed. Hit enter to exit")