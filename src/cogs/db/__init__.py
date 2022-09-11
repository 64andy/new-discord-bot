from sqlalchemy import create_engine as __create_engine
from sqlalchemy.orm import sessionmaker as __sessionmaker


engine = __create_engine("sqlite:///my_lovely.db")
Session = __sessionmaker(engine)
