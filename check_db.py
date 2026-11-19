from sqlalchemy import inspect

from database import DATABASE_URL, engine
from models import Base

Base.metadata.create_all(engine)
print("Connected to:", DATABASE_URL.split("@")[-1])
print("Tables:", inspect(engine).get_table_names())
