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

class ServerData(Base):
    __tablename__   = "Server"
    id              = Column(BigInteger, primary_key=True, comment="ID of server")
    prefix          = Column(String(MAX_PREFIX_LEN), default="alexa")
    archive_channel = Column(BigInteger, comment="ID of channel")
    
    
if __name__ == "__main__":
    print("sqlalchemy version:", v)
    print(getcwd())
    if input(
    "Y/N: Update schema? >").lower() == "y":
        Base.metadata.create_all(engine)
        input("Completed. Hit enter to exit")