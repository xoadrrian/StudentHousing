from sqlalchemy import inspect

from database import DATABASE_URL, engine

print("Connected to:", DATABASE_URL.split("@")[-1])
print("Tables:", inspect(engine).get_table_names())
