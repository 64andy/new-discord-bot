from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine("sqlite:///my_lovely.db")
Session = sessionmaker(engine)

if __name__ == "__main__":
    from tables import Base
    Base.metadata.create_all(engine)