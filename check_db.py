"""Step 1 check: creates the users table and prints which database you're on."""
from sqlalchemy import inspect

from database import DATABASE_URL, engine
from models import Base

Base.metadata.create_all(engine)
print("Connected to:", DATABASE_URL.split("@")[-1])  # hides the password
print("Tables:", inspect(engine).get_table_names())
